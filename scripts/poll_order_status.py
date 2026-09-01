#!/usr/bin/env python3
"""Poll MySkoda order status and publish to Home Assistant."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

from aiohttp import ClientSession
from dotenv import load_dotenv
from myskoda import MySkoda

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / ".refresh_token"

STATUS_LABELS = {
    "ORDER_CONFIRMED": "Bestätigt",
    "IN_PRODUCTION": "In Produktion",
    "IN_DELIVERY": "Unterwegs",
    "TO_HANDOVER": "Zur Übergabe",
}


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise SystemExit(f"Fehlende Umgebungsvariable: {name}")
    return value


def load_cached_refresh_token() -> str | None:
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        return token or None
    return None


def save_refresh_token(token: str) -> None:
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
    TOKEN_FILE.chmod(0o600)


def checkpoint_date(checkpoints: list[dict], status: str) -> str | None:
    for item in checkpoints:
        if item.get("status") == status and item.get("date"):
            return item["date"]
    return None


def build_ha_payload(data: dict) -> dict:
    order_status = data.get("orderStatus") or "unknown"
    checkpoints = data.get("checkPoints") or []
    spec = data.get("vehicleSpecification") or {}
    label = STATUS_LABELS.get(order_status, order_status)

    reached = []
    pending = []
    for cp in checkpoints:
        entry = {
            "status": cp.get("status"),
            "label": STATUS_LABELS.get(cp.get("status", ""), cp.get("status")),
            "date": cp.get("date"),
        }
        if cp.get("date"):
            reached.append(entry)
        else:
            pending.append(entry)

    attributes = {
        "friendly_name": f"Škoda {data.get('name', 'Bestellung')} Bestellstatus",
        "icon": "mdi:car-clock",
        "order_status": order_status,
        "order_status_label": label,
        "commission_id": data.get("commissionId"),
        "model": spec.get("model"),
        "trim_level": spec.get("trimLevel"),
        "exterior_colour": spec.get("exteriorColour"),
        "interior_colour": spec.get("interiorColour"),
        "battery_kwh": (spec.get("battery") or {}).get("capacityInKWh"),
        "max_performance_kw": spec.get("maxPerformanceInKW"),
        "dealer_id": (data.get("dealer") or {}).get("servicePartnerId"),
        "activation_state": data.get("activationState"),
        "order_confirmed_date": checkpoint_date(checkpoints, "ORDER_CONFIRMED"),
        "in_production_date": checkpoint_date(checkpoints, "IN_PRODUCTION"),
        "in_delivery_date": checkpoint_date(checkpoints, "IN_DELIVERY"),
        "to_handover_date": checkpoint_date(checkpoints, "TO_HANDOVER"),
        "checkpoints_reached": reached,
        "checkpoints_pending": pending,
        "last_poll": datetime.now(timezone.utc).isoformat(),
    }

    return {"state": label, "attributes": attributes}


async def fetch_order(session: ClientSession, commission_id: str) -> dict:
    myskoda = MySkoda(session, mqtt_enabled=False)
    refresh = load_cached_refresh_token() or os.getenv("MYSKODA_REFRESH_TOKEN") or None

    try:
        if refresh:
            await myskoda.connect(refresh_token=refresh)
        else:
            await myskoda.connect(
                email=env("MYSKODA_USER"),
                password=env("MYSKODA_PASSWORD"),
            )
    except Exception:
        if refresh:
            # Token ungültig → neu mit User/Pass
            await myskoda.connect(
                email=env("MYSKODA_USER"),
                password=env("MYSKODA_PASSWORD"),
            )
        else:
            raise

    new_refresh = await myskoda.get_refresh_token()
    if new_refresh:
        save_refresh_token(new_refresh)

    raw = await myskoda.rest_api.raw_request(
        f"/v2/garage/vehicles/ordered/{commission_id}",
        "GET",
    )
    await myskoda.disconnect()
    return json.loads(raw)


async def publish_to_ha(session: ClientSession, entity_id: str, payload: dict) -> None:
    ha_url = env("HA_URL").rstrip("/")
    token = env("HA_TOKEN")
    url = f"{ha_url}/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    async with session.post(url, headers=headers, json=payload) as resp:
        body = await resp.text()
        if resp.status >= 400:
            raise SystemExit(f"HA API Fehler {resp.status}: {body}")


async def main() -> None:
    load_dotenv(ROOT / ".env")
    commission_id = env("COMMISSION_ID")
    entity_id = os.getenv("HA_ENTITY_ID", "sensor.skoda_elroq_bestellstatus")

    async with ClientSession() as session:
        data = await fetch_order(session, commission_id)
        payload = build_ha_payload(data)
        await publish_to_ha(session, entity_id, payload)
        logger.info(
            f"{entity_id} = {payload['state']} "
            f"({payload['attributes']['order_status']})"
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except SystemExit as exc:
        if exc.code not in (None, 0):
            logger.error(str(exc) or f"Beendet mit Code {exc.code}")
        raise
    except Exception:
        logger.exception("Poll fehlgeschlagen")
        sys.exit(1)
