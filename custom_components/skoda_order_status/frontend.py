"""Register the Lovelace card as an extra JS module."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION

WWW_DIR = Path(__file__).parent / "www"
DATA_KEY = f"{DOMAIN}_frontend"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve www/ and load the card once per Home Assistant instance."""
    if hass.data.get(DATA_KEY):
        return
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/{DOMAIN}", str(WWW_DIR), True)]
    )
    add_extra_js_url(hass, f"/{DOMAIN}/skoda-order-card.js?v={VERSION}")
    hass.data[DATA_KEY] = True
