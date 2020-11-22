import logging
from datetime import timedelta

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity

from . import FordPassEntity
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([CarTracker(entry, "gps")], True)


class CarTracker(FordPassEntity, TrackerEntity):
    def __init__(self, coordinator, sensor):

        self._attr = {}
        self.sensor = sensor
        self.coordinator = coordinator
        self._device_id = "fordpass_tracker"

    @property
    def latitude(self):
        return float(self.coordinator.data[self.sensor]["latitude"])

    @property
    def longitude(self):
        return float(self.coordinator.data[self.sensor]["longitude"])

    @property
    def source_type(self):
        return SOURCE_TYPE_GPS

    @property
    def name(self):
        return "fordpass_tracker"

    @property
    def device_id(self):
        return self.device_id

    @property
    def device_state_attributes(self):
        return self.coordinator.data[self.sensor].items()
