"""Constants for the Škoda Order Status integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "skoda_order_status"

CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_REFRESH_TOKEN: Final = "refresh_token"
CONF_COMMISSION_ID: Final = "commission_id"
CONF_SCAN_INTERVAL: Final = "scan_interval"

DEFAULT_SCAN_INTERVAL: Final = 3600
MIN_SCAN_INTERVAL: Final = 900
MAX_SCAN_INTERVAL: Final = 86400

GARAGE_PATH: Final = (
    "/v2/garage?connectivityGenerations=MOD1"
    "&connectivityGenerations=MOD2"
    "&connectivityGenerations=MOD3"
    "&connectivityGenerations=MOD4"
)

STATUS_LABELS: Final = {
    "ORDER_CONFIRMED": "Bestätigt",
    "IN_PRODUCTION": "In Produktion",
    "IN_DELIVERY": "Unterwegs",
    "TO_HANDOVER": "Zur Übergabe",
}
