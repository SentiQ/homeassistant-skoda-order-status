"""Stub HA and myskoda so renders tests run with pytest only."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any


def _module(name: str, **attrs: Any) -> ModuleType:
    mod = ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


class _Platform:
    SENSOR = "sensor"


class _ConfigEntry:
    pass


class _DataUpdateCoordinator:
    def __class_getitem__(cls, _item: Any) -> type:
        return cls


class _UpdateFailed(Exception):
    pass


class _ClientSession:
    pass


class _MySkoda:
    pass


class _StaticPathConfig:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass


def _get_default_context() -> None:
    return None


async def _async_get_clientsession(_hass: Any) -> Any:
    return None


def _add_extra_js_url(_hass: Any, _url: str) -> None:
    pass


_module("homeassistant")
_module(
    "homeassistant.const",
    Platform=_Platform,
    EVENT_COMPONENT_LOADED="component_loaded",
)
_module("homeassistant.core", HomeAssistant=object, Event=object)
_module("homeassistant.config_entries", ConfigEntry=_ConfigEntry)
_module("homeassistant.helpers")
_module(
    "homeassistant.helpers.aiohttp_client",
    async_get_clientsession=_async_get_clientsession,
)
_module(
    "homeassistant.helpers.update_coordinator",
    DataUpdateCoordinator=_DataUpdateCoordinator,
    UpdateFailed=_UpdateFailed,
)
_module("homeassistant.util")
_module("homeassistant.util.ssl", get_default_context=_get_default_context)
_module("homeassistant.components")
_module("homeassistant.components.frontend", add_extra_js_url=_add_extra_js_url)
_module("homeassistant.components.http", StaticPathConfig=_StaticPathConfig)
_module("myskoda", MySkoda=_MySkoda)
_module("aiohttp", ClientSession=_ClientSession)
