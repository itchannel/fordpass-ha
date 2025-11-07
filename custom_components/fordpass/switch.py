"""Fordpass Switch Entities"""
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
        """Initialize"""
        self._device_id = "fordpass_" + switch
        self.switch = switch
        self.coordinator = coordinator
        self.data = coordinator.data["metrics"]
        # Required for HA 2022.7
        self.coordinator_context = object()

    async def async_turn_on(self, **kwargs):
        """Send request to vehicle on switch status on"""
        if self.switch == "ignition":
            await self.coordinator.vehicle.start()
            await self.coordinator.async_request_refresh()
        elif self.switch == "guardmode":
            await self.coordinator.vehicle.enable_guard()
            await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Send request to vehicle on switch status off"""
        if self.switch == "ignition":
            await self.coordinator.vehicle.stop()
            await self.coordinator.async_request_refresh()
        elif self.switch == "guardmode":
            await self.coordinator.vehicle.disable_guard()
            await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    @property
    def name(self):
        """return switch name"""
        return "fordpass_" + self.switch + "_Switch"

    @property
    def device_id(self):
        """return switch device id"""
        return self.device_id

    @property
    def is_on(self):
        """Check status of switch - considers both ignition and remote start status"""
        if self.switch == "ignition":
            if self.coordinator.data["metrics"] is None:
                return None
            
            # Check ignition status first
            ignition_status = None
            if (self.coordinator.data["metrics"].get("ignitionStatus") is not None):
                ignition_status = self.coordinator.data["metrics"]["ignitionStatus"]["value"]
                _LOGGER.debug(f"Ignition status: {ignition_status}")
            
            # Check remote start status using multiple methods
            remote_start_active = False
            
            # Method 1: Check countdown timer (most reliable)
            if "remoteStartCountdownTimer" in self.coordinator.data["metrics"]:
                countdown_timer = self.coordinator.data["metrics"]["remoteStartCountdownTimer"].get("value", 0)
                if countdown_timer and countdown_timer > 0:
                    remote_start_active = True
                    _LOGGER.debug(f"Remote start active via countdown timer: {countdown_timer}")
            
            
            # Vehicle is "on" if either ignition is on OR remote start is active
            if remote_start_active:
                _LOGGER.debug("Vehicle is ON via remote start")
                return True
            elif ignition_status in ["ON", "RUN", "START", "ACCESSORY"]:
                _LOGGER.debug("Vehicle is ON via ignition")
                return True
            elif ignition_status == "OFF":
                _LOGGER.debug("Vehicle is OFF")
                return False
            elif ignition_status is None:
                # If we can't get ignition status, fall back to remote start only
                _LOGGER.debug(f"No ignition status available, using remote start status: {remote_start_active}")
                return remote_start_active
            else:
                _LOGGER.warning(f"Unknown ignition status: {ignition_status}, using remote start status: {remote_start_active}")
                return remote_start_active  # Fall back to remote start status
                
        elif self.switch == "guardmode":
            # Guard mode logic remains the same
            guardstatus = self.coordinator.data.get("guardstatus", {})
            _LOGGER.debug(f"Guard status: {guardstatus}")
            
            if guardstatus.get("returnCode") == 200:
                if "session" in guardstatus and "gmStatus" in guardstatus["session"]:
                    if guardstatus["session"]["gmStatus"] == "enable":
                        return True
                    elif guardstatus["session"]["gmStatus"] == "disable":
                        return False
                return False
            return False
        
        return False

    @property
    def icon(self):
        """Return icon for switch"""
        return SWITCHES[self.switch]["icon"]