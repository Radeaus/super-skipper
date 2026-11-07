"""The sidebar page: its registration and the API it uses."""

from __future__ import annotations

import asyncio

from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.super_skipper.const import (
    CONF_ACTION,
    CONF_KEYWORDS,
    CONF_MAX_CONSECUTIVE,
    CONF_NAME,
    CONF_PLAYERS,
    CONF_RETURN_AFTER_MINUTES,
    CONF_STATION,
    DOMAIN,
    PANEL_URL_PATH,
)

from .conftest import PLAYER, advance, make_entry, play, rule, setup_entry


async def _next_event(client, msg_id: int, limit: int = 50):
    """The next event of a subscription (timeouts do not work with frozen time)."""
    for _ in range(limit):
        msg = await client.receive_json()
        if msg["id"] == msg_id and msg["type"] == "event":
            return msg["event"]
    raise AssertionError("no event")


async def _result(client, limit: int = 50):
    """The next result message, skipping subscription events."""
    for _ in range(limit):
        msg = await client.receive_json()
        if msg["type"] == "result":
            return msg
    raise AssertionError("no result")


async def test_panel_added_and_removed(hass: HomeAssistant) -> None:
    """The page is in the sidebar while the integration exists."""
    assert await async_setup_component(hass, "frontend", {})
    entry = await setup_entry(hass, make_entry())
    panels = hass.data[frontend.DATA_PANELS]
    panel = panels[PANEL_URL_PATH]
    assert panel.require_admin
    assert "super-skipper-panel.js?v=" in panel.config["_panel_custom"]["module_url"]

    # Reloading keeps the same panel.
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.data[frontend.DATA_PANELS][PANEL_URL_PATH] is panel

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert PANEL_URL_PATH not in hass.data[frontend.DATA_PANELS]


async def test_no_panel_without_frontend(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry())
    assert PANEL_URL_PATH not in hass.data.get(frontend.DATA_PANELS, {})
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()


async def test_not_configured(hass: HomeAssistant, hass_ws_client) -> None:
    """Without an entry the page says so, and the commands refuse."""
    assert await async_setup_component(hass, DOMAIN, {})
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/subscribe"})
    msg = await client.receive_json()
    assert msg["success"]
    assert (await _next_event(client, msg["id"])) == {"configured": False}

    await client.send_json_auto_id({"type": f"{DOMAIN}/save_rule", "data": rule()})
    assert (await _result(client))["error"]["code"] == "not_configured"
    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/save_options",
            "options": {
                "snooze_minutes": 5,
                "cooldown_seconds": 1,
                "confirm_seconds": 1,
            },
        }
    )
    assert (await _result(client))["error"]["code"] == "not_configured"
    await client.send_json_auto_id({"type": f"{DOMAIN}/snooze"})
    assert (await _result(client))["error"]["code"] == "not_loaded"
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/delete_rule", "subentry_id": "nope"}
    )
    assert (await _result(client))["error"]["code"] == "not_found"


async def test_manage_rules_from_panel(
    hass: HomeAssistant, hass_ws_client, freezer
) -> None:
    """Create, change, toggle, snooze and delete through the API."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    play(hass, title="Hello", artist="Adele")
    entry = await setup_entry(hass, make_entry())
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": f"{DOMAIN}/subscribe"})
    msg = await client.receive_json()
    assert msg["success"]
    sub_id = msg["id"]
    state = await _next_event(client, sub_id)
    assert state["configured"] and state["loaded"]
    assert state["rules"] == []
    assert state["options"]["snooze_minutes"] == 60

    # Validation errors come back as a result, per field.
    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/save_rule",
            "data": rule(**{CONF_NAME: " ", CONF_KEYWORDS: [], CONF_PLAYERS: []}),
        }
    )
    msg = await _result(client)
    assert msg["success"]
    assert msg["result"]["errors"] == {
        "name": "name_required",
        "keywords": "keywords_required",
        "players": "players_required",
    }
    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/save_rule",
            "data": rule(
                **{
                    CONF_ACTION: "switch",
                    CONF_RETURN_AFTER_MINUTES: 5,
                    CONF_STATION: None,
                }
            ),
        }
    )
    msg = await _result(client)
    assert msg["result"]["errors"] == {
        "station": "station_required",
        "return_fallback_media": "fallback_required",
    }
    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/save_rule",
            "data": rule(**{"match_mode": "regex", CONF_KEYWORDS: ["[abba"]}),
        }
    )
    msg = await _result(client)
    assert msg["result"]["errors"] == {"match_mode": "invalid_regex"}
    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/save_rule",
            "data": rule(conditions=[{"condition": "state", "entity_id": "x.y"}]),
        }
    )
    msg = await _result(client)
    assert msg["result"]["errors"] == {"conditions": "invalid_conditions"}

    # A malformed payload is refused by the schema.
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/save_rule", "data": {"name": "x"}}
    )
    msg = await _result(client)
    assert msg["error"]["code"] == "invalid_format"

    # Create a rule.
    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/save_rule",
            "data": rule(**{CONF_MAX_CONSECUTIVE: 3, "hold_seconds": 99}),
        }
    )
    msg = await _result(client)
    assert msg["success"], msg
    subentry_id = msg["result"]["subentry_id"]
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is ConfigEntryState.LOADED
    assert entry.subentries[subentry_id].title == "No ABBA"
    assert "hold_seconds" not in entry.subentries[subentry_id].data  # cleaned

    # The subscription saw it (after the debounce), with the switch of the rule.
    await advance(hass, freezer, 1)
    state = await _next_event(client, sub_id)
    for _ in range(10):
        if state.get("rules") and state["rules"][0].get("switch_entity"):
            break
        state = await _next_event(client, sub_id)
    assert state["rules"][0]["title"] == "No ABBA"
    assert state["rules"][0]["enabled"] is True
    assert state["rules"][0]["switch_entity"] == "switch.no_abba_enabled"

    # It works.
    play(hass)
    await advance(hass, freezer, 2)
    assert len(skips) == 1

    # Turn it off through the API: the switch follows.
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/set_enabled", "subentry_id": subentry_id, "enabled": False}
    )
    assert (await _result(client))["success"]
    await hass.async_block_till_done()
    assert hass.states.get("switch.no_abba_enabled").state == "off"
    play(hass, title="Waterloo")
    await advance(hass, freezer, 6)
    assert len(skips) == 1
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/set_enabled", "subentry_id": subentry_id, "enabled": True}
    )
    assert (await _result(client))["success"]

    # Change it.
    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/save_rule",
            "subentry_id": subentry_id,
            "data": rule(
                **{CONF_NAME: "No ABBA at all", CONF_KEYWORDS: ["ABBA", "Waterloo"]}
            ),
        }
    )
    msg = await _result(client)
    assert msg["success"], msg
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.subentries[subentry_id].title == "No ABBA at all"
    assert entry.subentries[subentry_id].data["keywords"] == ["ABBA", "Waterloo"]

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/save_rule", "subentry_id": "nope", "data": rule()}
    )
    assert (await _result(client))["error"]["code"] == "not_found"

    # Snooze.
    await client.send_json_auto_id({"type": f"{DOMAIN}/snooze"})
    assert (await _result(client))["success"]
    assert entry.runtime_data.snooze.active
    await client.send_json_auto_id({"type": f"{DOMAIN}/unsnooze"})
    assert (await _result(client))["success"]
    assert not entry.runtime_data.snooze.active

    # Options.
    await client.send_json_auto_id(
        {
            "type": f"{DOMAIN}/save_options",
            "options": {
                "snooze_minutes": 15,
                "cooldown_seconds": 2,
                "confirm_seconds": 0.5,
            },
        }
    )
    assert (await _result(client))["success"]
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.options["snooze_minutes"] == 15
    assert entry.state is ConfigEntryState.LOADED

    # Delete.
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/delete_rule", "subentry_id": subentry_id}
    )
    assert (await _result(client))["success"]
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert not entry.subentries
    assert hass.states.get("switch.no_abba_enabled") is None

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/set_enabled", "subentry_id": subentry_id, "enabled": True}
    )
    assert (await _result(client))["error"]["code"] == "not_found"


async def test_set_enabled_without_switch(hass: HomeAssistant, hass_ws_client) -> None:
    """When the switch entity is missing the watcher is set directly."""
    entry = await setup_entry(hass, make_entry(rule()))
    subentry_id = next(iter(entry.subentries))
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    registry.async_remove("switch.no_abba_enabled")
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/set_enabled", "subentry_id": subentry_id, "enabled": False}
    )
    assert (await _result(client))["success"]
    assert entry.runtime_data.watchers[subentry_id].enabled is False


async def test_state_while_not_loaded(hass: HomeAssistant, hass_ws_client) -> None:
    """An unloaded entry still lists its rules."""
    entry = await setup_entry(hass, make_entry(rule()))
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/subscribe"})
    msg = await client.receive_json()
    state = await _next_event(client, msg["id"])
    assert state["loaded"] is False
    assert state["rules"][0]["enabled"] is True
    assert state["rules"][0]["last_match"] is None
    await client.send_json_auto_id({"type": f"{DOMAIN}/snooze"})
    assert (await _result(client))["error"]["code"] == "not_loaded"
    assert PLAYER in state["rules"][0]["data"]["players"]
