"""The automatic action, and the history that survives restarts."""

from __future__ import annotations

from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.super_skipper.const import (
    CONF_ACTION,
    CONF_RETURN_AFTER_MINUTES,
    CONF_RETURN_FALLBACK_MEDIA,
    CONF_STATION,
    RuleAction,
)
from custom_components.super_skipper.history import STORAGE_KEY

from .conftest import PLAYER, advance, make_entry, play, rule, setup_entry
from .test_switch_action import FALLBACK, STATION


def auto_rule(**overrides):
    return rule(**{CONF_ACTION: RuleAction.AUTO.value, **overrides})


async def test_auto_skips_tracks(hass: HomeAssistant, freezer) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    mutes = async_mock_service(hass, "media_player", "volume_mute")
    await setup_entry(hass, make_entry(auto_rule()))
    # A Spotify track: known length and a spotify id.
    play(
        hass,
        media_duration=231,
        media_content_id="spotify:track:1",
        media_content_type="music",
    )
    await advance(hass, freezer, 2)
    assert len(skips) == 1
    assert not mutes
    sensor = hass.states.get("sensor.no_abba_last_match")
    assert sensor.attributes["action"] == "skip"


async def test_auto_mutes_streams_without_station(hass: HomeAssistant, freezer) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    mutes = async_mock_service(hass, "media_player", "volume_mute")
    await setup_entry(hass, make_entry(auto_rule()))
    # A radio stream: no duration, a stream url.
    play(
        hass,
        media_content_id="http://stream.example/radio2",
        media_content_type="music",
    )
    await advance(hass, freezer, 2)
    assert not skips
    assert len(mutes) == 1
    assert hass.states.get("sensor.no_abba_last_match").attributes["action"] == "mute"
    # Something else plays: the sound comes back.
    play(
        hass,
        title="Hello",
        artist="Adele",
        media_content_id="http://stream.example/radio2",
    )
    await advance(hass, freezer, 25)
    assert len(mutes) == 2
    # A player that cannot skip is treated like a stream as well.
    play(
        hass,
        title="Waterloo",
        media_duration=200,
        features=MediaPlayerEntityFeature.VOLUME_MUTE,
    )
    await advance(hass, freezer, 6)
    assert len(mutes) == 3


async def test_auto_switches_streams_with_station(hass: HomeAssistant, freezer) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    plays = async_mock_service(hass, "media_player", "play_media")
    await setup_entry(
        hass,
        make_entry(
            auto_rule(
                **{
                    CONF_STATION: STATION,
                    CONF_RETURN_AFTER_MINUTES: 1,
                    CONF_RETURN_FALLBACK_MEDIA: FALLBACK,
                }
            )
        ),
    )
    play(
        hass,
        media_content_type="channel",
        media_content_id="x-sonosapi-stream:s1?sid=254",
    )
    await advance(hass, freezer, 2)
    assert not skips
    assert len(plays) == 1
    assert plays[0].data["media_content_id"] == STATION["media_content_id"]
    assert hass.states.get("sensor.no_abba_last_match").attributes["action"] == "switch"
    # Meanwhile a track on the same rule still skips.
    play(hass, title="Waterloo", media_duration=180, media_content_id="spotify:track:2")
    await advance(hass, freezer, 6)
    assert len(skips) == 1


async def test_history_survives_reload_and_restart(
    hass: HomeAssistant, freezer, hass_storage
) -> None:
    """The last match and the activity are stored, and dropped with the rule."""
    async_mock_service(hass, "media_player", "media_next_track")
    entry = await setup_entry(hass, make_entry(rule(), rule(name="Other")))
    play(hass)
    await advance(hass, freezer, 2)
    sensor = hass.states.get("sensor.no_abba_last_match")
    assert sensor.state == "ABBA – Dancing Queen"
    rule_id = next(iter(entry.subentries))
    watcher = entry.runtime_data.watchers[rule_id]
    assert watcher.match_count == 1
    assert watcher.events[-1]["message"].startswith("skipped")

    # Saved (after the delay) ...
    await advance(hass, freezer, 3)
    assert rule_id in hass_storage[STORAGE_KEY]["data"]["rules"]

    # ... and still there after a reload.
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.no_abba_last_match").state == "ABBA – Dancing Queen"
    assert hass.states.get("sensor.no_abba_last_match").attributes["matches"] == 1
    assert entry.runtime_data.watchers[rule_id].events[-1]["player"] == PLAYER

    # Deleting the rule drops its history at the next load.
    hass.config_entries.async_remove_subentry(entry, rule_id)
    await hass.async_block_till_done()
    await advance(hass, freezer, 3)
    assert rule_id not in hass_storage[STORAGE_KEY]["data"]["rules"]
