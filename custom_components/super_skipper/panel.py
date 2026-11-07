"""The Super Skipper page in the sidebar."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    FEATURE_MODULE,
    NAME,
    PANEL_ELEMENT,
    PANEL_MODULE,
    PANEL_STATIC_URL,
    PANEL_URL_PATH,
)

FRONTEND_DIR = Path(__file__).parent / "frontend"
DATA_STATIC = f"{DOMAIN}_static_registered"


def _version() -> str:
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
    return str(manifest.get("version", "0"))


async def async_register_panel(hass: HomeAssistant) -> None:
    """Add the page to the sidebar and the card feature to the dashboards, once per run."""
    if "frontend" not in hass.config.components:
        return
    version = await hass.async_add_executor_job(_version)
    if not hass.data.get(DATA_STATIC):
        hass.data[DATA_STATIC] = True
        await hass.http.async_register_static_paths(
            [StaticPathConfig(PANEL_STATIC_URL, str(FRONTEND_DIR), False)]
        )
        # The "Add to Super Skipper" feature of the tile card, for media players.
        frontend.add_extra_js_url(
            hass, f"{PANEL_STATIC_URL}/{FEATURE_MODULE}?v={version}"
        )
    if PANEL_URL_PATH in hass.data.get(frontend.DATA_PANELS, {}):
        return
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_ELEMENT,
        module_url=f"{PANEL_STATIC_URL}/{PANEL_MODULE}?v={version}",
        sidebar_title=NAME,
        sidebar_icon="mdi:skip-next-circle",
        require_admin=True,
        config={},
    )


@callback
def async_remove_panel(hass: HomeAssistant) -> None:
    """Take the page out of the sidebar."""
    if "frontend" not in hass.config.components:
        return
    if PANEL_URL_PATH in hass.data.get(frontend.DATA_PANELS, {}):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
