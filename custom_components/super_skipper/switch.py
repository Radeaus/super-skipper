"""The switch that turns a rule on or off."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import SuperSkipperConfigEntry
from .engine import RuleWatcher
from .entity import RuleEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SuperSkipperConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add an enabled switch for every rule."""
    for watcher in entry.runtime_data.watchers.values():
        async_add_entities(
            [RuleEnabledSwitch(watcher)], config_subentry_id=watcher.subentry_id
        )


class RuleEnabledSwitch(RuleEntity, SwitchEntity, RestoreEntity):
    """Whether the rule acts."""

    _attr_translation_key = "enabled"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, watcher: RuleWatcher) -> None:
        super().__init__(watcher, "enabled")

    async def async_added_to_hass(self) -> None:
        """Restore the last position of the switch."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state == STATE_OFF:
            self.watcher.async_set_enabled(False)

    @property
    def is_on(self) -> bool:
        return self.watcher.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.watcher.async_set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.watcher.async_set_enabled(False)
