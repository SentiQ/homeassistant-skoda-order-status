from custom_components.skoda_order_status.renders import (
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
