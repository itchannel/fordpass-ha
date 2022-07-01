import logging
from datetime import timedelta

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity

from . import FordPassEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Entities from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]

    # Added a check to see if the car supports GPS
    if entry.data["gps"] != None:
        async_add_entities([CarTracker(entry, "gps")], True)
    else:
        _LOGGER.debug("Vehicle does not support GPS")


class CarTracker(FordPassEntity, TrackerEntity):
    def __init__(self, coordinator, sensor):

        self._attr = {}
        self.sensor = sensor
        self.coordinator = coordinator
        self._device_id = "fordpass_tracker"
        # Required for HA 2022.7
        self.coordinator_context = object()

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
    def extra_state_attributes(self):
        return self.coordinator.data[self.sensor].items()

    @property
    def icon(self):
        return "mdi:radar"
