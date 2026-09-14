from custom_components.skoda_order_status.renders import (
    list_images,
    paint_from_colour,
    parse_render_size,
    select_render,
)

HOME_URL = (
    "https://iprenders.blob.core.windows.net/basepylv27100102/"
    "0B1ZFJOUWZdfotvx13589-BCFHJLORUVafjklmsuvz257.-CEHJMNOQRTVXcjovxz0469-"
    "ADFJLNO-19201080dayvext_rotation_00031080.png"
)
SIDE_URL = HOME_URL.replace("00031080", "00031080")  # same file in fixture; distinct viewType


def _render(view_type: str, url: str, crop: bool = False) -> dict:
    item = {
        "viewType": view_type,
        "layers": [
            {"order": 0, "type": "REAL", "url": url, "viewPoint": "EXTERIOR_SIDE"}
        ],
    }
    if crop:
        item["modifications"] = {
            "adjustSpaceInPx": {"top": -317, "right": -139, "bottom": -193, "left": -167}
        }
    return item


def test_select_render_prefers_home():
    url, crop = select_render(
        [
            _render("UNMODIFIED_EXTERIOR_SIDE", "https://example.com/side.png"),
            _render("HOME", HOME_URL, crop=True),
        ]
    )
    assert url == HOME_URL
    assert crop == {
        "top": 317,
        "right": 139,
        "bottom": 193,
        "left": 167,
        "width": 1920,
        "height": 1080,
    }


def test_select_render_falls_back_to_unmodified_side():
    url, crop = select_render(
        [_render("UNMODIFIED_EXTERIOR_FRONT", "https://example.com/front.png"),
         _render("UNMODIFIED_EXTERIOR_SIDE", "https://example.com/side.png")]
    )
    assert url == "https://example.com/side.png"
    assert crop is None


def test_select_render_empty():
    assert select_render(None) == (None, None)
    assert select_render([]) == (None, None)


def test_list_images_empty():
    assert list_images(None) == []
    assert list_images([]) == []


def test_list_images_order_and_home_dedupe():
    renders = [
        _render("UNMODIFIED_EXTERIOR_SIDE", "https://example.com/side.png"),
        _render("HOME", HOME_URL, crop=True),
        _render("UNMODIFIED_EXTERIOR_FRONT", "https://example.com/front.png"),
        _render("UNMODIFIED_EXTERIOR_REAR", "https://example.com/rear.png"),
        _render("UNMODIFIED_INTERIOR_FRONT", "https://example.com/int-front.png"),
        _render("UNMODIFIED_INTERIOR_SIDE", "https://example.com/int-side.png"),
        _render("UNMODIFIED_INTERIOR_BOOT", "https://example.com/boot.png"),
    ]
    images = list_images(renders)
    assert [item["id"] for item in images] == [
        "side",
        "front",
        "rear",
        "interior_front",
        "interior_side",
        "boot",
    ]
    assert [item["label"] for item in images] == [
        "Seite",
        "Front",
        "Heck",
        "Innenraum vorne",
        "Innenraum Seite",
        "Kofferraum",
    ]
    assert images[0]["url"] == HOME_URL
    assert images[0]["crop"] == {
        "top": 317,
        "right": 139,
        "bottom": 193,
        "left": 167,
        "width": 1920,
        "height": 1080,
    }
    assert images[1]["url"] == "https://example.com/front.png"
    assert images[1]["crop"] is None


def test_list_images_side_fallback_without_home():
    images = list_images(
        [_render("UNMODIFIED_EXTERIOR_SIDE", "https://example.com/side.png")]
    )
    assert images == [
        {
            "id": "side",
            "label": "Seite",
            "url": "https://example.com/side.png",
            "crop": None,
        }
    ]


def test_list_images_skips_missing_views():
    images = list_images(
        [_render("UNMODIFIED_EXTERIOR_FRONT", "https://example.com/front.png")]
    )
    assert [item["id"] for item in images] == ["front"]


def test_parse_render_size_from_filename_not_rotation_suffix():
    assert parse_render_size(HOME_URL) == (1920, 1080)
    assert parse_render_size("https://cdn.example/car.png") == (1920, 1080)


def test_paint_longest_substring():
    name, hex_color = paint_from_colour(
        "Timiano-Grün Black-Magic Perleffekt"
    )
    assert name == "Timiano-Grün"
    assert hex_color == "#3d6b54"


def test_paint_unknown_falls_back():
    name, hex_color = paint_from_colour("Sonderlack XYZ")
    assert name is None
    assert hex_color == "#4a7a62"


def test_paint_none():
    name, hex_color = paint_from_colour(None)
    assert name is None
    assert hex_color == "#4a7a62"
