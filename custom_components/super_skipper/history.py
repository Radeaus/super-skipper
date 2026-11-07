"""What the rules did, kept across restarts."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.history"
MAX_EVENTS = 30
SAVE_DELAY = 2


def _empty() -> dict[str, Any]:
    return {"count": 0, "last_match": None, "events": []}


class History:
    """The last match, the number of matches and the recent events of every rule."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._rules: dict[str, dict[str, Any]] = {}

    async def async_load(self, keep: set[str]) -> None:
        """Read the file, dropping rules that no longer exist."""
        data = await self._store.async_load() or {}
        self._rules = {
            rule_id: {**_empty(), **rule}
            for rule_id, rule in data.get("rules", {}).items()
            if rule_id in keep
        }
        if set(data.get("rules", {})) - keep:
            self._save()

    def rule(self, rule_id: str) -> dict[str, Any]:
        """What is known about one rule."""
        return self._rules.get(rule_id) or _empty()

    @callback
    def record_match(
        self, rule_id: str, player: str, description: str, action: str
    ) -> None:
        """Count a match and remember it as the last one."""
        rule = self._rules.setdefault(rule_id, _empty())
        rule["count"] += 1
        rule["last_match"] = {
            "player": player,
            "description": description,
            "action": action,
            "when": dt_util.utcnow().isoformat(),
        }
        self._save()

    @callback
    def record_event(self, rule_id: str, player: str, message: str) -> None:
        """Add a line to the activity of a rule."""
        rule = self._rules.setdefault(rule_id, _empty())
        rule["events"].append(
            {"when": dt_util.utcnow().isoformat(), "player": player, "message": message}
        )
        del rule["events"][:-MAX_EVENTS]
        self._save()

    @callback
    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"rules": self._rules}, SAVE_DELAY)
