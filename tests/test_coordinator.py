import asyncio
from types import SimpleNamespace

import pytest

from custom_components.skoda_order_status.api import SkodaOrderApiError, SkodaOrderAuthError
from custom_components.skoda_order_status.coordinator import SkodaOrderCoordinator
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed


def _entry() -> SimpleNamespace:
    return SimpleNamespace(
        data={
            "username": "driver@example.com",
            "password": "secret",
            "commission_id": "C-1",
            "refresh_token": "old-token",
        },
        options={},
    )


def test_auth_error_raises_config_entry_auth_failed():
    async def _run() -> None:
        coordinator = SkodaOrderCoordinator(None, _entry())

        class Client:
            async def async_fetch_order(self, _commission_id: str) -> dict:
                raise SkodaOrderAuthError("denied")

        coordinator._client = Client()
        with pytest.raises(ConfigEntryAuthFailed, match="denied"):
            await coordinator._async_update_data()

    asyncio.run(_run())


def test_api_error_still_raises_update_failed():
    async def _run() -> None:
        coordinator = SkodaOrderCoordinator(None, _entry())

        class Client:
            async def async_fetch_order(self, _commission_id: str) -> dict:
                raise SkodaOrderApiError("timeout")

        coordinator._client = Client()
        with pytest.raises(UpdateFailed, match="timeout"):
            await coordinator._async_update_data()

    asyncio.run(_run())
