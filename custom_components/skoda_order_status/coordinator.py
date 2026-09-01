"""Data update coordinator for Škoda order status."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.ssl import get_default_context

from .api import SkodaOrderApiClient, SkodaOrderApiError, SkodaOrderAuthError
from .const import (
    CONF_COMMISSION_ID,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    STATUS_LABELS,
)

_LOGGER = logging.getLogger(__name__)

type SkodaOrderConfigEntry = ConfigEntry[SkodaOrderCoordinator]


class SkodaOrderCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch Škoda order status periodically."""

    config_entry: SkodaOrderConfigEntry

    def __init__(self, hass: HomeAssistant, entry: SkodaOrderConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = SkodaOrderApiClient(
            async_get_clientsession(hass),
            get_default_context(),
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data.get(CONF_REFRESH_TOKEN),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        commission_id = self.entry.data[CONF_COMMISSION_ID]
        try:
            data = await self._client.async_fetch_order(commission_id)
        except SkodaOrderAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except SkodaOrderApiError as err:
            raise UpdateFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed(str(err)) from err

        refresh_token = await self._client.async_get_refresh_token()
        if refresh_token and refresh_token != self.entry.data.get(CONF_REFRESH_TOKEN):
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={**self.entry.data, CONF_REFRESH_TOKEN: refresh_token},
            )

        return data

    @staticmethod
    def checkpoint_date(checkpoints: list[dict[str, Any]], status: str) -> str | None:
        """Return checkpoint date for a status."""
        for item in checkpoints:
            if item.get("status") == status and item.get("date"):
                return item["date"]
        return None

    @classmethod
    def status_label(cls, order_status: str) -> str:
        """Return localized status label."""
        return STATUS_LABELS.get(order_status, order_status)
