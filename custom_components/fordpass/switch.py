import logging

from homeassistant.components.switch import SwitchEntity

from . import FordPassEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Switch from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    switches = [Switch(entry)]
    async_add_entities(switches, False)


class Switch(FordPassEntity, SwitchEntity):
    """Define the Switch for turning ignition off/on"""

    def __init__(self, coordinator):
        super().__init__(
            device_id="fordpass_ignitionsw",
            name="fordpass_Ignition_Switch",
            coordinator=coordinator,
        )

    async def async_turn_on(self, **kwargs):
        await self.coordinator.hass.async_add_executor_job(
            self.coordinator.vehicle.start
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.hass.async_add_executor_job(
            self.coordinator.vehicle.stop
        )
        await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        """Determine if the vehicle is started."""
        if (
            self.coordinator.data is None
            or self.coordinator.data["remoteStartStatus"] is None
        ):
            return None
        return self.coordinator.data["remoteStartStatus"]["value"]

    @property
    def icon(self):
        return "mdi:key-star"

