"""Config flow for Škoda Order Status."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.ssl import get_default_context

from .api import SkodaOrderApiClient, SkodaOrderAuthError
from .const import (
    CONF_COMMISSION_ID,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _discover_orders(
    hass: HomeAssistant, username: str, password: str
) -> tuple[list[dict[str, Any]], str | None]:
    client = SkodaOrderApiClient(
        async_get_clientsession(hass),
        get_default_context(),
        username,
        password,
    )
    orders = await client.async_discover_orders()
    return orders, await client.async_get_refresh_token()


def _order_label(order: dict[str, Any]) -> str:
    commission_id = order.get("commissionId", "unknown")
    name = order.get("name") or order.get("model") or "Škoda"
    return f"{name} ({commission_id})"


class SkodaOrderStatusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Škoda Order Status."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._credentials: dict[str, str] = {}
        self._orders: list[dict[str, Any]] = []
        self._refresh_token: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._credentials = user_input
            try:
                self._orders, self._refresh_token = await _discover_orders(
                    self.hass,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
            except SkodaOrderAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during discovery")
                errors["base"] = "cannot_connect"
            else:
                if not self._orders:
                    errors["base"] = "no_orders"
                elif len(self._orders) == 1:
                    return await self._create_entry(self._orders[0]["commissionId"])
                return await self.async_step_order()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_order(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select an ordered vehicle."""
        if user_input is not None:
            return await self._create_entry(user_input[CONF_COMMISSION_ID])

        return self.async_show_form(
            step_id="order",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COMMISSION_ID): vol.In(
                        {
                            order["commissionId"]: _order_label(order)
                            for order in self._orders
                        }
                    )
                }
            ),
        )

    async def _create_entry(self, commission_id: str) -> ConfigFlowResult:
        await self.async_set_unique_id(commission_id)
        self._abort_if_unique_id_configured()

        title = next(
            (
                _order_label(order)
                for order in self._orders
                if order.get("commissionId") == commission_id
            ),
            commission_id,
        )

        data = {
            CONF_USERNAME: self._credentials[CONF_USERNAME],
            CONF_PASSWORD: self._credentials[CONF_PASSWORD],
            CONF_COMMISSION_ID: commission_id,
        }
        if self._refresh_token:
            data[CONF_REFRESH_TOKEN] = self._refresh_token

        return self.async_create_entry(
            title=title,
            data=data,
            options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return SkodaOrderStatusOptionsFlow()


class SkodaOrderStatusOptionsFlow(OptionsFlow):
    """Handle options for Škoda Order Status."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.config_entry.entry_id)
            )
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                        ),
                    )
                }
            ),
        )
