"""The skip action and the engine around it."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.super_skipper.const import (
    CONF_CONDITIONS,
    CONF_IGNORE_TEXTS,
    CONF_MATCH_FIELDS,
    CONF_MATCH_MODE,
    CONF_MAX_CONSECUTIVE,
    CONF_PERSONS,
    CONF_PLAYERS,
    CONF_PRESENCE_MODE,
    DOMAIN,
    MatchMode,
    PresenceMode,
)

from .conftest import OTHER_PLAYER, PLAYER, advance, make_entry, play, rule, setup_entry


async def test_skips_once_per_track(hass: HomeAssistant, freezer) -> None:
    """A matching track is skipped once, whatever else the player reports."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    play(hass, title="Hello", artist="Adele")
    entry = await setup_entry(hass, make_entry(rule()))
    assert entry.state is ConfigEntryState.LOADED

    play(hass)  # Dancing Queen by ABBA
    await hass.async_block_till_done()
    assert not skips  # waits for the confirmation delay
    await advance(hass, freezer, 1.1)
    assert len(skips) == 1
    assert skips[0].data["entity_id"] == PLAYER

    # Position updates do not count as a new track.
    play(hass, media_position=12)
    await advance(hass, freezer, 2)
    assert len(skips) == 1

    # Something else plays: nothing happens.
    play(hass, title="Hello", artist="Adele")
    await advance(hass, freezer, 2)
    assert len(skips) == 1

    sensor = hass.states.get("sensor.no_abba_last_match")
    assert sensor is not None
    assert sensor.state == "ABBA – Dancing Queen"
    assert sensor.attributes["player"] == PLAYER
    assert sensor.attributes["matches"] == 1


async def test_flicker_is_ignored(hass: HomeAssistant, freezer) -> None:
    """Metadata that changes again within the confirmation delay is not acted on."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(hass, make_entry(rule()))
    play(hass)
    await advance(hass, freezer, 0.5)
    play(hass, title="Hello", artist="Adele")
    await advance(hass, freezer, 2)
    assert not skips


async def test_consecutive_limit(hass: HomeAssistant, freezer) -> None:
    """After the limit the rule waits until something else plays."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(
        hass,
        make_entry(rule(**{CONF_MAX_CONSECUTIVE: 2})),
    )
    for index in range(4):
        play(hass, title=f"Track {index}")
        await advance(hass, freezer, 6)
    assert len(skips) == 2
    play(hass, title="Hello", artist="Adele")
    await advance(hass, freezer, 6)
    play(hass, title="Waterloo")
    await advance(hass, freezer, 6)
    assert len(skips) == 3


async def test_cooldown_delays_the_next_skip(hass: HomeAssistant, freezer) -> None:
    """A second match right after a skip waits for the cooldown."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(hass, make_entry(rule()))
    play(hass, title="Track 1")
    await advance(hass, freezer, 1.1)
    assert len(skips) == 1
    play(hass, title="Track 2")
    await advance(hass, freezer, 1.1)
    assert len(skips) == 1
    await advance(hass, freezer, 4)
    assert len(skips) == 2


async def test_player_without_skip(hass: HomeAssistant, freezer, caplog) -> None:
    """A player that cannot skip is left alone."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(hass, make_entry(rule()))
    play(hass, features=MediaPlayerEntityFeature.PLAY)
    await advance(hass, freezer, 2)
    assert not skips
    assert "cannot skip" in caplog.text


async def test_not_playing_and_group_members(hass: HomeAssistant, freezer) -> None:
    """Paused players and group members are not touched."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(hass, make_entry(rule(**{CONF_PLAYERS: [PLAYER, OTHER_PLAYER]})))
    play(hass, state=MediaPlayerState.PAUSED)
    await advance(hass, freezer, 2)
    assert not skips
    play(hass, OTHER_PLAYER, group_members=[PLAYER, OTHER_PLAYER])
    await advance(hass, freezer, 2)
    assert not skips
    play(hass, group_members=[PLAYER, OTHER_PLAYER])
    await advance(hass, freezer, 2)
    assert len(skips) == 1
    # Pausing during the confirmation delay cancels it.
    play(hass, title="Waterloo")
    await advance(hass, freezer, 0.5)
    play(hass, title="Waterloo", state=MediaPlayerState.PAUSED)
    await advance(hass, freezer, 6)
    assert len(skips) == 1
    hass.states.async_remove(PLAYER)
    await advance(hass, freezer, 2)
    assert len(skips) == 1


async def test_matching_options(hass: HomeAssistant, freezer) -> None:
    """Whole words, substrings, fields and ignored texts."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(
        hass,
        make_entry(
            rule(
                **{
                    CONF_MATCH_FIELDS: ["title", "artist", "channel"],
                    CONF_IGNORE_TEXTS: ["Radio 2"],
                }
            ),
        ),
    )
    play(hass, title="Kabbalah", artist="Someone")
    await advance(hass, freezer, 2)
    assert not skips
    play(hass, title="Gold", artist="Abba")
    await advance(hass, freezer, 2)
    assert len(skips) == 1
    # Station information in between does not count as a new track …
    play(hass, title="Radio 2 - De beste muziek", artist=None)
    await advance(hass, freezer, 6)
    assert len(skips) == 1
    # … so the same track afterwards is not skipped again.
    play(hass, title="Gold", artist="Abba")
    await advance(hass, freezer, 6)
    assert len(skips) == 1
    play(hass, title="Song", artist="Band", media_channel="ABBA Radio")
    await advance(hass, freezer, 6)
    assert len(skips) == 2


async def test_substring_and_regex(hass: HomeAssistant, freezer) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(
        hass,
        make_entry(
            rule(
                **{
                    "name": "Sub",
                    CONF_MATCH_MODE: MatchMode.SUBSTRING.value,
                    "keywords": ["abba"],
                }
            ),
            rule(
                **{
                    "name": "Re",
                    CONF_MATCH_MODE: MatchMode.REGEX.value,
                    "keywords": [r"^ad(vert)?\b"],
                }
            ),
        ),
    )
    play(hass, title="Kabbalah", artist="Someone")
    await advance(hass, freezer, 2)
    assert len(skips) == 1
    play(hass, title="Advert", artist=None)
    await advance(hass, freezer, 6)
    assert len(skips) == 2


async def test_switch_and_snooze(hass: HomeAssistant, freezer) -> None:
    """The enabled switch and the snooze button stop the rule."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(hass, make_entry(rule(), options={"snooze_minutes": 1}))
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.no_abba_enabled"}, blocking=True
    )
    play(hass, title="Track 1")
    await advance(hass, freezer, 2)
    assert not skips
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.no_abba_enabled"}, blocking=True
    )
    play(hass, title="Track 2")
    await advance(hass, freezer, 2)
    assert len(skips) == 1

    await hass.services.async_call(
        "button", "press", {"entity_id": "button.super_skipper_snooze"}, blocking=True
    )
    assert hass.states.get("sensor.super_skipper_snoozed_until").state != "unknown"
    play(hass, title="Track 3")
    await advance(hass, freezer, 6)
    assert len(skips) == 1
    await advance(hass, freezer, 60)
    assert hass.states.get("sensor.super_skipper_snoozed_until").state == "unknown"
    play(hass, title="Track 4")
    await advance(hass, freezer, 6)
    assert len(skips) == 2


async def test_enabled_switch_is_restored(hass: HomeAssistant, freezer) -> None:
    """A rule that was turned off stays off after a restart."""
    from homeassistant.core import State
    from pytest_homeassistant_custom_component.common import mock_restore_cache

    entry = make_entry(rule())
    mock_restore_cache(hass, [State("switch.no_abba_enabled", "off")])
    await setup_entry(hass, entry)
    assert hass.states.get("switch.no_abba_enabled").state == "off"


async def test_persons_and_conditions(hass: HomeAssistant, freezer) -> None:
    """Presence and extra conditions gate the rule."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(
        hass,
        make_entry(
            rule(
                **{
                    CONF_PERSONS: ["person.quinten"],
                    CONF_PRESENCE_MODE: PresenceMode.ANY_HOME.value,
                    CONF_CONDITIONS: [
                        {
                            "condition": "state",
                            "entity_id": "input_boolean.party",
                            "state": "off",
                        }
                    ],
                }
            )
        ),
    )
    hass.states.async_set("person.quinten", "not_home")
    hass.states.async_set("input_boolean.party", "off")
    play(hass, title="Track 1")
    await advance(hass, freezer, 2)
    assert not skips
    hass.states.async_set("person.quinten", "home")
    play(hass, title="Track 2")
    await advance(hass, freezer, 2)
    assert len(skips) == 1
    hass.states.async_set("input_boolean.party", "on")
    play(hass, title="Track 3")
    await advance(hass, freezer, 6)
    assert len(skips) == 1


async def test_presence_modes(hass: HomeAssistant, freezer) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(
        hass,
        make_entry(
            rule(
                name="All",
                **{
                    CONF_PERSONS: ["person.a", "person.b"],
                    CONF_PRESENCE_MODE: "all_home",
                },
            ),
            rule(
                name="None",
                **{CONF_PERSONS: ["person.a"], CONF_PRESENCE_MODE: "none_home"},
            ),
        ),
    )
    hass.states.async_set("person.a", "home")
    hass.states.async_set("person.b", "not_home")
    play(hass, title="Track 1")
    await advance(hass, freezer, 2)
    assert not skips  # "All": b is away; "None": a is home
    hass.states.async_set("person.b", "home")
    play(hass, title="Track 2")
    await advance(hass, freezer, 6)
    assert len(skips) == 1


async def test_unload_and_registry(hass: HomeAssistant, freezer) -> None:
    """Entities belong to the rule's subentry, and unloading stops everything."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    entry = await setup_entry(hass, make_entry(rule()))
    registry = er.async_get(hass)
    switch = registry.async_get("switch.no_abba_enabled")
    assert switch is not None
    subentry_id = next(iter(entry.subentries))
    assert switch.config_subentry_id == subentry_id
    assert switch.unique_id == f"{subentry_id}_enabled"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    play(hass)
    await advance(hass, freezer, 2)
    assert not skips


async def test_removing_a_rule_reloads(hass: HomeAssistant, freezer) -> None:
    """Deleting the subentry removes its entities."""
    entry = await setup_entry(hass, make_entry(rule()))
    assert hass.states.get("switch.no_abba_enabled") is not None
    subentry_id = next(iter(entry.subentries))
    hass.config_entries.async_remove_subentry(entry, subentry_id)
    await hass.async_block_till_done()
    assert hass.states.get("switch.no_abba_enabled") is None
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("button.super_skipper_snooze") is not None


async def test_diagnostics(hass: HomeAssistant, freezer) -> None:
    from custom_components.super_skipper.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    async_mock_service(hass, "media_player", "media_next_track")
    entry = await setup_entry(hass, make_entry(rule()))
    play(hass)
    await advance(hass, freezer, 2)
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["rules"][0]["matches"] == 1
    assert result["rules"][0]["last_match"]["description"] == "ABBA – Dancing Queen"
    assert result["rules"][0]["players"][PLAYER] == "playing"
    assert result["snoozed_until"] is None
    assert result["rules"][0]["data"]["keywords"] == ["ABBA"]
    assert DOMAIN in entry.domain
