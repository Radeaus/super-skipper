"""The order of the rules: the first rule that matches a track acts."""

from __future__ import annotations

from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.super_skipper.const import (
    CONF_ACTION,
    CONF_NAME,
    CONF_PLAYERS,
    CONF_RULE_ORDER,
    DOMAIN,
    PANEL_STATIC_URL,
)

from .conftest import OTHER_PLAYER, PLAYER, advance, make_entry, play, rule, setup_entry
from .test_panel import _next_event, _result


async def test_first_rule_wins(hass: HomeAssistant, freezer) -> None:
    """Two rules with the same keyword: only the first acts on the player."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    mutes = async_mock_service(hass, "media_player", "volume_mute")
    entry = await setup_entry(
        hass,
        make_entry(
            rule(**{CONF_NAME: "Skip it"}),
            rule(**{CONF_NAME: "Mute it", CONF_ACTION: "mute"}),
        ),
    )
    skip_id, mute_id = (subentry.subentry_id for subentry in entry.subentries.values())
    watchers = entry.runtime_data.watchers
    assert list(watchers) == [skip_id, mute_id]
    assert watchers[mute_id].above == [watchers[skip_id]]

    play(hass)
    await advance(hass, freezer, 2)
    assert len(skips) == 1
    assert not mutes
    assert watchers[skip_id].match_count == 1
    assert watchers[mute_id].match_count == 0

    # A rule that is off, or does not watch the player, leaves the track to
    # the rules below it.
    watchers[skip_id].async_set_enabled(False)
    play(hass, title="Waterloo")
    await advance(hass, freezer, 2)
    assert len(skips) == 1
    assert len(mutes) == 1

    watchers[skip_id].async_set_enabled(True)
    play(hass, title="Fernando")
    await advance(hass, freezer, 2)
    assert len(skips) == 2
    assert len(mutes) == 1


async def test_rules_above_only_count_for_their_players(
    hass: HomeAssistant, freezer
) -> None:
    skips = async_mock_service(hass, "media_player", "media_next_track")
    await setup_entry(
        hass,
        make_entry(
            rule(**{CONF_NAME: "Kitchen", CONF_PLAYERS: [OTHER_PLAYER]}),
            rule(**{CONF_NAME: "Living room"}),
        ),
    )
    play(hass)
    await advance(hass, freezer, 2)
    assert [call.data["entity_id"] for call in skips] == [PLAYER]


async def test_saved_order_is_used(hass: HomeAssistant, freezer) -> None:
    """The order in the entry data overrides the creation order; unknown last."""
    skips = async_mock_service(hass, "media_player", "media_next_track")
    mutes = async_mock_service(hass, "media_player", "volume_mute")
    entry = make_entry(
        rule(**{CONF_NAME: "Skip it"}),
        rule(**{CONF_NAME: "Mute it", CONF_ACTION: "mute"}),
        rule(**{CONF_NAME: "Third"}),
    )
    skip_id, mute_id, third_id = (
        subentry.subentry_id for subentry in entry.subentries.values()
    )
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        entry, data={CONF_RULE_ORDER: [mute_id, "gone", skip_id]}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert list(entry.runtime_data.watchers) == [mute_id, skip_id, third_id]

    play(hass)
    await advance(hass, freezer, 2)
    assert len(mutes) == 1
    assert not skips


async def test_reorder_from_panel(hass: HomeAssistant, hass_ws_client, freezer) -> None:
    """Reordering through the API applies at once, without a reload."""
    assert await async_setup_component(hass, "frontend", {})
    skips = async_mock_service(hass, "media_player", "media_next_track")
    mutes = async_mock_service(hass, "media_player", "volume_mute")
    entry = await setup_entry(
        hass,
        make_entry(
            rule(**{CONF_NAME: "Skip it"}),
            rule(**{CONF_NAME: "Mute it", CONF_ACTION: "mute"}),
        ),
    )
    skip_id, mute_id = (subentry.subentry_id for subentry in entry.subentries.values())
    data = entry.runtime_data
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": f"{DOMAIN}/subscribe"})
    msg = await client.receive_json()
    sub_id = msg["id"]
    state = await _next_event(client, sub_id)
    assert [r["id"] for r in state["rules"]] == [skip_id, mute_id]

    # Every rule must be listed exactly once.
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/reorder_rules", "order": [mute_id]}
    )
    assert (await _result(client))["error"]["code"] == "invalid_order"
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/reorder_rules", "order": [mute_id, skip_id, skip_id]}
    )
    assert (await _result(client))["error"]["code"] == "invalid_order"

    # The same order changes nothing.
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/reorder_rules", "order": [skip_id, mute_id]}
    )
    assert (await _result(client))["success"]
    assert CONF_RULE_ORDER not in entry.data

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/reorder_rules", "order": [mute_id, skip_id]}
    )
    assert (await _result(client))["success"]
    await hass.async_block_till_done()
    assert entry.data[CONF_RULE_ORDER] == [mute_id, skip_id]
    assert entry.runtime_data is data  # not reloaded
    assert data.reordering is False
    assert list(data.watchers) == [mute_id, skip_id]
    assert data.watchers[skip_id].above == [data.watchers[mute_id]]

    await advance(hass, freezer, 1)
    state = await _next_event(client, sub_id)
    assert [r["id"] for r in state["rules"]] == [mute_id, skip_id]

    play(hass)
    await advance(hass, freezer, 2)
    assert len(mutes) == 1
    assert not skips

    # The order survives a reload, and a later change still reloads.
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert list(entry.runtime_data.watchers) == [mute_id, skip_id]
    hass.config_entries.async_update_entry(entry, options={"snooze_minutes": 5})
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.snooze.minutes == 5

    # Without an entry the command refuses.
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    await client.send_json_auto_id({"type": f"{DOMAIN}/reorder_rules", "order": []})
    assert (await _result(client))["error"]["code"] == "not_configured"


async def test_reorder_while_not_loaded(hass: HomeAssistant, hass_ws_client) -> None:
    entry = await setup_entry(hass, make_entry(rule(), rule(**{CONF_NAME: "Two"})))
    first, second = (subentry.subentry_id for subentry in entry.subentries.values())
    await hass.config_entries.async_unload(entry.entry_id)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/reorder_rules", "order": [second, first]}
    )
    assert (await _result(client))["success"]
    assert entry.data[CONF_RULE_ORDER] == [second, first]


async def test_feature_module_is_loaded_everywhere(hass: HomeAssistant) -> None:
    """The tile card feature is registered as an extra module of the frontend."""
    assert await async_setup_component(hass, "frontend", {})
    await setup_entry(hass, make_entry())
    urls = hass.data[frontend.DATA_EXTRA_MODULE_URL].urls
    assert any(
        url.startswith(f"{PANEL_STATIC_URL}/super-skipper-feature.js?v=")
        for url in urls
    )
