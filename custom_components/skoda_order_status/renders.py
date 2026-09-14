"""Parse MyŠkoda order renders and paint names."""

from __future__ import annotations

import re
from typing import Any

from .const import DEFAULT_ACCENT, PAINT_COLORS

_SIZE_IN_NAME = re.compile(r"(\d{3,4})(\d{4})(?=day|studio)", re.IGNORECASE)


def parse_render_size(url: str) -> tuple[int, int]:
    """Return (width, height) from a render filename, default 1920x1080."""
    name = url.rsplit("/", 1)[-1]
    match = _SIZE_IN_NAME.search(name)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 1920, 1080


def _crop_from_render(item: dict[str, Any], url: str) -> dict[str, int] | None:
    insets = ((item.get("modifications") or {}).get("adjustSpaceInPx")) or None
    if not insets:
        return None
    width, height = parse_render_size(url)
    return {
        "top": abs(int(insets.get("top") or 0)),
        "right": abs(int(insets.get("right") or 0)),
        "bottom": abs(int(insets.get("bottom") or 0)),
        "left": abs(int(insets.get("left") or 0)),
        "width": width,
        "height": height,
    }


def _url_from_layers(item: dict[str, Any]) -> str | None:
    layers = item.get("layers") or []
    side = next((layer for layer in layers if layer.get("viewPoint") == "EXTERIOR_SIDE"), None)
    layer = side or (layers[0] if layers else None)
    if not layer:
        return None
    url = layer.get("url")
    return url if isinstance(url, str) and url else None


_IMAGE_SPECS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("side", ("HOME", "UNMODIFIED_EXTERIOR_SIDE"), "Seite"),
    ("front", ("UNMODIFIED_EXTERIOR_FRONT",), "Front"),
    ("rear", ("UNMODIFIED_EXTERIOR_REAR",), "Heck"),
    ("interior_front", ("UNMODIFIED_INTERIOR_FRONT",), "Innenraum vorne"),
    ("interior_side", ("UNMODIFIED_INTERIOR_SIDE",), "Innenraum Seite"),
    ("boot", ("UNMODIFIED_INTERIOR_BOOT",), "Kofferraum"),
)


def list_images(
    composite_renders: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Return unique configurator photos in display order."""
    if not composite_renders:
        return []
    by_type = {
        item.get("viewType"): item
        for item in composite_renders
        if item.get("viewType")
    }
    images: list[dict[str, Any]] = []
    for image_id, view_types, label in _IMAGE_SPECS:
        item = next((by_type[key] for key in view_types if key in by_type), None)
        if not item:
            continue
        url = _url_from_layers(item)
        if not url:
            continue
        crop = _crop_from_render(item, url) if item.get("viewType") == "HOME" else None
        images.append(
            {"id": image_id, "label": label, "url": url, "crop": crop}
        )
    return images


def select_render(
    composite_renders: list[dict[str, Any]] | None,
) -> tuple[str | None, dict[str, int] | None]:
    """Prefer HOME side view, else unmodified side; crop only when API provides it."""
    if not composite_renders:
        return None, None
    home = next((item for item in composite_renders if item.get("viewType") == "HOME"), None)
    side = next(
        (
            item
            for item in composite_renders
            if item.get("viewType") == "UNMODIFIED_EXTERIOR_SIDE"
        ),
        None,
    )
    chosen = home or side
    if not chosen:
        return None, None
    url = _url_from_layers(chosen)
    if not url:
        return None, None
    return url, _crop_from_render(chosen, url)


def paint_from_colour(exterior_colour: str | None) -> tuple[str | None, str]:
    """Longest substring match in PAINT_COLORS; fallback Škoda green."""
    if not exterior_colour:
        return None, DEFAULT_ACCENT
    matches = [name for name in PAINT_COLORS if name in exterior_colour]
    if not matches:
        return None, DEFAULT_ACCENT
    name = max(matches, key=len)
    return name, PAINT_COLORS[name]
