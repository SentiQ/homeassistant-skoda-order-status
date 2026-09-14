import hashlib
import json
from pathlib import Path

from custom_components.skoda_order_status.const import VERSION
from custom_components.skoda_order_status.frontend import CARD_PATHS, INTEGRATION_PATH, _card_url

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
    url = _card_url()
    assert url == f"{INTEGRATION_PATH}?v={VERSION}.{digest}"


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
