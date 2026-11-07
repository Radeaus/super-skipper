"""Base entities for Super Skipper."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, NAME
from .engine import RuleWatcher, Snooze


class RuleEntity(Entity):
    """An entity that belongs to one rule."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, watcher: RuleWatcher, key: str) -> None:
        self.watcher = watcher
        self._attr_unique_id = f"{watcher.subentry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, watcher.subentry_id)},
            name=watcher.name,
            manufacturer=NAME,
            model="Rule",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Follow the rule."""
        self.async_on_remove(self.watcher.async_add_listener(self.async_write_ha_state))


class SnoozeEntity(Entity):
    """An entity of the integration itself."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, snooze: Snooze, key: str) -> None:
        self.snooze = snooze
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer=NAME,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Follow the snooze."""
        self.async_on_remove(self.snooze.async_add_listener(self.async_write_ha_state))
