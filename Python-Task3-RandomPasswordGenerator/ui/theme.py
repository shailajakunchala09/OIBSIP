"""
ui/theme.py
===========
Design tokens for VaultForge: colors, typography, spacing and corner
radii for both the dark (default) and light themes.

The two themes are deliberately NOT simple palette swaps: the dark theme
leans on deep charcoal/navy surfaces with a cyan-violet security accent,
while the light theme uses a softer, warmer neutral surface with an
indigo accent, distinct card elevation styling, and different accent
saturation - so each reads as its own considered design rather than an
inverted clone of the other.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    # Surfaces
    app_bg: str
    panel_bg: str
    card_bg: str
    card_bg_alt: str
    border: str
    border_soft: str

    # Text
    text_primary: str
    text_secondary: str
    text_muted: str
    text_on_accent: str

    # Brand / accent
    accent: str
    accent_hover: str
    accent_soft: str

    # Semantic
    success: str
    warning: str
    danger: str
    info: str

    # Strength meter colors
    strength_weak: str
    strength_medium: str
    strength_strong: str
    strength_very_strong: str


DARK = Palette(
    app_bg="#0b0f19",
    panel_bg="#111726",
    card_bg="#161d2e",
    card_bg_alt="#1c2438",
    border="#232c42",
    border_soft="#1a2136",
    text_primary="#eef1fa",
    text_secondary="#a7b0c8",
    text_muted="#6b7591",
    text_on_accent="#0b0f19",
    accent="#5eead4",
    accent_hover="#7ff3df",
    accent_soft="#173733",
    success="#4ade80",
    warning="#fbbf24",
    danger="#f87171",
    info="#60a5fa",
    strength_weak="#f87171",
    strength_medium="#fbbf24",
    strength_strong="#60d394",
    strength_very_strong="#5eead4",
)

LIGHT = Palette(
    app_bg="#f4f2ee",
    panel_bg="#fbfaf8",
    card_bg="#ffffff",
    card_bg_alt="#f1eee7",
    border="#e2ddd2",
    border_soft="#ece7dc",
    text_primary="#211f2c",
    text_secondary="#5a5668",
    text_muted="#8b869a",
    text_on_accent="#ffffff",
    accent="#4f46e5",
    accent_hover="#6058ec",
    accent_soft="#e6e4fb",
    success="#16a34a",
    warning="#d97706",
    danger="#dc2626",
    info="#2563eb",
    strength_weak="#dc2626",
    strength_medium="#d97706",
    strength_strong="#16a34a",
    strength_very_strong="#4f46e5",
)


@dataclass(frozen=True)
class Typography:
    family: str = "Segoe UI"
    family_mono: str = "Consolas"

    size_display: int = 26
    size_h1: int = 17
    size_h2: int = 13
    size_body: int = 11
    size_small: int = 9
    size_password: int = 22


TYPOGRAPHY = Typography()

RADIUS_CARD = 14
RADIUS_BUTTON = 10
RADIUS_PILL = 999

SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 14
SPACE_LG = 20
SPACE_XL = 28


def get_palette(theme_name: str) -> Palette:
    return DARK if theme_name == "dark" else LIGHT
