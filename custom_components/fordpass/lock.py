"""Represents the primary lock of the vehicle."""
import logging

from homeassistant.components.lock import LockEntity

from . import FordPassEntity
from .const import DOMAIN, COORDINATOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add the lock from the config."""
    entry = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    locks = [Lock(entry)]
    async_add_entities(locks, False)


class Lock(FordPassEntity, LockEntity):
    """Defines the vehicle's lock."""

    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(
            device_id="fordpass_doorlock",
            name="fordpass_doorlock",
            coordinator=coordinator,
        )

    async def async_lock(self, **kwargs):
        """Locks the vehicle."""
        self._attr_is_locking = True
        self.async_write_ha_state()
        _LOGGER.debug("Locking %s", self.coordinator.vin)
        await self.coordinator.hass.async_add_executor_job(
            self.coordinator.vehicle.lock
        )
        await self.coordinator.async_request_refresh()
        self._attr_is_locking = False
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs):
        """Unlocks the vehicle."""
        self._attr_is_unlocking = True
        self.async_write_ha_state()
        _LOGGER.debug("Unlocking %s", self.coordinator.vin)
        await self.coordinator.hass.async_add_executor_job(
            self.coordinator.vehicle.unlock
        )
        await self.coordinator.async_request_refresh()
        self._attr_is_unlocking = False
        self.async_write_ha_state()

    @property
    def is_locked(self):
        """Determine if the lock is locked."""
        if self.coordinator.data is None or self.coordinator.data["lockStatus"] is None:
            return None
        return self.coordinator.data["lockStatus"]["value"] == "LOCKED"

    @property
    def icon(self):
        return "mdi:car-door-lock"
