import logging

from homeassistant.helpers.entity import Entity

from . import FordPassEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the lock from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    snrarray = [ "odometer"]
    sensors = []
    for snr in snrarray:
        sensors.append(CarSensor(entry, snr))
    async_add_entities(sensors, True)





class CarSensor(FordPassEntity,Entity):
    def __init__(self, coordinator, sensor):
        self.sensor = sensor
        self.coordinator = coordinator
        #TEST
        self._state = None

    async def async_update(self):
        await self.coordinator.async_request_refresh()#
        #Sensor check 1
        self.state = self.coordinator.data[self.sensor]["value"]


    @property
    def name(self):
        return self.sensor
    
    @property
    def state(self):
        return self.state


        

