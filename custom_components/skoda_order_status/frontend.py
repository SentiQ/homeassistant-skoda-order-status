"""Register the Lovelace card as a dashboard resource."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import Event, HomeAssistant

from .const import DOMAIN, VERSION

_LOGGER = logging.getLogger(__name__)

WWW_DIR = Path(__file__).parent / "www"
DATA_KEY = f"{DOMAIN}_frontend"
CARD_FILE = "skoda-order-card.js"
INTEGRATION_PATH = f"/{DOMAIN}/{CARD_FILE}"
CARD_PATHS = (INTEGRATION_PATH, f"/local/{DOMAIN}/{CARD_FILE}")


def _card_content_hash() -> str | None:
    """Return a short content hash, or None when the card file is missing."""
    js_path = WWW_DIR / CARD_FILE
    if not js_path.exists():
        return None
    return hashlib.sha256(js_path.read_bytes()).hexdigest()[:10]


def _card_url(content_hash: str) -> str:
    return f"{INTEGRATION_PATH}?v={VERSION}.{content_hash}"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve www/ and register the card as a Lovelace module."""
    if hass.data.get(DATA_KEY):
        return

    content_hash = await hass.async_add_executor_job(_card_content_hash)
    if content_hash is None:
        _LOGGER.warning("Lovelace card missing at %s", WWW_DIR / CARD_FILE)
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/{DOMAIN}", str(WWW_DIR), False)]
    )
    url = _card_url(content_hash)
    hass.data[DATA_KEY] = True
    if await _async_register_lovelace_resource(hass, url):
        return

    async def _on_lovelace_loaded(event: Event) -> None:
        if event.data.get("component") != "lovelace":
            return
        unsub()
        refreshed_hash = await hass.async_add_executor_job(_card_content_hash)
        if refreshed_hash is None:
            return
        await _async_register_lovelace_resource(hass, _card_url(refreshed_hash))

    unsub = hass.bus.async_listen(EVENT_COMPONENT_LOADED, _on_lovelace_loaded)


async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> bool:
    """Register or update the card resource. Returns False if Lovelace is not ready."""
    try:
        resources = hass.data["lovelace"].resources
    except (KeyError, AttributeError):
        return False
    try:
        if getattr(resources, "mode", "storage") != "storage":
            return True
        if not getattr(resources, "loaded", True):
            await resources.async_load()
        existing = None
        for item in resources.async_items():
            item_path = str(item.get("url", "")).split("?", 1)[0]
            if item_path in CARD_PATHS:
                existing = item
                if item_path == INTEGRATION_PATH:
                    break
        if existing:
            if existing.get("url") != url:
                await resources.async_update_item(
                    existing["id"], {"res_type": "module", "url": url}
                )
            return True
        await resources.async_create_item({"res_type": "module", "url": url})
        return True
    except Exception:  # noqa: BLE001 - Lovelace API varies by HA version
        _LOGGER.debug("Could not register Lovelace resource for %s", INTEGRATION_PATH, exc_info=True)
        return False
