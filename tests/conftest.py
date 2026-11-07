"""Fixtures for the Super Skipper tests."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed_exact,
)

from custom_components.super_skipper.const import (
    CONF_ACTION,
    CONF_KEYWORDS,
    CONF_NAME,
    CONF_PLAYERS,
    DOMAIN,
    SUBENTRY_TYPE_RULE,
    RuleAction,
)

PLAYER = "media_player.living_room"
OTHER_PLAYER = "media_player.kitchen"

ALL_FEATURES = (
    MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PLAY
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load the integration from custom_components."""


def rule(**overrides: Any) -> dict[str, Any]:
    """The data of a rule, with defaults a test can override."""
    data: dict[str, Any] = {
        CONF_NAME: "No ABBA",
        CONF_KEYWORDS: ["ABBA"],
        CONF_PLAYERS: [PLAYER],
        CONF_ACTION: RuleAction.SKIP.value,
    }
    data.update(overrides)
    return data


def make_entry(
    *rules: dict[str, Any], options: dict[str, Any] | None = None
) -> MockConfigEntry:
    """Build the integration entry with rules as subentries."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Super Skipper",
        data={},
        options=options or {},
        subentries_data=[
            {
                "data": data,
                "subentry_type": SUBENTRY_TYPE_RULE,
                "title": data[CONF_NAME],
                "unique_id": None,
            }
            for data in rules
        ],
    )


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> MockConfigEntry:
    """Add the entry and load it."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def play(
    hass: HomeAssistant,
    entity_id: str = PLAYER,
    title: str | None = "Dancing Queen",
    artist: str | None = "ABBA",
    state: str = MediaPlayerState.PLAYING,
    features: int = ALL_FEATURES,
    **attributes: Any,
) -> None:
    """Let a fake player report what it plays."""
    attrs: dict[str, Any] = {
        ATTR_SUPPORTED_FEATURES: features,
        "friendly_name": entity_id.split(".")[1].replace("_", " ").title(),
    }
    if title is not None:
        attrs["media_title"] = title
    if artist is not None:
        attrs["media_artist"] = artist
    attrs.update(attributes)
    hass.states.async_set(entity_id, state, attrs)


async def advance(hass: HomeAssistant, freezer, seconds: float) -> None:
    """Move time forward in small steps, so timers that schedule timers fire too."""
    await hass.async_block_till_done()
    while seconds > 0:
        step = min(seconds, 1.0)
        seconds -= step
        freezer.tick(step)
        async_fire_time_changed_exact(hass)
        await hass.async_block_till_done()
