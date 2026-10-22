import hashlib
import json
import re
from pathlib import Path

from custom_components.skoda_order_status.const import DEFAULT_ACCENT, PAINT_COLORS, VERSION
from custom_components.skoda_order_status.frontend import (
    CARD_PATHS,
    INTEGRATION_PATH,
    _card_content_hash,
    _card_url,
    async_register_frontend,
)

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "custom_components/skoda_order_status/www/skoda-order-card.js"
MANIFEST = ROOT / "custom_components/skoda_order_status/manifest.json"
FRONTEND = ROOT / "custom_components/skoda_order_status/frontend.py"


def test_version_matches_manifest():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert VERSION == manifest["version"]


def test_manifest_keys_sorted_for_hassfest():
    keys = list(json.loads(MANIFEST.read_text(encoding="utf-8")))
    expected = ["domain", "name"] + sorted(k for k in keys if k not in {"domain", "name"})
    assert keys == expected


def test_card_url_uses_integration_path_and_content_hash():
    digest = hashlib.sha256(JS.read_bytes()).hexdigest()[:10]
    assert _card_content_hash() == digest
    assert _card_url(digest) == f"{INTEGRATION_PATH}?v={VERSION}.{digest}"


def test_card_content_hash_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "custom_components.skoda_order_status.frontend.WWW_DIR", tmp_path
    )
    assert _card_content_hash() is None


def test_register_frontend_hashes_card_via_executor(monkeypatch):
    import asyncio

    calls = []

    async def _run():
        class Http:
            async def async_register_static_paths(self, paths):
                self.paths = paths

        class Hass:
            def __init__(self):
                self.data = {}
                self.http = Http()

            async def async_add_executor_job(self, func, *args):
                calls.append(func)
                return func(*args)

        hass = Hass()
        monkeypatch.setattr(
            "custom_components.skoda_order_status.frontend._async_register_lovelace_resource",
            _ready,
        )
        await async_register_frontend(hass)

    async def _ready(_hass, _url):
        return True

    asyncio.run(_run())
    assert calls == [_card_content_hash]


def test_card_paths_include_legacy_local_url():
    assert INTEGRATION_PATH in CARD_PATHS
    assert "/local/skoda_order_status/skoda-order-card.js" in CARD_PATHS


def test_frontend_does_not_use_extra_js_url():
    assert "add_extra_js_url" not in FRONTEND.read_text(encoding="utf-8")


def test_card_js_registers_custom_element():
    src = JS.read_text(encoding="utf-8")
    assert 'customElements.define("skoda-order-card"' in src
    assert "window.customCards" in src
    assert "MutationObserver" not in src


def test_card_config_form_includes_view():
    src = JS.read_text(encoding="utf-8")
    assert 'name: "view"' in src
    assert '{ value: "side", label: "Seite" }' in src
    assert '{ value: "boot", label: "Kofferraum" }' in src


def test_card_js_persists_view_in_local_storage():
    src = JS.read_text(encoding="utf-8")
    assert "skoda-order-card:" in src
    assert "localStorage.getItem" in src
    assert "localStorage.setItem" in src
    assert ":view" in src


def test_card_js_keeps_home_photo_frame():
    src = JS.read_text(encoding="utf-8")
    assert "aspect-ratio:16/9" not in src
    assert "aspect-ratio:16/6" in src
    assert "object-fit:cover" in src


def test_card_accent_accepts_only_hex():
    src = JS.read_text(encoding="utf-8")
    assert "function accentColor(" in src
    assert "/^#[0-9a-fA-F]{3,8}$/" in src
    assert "accentColor(attr.accent_color)" in src
    assert "const paint = accentColor(accent)" in src
    pattern = re.compile(r"^#[0-9a-fA-F]{3,8}$")
    for color in (*PAINT_COLORS.values(), DEFAULT_ACCENT):
        assert pattern.fullmatch(color)
    for unsafe in (
        "</style><img src=x onerror=alert(1)>",
        "red",
        "#4a7a62; }",
        "#gg0000",
        "var(--primary-color)",
    ):
        assert pattern.fullmatch(unsafe) is None


def test_card_js_applies_config_view_changes():
    src = JS.read_text(encoding="utf-8")
    assert "_lastView" in src
    assert ":configView" in src
