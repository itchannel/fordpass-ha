"""The FordPass integration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_DISTANCE_UNIT,
    CONF_PRESSURE_UNIT,
    DEFAULT_DISTANCE_UNIT,
    DEFAULT_PRESSURE_UNIT,
    DOMAIN,
    MANUFACTURER,
    REGION,
    VEHICLE,
    VIN,
)
from .fordpass_new import Vehicle

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["lock", "sensor", "switch", "device_tracker"]

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=300)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the FordPass component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up FordPass from a config entry."""
    user = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    vin = entry.data[VIN]
    for ar in entry.data:
        _LOGGER.debug(ar)
    if REGION in entry.data.keys():
        _LOGGER.debug(entry.data[REGION])
        region = entry.data[REGION]
    else:
        _LOGGER.debug("CANT GET REGION")
        region = "North America & Canada"
    coordinator = FordPassDataUpdateCoordinator(hass, user, password, vin, region, 1)

    await coordinator.async_refresh()  # Get initial data

    if not entry.options:
        await async_update_options(hass, entry)

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    async def async_refresh_status_service(service_call):
        await hass.async_add_executor_job(
            refresh_status, hass, service_call, coordinator
        )

    async def async_clear_tokens_service(service_call):
        await hass.async_add_executor_job(clear_tokens, hass, service_call, coordinator)

    async def async_clear_tokens_service(service_call):
        await hass.async_add_executor_job(clear_tokens, hass, service_call, coordinator)

    hass.services.async_register(
        DOMAIN,
        "refresh_status",
        async_refresh_status_service,
    )
    hass.services.async_register(
        DOMAIN,
        "clear_tokens",
        async_clear_tokens_service,
    )

    return True


async def async_update_options(hass, config_entry):
    options = {
        CONF_PRESSURE_UNIT: config_entry.data.get(
            CONF_PRESSURE_UNIT, DEFAULT_PRESSURE_UNIT
        )
    }
    options[CONF_DISTANCE_UNIT] = config_entry.data.get(
        CONF_DISTANCE_UNIT, DEFAULT_DISTANCE_UNIT
    )
    hass.config_entries.async_update_entry(config_entry, options=options)


def refresh_status(hass, service, coordinator):
    _LOGGER.debug("Running Service")
    vin = service.data.get("vin", "")
    status = coordinator.vehicle.requestUpdate(vin)
    if status == 401:
        _LOGGER.debug("Invalid VIN")
    elif status == 200:
        _LOGGER.debug("Refresh Sent")


def clear_tokens(hass, service, coordinator):
    _LOGGER.debug("Clearing Tokens")
    coordinator.vehicle.clearToken()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class FordPassDataUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator to handle fetching new data about the vehicle."""

    def __init__(self, hass, user, password, vin, region, saveToken=False):
        """Initialize the coordinator and set up the Vehicle object."""
        self._hass = hass
        self.vin = vin
        configPath = hass.config.path("custom_components/fordpass/" + user + "_fordpass_token.txt")
        self.vehicle = Vehicle(user, password, vin, region, saveToken, configPath)
        self._available = True

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from FordPass."""
        try:
            async with async_timeout.timeout(30):
                data = await self._hass.async_add_executor_job(
                    self.vehicle.status  # Fetch new status
                )

                # Temporarily removed due to Ford backend API changes
                # data["guardstatus"] = await self._hass.async_add_executor_job(
                #    self.vehicle.guardStatus  # Fetch new status
                # )

                data["messages"] = await self._hass.async_add_executor_job(
                    self.vehicle.messages
                )

                # If data has now been fetched but was previously unavailable, log and reset
                if not self._available:
                    _LOGGER.info("Restored connection to FordPass for %s", self.vin)
                    self._available = True

                return data
        except Exception as ex:
            self._available = False  # Mark as unavailable
            _LOGGER.warning(str(ex))
            _LOGGER.warning("Error communicating with FordPass for %s", self.vin)
            raise UpdateFailed(
                f"Error communicating with FordPass for {self.vin}"
            ) from ex


class FordPassEntity(CoordinatorEntity):
    """Defines a base FordPass entity."""

    def __init__(
        self, *, device_id: str, name: str, coordinator: FordPassDataUpdateCoordinator
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._name = name

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the entity."""
        return f"{self.coordinator.vin}-{self._device_id}"

    @property
    def device_info(self):
        """Return device information about this device."""
        if self._device_id is None:
            return None

        return {
            "identifiers": {(DOMAIN, self.coordinator.vin)},
            "name": f"{VEHICLE} ({self.coordinator.vin})",
            "manufacturer": MANUFACTURER,
        }
