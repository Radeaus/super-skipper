"""The mute action."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.super_skipper.const import (
    CONF_ACTION,
    CONF_HOLD_SECONDS,
    CONF_IGNORE_TEXTS,
    CONF_MAX_MUTE_MINUTES,
    RuleAction,
)

from .conftest import advance, make_entry, play, rule, setup_entry


def mute_rule(**overrides):
    data = {
        CONF_ACTION: RuleAction.MUTE.value,
        CONF_HOLD_SECONDS: 10,
        CONF_IGNORE_TEXTS: ["Radio 2"],
    }
    data.update(overrides)
    return rule(**data)


async def test_mute_until_over(hass: HomeAssistant, freezer) -> None:
    mutes = async_mock_service(hass, "media_player", "volume_mute")
    await setup_entry(hass, make_entry(mute_rule()))
    play(hass, is_volume_muted=False)
    await advance(hass, freezer, 2)
    assert len(mutes) == 1
    assert mutes[0].data["is_volume_muted"] is True

    # Station information in between keeps the mute.
    play(hass, title="Radio 2 - De beste muziek", artist=None, is_volume_muted=True)
    await advance(hass, freezer, 30)
    assert len(mutes) == 1

    # Another track: unmute after the hold time, unless the keyword returns.
    play(hass, title="Hello", artist="Adele", is_volume_muted=True)
    await advance(hass, freezer, 5)
    play(hass, title="Waterloo", is_volume_muted=True)
    await advance(hass, freezer, 20)
    assert len(mutes) == 1
    play(hass, title="Hello", artist="Adele", is_volume_muted=True)
    await advance(hass, freezer, 5)
    assert len(mutes) == 1
    await advance(hass, freezer, 7)
    assert len(mutes) == 2
    assert mutes[1].data["is_volume_muted"] is False


async def test_mute_with_volume_set(hass: HomeAssistant, freezer) -> None:
    """A player without mute support gets its volume set to zero and back."""
    volumes = async_mock_service(hass, "media_player", "volume_set")
    await setup_entry(hass, make_entry(mute_rule()))
    features = MediaPlayerEntityFeature.VOLUME_SET | MediaPlayerEntityFeature.PLAY
    play(hass, features=features, volume_level=0.4)
    await advance(hass, freezer, 2)
    assert volumes[0].data["volume_level"] == 0.0
    play(hass, title="Hello", artist="Adele", features=features, volume_level=0.0)
    await advance(hass, freezer, 12)
    assert volumes[1].data["volume_level"] == 0.4


async def test_mute_limits_and_stop(hass: HomeAssistant, freezer, caplog) -> None:
    mutes = async_mock_service(hass, "media_player", "volume_mute")
    await setup_entry(hass, make_entry(mute_rule(**{CONF_MAX_MUTE_MINUTES: 1})))
    # Already muted by the user: leave it.
    play(hass, is_volume_muted=True)
    await advance(hass, freezer, 2)
    assert not mutes
    play(hass, title="Waterloo", is_volume_muted=False)
    await advance(hass, freezer, 6)
    assert len(mutes) == 1
    # The safety limit unmutes.
    await advance(hass, freezer, 61)
    assert len(mutes) == 2
    # Stopping the player unmutes right away.
    play(hass, title="Gold", is_volume_muted=False)
    await advance(hass, freezer, 6)
    assert len(mutes) == 3
    play(hass, title="Gold", state=MediaPlayerState.OFF)
    await advance(hass, freezer, 1)
    assert len(mutes) == 4
    # A player that cannot be muted at all.
    play(hass, title="Money", features=MediaPlayerEntityFeature.PLAY)
    await advance(hass, freezer, 6)
    assert len(mutes) == 4
    assert "cannot be muted" in caplog.text


async def test_unload_unmutes(hass: HomeAssistant, freezer) -> None:
    mutes = async_mock_service(hass, "media_player", "volume_mute")
    entry = await setup_entry(hass, make_entry(mute_rule()))
    play(hass, is_volume_muted=False)
    await advance(hass, freezer, 2)
    assert len(mutes) == 1
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(mutes) == 2
    assert mutes[1].data["is_volume_muted"] is False
