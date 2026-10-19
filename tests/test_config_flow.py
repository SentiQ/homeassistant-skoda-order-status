import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "custom_components/skoda_order_status/config_flow.py"
STRINGS = ROOT / "custom_components/skoda_order_status/strings.json"


def test_reauth_updates_credentials_and_reloads():
    src = FLOW.read_text(encoding="utf-8")
    assert "async def async_step_reauth(" in src
    assert "async def async_step_reauth_confirm(" in src
    assert "async_update_reload_and_abort" in src
    assert "ConfigEntryAuthFailed" not in src


def test_reauth_strings_exist():
    strings = json.loads(STRINGS.read_text(encoding="utf-8"))
    step = strings["config"]["step"]["reauth_confirm"]
    assert step["data"]["username"]
    assert step["data"]["password"]
    assert strings["config"]["abort"]["reauth_successful"]
