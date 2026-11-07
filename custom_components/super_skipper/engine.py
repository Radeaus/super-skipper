"""Watch media players and apply the rules."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import voluptuous as vol
from homeassistant.components.media_player import ATTR_GROUP_MEMBERS, MediaPlayerState
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import STATE_HOME
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import condition
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util import dt as dt_util

from .actions import BaseAction, build_action
from .const import (
    CONF_ACTION,
    CONF_CONDITIONS,
    CONF_CONFIRM_SECONDS,
    CONF_COOLDOWN_SECONDS,
    CONF_PERSONS,
    CONF_PLAYERS,
    CONF_PRESENCE_MODE,
    CONF_SNOOZE_MINUTES,
    DEFAULT_CONFIRM_SECONDS,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_SNOOZE_MINUTES,
    SIGNAL_UPDATE,
    PresenceMode,
    RuleAction,
)
from .matching import Matcher, MatchKey, describe, match_key

_LOGGER = logging.getLogger(__name__)

PLAYING_STATES = {MediaPlayerState.PLAYING, MediaPlayerState.BUFFERING}


@dataclass
class LastMatch:
    """What the rule last acted on."""

    player: str
    description: str
    action: RuleAction
    when: datetime


@dataclass
class PlayerTracking:
    """What the rule knows about one player."""

    key: MatchKey | None = None
    matched: bool = False
    consecutive: int = 0
    last_action: float = 0.0
    pending: CALLBACK_TYPE | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class Snooze:
    """Pausing every rule for a while."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.until: datetime | None = None
        self._cancel: CALLBACK_TYPE | None = None
        self._listeners: list[Callable[[], None]] = []

    @property
    def minutes(self) -> int:
        return int(self.entry.options.get(CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES))

    @property
    def active(self) -> bool:
        return self.until is not None and dt_util.utcnow() < self.until

    @callback
    def async_start(self) -> None:
        """Pause the rules for the configured time."""
        self.async_stop()
        delay = self.minutes * 60
        self.until = dt_util.utcnow() + timedelta(seconds=delay)
        self._cancel = async_call_later(self.hass, delay, self._expired)
        self._notify()

    @callback
    def _expired(self, _now: datetime) -> None:
        self._cancel = None
        self.until = None
        self._notify()

    @callback
    def async_stop(self) -> None:
        """End the pause."""
        if self._cancel:
            self._cancel()
            self._cancel = None
        if self.until is not None:
            self.until = None
            self._notify()

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)


class RuleWatcher:
    """One rule: its players, matcher, conditions and action."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
        snooze: Snooze,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.subentry = subentry
        self.snooze = snooze
        data = subentry.data
        self.name = subentry.title
        self.players: list[str] = list(data.get(CONF_PLAYERS, []))
        self.rule_action = RuleAction(data[CONF_ACTION])
        self.matcher = Matcher.from_config(data)
        self.action: BaseAction = build_action(hass, self.name, self.rule_action, data)
        self.persons: list[str] = list(data.get(CONF_PERSONS, []))
        self.presence_mode = PresenceMode(
            data.get(CONF_PRESENCE_MODE, PresenceMode.ANY_HOME)
        )
        self.condition_configs: list[dict[str, Any]] = list(
            data.get(CONF_CONDITIONS, [])
        )
        self._check_conditions: Callable[[Any], bool] | None = None
        self.enabled = True
        self.last_match: LastMatch | None = None
        self.match_count = 0
        self._tracking: dict[str, PlayerTracking] = {}
        self._unsub: CALLBACK_TYPE | None = None
        self._listeners: list[Callable[[], None]] = []

    @property
    def subentry_id(self) -> str:
        return self.subentry.subentry_id

    @property
    def cooldown(self) -> float:
        return float(
            self.entry.options.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS)
        )

    @property
    def confirm_delay(self) -> float:
        return float(
            self.entry.options.get(CONF_CONFIRM_SECONDS, DEFAULT_CONFIRM_SECONDS)
        )

    async def async_start(self) -> None:
        """Compile the conditions and start listening."""
        if self.condition_configs:
            try:
                validated = await condition.async_validate_conditions_config(
                    self.hass, self.condition_configs
                )
                self._check_conditions = await condition.async_conditions_from_config(
                    self.hass, validated, _LOGGER, self.name
                )
            except (vol.Invalid, HomeAssistantError, KeyError) as err:
                _LOGGER.error(
                    "%s: the conditions are not valid, so the rule does nothing: %s",
                    self.name,
                    err,
                )
                self._check_conditions = lambda _variables: False
        if self.players:
            self._unsub = async_track_state_change_event(
                self.hass, self.players, self._state_changed
            )

    @callback
    def async_stop(self) -> None:
        """Stop listening and cancel everything that is pending."""
        if self._unsub:
            self._unsub()
            self._unsub = None
        for tracking in self._tracking.values():
            if tracking.pending:
                tracking.pending()
                tracking.pending = None
        self.action.async_shutdown()

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Let an entity follow the rule."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)

    @callback
    def async_set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self._notify()

    def _tracking_of(self, player: str) -> PlayerTracking:
        if (tracking := self._tracking.get(player)) is None:
            tracking = self._tracking[player] = PlayerTracking()
        return tracking

    @callback
    def _state_changed(self, event: Event[EventStateChangedData]) -> None:
        player = event.data["entity_id"]
        new_state = event.data["new_state"]
        tracking = self._tracking_of(player)
        self.action.async_player_state(player, new_state)

        if new_state is None or new_state.state not in PLAYING_STATES:
            self._cancel_pending(tracking)
            if tracking.key is not None or tracking.matched:
                tracking.key = None
                tracking.matched = False
                tracking.consecutive = 0
                self.action.async_player_stopped(player)
            return

        members = new_state.attributes.get(ATTR_GROUP_MEMBERS)
        if members and members[0] != player:
            return

        key = match_key(new_state.attributes)
        if key == tracking.key:
            return
        text = self.matcher.text_of(new_state.attributes)
        if self.matcher.is_ignored(text):
            return
        tracking.key = key
        self._cancel_pending(tracking)
        matches = self.matcher.matches(text)
        tracking.pending = self._confirm_later(self.confirm_delay, player, key, matches)

    def _confirm_later(
        self, delay: float, player: str, key: MatchKey, matches: bool
    ) -> CALLBACK_TYPE:
        async def _fire(_now: datetime) -> None:
            await self._confirm(player, key, matches)

        return async_call_later(self.hass, delay, _fire)

    @callback
    def _cancel_pending(self, tracking: PlayerTracking) -> None:
        if tracking.pending:
            tracking.pending()
            tracking.pending = None

    async def _confirm(self, player: str, key: MatchKey, matches: bool) -> None:
        """Act once the same track has played for a moment."""
        tracking = self._tracking_of(player)
        tracking.pending = None
        state = self.hass.states.get(player)
        if (
            state is None
            or state.state not in PLAYING_STATES
            or match_key(state.attributes) != key
        ):
            return
        if not matches:
            if tracking.matched:
                tracking.matched = False
                tracking.consecutive = 0
                await self.action.async_match_ended(player, state)
            return
        if not self.enabled or self.snooze.active or not self._conditions_met():
            tracking.matched = False
            tracking.consecutive = 0
            return
        remaining = tracking.last_action + self.cooldown - time.monotonic()
        if remaining > 0:
            tracking.pending = self._confirm_later(remaining, player, key, matches)
            return
        async with tracking.lock:
            tracking.matched = True
            tracking.consecutive += 1
            acted = await self.action.async_match(player, state, tracking.consecutive)
        if acted:
            tracking.last_action = time.monotonic()
            self.match_count += 1
            self.last_match = LastMatch(
                player=player,
                description=describe(state.attributes),
                action=self.rule_action,
                when=dt_util.utcnow(),
            )
            self._notify()

    def _conditions_met(self) -> bool:
        if self.persons:
            home = [
                (state := self.hass.states.get(person)) is not None
                and state.state == STATE_HOME
                for person in self.persons
            ]
            if self.presence_mode is PresenceMode.ANY_HOME and not any(home):
                return False
            if self.presence_mode is PresenceMode.ALL_HOME and not all(home):
                return False
            if self.presence_mode is PresenceMode.NONE_HOME and any(home):
                return False
        if self._check_conditions is not None:
            return self._check_conditions({"rule": self.name})
        return True
