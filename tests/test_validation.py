"""User input that is odd, stored as JSON, or has to be cleaned up afterwards."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.json import json_bytes
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.super_skipper import DATA_HISTORY
from custom_components.super_skipper.const import (
    CONF_ACTION,
    CONF_CONDITIONS,
    CONF_HOLD_SECONDS,
    CONF_IGNORE_TEXTS,
    CONF_KEYWORDS,
    CONF_MATCH_MODE,
    CONF_MAX_CONSECUTIVE,
    CONF_MAX_MUTE_MINUTES,
    CONF_PERSONS,
    CONF_PLAYERS,
    CONF_PRESENCE_MODE,
    CONF_REPEAT_LIMIT,
    CONF_REPEAT_MODE,
    CONF_RETURN_AFTER_MINUTES,
    CONF_RETURN_FALLBACK_ACTIONS,
    CONF_STATION,
    CONF_STATION_ACTIONS,
    RuleAction,
)
from custom_components.super_skipper.history import STORAGE_KEY
from custom_components.super_skipper.rules import async_validate_rule, clean_rule

from .conftest import PLAYER, advance, make_entry, play, rule, setup_entry
from .test_config_flow import BASICS, _start

MEDIA = {"media_content_id": "http://radio/1", "media_content_type": "music"}
GOOD_ACTIONS = [{"action": "script.turn_on", "target": {"entity_id": "script.x"}}]
BAD_ACTIONS = [{"not_an_action": True}]
TEMPLATE_CONDITION = {
    "condition": "template",
    "value_template": "{{ is_state('input_boolean.x', 'on') }}",
}


@pytest.mark.parametrize("blank", ["", "   "])
async def test_blank_keyword_matches_nothing(
    hass: HomeAssistant, freezer, blank: str
) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(hass, make_entry(rule(**{CONF_KEYWORDS: ["ABBA", blank]})))
    play(hass, title="Hello", artist="Adele")
    await advance(hass, freezer, 3)
    assert not skips


def test_clean_rule_drops_blanks() -> None:
    cleaned = clean_rule(
        rule(
            **{
                CONF_KEYWORDS: ["ABBA", " "],
                CONF_IGNORE_TEXTS: ["", "Radio 2"],
                CONF_ACTION: RuleAction.SWITCH.value,
                CONF_STATION: None,
            }
        )
    )
    assert cleaned[CONF_KEYWORDS] == ["ABBA"]
    assert cleaned[CONF_IGNORE_TEXTS] == ["Radio 2"]
    assert CONF_STATION not in cleaned


async def test_flow_refuses_only_blank_keywords(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry())
    result = await _start(hass, entry)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**BASICS, CONF_KEYWORDS: [" "]}
    )
    assert result["errors"] == {CONF_KEYWORDS: "keywords_required"}


@pytest.mark.parametrize(("switch", "expected"), [("on", 1), ("off", 0)])
async def test_template_condition_from_storage(
    hass: HomeAssistant, freezer, switch: str, expected: int
) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    hass.states.async_set("input_boolean.x", switch)
    await setup_entry(hass, make_entry(rule(**{CONF_CONDITIONS: [TEMPLATE_CONDITION]})))
    play(hass)
    await advance(hass, freezer, 3)
    assert len(skips) == expected


async def test_shorthand_condition_from_storage(hass: HomeAssistant, freezer) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    hass.states.async_set("input_boolean.x", "on")
    shorthand = {
        "or": [{"condition": "state", "entity_id": "input_boolean.x", "state": "on"}]
    }
    await setup_entry(hass, make_entry(rule(**{CONF_CONDITIONS: [shorthand]})))
    play(hass)
    await advance(hass, freezer, 3)
    assert len(skips) == 1


def _switch_rule(actions: list[dict[str, Any]]) -> dict[str, Any]:
    return rule(
        **{
            CONF_ACTION: RuleAction.SWITCH.value,
            CONF_STATION_ACTIONS: actions,
            CONF_RETURN_AFTER_MINUTES: 0,
        }
    )


async def test_actions_get_the_variables(hass: HomeAssistant, freezer) -> None:
    calls = async_mock_service(hass, "test", "radio")
    actions = [
        {"action": "test.radio", "data": {"who": "{{ player }}", "why": "{{ rule }}"}}
    ]
    await setup_entry(hass, make_entry(_switch_rule(actions)))
    play(hass)
    await advance(hass, freezer, 3)
    assert calls[0].data == {"who": PLAYER, "why": "No ABBA"}


async def test_actions_in_the_old_form(hass: HomeAssistant, freezer) -> None:
    calls = async_mock_service(hass, "test", "radio")
    await setup_entry(hass, make_entry(_switch_rule([{"service": "test.radio"}])))
    play(hass)
    await advance(hass, freezer, 3)
    assert len(calls) == 1


async def test_invalid_actions_only_warn(
    hass: HomeAssistant, freezer, caplog: pytest.LogCaptureFixture
) -> None:
    await setup_entry(hass, make_entry(_switch_rule(BAD_ACTIONS)))
    play(hass)
    await advance(hass, freezer, 3)
    assert "the station actions failed" in caplog.text


async def test_home_assistant_stop_unmutes(hass: HomeAssistant, freezer) -> None:
    calls = async_mock_service(hass, "media_player", "volume_mute")
    entry = await setup_entry(
        hass,
        make_entry(
            rule(
                **{
                    CONF_ACTION: RuleAction.MUTE.value,
                    CONF_HOLD_SECONDS: 0,
                    CONF_MAX_MUTE_MINUTES: 5,
                }
            )
        ),
    )
    play(hass)
    await advance(hass, freezer, 3)
    assert [call.data["is_volume_muted"] for call in calls] == [True]

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    assert [call.data["is_volume_muted"] for call in calls] == [True, False]

    # The listener is gone by now; unloading must not trip over it.
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_automatic_action_unmutes_on_stop(hass: HomeAssistant, freezer) -> None:
    calls = async_mock_service(hass, "media_player", "volume_mute")
    await setup_entry(hass, make_entry(rule(**{CONF_ACTION: RuleAction.AUTO.value})))
    play(hass, media_content_id="x-rincon-mp3radio://stream")
    await advance(hass, freezer, 3)
    assert len(calls) == 1
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    assert calls[-1].data["is_volume_muted"] is False


async def test_removing_deletes_the_history(
    hass: HomeAssistant, freezer, hass_storage
) -> None:
    async_mock_service(hass, "media_player", "media_next_track")
    entry = await setup_entry(hass, make_entry(rule()))
    play(hass)
    await advance(hass, freezer, 6)
    assert STORAGE_KEY in hass_storage
    history = hass.data[DATA_HISTORY]

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert STORAGE_KEY not in hass_storage

    # Something that still finishes after the removal must not bring the file back.
    history.record_event("rule", PLAYER, "late")
    await advance(hass, freezer, 5)
    assert STORAGE_KEY not in hass_storage


async def test_removing_a_never_loaded_entry(hass_storage, hass: HomeAssistant) -> None:
    hass_storage[STORAGE_KEY] = {"version": 1, "data": {"rules": {}}}
    entry = make_entry(rule())
    entry.add_to_hass(hass)
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert STORAGE_KEY not in hass_storage


async def test_reload_keeps_a_write_still_pending(
    hass: HomeAssistant, freezer, hass_storage
) -> None:
    async_mock_service(hass, "media_player", "media_next_track")
    entry = await setup_entry(hass, make_entry(rule()))
    rule_id = next(iter(entry.subentries))
    play(hass)
    await advance(hass, freezer, 1.5)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await advance(hass, freezer, 5)
    assert hass_storage[STORAGE_KEY]["data"]["rules"][rule_id]["count"] == 1
    assert entry.runtime_data.watchers[rule_id].match_count == 1


async def test_very_long_title_fits_the_sensor(hass: HomeAssistant, freezer) -> None:
    async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(hass, make_entry(rule()))
    play(hass, title="x" * 300)
    await advance(hass, freezer, 3)
    state = hass.states.get("sensor.no_abba_last_match").state
    assert state.startswith("ABBA – x")
    assert len(state) == 255


async def test_flow_stores_conditions_as_json(hass: HomeAssistant) -> None:
    """Templates and time periods would make the config entries unsavable."""
    entry = await setup_entry(hass, make_entry())
    conditions = [
        TEMPLATE_CONDITION,
        {
            "condition": "state",
            "entity_id": "input_boolean.x",
            "state": "on",
            "for": {"minutes": 1},
        },
        {"condition": "time", "after": "10:00:00"},
    ]
    result = await _start(hass, entry)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], BASICS
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_MAX_CONSECUTIVE: 3}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_PERSONS: [],
            CONF_PRESENCE_MODE: "any_home",
            "advanced": {CONF_CONDITIONS: conditions},
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_CONDITIONS] == conditions
    json_bytes(result["data"])
    await hass.async_block_till_done()
    assert hass.states.get("switch.no_abba_enabled") is not None


async def test_flow_refuses_invalid_actions(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry())
    result = await _start(hass, entry)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**BASICS, CONF_ACTION: "switch"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_STATION_ACTIONS: BAD_ACTIONS,
            CONF_RETURN_AFTER_MINUTES: 5,
            CONF_RETURN_FALLBACK_ACTIONS: BAD_ACTIONS,
            CONF_REPEAT_MODE: "limited",
            CONF_REPEAT_LIMIT: 5,
        },
    )
    assert result["errors"] == {
        CONF_STATION_ACTIONS: "invalid_actions",
        CONF_RETURN_FALLBACK_ACTIONS: "invalid_actions",
    }


def _section_suggestions(result: Any, name: str) -> dict[str, Any]:
    return {
        str(key): key.description.get("suggested_value")
        for key in result["data_schema"].schema[name].schema.schema
        if key.description and key.description.get("suggested_value") is not None
    }


async def test_reconfigure_shows_matching_and_conditions(hass: HomeAssistant) -> None:
    entry = await setup_entry(
        hass,
        make_entry(
            rule(
                **{
                    CONF_MATCH_MODE: "regex",
                    CONF_CONDITIONS: [TEMPLATE_CONDITION],
                    CONF_MAX_CONSECUTIVE: 3,
                }
            )
        ),
    )
    result = await _start(hass, entry, "reconfigure", next(iter(entry.subentries)))
    assert _section_suggestions(result, "matching") == {CONF_MATCH_MODE: "regex"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], BASICS
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_MAX_CONSECUTIVE: 3}
    )
    assert result["step_id"] == "conditions"
    assert _section_suggestions(result, "advanced") == {
        CONF_CONDITIONS: [TEMPLATE_CONDITION]
    }


async def test_validate_rule_reports_each_problem(hass: HomeAssistant) -> None:
    play(hass, features=MediaPlayerEntityFeature.PLAY)

    # A player Home Assistant does not know (yet) is not held against the rule.
    errors, _ = await async_validate_rule(
        hass, rule(**{CONF_PLAYERS: ["media_player.not_yet_there"]})
    )
    assert errors == {}

    errors, placeholders = await async_validate_rule(hass, rule())
    assert errors == {CONF_PLAYERS: "players_cannot_skip"}
    assert placeholders == {"players": "Living Room"}

    errors, placeholders = await async_validate_rule(
        hass,
        rule(
            **{
                CONF_ACTION: RuleAction.SWITCH.value,
                CONF_STATION: MEDIA,
                CONF_RETURN_AFTER_MINUTES: 5,
            }
        ),
    )
    assert errors == {
        CONF_STATION: "players_cannot_play_media",
        "return_fallback_media": "fallback_required",
    }
    assert placeholders == {"players": "Living Room"}

    errors, _ = await async_validate_rule(
        hass,
        rule(
            **{
                CONF_ACTION: RuleAction.SWITCH.value,
                CONF_STATION_ACTIONS: BAD_ACTIONS,
                CONF_RETURN_AFTER_MINUTES: 0,
                CONF_RETURN_FALLBACK_ACTIONS: GOOD_ACTIONS,
            }
        ),
    )
    assert errors == {CONF_STATION_ACTIONS: "invalid_actions"}
