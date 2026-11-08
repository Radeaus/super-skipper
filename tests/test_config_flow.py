"""The config, options and rule flows."""

from __future__ import annotations

from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.super_skipper.const import (
    CONF_ACTION,
    CONF_CONDITIONS,
    CONF_HOLD_SECONDS,
    CONF_IGNORE_TEXTS,
    CONF_KEYWORDS,
    CONF_MATCH_FIELDS,
    CONF_MATCH_MODE,
    CONF_MAX_CONSECUTIVE,
    CONF_MAX_MUTE_MINUTES,
    CONF_NAME,
    CONF_PERSONS,
    CONF_PLAYERS,
    CONF_PRESENCE_MODE,
    CONF_REPEAT_LIMIT,
    CONF_REPEAT_MODE,
    CONF_RETURN_AFTER_MINUTES,
    CONF_RETURN_FALLBACK_ACTIONS,
    CONF_RETURN_FALLBACK_MEDIA,
    CONF_SNOOZE_MINUTES,
    CONF_STATION,
    CONF_STATION_ACTIONS,
    DOMAIN,
    SUBENTRY_TYPE_RULE,
)

from .conftest import PLAYER, make_entry, play, rule, setup_entry

MEDIA = {
    "entity_id": PLAYER,
    "media_content_id": "media-source://radio_browser/1234",
    "media_content_type": "audio/mpeg",
    "metadata": {"title": "Radio 2"},
}
BASICS = {
    CONF_NAME: "No ABBA",
    CONF_KEYWORDS: ["ABBA"],
    CONF_PLAYERS: [PLAYER],
    CONF_ACTION: "skip",
    "matching": {
        CONF_MATCH_MODE: "whole_word",
        CONF_MATCH_FIELDS: ["title", "artist"],
        CONF_IGNORE_TEXTS: [],
    },
}


async def test_config_and_options_flow(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Super Skipper"
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is ConfigEntryState.LOADED

    # Only one entry.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_SNOOZE_MINUTES: 30, "cooldown_seconds": 3, "confirm_seconds": 2},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options[CONF_SNOOZE_MINUTES] == 30
    assert entry.state is ConfigEntryState.LOADED


async def _start(
    hass: HomeAssistant, entry, source: str = "user", subentry_id: str | None = None
):
    context = {"source": source}
    if subentry_id:
        context["subentry_id"] = subentry_id
    return await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_RULE), context=context
    )


async def test_create_skip_rule(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry())
    play(hass, features=MediaPlayerEntityFeature.PLAY)  # cannot skip
    result = await _start(hass, entry)
    assert result["step_id"] == "basics"

    # Validation
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**BASICS, CONF_KEYWORDS: [], CONF_PLAYERS: []}
    )
    assert result["errors"] == {
        CONF_KEYWORDS: "keywords_required",
        CONF_PLAYERS: "players_required",
    }
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            **BASICS,
            CONF_KEYWORDS: ["[abba"],
            "matching": {**BASICS["matching"], CONF_MATCH_MODE: "regex"},
        },
    )
    assert result["errors"] == {"base": "invalid_regex"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], BASICS
    )
    assert result["step_id"] == "skip"
    assert result["errors"] == {"base": "players_cannot_skip"}
    assert result["description_placeholders"] == {"players": "Living Room"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_MAX_CONSECUTIVE: 3}
    )
    assert result["step_id"] == "conditions"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_PERSONS: ["person.quinten"],
            CONF_PRESENCE_MODE: "any_home",
            "advanced": {
                CONF_CONDITIONS: [
                    {
                        "condition": "state",
                        "entity_id": "input_boolean.x",
                        "state": "on",
                    }
                ]
            },
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "No ABBA"
    assert result["data"] == {
        CONF_NAME: "No ABBA",
        CONF_KEYWORDS: ["ABBA"],
        CONF_PLAYERS: [PLAYER],
        CONF_ACTION: "skip",
        CONF_MATCH_MODE: "whole_word",
        CONF_MATCH_FIELDS: ["title", "artist"],
        CONF_IGNORE_TEXTS: [],
        CONF_MAX_CONSECUTIVE: 3,
        CONF_PERSONS: ["person.quinten"],
        CONF_PRESENCE_MODE: "any_home",
        # As entered: the normalized form cannot always be stored
        CONF_CONDITIONS: [
            {
                "condition": "state",
                "entity_id": "input_boolean.x",
                "state": "on",
            }
        ],
    }
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("switch.no_abba_enabled") is not None


async def test_create_switch_rule(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry())
    play(hass, features=MediaPlayerEntityFeature.PLAY)  # cannot play media
    result = await _start(hass, entry)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**BASICS, CONF_ACTION: "switch"}
    )
    assert result["step_id"] == "switch"
    base = {
        CONF_RETURN_AFTER_MINUTES: 5,
        CONF_REPEAT_MODE: "limited",
        CONF_REPEAT_LIMIT: 5,
    }

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], base
    )
    assert result["errors"] == {CONF_STATION: "station_required"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**base, CONF_STATION: MEDIA}
    )
    assert result["errors"] == {
        CONF_STATION: "players_cannot_play_media",
        CONF_RETURN_FALLBACK_MEDIA: "fallback_required",
    }
    assert result["description_placeholders"] == {"players": "Living Room"}

    actions = [{"action": "script.turn_on", "target": {"entity_id": "script.radio"}}]
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {**base, CONF_STATION_ACTIONS: actions, CONF_RETURN_FALLBACK_ACTIONS: actions},
    )
    assert result["step_id"] == "conditions"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_PERSONS: [], CONF_PRESENCE_MODE: "any_home", "advanced": {}},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_STATION_ACTIONS] == actions
    assert result["data"][CONF_CONDITIONS] == []
    assert CONF_STATION not in result["data"]


async def test_reconfigure_rule(hass: HomeAssistant) -> None:
    """Editing keeps the values, and changing the action drops the old settings."""
    entry = await setup_entry(hass, make_entry(rule(**{CONF_MAX_CONSECUTIVE: 3})))
    play(hass)
    subentry_id = next(iter(entry.subentries))
    result = await _start(hass, entry, "reconfigure", subentry_id)
    assert result["step_id"] == "basics"
    schema = result["data_schema"].schema
    suggested = {
        str(key): key.description.get("suggested_value")
        for key in schema
        if key.description
    }
    assert suggested[CONF_NAME] == "No ABBA"
    assert suggested[CONF_KEYWORDS] == ["ABBA"]

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**BASICS, CONF_NAME: "Mute ABBA", CONF_ACTION: "mute"}
    )
    assert result["step_id"] == "mute"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_HOLD_SECONDS: 15, CONF_MAX_MUTE_MINUTES: 5}
    )
    assert result["step_id"] == "conditions"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_PERSONS: [], CONF_PRESENCE_MODE: "any_home", "advanced": {}},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    subentry = entry.subentries[subentry_id]
    assert subentry.title == "Mute ABBA"
    assert subentry.data[CONF_HOLD_SECONDS] == 15
    assert CONF_MAX_CONSECUTIVE not in subentry.data
    assert entry.state is ConfigEntryState.LOADED
    # The entity ID stays; the device, and so the friendly name, follows the new title.
    state = hass.states.get("switch.no_abba_enabled")
    assert state is not None
    assert state.attributes["friendly_name"] == "Mute ABBA Enabled"


async def test_create_automatic_rule(hass: HomeAssistant) -> None:
    """The automatic action asks the skip and the switch settings; a station is optional."""
    entry = await setup_entry(hass, make_entry())
    result = await _start(hass, entry)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**BASICS, CONF_ACTION: "auto"}
    )
    assert result["step_id"] == "skip"
    assert result["errors"] == {}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_MAX_CONSECUTIVE: 4}
    )
    assert result["step_id"] == "switch"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_RETURN_AFTER_MINUTES: 5,
            CONF_REPEAT_MODE: "limited",
            CONF_REPEAT_LIMIT: 5,
        },
    )
    assert result["step_id"] == "conditions"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_PERSONS: [], CONF_PRESENCE_MODE: "any_home", "advanced": {}},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ACTION] == "auto"
    assert result["data"][CONF_MAX_CONSECUTIVE] == 4
    assert result["data"][CONF_RETURN_AFTER_MINUTES] == 5
    assert CONF_STATION not in result["data"]
