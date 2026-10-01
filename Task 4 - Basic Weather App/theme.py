"""Centralised theme system: two hand-tuned palettes plus weather 'atmospheres'.

Every widget reads colours from the active :class:`Palette` and re-renders when
:class:`ThemeManager` announces a change — no colours are hard-coded in widgets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from models import CLEAR, CLOUDS, FOG, RAIN, SNOW, STORM


# ── colour helpers (tk-free so they can be unit-tested) ──────────────────────
def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def rgb_to_hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(round(v)))) for v in rgb))


def mix(c1: str, c2: str, t: float) -> str:
    """Blend ``c1`` toward ``c2`` by ``t`` (0..1)."""
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex(tuple(x + (y - x) * t for x, y in zip(a, b)))


def luminance(color: str) -> float:
    r, g, b = (v / 255 for v in hex_to_rgb(color))
    lin = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def darken(color: str, amount: float) -> str:
    return mix(color, "#05080f", amount)


# ── palettes ──────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Palette:
    name: str
    bg: str
    surface: str
    surface_alt: str      # inputs, chips, icon badges
    border: str
    text: str
    text_muted: str
    text_faint: str
    accent: str
    accent_hover: str
    on_accent: str
    good: str
    warn: str
    danger: str
    danger_bg: str
    bordered: bool        # dark = crisp hairline borders, light = borderless soft shadows
    shadow_alpha: int
    shadow_blur: int
    shadow_offset: int


DARK = Palette(
    name="dark", bg="#0A0F1E", surface="#131B2E", surface_alt="#1B2640", border="#25314F",
    text="#EAF0FB", text_muted="#95A3C0", text_faint="#5F6E8C",
    accent="#4F9DFF", accent_hover="#74B2FF", on_accent="#04122B",
    good="#4ADE9A", warn="#FBBF24", danger="#FF6B7A", danger_bg="#2A1622",
    bordered=True, shadow_alpha=150, shadow_blur=6, shadow_offset=3,
)

LIGHT = Palette(
    name="light", bg="#EDF1F7", surface="#FFFFFF", surface_alt="#F1F5FB", border="#DCE4F0",
    text="#0E1A33", text_muted="#5A6A87", text_faint="#93A0B8",
    accent="#2563EB", accent_hover="#1D4FD0", on_accent="#FFFFFF",
    good="#0F9F6E", warn="#B7791F", danger="#D93A4F", danger_bg="#FDECEF",
    bordered=False, shadow_alpha=46, shadow_blur=8, shadow_offset=4,
)

PALETTES = {"dark": DARK, "light": LIGHT}


class ThemeManager:
    """Holds the active palette and notifies subscribed widgets when it changes."""

    def __init__(self, mode: str = "dark"):
        self.mode = mode if mode in PALETTES else "dark"
        self._listeners: list[Callable[[Palette], None]] = []

    @property
    def palette(self) -> Palette:
        return PALETTES[self.mode]

    def subscribe(self, callback: Callable[[Palette], None]) -> None:
        self._listeners.append(callback)

    def set_mode(self, mode: str) -> None:
        if mode not in PALETTES or mode == self.mode:
            return
        self.mode = mode
        for callback in list(self._listeners):
            callback(self.palette)

    def toggle(self) -> str:
        self.set_mode("light" if self.mode == "dark" else "dark")
        return self.mode


# ── weather atmospheres (hero card + today's card) ───────────────────────────
@dataclass(frozen=True)
class Atmosphere:
    kind: str            # clear, clouds, rain, storm, snow, fog or night
    top: str
    bottom: str
    text: str
    muted: str
    pill: str            # translucent chip colour drawn over the gradient
    night: bool


_BASE = {
    # kind: ((dark top, dark bottom), (light top, light bottom))
    CLEAR: (("#1D5FB8", "#0B7C8F"), ("#FFE9B0", "#8CCBFA")),
    CLOUDS: (("#3A4D6E", "#1F2C46"), ("#DDE7F3", "#A9BDD6")),
    RAIN: (("#24466F", "#101F3A"), ("#BCCBE0", "#7F98B9")),
    STORM: (("#2E2852", "#12101F"), ("#7E8CA9", "#48567A")),
    SNOW: (("#41607F", "#24374F"), ("#DCE9F7", "#A6C3E4")),
    FOG: (("#404D5F", "#232B38"), ("#E6EBF1", "#B7C1CF")),
    "night": (("#151D42", "#090D22"), ("#5B6FAE", "#2C3868")),
}


def atmosphere(mode: str, kind: str, night: bool) -> Atmosphere:
    """Gradient + text colours for a weather kind, adapted to theme and time of day."""
    if night and kind in (CLEAR, CLOUDS):
        kind_key = "night"
    else:
        kind_key = kind if kind in _BASE else CLOUDS
    dark_pair, light_pair = _BASE[kind_key]
    top, bottom = dark_pair if mode == "dark" else light_pair
    if night and kind_key != "night":  # rain/snow/storm/fog after dark
        top, bottom = darken(top, 0.38), darken(bottom, 0.45)
    average = mix(top, bottom, 0.5)
    text = "#F5F8FF" if luminance(average) < 0.30 else "#0E1A33"
    return Atmosphere(
        kind=kind_key, top=top, bottom=bottom, text=text,
        muted=mix(text, average, 0.32), pill=mix(top, text, 0.16), night=night or kind_key == "night",
    )
