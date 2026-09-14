"""Sensor platform for Škoda order status."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_COMMISSION_ID, DOMAIN, STATUS_LABELS
from .coordinator import SkodaOrderCoordinator
from .renders import list_images, paint_from_colour, select_render

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Škoda order status sensor."""
    coordinator: SkodaOrderCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SkodaOrderStatusSensor(coordinator)])


class SkodaOrderStatusSensor(CoordinatorEntity[SkodaOrderCoordinator], SensorEntity):
    """Representation of a Škoda order status."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:car-clock"
    _attr_translation_key = "order_status"

    def __init__(self, coordinator: SkodaOrderCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.entry.data[CONF_COMMISSION_ID]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        data = self.coordinator.data or {}
        spec = data.get("vehicleSpecification") or {}
        model = spec.get("model") or data.get("name") or "Škoda Bestellung"
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.data[CONF_COMMISSION_ID])},
            name=model,
            manufacturer="Škoda",
            model=spec.get("trimLevel"),
        )

    @property
    def native_value(self) -> str | None:
        """Return the human-readable order status."""
        if not self.coordinator.data:
            return None
        order_status = self.coordinator.data.get("orderStatus")
        if not order_status:
            return None
        return STATUS_LABELS.get(order_status, order_status)

    @property
    def entity_picture(self) -> str | None:
        """Return the configurator side-view URL."""
        if not self.coordinator.data:
            return None
        url, _crop = select_render(self.coordinator.data.get("compositeRenders"))
        return url

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return order details."""
        data = self.coordinator.data or {}
        order_status = data.get("orderStatus")
        checkpoints = data.get("checkPoints") or []
        spec = data.get("vehicleSpecification") or {}
        _picture_url, image_crop = select_render(data.get("compositeRenders"))
        images = list_images(data.get("compositeRenders"))
        paint_name, accent_color = paint_from_colour(spec.get("exteriorColour"))

        reached = []
        pending = []
        for checkpoint in checkpoints:
            entry = {
                "status": checkpoint.get("status"),
                "label": STATUS_LABELS.get(
                    checkpoint.get("status", ""), checkpoint.get("status")
                ),
                "date": checkpoint.get("date"),
            }
            if checkpoint.get("date"):
                reached.append(entry)
            else:
                pending.append(entry)

        return {
            "order_status": order_status,
            "order_status_label": self.native_value,
            "commission_id": data.get("commissionId"),
            "model": spec.get("model"),
            "trim_level": spec.get("trimLevel"),
            "exterior_colour": spec.get("exteriorColour"),
            "interior_colour": spec.get("interiorColour"),
            "battery_kwh": (spec.get("battery") or {}).get("capacityInKWh"),
            "max_performance_kw": spec.get("maxPerformanceInKW"),
            "dealer_id": (data.get("dealer") or {}).get("servicePartnerId"),
            "activation_state": data.get("activationState"),
            "order_confirmed_date": self.coordinator.checkpoint_date(
                checkpoints, "ORDER_CONFIRMED"
            ),
            "in_production_date": self.coordinator.checkpoint_date(
                checkpoints, "IN_PRODUCTION"
            ),
            "in_delivery_date": self.coordinator.checkpoint_date(
                checkpoints, "IN_DELIVERY"
            ),
            "to_handover_date": self.coordinator.checkpoint_date(
                checkpoints, "TO_HANDOVER"
            ),
            "checkpoints_reached": reached,
            "checkpoints_pending": pending,
            "last_poll": datetime.now(timezone.utc).isoformat(),
            "image_crop": image_crop,
            "images": images,
            "accent_color": accent_color,
            "paint_name": paint_name,
        }
