"""
ui/widgets.py
=============
Custom, canvas-based Tkinter widgets used to give VaultForge a premium,
product-like appearance instead of relying on stock Tkinter defaults.

All widgets here are self-contained and take a ``palette`` (see
``ui.theme``) so they can be redrawn cleanly when the user switches
between the dark and light themes.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional

from ui.theme import Palette, RADIUS_BUTTON, RADIUS_CARD, TYPOGRAPHY


def _round_rect_points(x1, y1, x2, y2, r):
    """Return the point list for a rounded-rectangle polygon."""
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    return [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]


class Card(tk.Frame):
    """A rounded, elevated panel drawn on a Canvas, with a normal Frame
    inside it for placing regular child widgets."""

    def __init__(self, master, palette: Palette, radius: int = RADIUS_CARD,
                 bg_color: Optional[str] = None, border_color: Optional[str] = None,
                 **kwargs):
        super().__init__(master, bg=palette.panel_bg, highlightthickness=0)
        self.palette = palette
        self._radius = radius
        self._bg_color = bg_color or palette.card_bg
        self._border_color = border_color or palette.border

        self._canvas = tk.Canvas(self, bg=palette.panel_bg, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)

        self.body = tk.Frame(self._canvas, bg=self._bg_color, **kwargs)
        self._window = self._canvas.create_window(0, 0, window=self.body, anchor="nw")

        self._canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        w, h = event.width, event.height
        self._canvas.delete("card_bg")
        if w > 2 and h > 2:
            points = _round_rect_points(1, 1, w - 1, h - 1, self._radius)
            self._canvas.create_polygon(
                points, smooth=True, fill=self._bg_color,
                outline=self._border_color, width=1, tags="card_bg",
            )
            self._canvas.tag_lower("card_bg")
        self._canvas.itemconfigure(self._window, width=w, height=h)

    def set_palette(self, palette: Palette, bg_color: Optional[str] = None,
                     border_color: Optional[str] = None) -> None:
        self.palette = palette
        self._bg_color = bg_color or palette.card_bg
        self._border_color = border_color or palette.border
        self._canvas.configure(bg=palette.panel_bg)
        self.body.configure(bg=self._bg_color)
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w > 2 and h > 2:
            self._canvas.delete("card_bg")
            points = _round_rect_points(1, 1, w - 1, h - 1, self._radius)
            self._canvas.create_polygon(
                points, smooth=True, fill=self._bg_color,
                outline=self._border_color, width=1, tags="card_bg",
            )
            self._canvas.tag_lower("card_bg")


class PillButton(tk.Canvas):
    """A rounded, pill-shaped button with hover/press states and an
    optional 'primary' (filled) or 'secondary' (outlined) style."""

    def __init__(self, master, palette: Palette, text: str,
                 command: Optional[Callable[[], None]] = None,
                 style: str = "primary", width: int = 160, height: int = 40,
                 font_size: int = TYPOGRAPHY.size_body, **kwargs):
        super().__init__(master, width=width, height=height,
                          highlightthickness=0, bd=0, **kwargs)
        self.palette = palette
        self._text = text
        self._command = command
        self._style = style
        self._enabled = True
        self._font = tkfont.Font(family=TYPOGRAPHY.family, size=font_size, weight="bold")

        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self._hovering = False
        self.configure(cursor="hand2")
        self._draw()

    def _colors(self):
        p = self.palette
        if self._style == "primary":
            fill = p.accent_hover if self._hovering else p.accent
            text_color = p.text_on_accent
            outline = ""
        elif self._style == "danger":
            fill = p.danger
            text_color = "#ffffff"
            outline = ""
        else:  # secondary / ghost
            fill = p.card_bg_alt if self._hovering else p.card_bg
            text_color = p.text_primary
            outline = p.border
        if not self._enabled:
            fill = p.border_soft
            text_color = p.text_muted
        return fill, text_color, outline

    def _draw(self) -> None:
        self.delete("all")
        w = self.winfo_width() or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        fill, text_color, outline = self._colors()
        points = _round_rect_points(1, 1, w - 1, h - 1, h / 2)
        self.configure(bg=self.master["bg"] if "bg" in self.master.keys() else self.palette.card_bg)
        self.create_polygon(points, smooth=True, fill=fill,
                             outline=outline or fill, width=1)
        self.create_text(w / 2, h / 2, text=self._text, fill=text_color,
                          font=self._font)

    def _on_enter(self, _event) -> None:
        if self._enabled:
            self._hovering = True
            self._draw()

    def _on_leave(self, _event) -> None:
        self._hovering = False
        self._draw()

    def _on_click(self, _event) -> None:
        if self._enabled and self._command:
            self._command()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def set_text(self, text: str) -> None:
        self._text = text
        self._draw()

    def set_palette(self, palette: Palette) -> None:
        self.palette = palette
        self._draw()


class ToggleSwitch(tk.Canvas):
    """An iOS-style rounded toggle switch bound to a tk.BooleanVar."""

    def __init__(self, master, palette: Palette, variable: tk.BooleanVar,
                 command: Optional[Callable[[], None]] = None,
                 width: int = 46, height: int = 24, **kwargs):
        super().__init__(master, width=width, height=height,
                          highlightthickness=0, bd=0, **kwargs)
        self.palette = palette
        self.variable = variable
        self._command = command
        self.configure(cursor="hand2")
        self.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *_: self._draw())
        self._draw()

    def _toggle(self, _event=None) -> None:
        self.variable.set(not self.variable.get())
        if self._command:
            self._command()

    def _draw(self) -> None:
        self.delete("all")
        w = int(self["width"])
        h = int(self["height"])
        on = self.variable.get()
        track_color = self.palette.accent if on else self.palette.border
        knob_color = self.palette.text_on_accent if on else self.palette.text_secondary

        points = _round_rect_points(1, 1, w - 1, h - 1, h / 2)
        self.create_polygon(points, smooth=True, fill=track_color, outline="")

        knob_r = (h - 6) / 2
        cx = (w - h / 2 - knob_r) if on else (h / 2)
        self.create_oval(cx - knob_r, 3, cx + knob_r, h - 3, fill=knob_color, outline="")

    def set_palette(self, palette: Palette) -> None:
        self.palette = palette
        self._draw()


class StrengthMeter(tk.Canvas):
    """A segmented horizontal strength bar with a color that reflects
    the current strength category."""

    def __init__(self, master, palette: Palette, width: int = 320, height: int = 10,
                 segments: int = 4, **kwargs):
        super().__init__(master, width=width, height=height,
                          highlightthickness=0, bd=0, **kwargs)
        self.palette = palette
        self._segments = segments
        self._fraction = 0.0
        self._color = palette.strength_weak
        self.bind("<Configure>", lambda e: self._draw())
        self._draw()

    def set_value(self, fraction: float, color: str) -> None:
        self._fraction = max(0.0, min(1.0, fraction))
        self._color = color
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        w = self.winfo_width() or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        gap = 6
        seg_w = (w - gap * (self._segments - 1)) / self._segments
        filled_segments = round(self._fraction * self._segments)

        for i in range(self._segments):
            x1 = i * (seg_w + gap)
            x2 = x1 + seg_w
            color = self._color if i < filled_segments else self.palette.border
            points = _round_rect_points(x1, 0, x2, h, h / 2)
            self.create_polygon(points, smooth=True, fill=color, outline="")

    def set_palette(self, palette: Palette) -> None:
        self.palette = palette
        self._draw()


class Tooltip:
    """A lightweight hover tooltip attached to any Tk widget."""

    def __init__(self, widget: tk.Widget, text: str, palette: Palette):
        self.widget = widget
        self.text = text
        self.palette = palette
        self._tip: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def set_palette(self, palette: Palette) -> None:
        self.palette = palette

    def _show(self, _event=None) -> None:
        if self._tip is not None:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        self._tip.attributes("-topmost", True)

        label = tk.Label(
            self._tip, text=self.text, justify="left",
            bg=self.palette.card_bg_alt, fg=self.palette.text_primary,
            font=(TYPOGRAPHY.family, TYPOGRAPHY.size_small),
            padx=10, pady=6, bd=1, relief="solid",
            highlightbackground=self.palette.border,
        )
        label.pack()

    def _hide(self, _event=None) -> None:
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


class RequirementRow(tk.Frame):
    """A single line in the live requirement checklist, with a status
    dot that turns on/off as requirements are satisfied."""

    def __init__(self, master, palette: Palette, label: str, **kwargs):
        super().__init__(master, bg=master["bg"], **kwargs)
        self.palette = palette
        self._label_text = label
        self._satisfied = False

        self._dot = tk.Canvas(self, width=14, height=14, highlightthickness=0,
                               bd=0, bg=master["bg"])
        self._dot.pack(side="left", padx=(0, 8))

        self._label = tk.Label(
            self, text=label, bg=master["bg"], fg=palette.text_secondary,
            font=(TYPOGRAPHY.family, TYPOGRAPHY.size_body), anchor="w",
        )
        self._label.pack(side="left", fill="x", expand=True)

        self._draw_dot()

    def _draw_dot(self) -> None:
        self._dot.delete("all")
        color = self.palette.success if self._satisfied else self.palette.text_muted
        self._dot.create_oval(2, 2, 12, 12, fill=color, outline="")

    def set_satisfied(self, satisfied: bool) -> None:
        self._satisfied = satisfied
        self._label.configure(
            fg=self.palette.text_primary if satisfied else self.palette.text_secondary
        )
        self._draw_dot()

    def set_palette(self, palette: Palette) -> None:
        self.palette = palette
        self.configure(bg=self.master["bg"])
        self._dot.configure(bg=self.master["bg"])
        self._label.configure(bg=self.master["bg"], fg=palette.text_secondary)
        self._draw_dot()
