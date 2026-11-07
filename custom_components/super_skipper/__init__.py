"""The Super Skipper integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, SUBENTRY_TYPE_RULE
from .engine import RuleWatcher, Snooze

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = [Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]


@dataclass
class SuperSkipperData:
    """What a loaded entry keeps at runtime."""

    snooze: Snooze
    watchers: dict[str, RuleWatcher]


type SuperSkipperConfigEntry = ConfigEntry[SuperSkipperData]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Nothing to set up without an entry."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: SuperSkipperConfigEntry
) -> bool:
    """Start watching the players of every rule."""
    snooze = Snooze(hass, entry)
    watchers = {
        subentry.subentry_id: RuleWatcher(hass, entry, subentry, snooze)
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_TYPE_RULE
    }
    entry.runtime_data = SuperSkipperData(snooze=snooze, watchers=watchers)
    for watcher in watchers.values():
        await watcher.async_start()
        entry.async_on_unload(watcher.async_stop)
    entry.async_on_unload(snooze.async_stop)
    # Rules are added, changed and removed through the entry; reload to apply.
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_entry_updated(
    hass: HomeAssistant, entry: SuperSkipperConfigEntry
) -> None:
    hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: SuperSkipperConfigEntry
) -> bool:
    """Stop watching."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
