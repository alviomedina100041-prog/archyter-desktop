from __future__ import annotations

import os


def _colorref(hex_color: str) -> int:
    value = hex_color.lstrip("#")
    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    return red | (green << 8) | (blue << 16)


def apply_light_titlebar(window) -> None:
    if os.name != "nt":
        return

    try:
        import ctypes

        hwnd = int(window.winId())
        dwmapi = ctypes.windll.dwmapi

        dark_mode = ctypes.c_int(0)
        for attribute in (20, 19):
            try:
                dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    attribute,
                    ctypes.byref(dark_mode),
                    ctypes.sizeof(dark_mode),
                )
                break
            except Exception:
                continue

        attributes = {
            34: "#d8e4ef",
            35: "#ffffff",
            36: "#172033",
        }

        for attribute, color in attributes.items():
            value = ctypes.c_int(_colorref(color))
            try:
                dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    attribute,
                    ctypes.byref(value),
                    ctypes.sizeof(value),
                )
            except Exception:
                pass
    except Exception:
        # Titlebar cosmetics must never prevent the IDE from starting.
        return
