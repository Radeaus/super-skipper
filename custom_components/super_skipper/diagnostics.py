"""Diagnostics for Super Skipper."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import SuperSkipperConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SuperSkipperConfigEntry
) -> dict[str, Any]:
    """Return the rules and what they last did."""
    data = entry.runtime_data
    rules = []
    for watcher in data.watchers.values():
        last = watcher.last_match
        rules.append(
            {
                "title": watcher.name,
                "data": dict(watcher.subentry.data),
                "enabled": watcher.enabled,
                "matches": watcher.match_count,
                "last_match": {
                    "player": last.player,
                    "description": last.description,
                    "action": str(last.action),
                    "when": last.when.isoformat(),
                }
                if last
                else None,
                "players": {
                    player: (
                        state.state if (state := hass.states.get(player)) else None
                    )
                    for player in watcher.players
                },
            }
        )
    return {
        "options": dict(entry.options),
        "snoozed_until": data.snooze.until.isoformat() if data.snooze.until else None,
        "rules": rules,
    }
