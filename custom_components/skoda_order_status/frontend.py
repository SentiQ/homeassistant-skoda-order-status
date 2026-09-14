"""Register the Lovelace card via /local/ so Firefox and the Companion app pick it up."""

from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import Event, HomeAssistant

from .const import DOMAIN, VERSION

_LOGGER = logging.getLogger(__name__)

WWW_DIR = Path(__file__).parent / "www"
DATA_KEY = f"{DOMAIN}_frontend"
CARD_FILE = "skoda-order-card.js"
INTEGRATION_PATH = f"/{DOMAIN}/{CARD_FILE}"
LOCAL_PATH = f"/local/{DOMAIN}/{CARD_FILE}"
CARD_PATHS = (LOCAL_PATH, INTEGRATION_PATH)


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def _card_url(public_path: str = LOCAL_PATH) -> str:
    js_path = WWW_DIR / CARD_FILE
    stamp = VERSION
    if js_path.exists():
        stamp = f"{VERSION}.{_file_digest(js_path)}"
    return f"{public_path}?v={stamp}"


def _install_local_copy(www_root: Path) -> Path:
    dest_dir = www_root / DOMAIN
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / CARD_FILE
    shutil.copy2(WWW_DIR / CARD_FILE, dest)
    return dest


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve www/, copy the card to /local/, and register the Lovelace module."""
    if hass.data.get(DATA_KEY):
        return

    js_path = WWW_DIR / CARD_FILE
    if not js_path.exists():
        _LOGGER.warning("Lovelace card missing at %s", js_path)
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/{DOMAIN}", str(WWW_DIR), False)]
    )
    await hass.async_add_executor_job(_install_local_copy, Path(hass.config.path("www")))

    url = _card_url()
    add_extra_js_url(hass, url)
    hass.data[DATA_KEY] = True
    if await _async_register_lovelace_resource(hass, url):
        return

    async def _on_lovelace_loaded(event: Event) -> None:
        if event.data.get("component") != "lovelace":
            return
        unsub()
        await _async_register_lovelace_resource(hass, _card_url())

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
                if item_path == LOCAL_PATH:
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
        _LOGGER.debug("Could not register Lovelace resource for %s", LOCAL_PATH, exc_info=True)
        return False
