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
    snrarray = [ "odometer"]
    sensors = []
    for snr in snrarray:
        sensors.append(CarSensor(entry, snr))
    async_add_entities(sensors, False)





class CarSensor(FordPassEntity,Entity):
    def __init__(self, coordinator, sensor):
        self.sensor = sensor
        self.coordinator = coordinator
        self._device_id = sensor
        #TEST
        self._state = None

    async def async_update(self):
        await self.coordinator.async_request_refresh()
        #Sensor check 1
        if self.coordinator.data is None or self.coordinator.data[self.sensor] is None:
            return None
        self._state = self.coordinator.data[self.sensor]["value"]


    @property
    def name(self):
        return self.sensor
    
    @property
    def state(self):
        return self.state

    @property
    def device_id(self):
        return self.device_id


        

