"""Config flow for Super Skipper."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components.media_player import (
    DOMAIN as MEDIA_PLAYER_DOMAIN,
)
from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    ActionSelector,
    ConditionSelector,
    EntitySelector,
    EntitySelectorConfig,
    MediaSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_ACTION,
    CONF_CONDITIONS,
    CONF_CONFIRM_SECONDS,
    CONF_COOLDOWN_SECONDS,
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
    DEFAULT_CONFIRM_SECONDS,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_HOLD_SECONDS,
    DEFAULT_MATCH_FIELDS,
    DEFAULT_MAX_CONSECUTIVE,
    DEFAULT_MAX_MUTE_MINUTES,
    DEFAULT_REPEAT_LIMIT,
    DEFAULT_RETURN_AFTER_MINUTES,
    DEFAULT_SNOOZE_MINUTES,
    DOMAIN,
    NAME,
    SUBENTRY_TYPE_RULE,
    MatchField,
    MatchMode,
    PresenceMode,
    RepeatMode,
    RuleAction,
)
from .matching import compile_keywords

SECTION_MATCHING = "matching"
SECTION_ADVANCED = "advanced"

# The keys each action step stores, so switching action drops the others.
ACTION_KEYS = {
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


def _select(options: type[Any], key: str, multiple: bool = False) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[option.value for option in options],
            translation_key=key,
            multiple=multiple,
            mode=SelectSelectorMode.DROPDOWN if multiple else SelectSelectorMode.LIST,
        )
    )


def _number(
    minimum: float, maximum: float, step: float = 1, unit: str | None = None
) -> NumberSelector:
    config = NumberSelectorConfig(
        min=minimum, max=maximum, step=step, mode=NumberSelectorMode.BOX
    )
    if unit:
        config["unit_of_measurement"] = unit
    return NumberSelector(config)


def _players_without(
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


class SuperSkipperConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create the one Super Skipper entry."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SuperSkipperOptionsFlow:
        """Return the options flow."""
        return SuperSkipperOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Rules are subentries."""
        return {SUBENTRY_TYPE_RULE: RuleSubentryFlow}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Explain what happens next, then create the entry."""
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))


class SuperSkipperOptionsFlow(OptionsFlow):
    """Settings that apply to every rule."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SNOOZE_MINUTES, default=DEFAULT_SNOOZE_MINUTES
                ): _number(1, 1440, unit="min"),
                vol.Required(
                    CONF_COOLDOWN_SECONDS, default=DEFAULT_COOLDOWN_SECONDS
                ): _number(0, 120, unit="s"),
                vol.Required(
                    CONF_CONFIRM_SECONDS, default=DEFAULT_CONFIRM_SECONDS
                ): _number(0, 30, 0.5, unit="s"),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, self.config_entry.options
            ),
        )


class RuleSubentryFlow(ConfigSubentryFlow):
    """Create a rule, or change one."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Start a new rule."""
        self._data = {}
        return await self.async_step_basics()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Change an existing rule."""
        self._data = dict(self._get_reconfigure_subentry().data)
        return await self.async_step_basics()

    # Step 1: what to look for, where, and what to do

    async def async_step_basics(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Name, keywords, players and action."""
        errors: dict[str, str] = {}
        if user_input is not None:
            matching = user_input.pop(SECTION_MATCHING, {})
            flat = {**user_input, **matching}
            if not flat.get(CONF_KEYWORDS):
                errors[CONF_KEYWORDS] = "keywords_required"
            if not flat.get(CONF_PLAYERS):
                errors[CONF_PLAYERS] = "players_required"
            try:
                compile_keywords(
                    list(flat.get(CONF_KEYWORDS, [])), MatchMode(flat[CONF_MATCH_MODE])
                )
            except re.error:
                errors["base"] = "invalid_regex"
            if not errors:
                previous = self._data.get(CONF_ACTION)
                self._data.update(flat)
                if previous and previous != flat[CONF_ACTION]:
                    for key in ACTION_KEYS[RuleAction(previous)]:
                        self._data.pop(key, None)
                return await self._async_step_for_action()
            suggested: Mapping[str, Any] = {**user_input, SECTION_MATCHING: matching}
        else:
            suggested = self._suggested_basics()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): TextSelector(),
                vol.Required(CONF_KEYWORDS): TextSelector(
                    TextSelectorConfig(multiple=True)
                ),
                vol.Required(CONF_PLAYERS): EntitySelector(
                    EntitySelectorConfig(domain=MEDIA_PLAYER_DOMAIN, multiple=True)
                ),
                vol.Required(CONF_ACTION, default=RuleAction.SKIP.value): _select(
                    RuleAction, CONF_ACTION
                ),
                vol.Required(SECTION_MATCHING): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_MATCH_MODE, default=MatchMode.WHOLE_WORD.value
                            ): _select(MatchMode, CONF_MATCH_MODE),
                            vol.Required(
                                CONF_MATCH_FIELDS,
                                default=[field.value for field in DEFAULT_MATCH_FIELDS],
                            ): _select(MatchField, CONF_MATCH_FIELDS, multiple=True),
                            vol.Optional(CONF_IGNORE_TEXTS, default=[]): TextSelector(
                                TextSelectorConfig(multiple=True)
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )
        return self.async_show_form(
            step_id="basics",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            errors=errors,
            last_step=False,
        )

    def _suggested_basics(self) -> dict[str, Any]:
        data = self._data
        matching = {
            key: data[key]
            for key in (CONF_MATCH_MODE, CONF_MATCH_FIELDS, CONF_IGNORE_TEXTS)
            if key in data
        }
        suggested = {
            key: data[key]
            for key in (CONF_NAME, CONF_KEYWORDS, CONF_PLAYERS, CONF_ACTION)
            if key in data
        }
        if matching:
            suggested[SECTION_MATCHING] = matching
        return suggested

    async def _async_step_for_action(self) -> SubentryFlowResult:
        action = RuleAction(self._data[CONF_ACTION])
        if action is RuleAction.SKIP:
            return await self.async_step_skip()
        if action is RuleAction.SWITCH:
            return await self.async_step_switch()
        return await self.async_step_mute()

    # Step 2: the details of the action

    async def async_step_skip(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Settings of the skip action."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_conditions()
        if missing := _players_without(
            self.hass, self._data[CONF_PLAYERS], MediaPlayerEntityFeature.NEXT_TRACK
        ):
            errors["base"] = "players_cannot_skip"
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAX_CONSECUTIVE, default=DEFAULT_MAX_CONSECUTIVE
                ): _number(0, 50),
            }
        )
        return self.async_show_form(
            step_id="skip",
            data_schema=self.add_suggested_values_to_schema(schema, self._data),
            errors=errors,
            description_placeholders={"players": ", ".join(missing)},
            last_step=False,
        )

    async def async_step_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Settings of the switch action."""
        errors: dict[str, str] = {}
        missing: list[str] = []
        if user_input is not None:
            if not user_input.get(CONF_STATION) and not user_input.get(
                CONF_STATION_ACTIONS
            ):
                errors[CONF_STATION] = "station_required"
            if (
                user_input[CONF_RETURN_AFTER_MINUTES]
                and not user_input.get(CONF_RETURN_FALLBACK_MEDIA)
                and not user_input.get(CONF_RETURN_FALLBACK_ACTIONS)
            ):
                errors[CONF_RETURN_FALLBACK_MEDIA] = "fallback_required"
            if user_input.get(CONF_STATION) and (
                missing := _players_without(
                    self.hass,
                    self._data[CONF_PLAYERS],
                    MediaPlayerEntityFeature.PLAY_MEDIA,
                )
            ):
                errors[CONF_STATION] = "players_cannot_play_media"
            if not errors:
                for key in ACTION_KEYS[RuleAction.SWITCH]:
                    self._data.pop(key, None)
                self._data.update(user_input)
                return await self.async_step_conditions()
            suggested: Mapping[str, Any] = user_input
        else:
            suggested = self._data
        schema = vol.Schema(
            {
                vol.Optional(CONF_STATION): MediaSelector(),
                vol.Optional(CONF_STATION_ACTIONS): ActionSelector(),
                vol.Required(
                    CONF_RETURN_AFTER_MINUTES, default=DEFAULT_RETURN_AFTER_MINUTES
                ): _number(0, 1440, unit="min"),
                vol.Optional(CONF_RETURN_FALLBACK_MEDIA): MediaSelector(),
                vol.Optional(CONF_RETURN_FALLBACK_ACTIONS): ActionSelector(),
                vol.Required(
                    CONF_REPEAT_MODE, default=RepeatMode.LIMITED.value
                ): _select(RepeatMode, CONF_REPEAT_MODE),
                vol.Required(CONF_REPEAT_LIMIT, default=DEFAULT_REPEAT_LIMIT): _number(
                    1, 50
                ),
            }
        )
        return self.async_show_form(
            step_id="switch",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            errors=errors,
            description_placeholders={"players": ", ".join(missing)},
            last_step=False,
        )

    async def async_step_mute(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Settings of the mute action."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_conditions()
        schema = vol.Schema(
            {
                vol.Required(CONF_HOLD_SECONDS, default=DEFAULT_HOLD_SECONDS): _number(
                    0, 300, unit="s"
                ),
                vol.Required(
                    CONF_MAX_MUTE_MINUTES, default=DEFAULT_MAX_MUTE_MINUTES
                ): _number(0, 180, unit="min"),
            }
        )
        return self.async_show_form(
            step_id="mute",
            data_schema=self.add_suggested_values_to_schema(schema, self._data),
            last_step=False,
        )

    # Step 3: when the rule may act

    async def async_step_conditions(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Persons at home and other conditions."""
        if user_input is not None:
            # The condition selector has validated the conditions already.
            advanced = user_input.pop(SECTION_ADVANCED, {})
            self._data.update(user_input)
            self._data[CONF_CONDITIONS] = advanced.get(CONF_CONDITIONS) or []
            return self._finish()
        suggested = {
            key: self._data[key]
            for key in (CONF_PERSONS, CONF_PRESENCE_MODE)
            if key in self._data
        }
        if CONF_CONDITIONS in self._data:
            suggested[SECTION_ADVANCED] = {CONF_CONDITIONS: self._data[CONF_CONDITIONS]}
        schema = vol.Schema(
            {
                vol.Optional(CONF_PERSONS, default=[]): EntitySelector(
                    EntitySelectorConfig(domain="person", multiple=True)
                ),
                vol.Required(
                    CONF_PRESENCE_MODE, default=PresenceMode.ANY_HOME.value
                ): _select(PresenceMode, CONF_PRESENCE_MODE),
                vol.Required(SECTION_ADVANCED): section(
                    vol.Schema({vol.Optional(CONF_CONDITIONS): ConditionSelector()}),
                    {"collapsed": True},
                ),
            }
        )
        return self.async_show_form(
            step_id="conditions",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
        )

    def _finish(self) -> SubentryFlowResult:
        title = self._data[CONF_NAME]
        if self.source == SOURCE_USER:
            return self.async_create_entry(title=title, data=self._data)
        return self.async_update_and_abort(
            self._get_entry(),
            self._get_reconfigure_subentry(),
            title=title,
            data=self._data,
        )
