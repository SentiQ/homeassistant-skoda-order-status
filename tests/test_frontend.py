import hashlib
import json
from pathlib import Path

from custom_components.skoda_order_status.const import VERSION
from custom_components.skoda_order_status.frontend import (
    CARD_PATHS,
    LOCAL_PATH,
    _card_url,
    _install_local_copy,
)

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "custom_components/skoda_order_status/www/skoda-order-card.js"
MANIFEST = ROOT / "custom_components/skoda_order_status/manifest.json"


def test_version_matches_manifest():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert VERSION == manifest["version"]


def test_manifest_keys_sorted_for_hassfest():
    keys = list(json.loads(MANIFEST.read_text(encoding="utf-8")))
    expected = ["domain", "name"] + sorted(k for k in keys if k not in {"domain", "name"})
    assert keys == expected


def test_card_url_uses_local_path_and_content_hash():
    digest = hashlib.sha256(JS.read_bytes()).hexdigest()[:10]
    url = _card_url()
    assert url == f"{LOCAL_PATH}?v={VERSION}.{digest}"
    assert url.startswith("/local/skoda_order_status/skoda-order-card.js?v=")


def test_card_paths_include_local_and_legacy():
    assert LOCAL_PATH in CARD_PATHS
    assert "/skoda_order_status/skoda-order-card.js" in CARD_PATHS


def test_install_local_copy(tmp_path):
    dest = _install_local_copy(tmp_path)
    assert dest == tmp_path / "skoda_order_status" / "skoda-order-card.js"
    assert dest.read_bytes() == JS.read_bytes()
