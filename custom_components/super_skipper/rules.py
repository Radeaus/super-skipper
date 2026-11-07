"""The shape and the checks of a rule, shared by the config flow and the panel."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import condition
from homeassistant.helpers import config_validation as cv

from .const import (
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
    CONF_STATION,
    CONF_STATION_ACTIONS,
    DEFAULT_MATCH_FIELDS,
    MatchField,
    MatchMode,
    PresenceMode,
    RepeatMode,
    RuleAction,
)
from .matching import compile_keywords

# The keys each action stores, so changing the action drops the others.
ACTION_KEYS: dict[RuleAction, set[str]] = {
    RuleAction.SKIP: {CONF_MAX_CONSECUTIVE},
    RuleAction.SWITCH: {
        CONF_STATION,
        CONF_STATION_ACTIONS,
        CONF_RETURN_AFTER_MINUTES,
        CONF_RETURN_FALLBACK_MEDIA,
        CONF_RETURN_FALLBACK_ACTIONS,
        CONF_REPEAT_MODE,
        CONF_REPEAT_LIMIT,
    },
    RuleAction.MUTE: {CONF_HOLD_SECONDS, CONF_MAX_MUTE_MINUTES},
}
ACTION_KEYS[RuleAction.AUTO] = (
    ACTION_KEYS[RuleAction.SKIP] | ACTION_KEYS[RuleAction.SWITCH]
)

MEDIA_SCHEMA = vol.Schema(
    {
        vol.Optional("entity_id"): cv.string,
        vol.Required("media_content_id"): cv.string,
        vol.Required("media_content_type"): cv.string,
    },
    extra=vol.REMOVE_EXTRA,
)

_optional_media = vol.Any(None, MEDIA_SCHEMA)
_optional_actions = vol.Any(None, [dict])

RULE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_KEYWORDS): [cv.string],
        vol.Required(CONF_PLAYERS): [cv.string],
        vol.Required(CONF_ACTION): vol.In([action.value for action in RuleAction]),
        vol.Optional(CONF_MATCH_MODE, default=MatchMode.WHOLE_WORD.value): vol.In(
            [mode.value for mode in MatchMode]
        ),
        vol.Optional(
            CONF_MATCH_FIELDS, default=[field.value for field in DEFAULT_MATCH_FIELDS]
        ): [vol.In([field.value for field in MatchField])],
        vol.Optional(CONF_IGNORE_TEXTS, default=[]): [cv.string],
        vol.Optional(CONF_MAX_CONSECUTIVE): vol.Coerce(int),
        vol.Optional(CONF_STATION): _optional_media,
        vol.Optional(CONF_STATION_ACTIONS): _optional_actions,
        vol.Optional(CONF_RETURN_AFTER_MINUTES): vol.Coerce(float),
        vol.Optional(CONF_RETURN_FALLBACK_MEDIA): _optional_media,
        vol.Optional(CONF_RETURN_FALLBACK_ACTIONS): _optional_actions,
        vol.Optional(CONF_REPEAT_MODE): vol.In([mode.value for mode in RepeatMode]),
        vol.Optional(CONF_REPEAT_LIMIT): vol.Coerce(int),
        vol.Optional(CONF_HOLD_SECONDS): vol.Coerce(float),
        vol.Optional(CONF_MAX_MUTE_MINUTES): vol.Coerce(float),
        vol.Optional(CONF_PERSONS, default=[]): [cv.string],
        vol.Optional(CONF_PRESENCE_MODE, default=PresenceMode.ANY_HOME.value): vol.In(
            [mode.value for mode in PresenceMode]
        ),
        vol.Optional(CONF_CONDITIONS): vol.Any(None, [dict]),
    },
    extra=vol.REMOVE_EXTRA,
)


def players_without(
    hass: HomeAssistant, players: list[str], feature: MediaPlayerEntityFeature
) -> list[str]:
    """Return the names of known players that lack a feature."""
    missing = []
    for player in players:
        state = hass.states.get(player)
        if state is None:
            continue
        if not int(state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)) & feature:
            missing.append(state.name)
    return missing


def clean_rule(data: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only what the chosen action uses, and drop empty optional values."""
    action = RuleAction(data[CONF_ACTION])
    keep = ACTION_KEYS[action]
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if key not in keep and any(key in keys for keys in ACTION_KEYS.values()):
            continue
        if value is None and key in (
            CONF_STATION,
            CONF_STATION_ACTIONS,
            CONF_RETURN_FALLBACK_MEDIA,
            CONF_RETURN_FALLBACK_ACTIONS,
        ):
            continue
        cleaned[key] = value
    cleaned[CONF_CONDITIONS] = list(data.get(CONF_CONDITIONS) or [])
    return cleaned


async def async_validate_rule(
    hass: HomeAssistant, data: Mapping[str, Any]
) -> tuple[dict[str, str], dict[str, str]]:
    """Check a rule the way the wizard does.

    Returns the errors per field (or "base") and the placeholders for their texts.
    """
    errors: dict[str, str] = {}
    placeholders: dict[str, str] = {"players": ""}
    keywords = [keyword for keyword in data.get(CONF_KEYWORDS, []) if keyword.strip()]
    players = list(data.get(CONF_PLAYERS, []))
    if not str(data.get(CONF_NAME, "")).strip():
        errors[CONF_NAME] = "name_required"
    if not keywords:
        errors[CONF_KEYWORDS] = "keywords_required"
    if not players:
        errors[CONF_PLAYERS] = "players_required"
    try:
        compile_keywords(
            keywords, MatchMode(data.get(CONF_MATCH_MODE, MatchMode.WHOLE_WORD))
        )
    except re.error:
        errors[CONF_MATCH_MODE] = "invalid_regex"

    action = RuleAction(data[CONF_ACTION])
    if action is RuleAction.SKIP:
        if missing := players_without(
            hass, players, MediaPlayerEntityFeature.NEXT_TRACK
        ):
            errors[CONF_PLAYERS] = "players_cannot_skip"
            placeholders["players"] = ", ".join(missing)
    elif action in (RuleAction.SWITCH, RuleAction.AUTO):
        has_station = bool(data.get(CONF_STATION) or data.get(CONF_STATION_ACTIONS))
        if action is RuleAction.SWITCH and not has_station:
            errors[CONF_STATION] = "station_required"
        if (
            has_station
            and data.get(CONF_RETURN_AFTER_MINUTES)
            and not data.get(CONF_RETURN_FALLBACK_MEDIA)
            and not data.get(CONF_RETURN_FALLBACK_ACTIONS)
        ):
            errors[CONF_RETURN_FALLBACK_MEDIA] = "fallback_required"
        if (
            action is RuleAction.SWITCH
            and data.get(CONF_STATION)
            and (
                missing := players_without(
                    hass, players, MediaPlayerEntityFeature.PLAY_MEDIA
                )
            )
        ):
            errors[CONF_STATION] = "players_cannot_play_media"
            placeholders["players"] = ", ".join(missing)

    conditions = data.get(CONF_CONDITIONS) or []
    try:
        cv.CONDITIONS_SCHEMA(conditions)
        await condition.async_validate_conditions_config(hass, conditions)
    except (vol.Invalid, HomeAssistantError, KeyError):
        errors[CONF_CONDITIONS] = "invalid_conditions"
    return errors, placeholders
