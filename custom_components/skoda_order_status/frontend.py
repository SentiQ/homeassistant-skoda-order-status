"""Register the Lovelace card as an extra JS module."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION

_LOGGER = logging.getLogger(__name__)

WWW_DIR = Path(__file__).parent / "www"
DATA_KEY = f"{DOMAIN}_frontend"
CARD_PATH = f"/{DOMAIN}/skoda-order-card.js"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve www/ and load the card once per Home Assistant instance."""
    if hass.data.get(DATA_KEY):
        return
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/{DOMAIN}", str(WWW_DIR), True)]
    )
    url = f"{CARD_PATH}?v={VERSION}"
    add_extra_js_url(hass, url)
    await _async_register_lovelace_resource(hass, url)
    hass.data[DATA_KEY] = True


async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Register the card in Lovelace so it appears in the card picker."""
    try:
        resources = hass.data["lovelace"].resources
    except (KeyError, AttributeError):
        return
    try:
        if getattr(resources, "mode", "storage") != "storage":
            return
        if not getattr(resources, "loaded", True):
            await resources.async_load()
        existing = None
        for item in resources.async_items():
            item_url = str(item.get("url", ""))
            if item_url.split("?")[0] == CARD_PATH:
                existing = item
                break
        if existing:
            if existing.get("url") != url:
                await resources.async_update_item(
                    existing["id"], {"res_type": "module", "url": url}
                )
            return
        await resources.async_create_item({"res_type": "module", "url": url})
    except Exception:  # noqa: BLE001 - Lovelace API varies by HA version
        _LOGGER.debug("Could not register Lovelace resource for %s", CARD_PATH, exc_info=True)
