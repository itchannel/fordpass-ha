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

    def __init__(self, coorditnator):
        super().__init__(device_id="fordpass_ignitionsw", name="Ignition Switch", coordinator=coordinator)

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
        if self.coordinator.data is None or self.coordinator.data["ignitionStatus"] is None:
            return None
        if self.coordinator.data["ignitionStatus"]["value"] == "On":
            return True
        else:
            return False