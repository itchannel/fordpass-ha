import logging

from homeassistant.helpers.entity import Entity

from . import FordPassEntity
from .const import DOMAIN
from datetime import timedelta


_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=300)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the lock from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    snrarray = [ "odometer", "fuel", "battery", "oil", "tirePressure", "gps"]
    sensors = []
    for snr in snrarray:
        async_add_entities([CarSensor(entry, snr)], True)





class CarSensor(FordPassEntity,Entity):
    def __init__(self, coordinator, sensor):
        self.sensor = sensor
        self._attr = {}
        self.coordinator = coordinator
        self._device_id = "fordpass_" + sensor
        self._state = None

    async def async_update(self):
        await self.coordinator.async_request_refresh()
        if self.coordinator.data is None or self.coordinator.data[self.sensor] is None:
            return None
            
        if self.sensor ==  "odometer":
            self._state = self.coordinator.data[self.sensor]["value"]
            self._measurement = "km"
            for key, value in self.coordinator.data[self.sensor].items():
                self._attr[key] = value
        elif self.sensor == "fuel":
            self._state = self.coordinator.data[self.sensor]["fuelLevel"]
            self._measurement = "L"
            for key, value in self.coordinator.data[self.sensor].items():
                self._attr[key] = value
        elif self.sensor == "battery":
            self._state = self.coordinator.data[self.sensor]["batteryHealth"]["value"]
        elif self.sensor == "oil":
            self._state = self.coordinator.data[self.sensor]["oilLife"]
            for key, value in self.coordinator.data[self.sensor].items():
                self._attr[key] = value
        elif self.sensor == "tirePressure":
            self._state = self.coordinator.data[self.sensor]["value"]
            for key, value in self.coordinator.data[self.sensor].items():
                self._attr[key] = value
        elif self.sensor == "gps":
            self._state = self.coordinator.data[self.sensor]["gpsState"]
            for key, value in self.coordinator.data[self.sensor].items():
                self._attr[key] = value
    

    @property
    def name(self):
        return "fordpass_" + self.sensor
    
    @property
    def state(self):
        return self._state

    @property
    def device_id(self):
        return self.device_id

    @property
    def device_state_attributes(self):
        return self._attr

    @property
    def unit_of_measurement(self):
        return self._measurement


        

