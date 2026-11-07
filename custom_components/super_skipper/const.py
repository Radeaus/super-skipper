"""Constants for Super Skipper."""

from __future__ import annotations

from enum import StrEnum

DOMAIN = "super_skipper"
NAME = "Super Skipper"

SUBENTRY_TYPE_RULE = "rule"

PANEL_URL_PATH = "super-skipper"
PANEL_ELEMENT = "super-skipper-panel"
PANEL_STATIC_URL = "/super_skipper_static"
SIGNAL_UPDATE = f"{DOMAIN}_update"

# Options of the integration entry
CONF_SNOOZE_MINUTES = "snooze_minutes"
CONF_COOLDOWN_SECONDS = "cooldown_seconds"
CONF_CONFIRM_SECONDS = "confirm_seconds"

DEFAULT_SNOOZE_MINUTES = 60
DEFAULT_COOLDOWN_SECONDS = 5
DEFAULT_CONFIRM_SECONDS = 1.0

# A rule
CONF_NAME = "name"
CONF_KEYWORDS = "keywords"
CONF_PLAYERS = "players"
CONF_ACTION = "action"
CONF_MATCH_MODE = "match_mode"
CONF_MATCH_FIELDS = "match_fields"
CONF_IGNORE_TEXTS = "ignore_texts"

CONF_MAX_CONSECUTIVE = "max_consecutive"

CONF_STATION = "station"
CONF_STATION_ACTIONS = "station_actions"
CONF_RETURN_AFTER_MINUTES = "return_after_minutes"
CONF_RETURN_FALLBACK_MEDIA = "return_fallback_media"
CONF_RETURN_FALLBACK_ACTIONS = "return_fallback_actions"
CONF_REPEAT_MODE = "repeat_mode"
CONF_REPEAT_LIMIT = "repeat_limit"

CONF_HOLD_SECONDS = "hold_seconds"
CONF_MAX_MUTE_MINUTES = "max_mute_minutes"

CONF_PERSONS = "persons"
CONF_PRESENCE_MODE = "presence_mode"
CONF_CONDITIONS = "conditions"

DEFAULT_MAX_CONSECUTIVE = 5
DEFAULT_RETURN_AFTER_MINUTES = 5
DEFAULT_REPEAT_LIMIT = 5
DEFAULT_HOLD_SECONDS = 20
DEFAULT_MAX_MUTE_MINUTES = 10

# How long the integration waits for a player to be back on its source
VERIFY_RETURN_SECONDS = 10
# How long after the switch the first content id counts as the alternative station
ALTERNATIVE_SETTLE_SECONDS = 15
# Spotify only polls every 30 seconds; ask it to refresh after a skip
REFRESH_AFTER_SKIP_SECONDS = 2


class RuleAction(StrEnum):
    """What a rule does when a keyword plays."""

    AUTO = "auto"
    SKIP = "skip"
    SWITCH = "switch"
    MUTE = "mute"


class MatchMode(StrEnum):
    """How keywords are compared with what plays."""

    WHOLE_WORD = "whole_word"
    SUBSTRING = "substring"
    REGEX = "regex"


class MatchField(StrEnum):
    """Which media player attributes are searched."""

    TITLE = "title"
    ARTIST = "artist"
    ALBUM = "album"
    CHANNEL = "channel"


class RepeatMode(StrEnum):
    """What happens when the keyword still plays after returning."""

    LIMITED = "limited"
    UNLIMITED = "unlimited"
    ONCE = "once"


class PresenceMode(StrEnum):
    """How the chosen persons must be at home for the rule to act."""

    ANY_HOME = "any_home"
    ALL_HOME = "all_home"
    NONE_HOME = "none_home"


DEFAULT_MATCH_FIELDS = [MatchField.TITLE, MatchField.ARTIST]
