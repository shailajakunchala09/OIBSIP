"""DPI scaling and font helpers shared by every widget."""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import font as tkfont

from PIL import ImageTk

_FACTOR = 1.0
_FAMILY = "TkDefaultFont"
_FONTS: dict = {}
_PREFERRED = ("Segoe UI Variable Display", "Segoe UI", "SF Pro Display", "Helvetica Neue",
              "Inter", "Poppins", "Ubuntu", "Noto Sans", "DejaVu Sans")


def init(root: tk.Misc) -> None:
    """Call once after creating the Tk root."""
    global _FACTOR, _FAMILY
    _FACTOR = 1.0 if sys.platform == "darwin" else min(3.0, max(1.0, root.winfo_fpixels("1i") / 96.0))
    available = {name.lower(): name for name in tkfont.families(root)}
    for name in _PREFERRED:
        if name.lower() in available:
            _FAMILY = available[name.lower()]
            break
    _FONTS.clear()


def S(value: float) -> int:
    """Scale a design pixel value to real pixels for the current display."""
    return int(round(value * _FACTOR))


def font(px: float, bold: bool = False) -> tkfont.Font:
    key = (px, bold)
    if key not in _FONTS:
        _FONTS[key] = tkfont.Font(family=_FAMILY, size=-S(px), weight="bold" if bold else "normal")
    return _FONTS[key]


def fit_text(f: tkfont.Font, text: str, max_px: int) -> str:
    """Ellipsise ``text`` so it fits in ``max_px`` pixels."""
    if max_px <= 0:
        return ""
    if f.measure(text) <= max_px:
        return text
    while text and f.measure(text + "…") > max_px:
        text = text[:-1]
    return text.rstrip() + "…"


def photo(image) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(image)
