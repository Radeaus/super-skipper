"""What a rule does when a keyword plays: skip, switch station, or mute."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Coroutine, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.components.logbook import async_log_entry
from homeassistant.components.media_player import (
    ATTR_INPUT_SOURCE,
    ATTR_INPUT_SOURCE_LIST,
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_DURATION,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    SERVICE_PLAY_MEDIA,
    SERVICE_SELECT_SOURCE,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.components.media_player import (
    DOMAIN as MEDIA_PLAYER_DOMAIN,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_SET,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.script import Script

from .const import (
    ALTERNATIVE_SETTLE_SECONDS,
    CONF_HOLD_SECONDS,
    CONF_MAX_CONSECUTIVE,
    CONF_MAX_MUTE_MINUTES,
    CONF_REPEAT_LIMIT,
    CONF_REPEAT_MODE,
    CONF_RETURN_AFTER_MINUTES,
    CONF_RETURN_FALLBACK_ACTIONS,
    CONF_RETURN_FALLBACK_MEDIA,
    CONF_STATION,
    CONF_STATION_ACTIONS,
    DEFAULT_HOLD_SECONDS,
    DEFAULT_MAX_CONSECUTIVE,
    DEFAULT_MAX_MUTE_MINUTES,
    DEFAULT_REPEAT_LIMIT,
    DEFAULT_RETURN_AFTER_MINUTES,
    DOMAIN,
    NAME,
    REFRESH_AFTER_SKIP_SECONDS,
    VERIFY_RETURN_SECONDS,
    RepeatMode,
    RuleAction,
)
from .matching import describe

_LOGGER = logging.getLogger(__name__)

SONOS_DOMAIN = "sonos"
SPOTIFY_DOMAIN = "spotify"

# Content ids that a player can be asked to play again.
REPLAYABLE_CONTENT_ID = re.compile(
    r"^(https?://|media-source://|library://|spotify:|x-rincon-mp3radio://"
    r"|x-sonosapi-stream:|x-sonosapi-radio:|x-sonos-http:|x-file-cifs://)",
    re.IGNORECASE,
)

PLAYING_STATES = {MediaPlayerState.PLAYING, MediaPlayerState.BUFFERING}


def supports(state: State, feature: MediaPlayerEntityFeature) -> bool:
    """Return whether a player state reports a feature."""
    return bool(int(state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)) & feature)


def platform_of(hass: HomeAssistant, entity_id: str) -> str | None:
    """Return the integration that provides an entity."""
    entry = er.async_get(hass).async_get(entity_id)
    return entry.platform if entry else None


def friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    """Return the name of a player, for log messages."""
    state = hass.states.get(entity_id)
    return state.name if state else entity_id


class BaseAction:
    """Common parts of the actions."""

    kind = "none"

    def __init__(
        self, hass: HomeAssistant, rule_name: str, data: Mapping[str, Any]
    ) -> None:
        self.hass = hass
        self.rule_name = rule_name
        self.data = data
        self.on_log: Callable[[str, str], None] | None = None
        self._timers: dict[tuple[str, str], CALLBACK_TYPE] = {}

    def _schedule(
        self,
        player: str,
        kind: str,
        delay: float,
        run: Callable[[], Coroutine[Any, Any, Any]],
    ) -> None:
        """Replace the timer of one kind for one player."""
        self._cancel(player, kind)

        async def _fire(_now: datetime) -> None:
            self._timers.pop((player, kind), None)
            await run()

        self._timers[(player, kind)] = async_call_later(self.hass, delay, _fire)

    def _cancel(self, player: str, kind: str) -> None:
        if cancel := self._timers.pop((player, kind), None):
            cancel()

    def _cancel_player(self, player: str) -> None:
        for key in [key for key in self._timers if key[0] == player]:
            self._timers.pop(key)()

    @callback
    def async_shutdown(self) -> None:
        """Cancel every timer."""
        for cancel in self._timers.values():
            cancel()
        self._timers.clear()

    def log(self, player: str, message: str) -> None:
        """Write a line to the logbook and to the activity of the rule."""
        _LOGGER.debug("%s: %s (%s)", self.rule_name, message, player)
        async_log_entry(self.hass, NAME, f"{self.rule_name}: {message}", DOMAIN, player)
        if self.on_log is not None:
            self.on_log(player, message)

    def kind_for(self, player: str) -> str:
        """Which action was taken for the player, for the last match."""
        return self.kind

    async def _call(
        self, service: str, data: dict[str, Any], domain: str = MEDIA_PLAYER_DOMAIN
    ) -> bool:
        """Call an action and report failure instead of raising."""
        try:
            await self.hass.services.async_call(domain, service, data, blocking=True)
        except HomeAssistantError as err:
            _LOGGER.warning(
                "%s: %s.%s failed: %s", self.rule_name, domain, service, err
            )
            return False
        return True

    async def _run_actions(
        self, player: str, sequence: list[dict[str, Any]], what: str
    ) -> bool:
        """Run the actions a user configured."""
        script = Script(
            self.hass,
            sequence,
            f"{self.rule_name} {what}",
            DOMAIN,
            running_description=f"{NAME} {what}",
        )
        try:
            await script.async_run(
                {"player": player, "rule": self.rule_name}, context=None
            )
        except HomeAssistantError as err:
            _LOGGER.warning("%s: the %s actions failed: %s", self.rule_name, what, err)
            return False
        return True

    async def _play(
        self,
        player: str,
        media: Mapping[str, Any] | None,
        actions: list | None,
        what: str,
    ) -> bool:
        """Play configured media, or run configured actions."""
        if media:
            return await self._call(
                SERVICE_PLAY_MEDIA,
                {
                    ATTR_ENTITY_ID: player,
                    ATTR_MEDIA_CONTENT_ID: media[ATTR_MEDIA_CONTENT_ID],
                    ATTR_MEDIA_CONTENT_TYPE: media[ATTR_MEDIA_CONTENT_TYPE],
                },
            )
        if actions:
            return await self._run_actions(player, list(actions), what)
        return False

    # Hooks the engine calls

    def repeat_is_stale(self, player: str) -> bool:
        """Whether the track acted on, reported again soon after, is stale metadata."""
        return True

    async def async_match(self, player: str, state: State, consecutive: int) -> bool:
        """A keyword started playing. Return whether something was done."""
        raise NotImplementedError

    async def async_match_ended(self, player: str, state: State) -> None:
        """Something that does not match now plays."""

    @callback
    def async_player_state(self, player: str, state: State | None) -> None:
        """The player changed state or attributes (called for every change)."""

    @callback
    def async_player_stopped(self, player: str) -> None:
        """The player stopped, was turned off or became unavailable."""
        self._cancel_player(player)


class SkipAction(BaseAction):
    """Go to the next track."""

    kind = RuleAction.SKIP.value

    def __init__(
        self, hass: HomeAssistant, rule_name: str, data: Mapping[str, Any]
    ) -> None:
        super().__init__(hass, rule_name, data)
        self.max_consecutive = int(
            data.get(CONF_MAX_CONSECUTIVE, DEFAULT_MAX_CONSECUTIVE)
        )
        self._limited: set[str] = set()

    async def async_match(self, player: str, state: State, consecutive: int) -> bool:
        if player in self._limited:
            return False
        if self.max_consecutive and consecutive > self.max_consecutive:
            self._limited.add(player)
            self.log(
                player,
                f"skipped {self.max_consecutive} tracks in a row on "
                f"{friendly_name(self.hass, player)}; leaving “{describe(state.attributes)}” on",
            )
            return False
        if not supports(state, MediaPlayerEntityFeature.NEXT_TRACK):
            _LOGGER.warning("%s: %s cannot skip tracks", self.rule_name, player)
            return False
        if not await self._call(SERVICE_MEDIA_NEXT_TRACK, {ATTR_ENTITY_ID: player}):
            return False
        self.log(
            player,
            f"skipped “{describe(state.attributes)}” on {friendly_name(self.hass, player)}",
        )
        if platform_of(self.hass, player) == SPOTIFY_DOMAIN:
            self._schedule(
                player,
                "refresh",
                REFRESH_AFTER_SKIP_SECONDS,
                lambda: self._call(
                    "update_entity", {ATTR_ENTITY_ID: player}, "homeassistant"
                ),
            )
        return True

    async def async_match_ended(self, player: str, state: State) -> None:
        self._limited.discard(player)

    @callback
    def async_player_stopped(self, player: str) -> None:
        super().async_player_stopped(player)
        self._limited.discard(player)


@dataclass
class Source:
    """What a player played before the switch."""

    content_id: str | None
    content_type: str | None
    source: str | None
    source_list: list[str]
    volume: float | None
    sonos: bool

    @classmethod
    def from_state(cls, state: State, sonos: bool) -> Source:
        attributes = state.attributes
        return cls(
            content_id=attributes.get(ATTR_MEDIA_CONTENT_ID),
            content_type=attributes.get(ATTR_MEDIA_CONTENT_TYPE),
            source=attributes.get(ATTR_INPUT_SOURCE),
            source_list=list(attributes.get(ATTR_INPUT_SOURCE_LIST) or []),
            volume=attributes.get(ATTR_MEDIA_VOLUME_LEVEL),
            sonos=sonos,
        )

    @property
    def replayable(self) -> bool:
        return (
            bool(self.content_id)
            and REPLAYABLE_CONTENT_ID.match(self.content_id) is not None
        )

    @property
    def selectable(self) -> bool:
        return bool(self.source) and self.source in self.source_list

    def is_playing(self, state: State) -> bool:
        """Return whether the state shows the source again."""
        if state.state not in PLAYING_STATES:
            return False
        attributes = state.attributes
        if self.content_id and attributes.get(ATTR_MEDIA_CONTENT_ID) == self.content_id:
            return True
        return (
            bool(self.source)
            and attributes.get(ATTR_INPUT_SOURCE) == self.source
            and not self.content_id
        )


@dataclass
class Diversion:
    """A player that was sent to the alternative station."""

    source: Source
    repeats: int = 0
    phase: str = "diverted"  # diverted, returning, returned
    alternative_ids: set[str] = field(default_factory=set)
    settling: bool = True


class SwitchAction(BaseAction):
    """Play another station, and come back later."""

    kind = RuleAction.SWITCH.value

    def __init__(
        self, hass: HomeAssistant, rule_name: str, data: Mapping[str, Any]
    ) -> None:
        super().__init__(hass, rule_name, data)
        self.station: Mapping[str, Any] | None = data.get(CONF_STATION)
        self.station_actions: list | None = data.get(CONF_STATION_ACTIONS)
        self.return_after = (
            float(data.get(CONF_RETURN_AFTER_MINUTES, DEFAULT_RETURN_AFTER_MINUTES))
            * 60
        )
        self.fallback_media: Mapping[str, Any] | None = data.get(
            CONF_RETURN_FALLBACK_MEDIA
        )
        self.fallback_actions: list | None = data.get(CONF_RETURN_FALLBACK_ACTIONS)
        self.repeat_mode = RepeatMode(data.get(CONF_REPEAT_MODE, RepeatMode.LIMITED))
        self.repeat_limit = int(data.get(CONF_REPEAT_LIMIT, DEFAULT_REPEAT_LIMIT))
        self.diversions: dict[str, Diversion] = {}

    async def async_match(self, player: str, state: State, consecutive: int) -> bool:
        diversion = self.diversions.get(player)
        if diversion is not None and diversion.phase != "returned":
            # The alternative station plays the keyword as well; leave it.
            return False
        repeats = 0
        stay = False
        if diversion is not None:
            # Back on the source and the keyword still plays.
            repeats = diversion.repeats + 1
            if self.repeat_mode is RepeatMode.ONCE:
                self.diversions.pop(player)
                self.log(
                    player,
                    f"“{describe(state.attributes)}” still plays on "
                    f"{friendly_name(self.hass, player)}; switching only once",
                )
                return False
            if self.repeat_mode is RepeatMode.LIMITED and repeats >= self.repeat_limit:
                stay = True
        return await self._divert(player, state, repeats, stay)

    async def _divert(
        self, player: str, state: State, repeats: int, stay: bool
    ) -> bool:
        sonos = platform_of(
            self.hass, player
        ) == SONOS_DOMAIN and self.hass.services.has_service(SONOS_DOMAIN, "snapshot")
        source = Source.from_state(state, sonos)
        if sonos and not stay and self.return_after:
            await self._call("snapshot", {ATTR_ENTITY_ID: player}, SONOS_DOMAIN)
        if not await self._play(player, self.station, self.station_actions, "station"):
            return False
        name = friendly_name(self.hass, player)
        what = describe(state.attributes)
        if stay or not self.return_after:
            self.diversions.pop(player, None)
            if stay:
                self.log(
                    player,
                    f"“{what}” kept playing after {repeats} returns on {name}; "
                    "staying on the alternative station",
                )
            else:
                self.log(player, f"switched {name} away from “{what}”")
            return True
        diversion = Diversion(source=source, repeats=repeats)
        self.diversions[player] = diversion
        self._schedule(
            player, "settle", ALTERNATIVE_SETTLE_SECONDS, lambda: self._settled(player)
        )
        self._schedule(
            player, "return", self.return_after, lambda: self._return(player)
        )
        minutes = int(self.return_after // 60)
        self.log(
            player,
            f"switched {name} away from “{what}” for {minutes} minutes",
        )
        return True

    async def _settled(self, player: str) -> None:
        if diversion := self.diversions.get(player):
            diversion.settling = False

    async def _return(self, player: str) -> None:
        """Try to play the source again, then check whether it worked."""
        diversion = self.diversions.get(player)
        if diversion is None:
            return
        diversion.phase = "returning"
        source = diversion.source
        name = friendly_name(self.hass, player)
        attempted = False
        if source.sonos:
            attempted = await self._call(
                "restore", {ATTR_ENTITY_ID: player}, SONOS_DOMAIN
            )
        if not attempted and source.replayable:
            attempted = await self._call(
                SERVICE_PLAY_MEDIA,
                {
                    ATTR_ENTITY_ID: player,
                    ATTR_MEDIA_CONTENT_ID: source.content_id,
                    ATTR_MEDIA_CONTENT_TYPE: source.content_type or "music",
                },
            )
        if not attempted and source.selectable:
            attempted = await self._call(
                SERVICE_SELECT_SOURCE,
                {ATTR_ENTITY_ID: player, ATTR_INPUT_SOURCE: source.source},
            )
        if not attempted:
            await self._fallback(player, "could not return")
            return
        self.log(player, f"returning {name} to what played before")
        self._schedule(
            player, "verify", VERIFY_RETURN_SECONDS, lambda: self._verify(player)
        )

    async def _verify(self, player: str) -> None:
        diversion = self.diversions.get(player)
        if diversion is None or diversion.phase != "returning":
            return
        state = self.hass.states.get(player)
        if state is not None and diversion.source.is_playing(state):
            self._returned(player)
            return
        await self._fallback(player, "did not come back")

    async def _fallback(self, player: str, why: str) -> None:
        name = friendly_name(self.hass, player)
        played = await self._play(
            player, self.fallback_media, self.fallback_actions, "fallback"
        )
        if played:
            self.log(player, f"{name} {why}; playing the fallback instead")
        else:
            self.log(player, f"{name} {why}, and the fallback failed")
        self.diversions.pop(player, None)

    @callback
    def _returned(self, player: str) -> None:
        if diversion := self.diversions.get(player):
            diversion.phase = "returned"
            self.log(
                player,
                f"{friendly_name(self.hass, player)} is back on what played before",
            )

    @callback
    def async_player_state(self, player: str, state: State | None) -> None:
        diversion = self.diversions.get(player)
        if diversion is None or state is None:
            return
        content_id = state.attributes.get(ATTR_MEDIA_CONTENT_ID)
        if diversion.phase == "diverted":
            if state.state not in PLAYING_STATES or not content_id:
                return
            if diversion.settling:
                diversion.alternative_ids.add(content_id)
            elif (
                content_id not in diversion.alternative_ids
                and content_id != diversion.source.content_id
            ):
                # The user started something else; do not interfere later.
                self._cancel_player(player)
                self.diversions.pop(player)
                self.log(
                    player,
                    f"{friendly_name(self.hass, player)} plays something else; not returning",
                )
        elif diversion.phase == "returning" and diversion.source.is_playing(state):
            self._cancel(player, "verify")
            self._returned(player)

    def repeat_is_stale(self, player: str) -> bool:
        # Back on the source after a return, the same track really plays again.
        diversion = self.diversions.get(player)
        return diversion is None or diversion.phase != "returned"

    async def async_match_ended(self, player: str, state: State) -> None:
        diversion = self.diversions.get(player)
        if diversion is not None and diversion.phase == "returned":
            # Back on the source and the keyword is gone: the episode is over.
            self.diversions.pop(player)

    @callback
    def async_player_stopped(self, player: str) -> None:
        diversion = self.diversions.get(player)
        if (
            diversion is not None
            and diversion.phase == "diverted"
            and not diversion.settling
        ):
            self._cancel_player(player)
            self.diversions.pop(player)
            self.log(
                player, f"{friendly_name(self.hass, player)} stopped; not returning"
            )


class MuteAction(BaseAction):
    """Mute the player until the keyword is gone."""

    kind = RuleAction.MUTE.value

    def __init__(
        self, hass: HomeAssistant, rule_name: str, data: Mapping[str, Any]
    ) -> None:
        super().__init__(hass, rule_name, data)
        self.hold = float(data.get(CONF_HOLD_SECONDS, DEFAULT_HOLD_SECONDS))
        self.max_mute = (
            float(data.get(CONF_MAX_MUTE_MINUTES, DEFAULT_MAX_MUTE_MINUTES)) * 60
        )
        # player -> previous volume level (None when muted with volume_mute)
        self.muted: dict[str, float | None] = {}

    async def async_match(self, player: str, state: State, consecutive: int) -> bool:
        self._cancel(player, "unmute")
        if player in self.muted:
            return False
        name = friendly_name(self.hass, player)
        if supports(state, MediaPlayerEntityFeature.VOLUME_MUTE):
            if state.attributes.get(ATTR_MEDIA_VOLUME_MUTED):
                return False
            previous = None
            ok = await self._call(
                SERVICE_VOLUME_MUTE,
                {ATTR_ENTITY_ID: player, ATTR_MEDIA_VOLUME_MUTED: True},
            )
        elif supports(state, MediaPlayerEntityFeature.VOLUME_SET):
            previous = state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL)
            if previous is None:
                return False
            ok = await self._call(
                SERVICE_VOLUME_SET,
                {ATTR_ENTITY_ID: player, ATTR_MEDIA_VOLUME_LEVEL: 0.0},
            )
        else:
            _LOGGER.warning("%s: %s cannot be muted", self.rule_name, player)
            return False
        if not ok:
            return False
        self.muted[player] = previous
        self.log(player, f"muted {name} for “{describe(state.attributes)}”")
        if self.max_mute:
            self._schedule(
                player,
                "max",
                self.max_mute,
                lambda: self._unmute(player, "after the maximum time"),
            )
        return True

    async def async_match_ended(self, player: str, state: State) -> None:
        if player in self.muted:
            self._schedule(
                player,
                "unmute",
                self.hold,
                lambda: self._unmute(player, ""),
            )

    async def _unmute(self, player: str, why: str) -> None:
        if player not in self.muted:
            return
        previous = self.muted.pop(player)
        self._cancel_player(player)
        if previous is None:
            ok = await self._call(
                SERVICE_VOLUME_MUTE,
                {ATTR_ENTITY_ID: player, ATTR_MEDIA_VOLUME_MUTED: False},
            )
        else:
            ok = await self._call(
                SERVICE_VOLUME_SET,
                {ATTR_ENTITY_ID: player, ATTR_MEDIA_VOLUME_LEVEL: previous},
            )
        if ok:
            suffix = f" {why}" if why else ""
            self.log(player, f"unmuted {friendly_name(self.hass, player)}{suffix}")

    @callback
    def async_player_stopped(self, player: str) -> None:
        super().async_player_stopped(player)
        if player in self.muted:
            self.hass.async_create_task(self._unmute(player, "because it stopped"))

    @callback
    def async_shutdown(self) -> None:
        super().async_shutdown()
        for player in list(self.muted):
            self.hass.async_create_task(self._unmute(player, ""))


LIVE_STREAM_ID = re.compile(
    r"^(media-source://radio_browser|x-sonosapi-stream:|x-sonosapi-radio:|x-sonosapi-hls:"
    r"|x-rincon-mp3radio://|library://radio/|aac://|hls://|icy://)",
    re.IGNORECASE,
)


def is_live_stream(state: State) -> bool:
    """Whether a player plays a radio stream rather than a track."""
    attributes = state.attributes
    content_id = str(attributes.get(ATTR_MEDIA_CONTENT_ID) or "")
    if content_id.startswith("spotify:"):
        return False
    if attributes.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.CHANNEL:
        return True
    if LIVE_STREAM_ID.match(content_id):
        return True
    # Tracks have a known length; streams do not.
    return not attributes.get(ATTR_MEDIA_DURATION)


class AutoAction(BaseAction):
    """Skip tracks; switch station on radio, or mute when no station is set."""

    kind = RuleAction.AUTO.value

    def __init__(
        self, hass: HomeAssistant, rule_name: str, data: Mapping[str, Any]
    ) -> None:
        super().__init__(hass, rule_name, data)
        self.skip = SkipAction(hass, rule_name, data)
        self.switch = SwitchAction(hass, rule_name, data)
        self.mute = MuteAction(hass, rule_name, data)
        self.has_station = bool(
            data.get(CONF_STATION) or data.get(CONF_STATION_ACTIONS)
        )
        self._chosen: dict[str, BaseAction] = {}
        self._actions = (self.skip, self.switch, self.mute)
        self.on_log = self._on_log

    @property
    def on_log(self) -> Callable[[str, str], None] | None:  # type: ignore[override]
        return self._on_log

    @on_log.setter
    def on_log(self, value: Callable[[str, str], None] | None) -> None:
        self._on_log = value
        # The base class sets this before the three actions exist.
        for action in getattr(self, "_actions", ()):
            action.on_log = value

    def _choose(self, player: str, state: State) -> BaseAction:
        if is_live_stream(state) or not supports(
            state, MediaPlayerEntityFeature.NEXT_TRACK
        ):
            chosen = self.switch if self.has_station else self.mute
        else:
            chosen = self.skip
        self._chosen[player] = chosen
        return chosen

    def kind_for(self, player: str) -> str:
        chosen = self._chosen.get(player)
        return chosen.kind if chosen else self.kind

    def repeat_is_stale(self, player: str) -> bool:
        return self.switch.repeat_is_stale(player)

    async def async_match(self, player: str, state: State, consecutive: int) -> bool:
        chosen = self._choose(player, state)
        _LOGGER.debug(
            "%s: %s plays a %s; using %s",
            self.rule_name,
            player,
            "stream" if chosen is not self.skip else "track",
            chosen.kind,
        )
        return await chosen.async_match(player, state, consecutive)

    async def async_match_ended(self, player: str, state: State) -> None:
        for action in (self.skip, self.switch, self.mute):
            await action.async_match_ended(player, state)

    @callback
    def async_player_state(self, player: str, state: State | None) -> None:
        self.switch.async_player_state(player, state)

    @callback
    def async_player_stopped(self, player: str) -> None:
        for action in (self.skip, self.switch, self.mute):
            action.async_player_stopped(player)

    @callback
    def async_shutdown(self) -> None:
        for action in (self.skip, self.switch, self.mute):
            action.async_shutdown()


ACTIONS: dict[RuleAction, type[BaseAction]] = {
    RuleAction.AUTO: AutoAction,
    RuleAction.SKIP: SkipAction,
    RuleAction.SWITCH: SwitchAction,
    RuleAction.MUTE: MuteAction,
}


def build_action(
    hass: HomeAssistant, rule_name: str, action: RuleAction, data: Mapping[str, Any]
) -> BaseAction:
    """Create the action object of a rule."""
    return ACTIONS[action](hass, rule_name, data)
