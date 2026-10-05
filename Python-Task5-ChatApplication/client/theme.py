"""Colour palettes, fonts and small visual helpers."""
from __future__ import annotations

import sys
import zlib

PALETTES: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#0C0E14", "sidebar": "#11141C", "surface": "#161A24", "surface_alt": "#1D2230",
        "input_bg": "#1A1F2B", "border": "#272D3C", "hover": "#1A1F2C",
        "text": "#E7E9EF", "text_dim": "#8E96AA", "text_faint": "#5C6479",
        "accent": "#6C78F2", "accent_hover": "#7F8AF6", "accent_press": "#5966DC", "accent_text": "#FFFFFF",
        "own_bubble": "#28306A", "own_text": "#ECEEFF",
        "success": "#3DD68C", "danger": "#FF6B6B", "warning": "#F5B94B",
    },
    "light": {
        "bg": "#F3F4F8", "sidebar": "#FFFFFF", "surface": "#FFFFFF", "surface_alt": "#ECEEF5",
        "input_bg": "#F3F4F9", "border": "#DADEEA", "hover": "#F0F2F8",
        "text": "#171B26", "text_dim": "#5A6378", "text_faint": "#98A0B3",
        "accent": "#4F5BE8", "accent_hover": "#3F4BD6", "accent_press": "#343FBF", "accent_text": "#FFFFFF",
        "own_bubble": "#DEE2FF", "own_text": "#171B26",
        "success": "#1FA86B", "danger": "#E0434B", "warning": "#C98A12",
    },
}

AVATAR_COLORS = ["#6C78F2", "#2FB5A0", "#E08A4B", "#B863D6", "#4C9BE8", "#D6567A", "#7DA83B", "#B8923A"]

FONT_FAMILY = {"win32": "Segoe UI", "darwin": "Helvetica Neue"}.get(sys.platform, "DejaVu Sans")
EMOJI_FONT = "Segoe UI Emoji" if sys.platform == "win32" else FONT_FAMILY


class Theme:
    def __init__(self, mode: str = "dark") -> None:
        self.mode = mode if mode in PALETTES else "dark"

    @property
    def c(self) -> dict[str, str]:
        return PALETTES[self.mode]

    def set_mode(self, mode: str) -> None:
        if mode in PALETTES:
            self.mode = mode


theme = Theme()


def font(size: int = 10, *styles: str, family: str | None = None) -> tuple:
    family = family or FONT_FAMILY
    styles = tuple(style for style in styles if style)
    return (family, size, " ".join(styles)) if styles else (family, size)


def avatar_color(name: str) -> str:
    return AVATAR_COLORS[zlib.crc32(name.lower().encode("utf-8")) % len(AVATAR_COLORS)]
