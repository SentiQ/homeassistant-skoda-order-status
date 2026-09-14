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

VERSION: Final = "1.0.6"

CHECKPOINT_STATUSES: Final = (
    "ORDER_CONFIRMED",
    "IN_PRODUCTION",
    "IN_DELIVERY",
    "TO_HANDOVER",
)

DEFAULT_ACCENT: Final = "#4a7a62"

PAINT_COLORS: Final = {
    "Timiano-Grün": "#3d6b54",
    "Sage-Grün": "#6b7f5a",
    "Race-Blau": "#1e3a5f",
    "Energy-Blau": "#2f5f8a",
    "Velvet-Rot": "#7a2430",
    "Phoenix-Orange": "#c45c2a",
    "Graphite-Grau": "#5c5c5c",
    "Steel-Grau": "#7a7d80",
    "Pebble-Silber": "#b8b5ae",
    "Brilliant-Silber": "#c5c7c8",
    "Moon-Weiß": "#e8e4dc",
    "Candy-Weiß": "#f4f4f4",
    "Black-Magic": "#1a1a1a",
}
