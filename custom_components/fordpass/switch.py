import logging

from homeassistant.components.switch import SwitchEntity

from . import FordPassEntity
from .const import DOMAIN, SWITCHES, COORDINATOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the Switch from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    # switches = [Switch(entry)]
    # async_add_entities(switches, False)
    for key, value in SWITCHES.items():
        sw = Switch(entry, key, config_entry.options)
        # Only add guard entity if supported by the car
        if key == "guardmode":
            if "guardstatus" in sw.coordinator.data:
                if sw.coordinator.data["guardstatus"]["returnCode"] == 200:
                    async_add_entities([sw], False)
                else:
                    _LOGGER.debug("Guard mode not supported on this vehicle")
        else:
            async_add_entities([sw], False)


class Switch(FordPassEntity, SwitchEntity):
    """Define the Switch for turning ignition off/on"""

    def __init__(self, coordinator, switch, options):

        self._device_id = "fordpass_" + switch
        self.switch = switch
        self.coordinator = coordinator
        # Required for HA 2022.7
        self.coordinator_context = object()

    async def async_turn_on(self, **kwargs):
        if self.switch == "ignition":
            await self.coordinator.hass.async_add_executor_job(
                self.coordinator.vehicle.start
            )
            await self.coordinator.async_request_refresh()
        elif self.switch == "guardmode":
            await self.coordinator.hass.async_add_executor_job(
                self.coordinator.vehicle.enableGuard
            )
            await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if self.switch == "ignition":
            await self.coordinator.hass.async_add_executor_job(
                self.coordinator.vehicle.stop
            )
            await self.coordinator.async_request_refresh()
        elif self.switch == "guardmode":
            await self.coordinator.hass.async_add_executor_job(
                self.coordinator.vehicle.disableGuard
            )
            await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    @property
    def name(self):
        return "fordpass_" + self.switch + "_Switch"

    @property
    def device_id(self):
        return self.device_id

    @property
    def is_on(self):
        if self.switch == "ignition":
            """Determine if the vehicle is started."""
            if (
                self.coordinator.data is None
                or self.coordinator.data["remoteStartStatus"] is None
            ):
                return None
            return self.coordinator.data["remoteStartStatus"]["value"]
        elif self.switch == "guardmode":
            # Need to find the correct response for enabled vs disabled so this may be spotty at the moment
            guardstatus = self.coordinator.data["guardstatus"]

            _LOGGER.debug(guardstatus)
            if guardstatus["returnCode"] == 200:
                if "gmStatus" in guardstatus:
                    if guardstatus["session"]["gmStatus"] == "enable":
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False

    @property
    def icon(self):
        return SWITCHES[self.switch]["icon"]
