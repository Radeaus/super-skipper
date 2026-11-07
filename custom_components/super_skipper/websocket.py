"""The API the Super Skipper page uses."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import (
    SIGNAL_CONFIG_ENTRY_CHANGED,
    ConfigEntry,
    ConfigEntryChange,
    ConfigEntryState,
    ConfigSubentry,
)
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_call_later

from .const import (
    CONF_CONFIRM_SECONDS,
    CONF_COOLDOWN_SECONDS,
    CONF_NAME,
    CONF_RULE_ORDER,
    CONF_SNOOZE_MINUTES,
    DEFAULT_CONFIRM_SECONDS,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_SNOOZE_MINUTES,
    DOMAIN,
    SIGNAL_UPDATE,
    SUBENTRY_TYPE_RULE,
)
from .engine import order_watchers
from .rules import RULE_SCHEMA, async_validate_rule, clean_rule, ordered_rules

if TYPE_CHECKING:
    from . import SuperSkipperConfigEntry

UPDATE_DELAY = 0.2

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SNOOZE_MINUTES): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=1440)
        ),
        vol.Required(CONF_COOLDOWN_SECONDS): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=120)
        ),
        vol.Required(CONF_CONFIRM_SECONDS): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=30)
        ),
    }
)


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register every command."""
    for command in (
        ws_subscribe,
        ws_save_rule,
        ws_delete_rule,
        ws_reorder_rules,
        ws_set_enabled,
        ws_snooze,
        ws_unsnooze,
        ws_save_options,
    ):
        websocket_api.async_register_command(hass, command)


def _entry(hass: HomeAssistant) -> SuperSkipperConfigEntry | None:
    entries = hass.config_entries.async_entries(DOMAIN)
    return entries[0] if entries else None


def _loaded_entry(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> SuperSkipperConfigEntry | None:
    entry = _entry(hass)
    if entry is None or entry.state is not ConfigEntryState.LOADED:
        connection.send_error(msg["id"], "not_loaded", "Super Skipper is not loaded")
        return None
    return entry


def _subentry(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> tuple[ConfigEntry, ConfigSubentry] | None:
    entry = _entry(hass)
    subentry = entry.subentries.get(msg["subentry_id"]) if entry else None
    if (
        entry is None
        or subentry is None
        or subentry.subentry_type != SUBENTRY_TYPE_RULE
    ):
        connection.send_error(msg["id"], "not_found", "Unknown rule")
        return None
    return entry, subentry


@callback
def build_state(hass: HomeAssistant) -> dict[str, Any]:
    """Everything the page shows."""
    entry = _entry(hass)
    if entry is None:
        return {"configured": False}
    loaded = entry.state is ConfigEntryState.LOADED
    data = entry.runtime_data if loaded else None
    registry = er.async_get(hass)
    rules = []
    for subentry in ordered_rules(entry):
        watcher = data.watchers.get(subentry.subentry_id) if data else None
        last = watcher.last_match if watcher else None
        rules.append(
            {
                "id": subentry.subentry_id,
                "title": subentry.title,
                "data": dict(subentry.data),
                "enabled": watcher.enabled if watcher else True,
                "matches": watcher.match_count if watcher else 0,
                "last_match": last,
                "events": list(watcher.events[-20:]) if watcher else [],
                "switch_entity": registry.async_get_entity_id(
                    SWITCH_DOMAIN, DOMAIN, f"{subentry.subentry_id}_enabled"
                ),
            }
        )
    return {
        "configured": True,
        "loaded": loaded,
        "reason": entry.reason if not loaded else None,
        "options": {
            CONF_SNOOZE_MINUTES: entry.options.get(
                CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES
            ),
            CONF_COOLDOWN_SECONDS: entry.options.get(
                CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS
            ),
            CONF_CONFIRM_SECONDS: entry.options.get(
                CONF_CONFIRM_SECONDS, DEFAULT_CONFIRM_SECONDS
            ),
        },
        "snoozed_until": data.snooze.until.isoformat()
        if data and data.snooze.until
        else None,
        "rules": rules,
    }


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/subscribe"})
@websocket_api.require_admin
@callback
def ws_subscribe(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Send the state now and whenever it changes."""
    pending: Callable[[], None] | None = None

    @callback
    def send(_now: Any = None) -> None:
        nonlocal pending
        pending = None
        connection.send_message(
            websocket_api.event_message(msg["id"], build_state(hass))
        )

    @callback
    def schedule(*_args: Any) -> None:
        nonlocal pending
        if pending is None:
            pending = async_call_later(hass, UPDATE_DELAY, send)

    @callback
    def entry_changed(change: ConfigEntryChange, entry: ConfigEntry) -> None:
        if entry.domain == DOMAIN:
            schedule()

    unsubs = [
        async_dispatcher_connect(hass, SIGNAL_UPDATE, schedule),
        async_dispatcher_connect(hass, SIGNAL_CONFIG_ENTRY_CHANGED, entry_changed),
    ]

    @callback
    def unsubscribe() -> None:
        for unsub in unsubs:
            unsub()
        if pending is not None:
            pending()

    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"])
    send()


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_rule",
        vol.Optional("subentry_id"): cv.string,
        vol.Required("data"): RULE_SCHEMA,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save_rule(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Create a rule, or change one. Field errors come back as a result."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(
            msg["id"], "not_configured", "Super Skipper is not set up"
        )
        return
    errors, placeholders = await async_validate_rule(hass, msg["data"])
    if errors:
        connection.send_result(
            msg["id"], {"errors": errors, "placeholders": placeholders}
        )
        return
    data = clean_rule(msg["data"])
    title = data[CONF_NAME].strip()
    if subentry_id := msg.get("subentry_id"):
        subentry = entry.subentries.get(subentry_id)
        if subentry is None or subentry.subentry_type != SUBENTRY_TYPE_RULE:
            connection.send_error(msg["id"], "not_found", "Unknown rule")
            return
        hass.config_entries.async_update_subentry(
            entry, subentry, title=title, data=data
        )
    else:
        subentry = ConfigSubentry(
            data=data, subentry_type=SUBENTRY_TYPE_RULE, title=title, unique_id=None
        )
        hass.config_entries.async_add_subentry(entry, subentry)
    connection.send_result(msg["id"], {"subentry_id": subentry.subentry_id})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_rule",
        vol.Required("subentry_id"): cv.string,
    }
)
@websocket_api.require_admin
@callback
def ws_delete_rule(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Delete a rule."""
    if (found := _subentry(hass, connection, msg)) is None:
        return
    entry, subentry = found
    hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/reorder_rules",
        vol.Required("order"): [cv.string],
    }
)
@websocket_api.require_admin
@callback
def ws_reorder_rules(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Save the order in which the rules are checked; the first match acts."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(
            msg["id"], "not_configured", "Super Skipper is not set up"
        )
        return
    order: list[str] = msg["order"]
    rule_ids = [subentry.subentry_id for subentry in ordered_rules(entry)]
    if sorted(order) != sorted(rule_ids):
        connection.send_error(
            msg["id"], "invalid_order", "The order must list every rule once"
        )
        return
    if order == rule_ids:
        connection.send_result(msg["id"])
        return
    if entry.state is ConfigEntryState.LOADED:
        data = entry.runtime_data
        data.watchers = order_watchers(data.watchers, order)
        data.reordering = True
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_RULE_ORDER: order}
    )
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_enabled",
        vol.Required("subentry_id"): cv.string,
        vol.Required("enabled"): cv.boolean,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_set_enabled(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Turn a rule on or off, through its switch so the choice survives restarts."""
    if (found := _subentry(hass, connection, msg)) is None:
        return
    entry, subentry = found
    switch = er.async_get(hass).async_get_entity_id(
        SWITCH_DOMAIN, DOMAIN, f"{subentry.subentry_id}_enabled"
    )
    if switch and hass.states.get(switch) is not None:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON if msg["enabled"] else SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: switch},
            blocking=True,
        )
    elif entry.state is ConfigEntryState.LOADED and (
        watcher := entry.runtime_data.watchers.get(subentry.subentry_id)
    ):
        watcher.async_set_enabled(msg["enabled"])
    connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/snooze"})
@websocket_api.require_admin
@callback
def ws_snooze(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Pause every rule for the snooze time."""
    if (entry := _loaded_entry(hass, connection, msg)) is None:
        return
    entry.runtime_data.snooze.async_start()
    connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/unsnooze"})
@websocket_api.require_admin
@callback
def ws_unsnooze(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """End the pause."""
    if (entry := _loaded_entry(hass, connection, msg)) is None:
        return
    entry.runtime_data.snooze.async_stop()
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_options",
        vol.Required("options"): OPTIONS_SCHEMA,
    }
)
@websocket_api.require_admin
@callback
def ws_save_options(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Change the settings that apply to every rule."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(
            msg["id"], "not_configured", "Super Skipper is not set up"
        )
        return
    hass.config_entries.async_update_entry(entry, options=msg["options"])
    connection.send_result(msg["id"])
