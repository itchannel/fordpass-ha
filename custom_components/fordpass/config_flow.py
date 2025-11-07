"""Config flow for FordPass integration."""
import logging
import re
import random
import string
import hashlib
import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.storage import Store
from base64 import urlsafe_b64encode


from .const import (  # pylint:disable=unused-import
    CONF_DISTANCE_UNIT,
    CONF_PRESSURE_UNIT,
    DEFAULT_DISTANCE_UNIT,
    DEFAULT_PRESSURE_UNIT,
    DISTANCE_UNITS,
    DOMAIN,
    PRESSURE_UNITS,
    REGION,
    REGION_OPTIONS,
    REGIONS,
    VIN,
    UPDATE_INTERVAL,
    UPDATE_INTERVAL_DEFAULT,
    DISTANCE_CONVERSION_DISABLED,
    DISTANCE_CONVERSION_DISABLED_DEFAULT,
    STORAGE_VERSION,
    STORAGE_KEY_PREFIX,
)
from .fordpass_new import Vehicle

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        # vol.Required(CONF_PASSWORD): str,
        vol.Required(REGION): vol.In(REGION_OPTIONS),
    }
)

VIN_SCHEME = vol.Schema(
    {
        vol.Required(VIN, default=""): str,
    }
)

# Schema for adding vehicle to existing account
ADD_VEHICLE_SCHEMA = vol.Schema(
    {
        vol.Required("account"): str,
    }
)


@callback
def configured_vehicles(hass):
    """Return a list of configured vehicles"""
    return {
        entry.data[VIN]
        for entry in hass.config_entries.async_entries(DOMAIN)
    }


@callback
def configured_accounts(hass):
    """Return a dict of configured accounts and their entry data"""
    accounts = {}
    for entry in hass.config_entries.async_entries(DOMAIN):
        username = entry.data.get(CONF_USERNAME)
        if username:
            if username not in accounts:
                accounts[username] = []
            accounts[username].append({
                "entry_id": entry.entry_id,
                "vin": entry.data.get(VIN),
                "region": entry.data.get(REGION),
                "title": entry.title
            })
    return accounts


async def validate_token(hass: core.HomeAssistant, data):
    _LOGGER.debug(data)
    token_store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{data['username']}")
    vehicle = Vehicle(data["username"], "", "", data["region"], token_store, hass)
    results = await vehicle.generate_tokens(
        data["tokenstr"],
        data["code_verifier"]
    )

    if results:
        _LOGGER.debug("Getting Vehicles")
        vehicles = await vehicle.vehicles()
        _LOGGER.debug(vehicles)
        return vehicles


async def validate_existing_account(hass: core.HomeAssistant, username, region):
    """Validate existing account and get vehicles"""
    token_store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{username}")
    vehicle = Vehicle(username, "", "", region, token_store, hass)
    
    try:
        # Try to get vehicles with existing token
        vehicles = await vehicle.vehicles()
        if vehicles:
            return vehicles
    except Exception as ex:
        _LOGGER.debug(f"Failed to get vehicles with existing token: {ex}")
        raise CannotConnect


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    _LOGGER.debug(data[REGION])
    token_store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{data[CONF_USERNAME]}")
    vehicle = Vehicle(data[CONF_USERNAME], data[CONF_PASSWORD], "", data[REGION], token_store, hass)

    try:
        result = await vehicle.auth()
    except Exception as ex:
        raise InvalidAuth from ex
    try:
        if result:
            vehicles = await vehicle.vehicles()
    except Exception:
        vehicles = None

    if not result:
        _LOGGER.error("Failed to authenticate with fordpass")
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return vehicles


async def validate_vin(hass: core.HomeAssistant, data):
    token_store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{data[CONF_USERNAME]}")
    vehicle = Vehicle(data[CONF_USERNAME], data[CONF_PASSWORD], data[VIN], data[REGION], token_store, hass)
    test = await vehicle.status()
    _LOGGER.debug("GOT SOMETHING BACK?")
    _LOGGER.debug(test)
    if test:
        _LOGGER.debug("Got valid response")
        return True
    if not test:
        raise InvalidVin
    return False


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FordPass."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    region = None
    username = None
    login_input = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        # Check if there are existing accounts
        accounts = configured_accounts(self.hass)
        
        if user_input is not None:
            if user_input.get("setup_type") == "new_account":
                return await self.async_step_new_account()
            elif user_input.get("setup_type") == "add_vehicle":
                return await self.async_step_add_vehicle()
            else:
                # Legacy path - treat as new account
                try:
                    _LOGGER.debug(user_input[REGION])
                    self.region = user_input[REGION]
                    self.username = user_input[CONF_USERNAME]
                    return await self.async_step_token(None)
                except CannotConnect:
                    errors["base"] = "cannot_connect"

        # Show different options based on existing accounts
        if accounts:
            # Show option to add new account or add vehicle to existing account
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("setup_type"): vol.In({
                        "new_account": "Add New Account",
                        "add_vehicle": "Add Vehicle to Existing Account"
                    })
                }),
                errors=errors
            )
        else:
            # No existing accounts, go directly to new account setup
            return await self.async_step_new_account()

    async def async_step_new_account(self, user_input=None):
        """Handle setting up a new account."""
        errors = {}
        if user_input is not None:
            try:
                _LOGGER.debug(user_input[REGION])
                self.region = user_input[REGION]
                self.username = user_input[CONF_USERNAME]
                return await self.async_step_token(None)
            except CannotConnect:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="new_account", 
            data_schema=DATA_SCHEMA, 
            errors=errors,
            description_placeholders={"setup_type": "new account"}
        )

    async def async_step_add_vehicle(self, user_input=None):
        """Handle adding a vehicle to an existing account."""
        errors = {}
        accounts = configured_accounts(self.hass)
        
        if user_input is not None:
            selected_account = user_input["account"]
            # Get account details from first entry of this account
            account_entries = accounts[selected_account]
            first_entry = account_entries[0]
            
            self.username = selected_account
            self.region = first_entry["region"]
            
            try:
                # Validate the existing account can still access Ford API
                vehicles = await validate_existing_account(self.hass, selected_account, first_entry["region"])
                if vehicles and "userVehicles" in vehicles:
                    self.vehicles = vehicles["userVehicles"]["vehicleDetails"]
                    # Set login_input for compatibility with existing flow
                    self.login_input = {
                        "username": selected_account,
                        "region": first_entry["region"],
                        "password": ""  # Not needed for existing accounts
                    }
                    return await self.async_step_vehicle()
                else:
                    self.vehicles = None
                    return await self.async_step_vin()
                    
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as ex:
                _LOGGER.error(f"Error validating existing account: {ex}")
                errors["base"] = "unknown"

        # Create account selection options
        account_options = {}
        for username, entries in accounts.items():
            vehicle_count = len(entries)
            account_options[username] = f"{username} ({vehicle_count} vehicle{'s' if vehicle_count != 1 else ''})"

        return self.async_show_form(
            step_id="add_vehicle",
            data_schema=vol.Schema({
                vol.Required("account"): vol.In(account_options)
            }),
            errors=errors
        )

    async def async_step_token(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                token = user_input["tokenstr"]
                if self.check_token(token):
                    user_input["region"] = self.region
                    user_input["username"] = self.username
                    user_input["password"] = ""
                    user_input["code_verifier"] = self.login_input["code_verifier"]
                    _LOGGER.debug(user_input)
                    info = await validate_token(self.hass, user_input)
                    self.login_input = user_input
                    if info is None:
                        self.vehicles = None
                        _LOGGER.debug("NO VEHICLES FOUND")
                    else:
                        self.vehicles = info["userVehicles"]["vehicleDetails"]
                    if self.vehicles is None:
                        return await self.async_step_vin()
                    return await self.async_step_vehicle()

                else:
                    errors["base"] = "invalid_token"

            except CannotConnect:
                print("EXCEPT")
                errors["base"] = "cannot_connect"

        if self.region is not None:
            _LOGGER.debug("Region")
            _LOGGER.debug(self.region)
            return self.async_show_form(
                step_id="token", data_schema=vol.Schema(
                    {
                        vol.Optional(CONF_URL, default=self.generate_url(self.region)): str,
                        vol.Required("tokenstr"): str,
                    }
                ), errors=errors
            )

    def check_token(self, token):
        if "fordapp://userauthorized/?code=" in token:
            return True
        return False

    def generate_url(self, region):
        _LOGGER.debug(REGIONS[region])
        code1 = ''.join(random.choice(string.ascii_lowercase) for i in range(43))
        code_verifier = self.generate_hash(code1)
        self.login_input["code_verifier"] = code1

        url = f"{REGIONS[region]['locale_url']}/4566605f-43a7-400a-946e-89cc9fdb0bd7/B2C_1A_SignInSignUp_{REGIONS[region]['locale']}/oauth2/v2.0/authorize?redirect_uri=fordapp://userauthorized&response_type=code&max_age=3600&code_challenge={code_verifier}&code_challenge_method=S256&scope=%2009852200-05fd-41f6-8c21-d36d3497dc64%20openid&client_id=09852200-05fd-41f6-8c21-d36d3497dc64&ui_locales={REGIONS[region]['locale']}&language_code={REGIONS[region]['locale']}&country_code={REGIONS[region]['locale_short']}&ford_application_id={REGIONS[region]['region']}"
        return url

    def base64_url_encode(self, data):
        """Encode string to base64"""
        return urlsafe_b64encode(data).rstrip(b'=')

    def generate_hash(self, code):
        """Generate hash for login"""
        hashengine = hashlib.sha256()
        hashengine.update(code.encode('utf-8'))
        return self.base64_url_encode(hashengine.digest()).decode('utf-8')

    def validNumber(self, phone_number):
        pattern = re.compile(r'^([+]\d{2})?\d{10}$', re.IGNORECASE)
        pattern2 = re.compile(r'^([+]\d{2})?\d{9}$', re.IGNORECASE)
        return pattern.match(phone_number) is not None or pattern2.match(phone_number) is not None

    async def async_step_vin(self, user_input=None):
        """Handle manual VIN entry"""
        errors = {}
        if user_input is not None:
            _LOGGER.debug(self.login_input)
            _LOGGER.debug(user_input)
            data = self.login_input.copy()
            data["vin"] = user_input["vin"]
            vehicle = None
            try:
                vehicle = await validate_vin(self.hass, data)
            except InvalidVin:
                errors["base"] = "invalid_vin"
            except Exception:
                errors["base"] = "unknown"

            if vehicle:
                self.login_input[VIN] = user_input["vin"]
                return self.async_create_entry(
                    title=f"Vehicle ({user_input[VIN]})", 
                    data=self.login_input
                )

        _LOGGER.debug(self.login_input)
        return self.async_show_form(step_id="vin", data_schema=VIN_SCHEME, errors=errors)

    async def async_step_vehicle(self, user_input=None):
        if user_input is not None:
            _LOGGER.debug("Checking Vehicle is accessible")
            self.login_input[VIN] = user_input["vin"]
            _LOGGER.debug(self.login_input)
            return self.async_create_entry(title=f"Vehicle ({user_input[VIN]})", data=self.login_input)

        _LOGGER.debug(self.vehicles)

        configured = configured_vehicles(self.hass)
        _LOGGER.debug(configured)
        available_vehicles = {}
        for vehicle in self.vehicles:
            _LOGGER.debug(vehicle)
            if vehicle["VIN"] not in configured:
                if "nickName" in vehicle:
                    available_vehicles[vehicle["VIN"]] = vehicle["nickName"] + f" ({vehicle['VIN']})"
                else:
                    available_vehicles[vehicle["VIN"]] = f" ({vehicle['VIN']})"

        if not available_vehicles:
            _LOGGER.debug("No Available Vehicles")
            return self.async_abort(reason="no_vehicles")
        return self.async_show_form(
            step_id="vehicle",
            data_schema=vol.Schema(
                {vol.Required(VIN): vol.In(available_vehicles)}
            ),
            errors={}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        options = {
            vol.Optional(
                CONF_PRESSURE_UNIT,
                default=self._config_entry.options.get(
                    CONF_PRESSURE_UNIT, DEFAULT_PRESSURE_UNIT
                ),
            ): vol.In(PRESSURE_UNITS),
            vol.Optional(
                CONF_DISTANCE_UNIT,
                default=self._config_entry.options.get(
                    CONF_DISTANCE_UNIT, DEFAULT_DISTANCE_UNIT
                ),
            ): vol.In(DISTANCE_UNITS),
            vol.Optional(
                DISTANCE_CONVERSION_DISABLED,
                default=self._config_entry.options.get(
                    DISTANCE_CONVERSION_DISABLED, DISTANCE_CONVERSION_DISABLED_DEFAULT
                ),
            ): bool,
            vol.Optional(
                UPDATE_INTERVAL,
                default=self._config_entry.options.get(
                    UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT
                ),
            ): int,

        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidToken(exceptions.HomeAssistantError):
    """Error to indicate there is invalid token."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidVin(exceptions.HomeAssistantError):
    """Error to indicate the wrong vin"""


class InvalidMobile(exceptions.HomeAssistantError):
    """Error to indicate the wrong vin"""