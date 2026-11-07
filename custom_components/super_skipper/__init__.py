"""The Super Skipper integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, SIGNAL_UPDATE
from .engine import RuleWatcher, Snooze, order_watchers
from .history import History
from .panel import async_register_panel, async_remove_panel
from .rules import ordered_rules
from .websocket import async_register_websocket_commands

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = [Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]


@dataclass
class SuperSkipperData:
    """What a loaded entry keeps at runtime."""

    snooze: Snooze
    watchers: dict[str, RuleWatcher]
    history: History
    # Set while the order of the rules is saved, which needs no reload.
    reordering: bool = field(default=False)


type SuperSkipperConfigEntry = ConfigEntry[SuperSkipperData]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the API the sidebar page talks to."""
    async_register_websocket_commands(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: SuperSkipperConfigEntry
) -> bool:
    """Start watching the players of every rule."""
    await async_register_panel(hass)
    snooze = Snooze(hass, entry)
    rules = ordered_rules(entry)
    history = History(hass)
    await history.async_load({subentry.subentry_id for subentry in rules})
    watchers = order_watchers(
        {
            subentry.subentry_id: RuleWatcher(hass, entry, subentry, snooze, history)
            for subentry in rules
        },
        [subentry.subentry_id for subentry in rules],
    )
    entry.runtime_data = SuperSkipperData(
        snooze=snooze, watchers=watchers, history=history
    )
    for watcher in watchers.values():
        await watcher.async_start()
        entry.async_on_unload(watcher.async_stop)
    entry.async_on_unload(snooze.async_stop)
    # Rules are added, changed and removed through the entry; reload to apply.
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_dispatcher_send(hass, SIGNAL_UPDATE)
    return True


async def _async_entry_updated(
    hass: HomeAssistant, entry: SuperSkipperConfigEntry
) -> None:
    data = entry.runtime_data
    if data.reordering:
        # Only the order changed; the watchers were put in order already.
        data.reordering = False
        return
    hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: SuperSkipperConfigEntry
) -> bool:
    """Stop watching."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_dispatcher_send(hass, SIGNAL_UPDATE)
    return unloaded


async def async_remove_entry(
    hass: HomeAssistant, entry: SuperSkipperConfigEntry
) -> None:
    """Take the page out of the sidebar."""
    async_remove_panel(hass)
