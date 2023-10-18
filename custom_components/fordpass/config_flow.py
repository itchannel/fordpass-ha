"""Config flow for FordPass integration."""
import logging

import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

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
    VIN,
    UPDATE_INTERVAL,
    UPDATE_INTERVAL_DEFAULT,
    DISTANCE_CONVERSION_DISABLED,
    DISTANCE_CONVERSION_DISABLED_DEFAULT
)
from .fordpass_new import Vehicle

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(REGION): vol.In(REGION_OPTIONS),
    }
)

VIN_SCHEME = vol.Schema(
    {
        vol.Required(VIN): str,
    }
)

@callback
def configured_vehicles(hass):
    """Return a list of configured vehicles"""
    return {
        entry.data[VIN]
        for entry in hass.config_entries.async_entries(DOMAIN)
    }


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    _LOGGER.debug(data[REGION])
    configPath = hass.config.path("custom_components/fordpass/" + data[CONF_USERNAME] + "_fordpass_token.txt")
    vehicle = Vehicle(data[CONF_USERNAME], data[CONF_PASSWORD], "", data[REGION], 1, configPath)

    try:
        result = await hass.async_add_executor_job(vehicle.auth)
    except Exception as ex:
        raise InvalidAuth from ex
    try:
        if result:
            vehicles = await(hass.async_add_executor_job(vehicle.vehicles))
    except Exception as ex:
        vehicles = None
    #except Exception as ex:
    #    raise InvalidAuth from ex

    #result3 = await hass.async_add_executor_job(vehicle.vehicles)
    # Disabled due to API change
    #vinfound = False
    #for car in result3:
    #    if car["vin"] == data[VIN]:
    #        vinfound = True
    #if vinfound == False:
    #    _LOGGER.debug("Vin not found in account, Is your VIN valid?")
    if not result:
        _LOGGER.error("Failed to authenticate with fordpass")
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return vehicles
    #return {"title": f"Vehicle ({data[VIN]})"}

async def validate_vin(hass: core.HomeAssistant, data):
    configPath = hass.config.path("custom_components/fordpass/" + data[CONF_USERNAME] + "_fordpass_token.txt")

    vehicle = Vehicle(data[CONF_USERNAME], data[CONF_PASSWORD], data[VIN], data[REGION], 1, configPath)
    test = await(hass.async_add_executor_job(vehicle.get_status))
    _LOGGER.debug("GOT SOMETHING BACK?")
    _LOGGER.debug(test)
    if test and test.status_code == 200:
        _LOGGER.debug("200 Code")
        return True
    if not test:
        raise InvalidVin
    return False

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FordPass."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                self.login_input = user_input
                if info is None:
                    self.vehicles = None
                    _LOGGER.debug("NO VEHICLES FOUND")
                else:
                    self.vehicles = info["userVehicles"]["vehicleDetails"]
                if self.vehicles is None:
                    return await self.async_step_vin()
                return await self.async_step_vehicle()
                #return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                print("EXCEPT")
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidVin:
                errors["base"] = "invalid_vin"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
    
    async def async_step_vin(self, user_input=None):
        """Handle manual VIN entry"""
        errors = {}
        if user_input is not None:
            _LOGGER.debug(self.login_input)
            _LOGGER.debug(user_input)
            data = self.login_input
            data["vin"] = user_input["vin"]
            vehicle = None
            try:
                vehicle = await validate_vin(self.hass, data)
            except InvalidVin:
                errors["base"] = "invalid_vin"
            except Exception:
                errors["base"] = "unknown"

            if vehicle :
                return self.async_create_entry(title=f"Vehicle ({user_input[VIN]})", data=self.login_input)

            # return self.async_create_entry(title=f"Enter VIN", data=self.login_input)
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
        avaliable_vehicles = {}
        for vehicle in self.vehicles:
            _LOGGER.debug(vehicle)
            if vehicle["VIN"] not in configured:
                if "nickName" in vehicle:
                    avaliable_vehicles[vehicle["VIN"]] = vehicle["nickName"] + f" ({vehicle['VIN']})"
                else:
                    avaliable_vehicles[vehicle["VIN"]] = f" ({vehicle['VIN']})"

        if not avaliable_vehicles:
            _LOGGER.debug("No Vehicles?")
            return self.async_abort(reason="no_vehicles")
        return self.async_show_form(
            step_id="vehicle",
            data_schema = vol.Schema(
            { vol.Required(VIN): vol.In(avaliable_vehicles)}
            ),
            errors = {}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        options = {
            vol.Optional(
                CONF_PRESSURE_UNIT,
                default=self.config_entry.options.get(
                    CONF_PRESSURE_UNIT, DEFAULT_PRESSURE_UNIT
                ),
            ): vol.In(PRESSURE_UNITS),
            vol.Optional(
                CONF_DISTANCE_UNIT,
                default=self.config_entry.options.get(
                    CONF_DISTANCE_UNIT, DEFAULT_DISTANCE_UNIT
                ),
            ): vol.In(DISTANCE_UNITS),
            vol.Optional(
                DISTANCE_CONVERSION_DISABLED,
                default = self.config_entry.options.get(
                    DISTANCE_CONVERSION_DISABLED, DISTANCE_CONVERSION_DISABLED_DEFAULT
                ),
            ): bool,
            vol.Optional(
                UPDATE_INTERVAL,
                default=self.config_entry.options.get(
                    UPDATE_INTERVAL, UPDATE_INTERVAL_DEFAULT
                ),
            ): int,
            
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidVin(exceptions.HomeAssistantError):
    """Error to indicate the wrong vin"""
