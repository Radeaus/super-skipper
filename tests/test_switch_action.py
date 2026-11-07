"""The switch-station action: diverting, returning, verifying, fallback."""

from __future__ import annotations

from homeassistant.components.media_player import MediaPlayerState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.super_skipper.const import (
    CONF_ACTION,
    CONF_REPEAT_LIMIT,
    CONF_REPEAT_MODE,
    CONF_RETURN_AFTER_MINUTES,
    CONF_RETURN_FALLBACK_ACTIONS,
    CONF_RETURN_FALLBACK_MEDIA,
    CONF_STATION,
    CONF_STATION_ACTIONS,
    RepeatMode,
    RuleAction,
)

from .conftest import PLAYER, advance, make_entry, play, rule, setup_entry

STATION = {
    "entity_id": PLAYER,
    "media_content_id": "media-source://radio_browser/1234",
    "media_content_type": "audio/mpeg",
}
FALLBACK = {
    "entity_id": PLAYER,
    "media_content_id": "media-source://radio_browser/9999",
    "media_content_type": "audio/mpeg",
}
SOURCE_ID = "http://stream.example/radio2"
ALT_ID = "http://resolved.example/1234.mp3"


def switch_rule(**overrides):
    data = {
        CONF_ACTION: RuleAction.SWITCH.value,
        CONF_STATION: STATION,
        CONF_RETURN_AFTER_MINUTES: 1,
        CONF_RETURN_FALLBACK_MEDIA: FALLBACK,
    }
    data.update(overrides)
    return rule(**data)


def radio(
    hass: HomeAssistant,
    title: str = "Dancing Queen",
    artist: str | None = "ABBA",
    content_id: str = SOURCE_ID,
    **kw,
):
    play(
        hass,
        title=title,
        artist=artist,
        media_content_id=content_id,
        media_content_type="music",
        **kw,
    )


async def test_switch_and_return(hass: HomeAssistant, freezer) -> None:
    """Switch to the station, come back after a minute, and verify."""
    plays = async_mock_service(hass, "media_player", "play_media")
    await setup_entry(hass, make_entry(switch_rule()))
    radio(hass)
    await advance(hass, freezer, 2)
    assert len(plays) == 1
    assert plays[0].data["media_content_id"] == STATION["media_content_id"]
    assert plays[0].data["media_content_type"] == "audio/mpeg"

    # The player reports the alternative station; it may match the keyword too.
    radio(hass, title="ABBA Gold hour", artist="Alt station", content_id=ALT_ID)
    await advance(hass, freezer, 20)
    assert len(plays) == 1

    # After a minute Super Skipper plays the source again.
    await advance(hass, freezer, 45)
    assert len(plays) == 2
    assert plays[1].data["media_content_id"] == SOURCE_ID
    assert plays[1].data["media_content_type"] == "music"

    # The player confirms within the verification window: no fallback.
    radio(hass, title="Hello", artist="Adele")
    await advance(hass, freezer, 15)
    assert len(plays) == 2
    sensor = hass.states.get("sensor.no_abba_last_match")
    assert sensor.attributes["action"] == "switch"


async def test_fallback_when_return_fails(hass: HomeAssistant, freezer) -> None:
    """When the player does not come back, the fallback plays."""
    plays = async_mock_service(hass, "media_player", "play_media")
    await setup_entry(hass, make_entry(switch_rule()))
    radio(hass)
    await advance(hass, freezer, 2)
    radio(hass, title="Other", artist="Alt", content_id=ALT_ID)
    await advance(hass, freezer, 65)
    assert len(plays) == 2
    # Still on the alternative station after the verification window.
    await advance(hass, freezer, 11)
    assert len(plays) == 3
    assert plays[2].data["media_content_id"] == FALLBACK["media_content_id"]


async def test_fallback_actions_when_source_cannot_replay(
    hass: HomeAssistant, freezer
) -> None:
    """A source without a replayable id goes straight to the fallback actions."""
    plays = async_mock_service(hass, "media_player", "play_media")
    scripts = async_mock_service(hass, "script", "turn_on")
    await setup_entry(
        hass,
        make_entry(
            switch_rule(
                **{
                    CONF_RETURN_FALLBACK_MEDIA: None,
                    CONF_RETURN_FALLBACK_ACTIONS: [
                        {
                            "action": "script.turn_on",
                            "target": {"entity_id": "script.radio2"},
                        }
                    ],
                }
            )
        ),
    )
    radio(hass, content_id="x-rincon-queue:RINCON_123#0")
    await advance(hass, freezer, 2)
    assert len(plays) == 1
    await advance(hass, freezer, 70)
    assert len(plays) == 1
    assert len(scripts) == 1
    assert scripts[0].data["entity_id"] == ["script.radio2"]


async def test_select_source_return(hass: HomeAssistant, freezer) -> None:
    """Without a content id the source input is selected again."""
    plays = async_mock_service(hass, "media_player", "play_media")
    selects = async_mock_service(hass, "media_player", "select_source")
    await setup_entry(hass, make_entry(switch_rule()))
    play(hass, source="Radio 2", source_list=["Radio 2", "TV"])
    await advance(hass, freezer, 2)
    assert len(plays) == 1
    await advance(hass, freezer, 70)
    assert len(selects) == 1
    assert selects[0].data["source"] == "Radio 2"
    play(
        hass,
        title="Hello",
        artist="Adele",
        source="Radio 2",
        source_list=["Radio 2", "TV"],
    )
    await advance(hass, freezer, 15)
    assert len(plays) == 1  # verified through the source, no fallback


async def test_station_actions_and_no_return(hass: HomeAssistant, freezer) -> None:
    """Actions instead of a station, and staying there."""
    plays = async_mock_service(hass, "media_player", "play_media")
    scripts = async_mock_service(hass, "script", "turn_on")
    await setup_entry(
        hass,
        make_entry(
            switch_rule(
                **{
                    CONF_STATION: None,
                    CONF_STATION_ACTIONS: [
                        {
                            "action": "script.turn_on",
                            "target": {"entity_id": "script.alt"},
                        }
                    ],
                    CONF_RETURN_AFTER_MINUTES: 0,
                }
            )
        ),
    )
    radio(hass)
    await advance(hass, freezer, 2)
    assert len(scripts) == 1
    await advance(hass, freezer, 600)
    assert not plays


async def test_user_change_cancels_return(hass: HomeAssistant, freezer) -> None:
    """When the user starts something else, Super Skipper does not come back."""
    plays = async_mock_service(hass, "media_player", "play_media")
    await setup_entry(hass, make_entry(switch_rule()))
    radio(hass)
    await advance(hass, freezer, 2)
    radio(hass, title="Other", artist="Alt", content_id=ALT_ID)
    await advance(hass, freezer, 20)  # the alternative station has settled
    radio(hass, title="Podcast", artist="Someone", content_id="spotify:episode:1")
    await advance(hass, freezer, 70)
    assert len(plays) == 1


async def test_stop_cancels_return(hass: HomeAssistant, freezer) -> None:
    plays = async_mock_service(hass, "media_player", "play_media")
    await setup_entry(hass, make_entry(switch_rule()))
    radio(hass)
    await advance(hass, freezer, 2)
    radio(hass, title="Other", artist="Alt", content_id=ALT_ID)
    await advance(hass, freezer, 20)
    radio(
        hass, title="Other", artist="Alt", content_id=ALT_ID, state=MediaPlayerState.OFF
    )
    await advance(hass, freezer, 70)
    assert len(plays) == 1


async def test_repeat_limited(hass: HomeAssistant, freezer) -> None:
    """The keyword keeps playing after returning: switch again up to the limit."""
    plays = async_mock_service(hass, "media_player", "play_media")
    await setup_entry(hass, make_entry(switch_rule(**{CONF_REPEAT_LIMIT: 2})))

    async def episode(expected_returns: bool) -> None:
        radio(hass, title="Other", artist="Alt", content_id=ALT_ID)
        before = len(plays)
        # Wait for the return, then put the source back within the verification window.
        for _ in range(70):
            await advance(hass, freezer, 1)
            if len(plays) > before:
                break
        if expected_returns:
            radio(hass)  # back on the source, ABBA still plays
            await advance(hass, freezer, 15)

    radio(hass)
    await advance(hass, freezer, 2)
    assert len(plays) == 1  # first switch
    await episode(True)
    # return (2) + second switch after the keyword is found again (3)
    assert len(plays) == 3
    await episode(True)
    # return (4) + the limit is reached: switch once more and stay (5)
    assert len(plays) == 5
    await episode(False)
    assert len(plays) == 5  # no more returns


async def test_repeat_once_and_unlimited(hass: HomeAssistant, freezer) -> None:
    plays = async_mock_service(hass, "media_player", "play_media")
    await setup_entry(
        hass, make_entry(switch_rule(**{CONF_REPEAT_MODE: RepeatMode.ONCE.value}))
    )
    radio(hass)
    await advance(hass, freezer, 2)
    radio(hass, title="Other", artist="Alt", content_id=ALT_ID)
    await advance(hass, freezer, 65)
    assert len(plays) == 2
    radio(hass)
    await advance(hass, freezer, 15)
    assert len(plays) == 2  # once: leave it
    # Later the same keyword starts a new episode.
    radio(hass, title="Hello", artist="Adele")
    await advance(hass, freezer, 6)
    radio(hass, title="Waterloo")
    await advance(hass, freezer, 6)
    assert len(plays) == 3


async def test_sonos_snapshot_and_restore(hass: HomeAssistant, freezer) -> None:
    """Sonos players use snapshot and restore."""
    plays = async_mock_service(hass, "media_player", "play_media")
    snapshots = async_mock_service(hass, "sonos", "snapshot")
    restores = async_mock_service(hass, "sonos", "restore")
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "media_player", "sonos", "RINCON_1", suggested_object_id="living_room"
    )
    await setup_entry(hass, make_entry(switch_rule()))
    radio(hass, content_id="x-sonosapi-stream:s1234?sid=254")
    await advance(hass, freezer, 2)
    assert len(snapshots) == 1
    assert len(plays) == 1
    radio(hass, title="Other", artist="Alt", content_id=ALT_ID)
    await advance(hass, freezer, 65)
    assert len(restores) == 1
    assert len(plays) == 1


async def test_failed_service_calls(hass: HomeAssistant, freezer, caplog) -> None:
    """A station that cannot be played is reported, not raised."""
    await setup_entry(hass, make_entry(switch_rule()))
    radio(hass)
    await advance(hass, freezer, 2)  # media_player.play_media is not registered
    assert "play_media failed" in caplog.text
    assert hass.states.get("sensor.no_abba_last_match").state == "unknown"
