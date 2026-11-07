"""Sensors that show what Super Skipper did."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SuperSkipperConfigEntry
from .engine import RuleWatcher, Snooze
from .entity import RuleEntity, SnoozeEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SuperSkipperConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a last-match sensor per rule and the snooze sensor."""
    for watcher in entry.runtime_data.watchers.values():
        async_add_entities(
            [RuleLastMatchSensor(watcher)], config_subentry_id=watcher.subentry_id
        )
    async_add_entities([SnoozedUntilSensor(entry, entry.runtime_data.snooze)])


class RuleLastMatchSensor(RuleEntity, SensorEntity):
    """The track the rule last acted on."""

    _attr_translation_key = "last_match"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, watcher: RuleWatcher) -> None:
        super().__init__(watcher, "last_match")

    @property
    def native_value(self) -> str | None:
        last = self.watcher.last_match
        return last.description if last else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        last = self.watcher.last_match
        return {
            "player": last.player if last else None,
            "action": str(last.action) if last else None,
            "matched_at": last.when.isoformat() if last else None,
            "matches": self.watcher.match_count,
        }


class SnoozedUntilSensor(SnoozeEntity, SensorEntity):
    """Until when the rules are paused."""

    _attr_translation_key = "snoozed_until"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: SuperSkipperConfigEntry, snooze: Snooze) -> None:
        super().__init__(entry, snooze, "snoozed_until")

    @property
    def native_value(self) -> datetime | None:
        return self.snooze.until
