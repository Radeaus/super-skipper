"""The snooze button."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SuperSkipperConfigEntry
from .engine import Snooze
from .entity import SnoozeEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SuperSkipperConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the snooze button."""
    async_add_entities([SnoozeButton(entry, entry.runtime_data.snooze)])


class SnoozeButton(SnoozeEntity, ButtonEntity):
    """Pause every rule for the configured time."""

    _attr_translation_key = "snooze"

    def __init__(self, entry: SuperSkipperConfigEntry, snooze: Snooze) -> None:
        super().__init__(entry, snooze, "snooze")

    async def async_press(self) -> None:
        self.snooze.async_start()
