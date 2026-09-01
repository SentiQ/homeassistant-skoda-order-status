"""MySkoda API client for ordered vehicles."""

from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import ClientSession
from homeassistant.util.ssl import SSLContext
from myskoda import MySkoda

from .const import GARAGE_PATH

_LOGGER = logging.getLogger(__name__)


class SkodaOrderApiError(Exception):
    """Base API error."""


class SkodaOrderAuthError(SkodaOrderApiError):
    """Authentication failed."""


class SkodaOrderApiClient:
    """Fetch order status from the unofficial MySkoda API."""

    def __init__(
        self,
        session: ClientSession,
        ssl_context: SSLContext,
        username: str,
        password: str,
        refresh_token: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._ssl_context = ssl_context
        self._username = username
        self._password = password
        self._refresh_token = refresh_token

    async def async_get_refresh_token(self) -> str | None:
        """Return the latest refresh token after a successful connect."""
        return self._refresh_token

    async def async_discover_orders(self) -> list[dict[str, Any]]:
        """Return ordered vehicles from the MySkoda garage."""
        myskoda = MySkoda(self._session, self._ssl_context, mqtt_enabled=False)
        try:
            await self._connect(myskoda)
            raw = await myskoda.rest_api.raw_request(GARAGE_PATH, "GET")
            garage = json.loads(raw)
            orders = [
                vehicle
                for vehicle in garage.get("orderedVehicles", [])
                if vehicle.get("commissionId")
            ]
            await self._store_refresh_token(myskoda)
            return orders
        finally:
            await myskoda.disconnect()

    async def async_fetch_order(self, commission_id: str) -> dict[str, Any]:
        """Return order details for a commission ID."""
        myskoda = MySkoda(self._session, self._ssl_context, mqtt_enabled=False)
        try:
            await self._connect(myskoda)
            raw = await myskoda.rest_api.raw_request(
                f"/v2/garage/vehicles/ordered/{commission_id}",
                "GET",
            )
            await self._store_refresh_token(myskoda)
            return json.loads(raw)
        finally:
            await myskoda.disconnect()

    async def _connect(self, myskoda: MySkoda) -> None:
        if self._refresh_token:
            try:
                await myskoda.connect(refresh_token=self._refresh_token)
                return
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Refresh token login failed, retrying with password: %s", err)

        try:
            await myskoda.connect(email=self._username, password=self._password)
        except Exception as err:
            raise SkodaOrderAuthError(str(err)) from err

    async def _store_refresh_token(self, myskoda: MySkoda) -> None:
        token = await myskoda.get_refresh_token()
        if token:
            self._refresh_token = token
