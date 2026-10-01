"""Reusable, theme-aware Tk widgets for SkyPulse."""
from __future__ import annotations

import tkinter as tk

from theme import ThemeManager, mix
from ui import render
from ui.icons import ui_icon
from ui.style import S, font, photo


# ─────────────────────────────────────────────────────────────────────────────
# Simple themed widgets
# ─────────────────────────────────────────────────────────────────────────────

class ThemedFrame(tk.Frame):
    def __init__(self, master, theme: ThemeManager, bg: str = "bg", **kw):
        super().__init__(master, bd=0, highlightthickness=0, **kw)
        self.theme = theme
        self.bg_role = bg
        theme.subscribe(self._apply)
        self._apply(theme.palette)

    def _apply(self, p):
        self.configure(bg=getattr(p, self.bg_role))


class ThemedLabel(tk.Label):
    def __init__(
        self,
        master,
        theme: ThemeManager,
        text: str = "",
        fg: str = "text",
        bg: str = "bg",
        **kw
    ):
        super().__init__(
            master,
            text=text,
            bd=0,
            highlightthickness=0,
            **kw
        )
        self.theme = theme
        self.fg_role = fg
        self.bg_role = bg

        theme.subscribe(self._apply)
        self._apply(theme.palette)

    def _apply(self, p):
        self.configure(
            fg=getattr(p, self.fg_role),
            bg=getattr(p, self.bg_role)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Canvas card
# ─────────────────────────────────────────────────────────────────────────────

class CanvasCard(tk.Canvas):
    """Rounded weather card that automatically fills its grid cell."""

    radius = 20

    def __init__(
        self,
        master,
        theme: ThemeManager,
        height: int,
        inset: int = 8,
        surface_role: str = "surface",
        **kw
    ):
        self.theme = theme
        self.surface_role = surface_role

        self._height_design = height
        self._inset_design = inset

        super().__init__(
            master,
            width=S(300),
            height=S(height),
            bd=0,
            highlightthickness=0,
            bg=theme.palette.bg,
            **kw
        )

        self.inset = S(inset)

        self._refs = []
        self._redraw_job = None

        # IMPORTANT:
        # CanvasCard must redraw when grid expands it.
        self.bind("<Configure>", self._on_configure)

        theme.subscribe(self._on_theme)

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    def _on_configure(self, event=None):
        if event is not None:
            # Keep the canvas's real size.
            if event.width > 20:
                self._current_width = event.width
            if event.height > 20:
                self._current_height = event.height

        self._schedule_redraw()

    def _schedule_redraw(self):
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass

        self._redraw_job = self.after(20, self.redraw)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _on_theme(self, p):
        try:
            self.configure(bg=p.bg)
        except tk.TclError:
            return

        self._schedule_redraw()

    # ------------------------------------------------------------------
    # Surface
    # ------------------------------------------------------------------

    def shadow_args(self, p) -> dict:
        return {
            "shadow_alpha": p.shadow_alpha,
            "shadow_offset": S(p.shadow_offset),
            "shadow_blur": min(
                S(p.shadow_blur),
                max(2, int(self.inset * 0.75))
            ),
        }

    def surface_args(self, p) -> dict:
        return {
            "fill": getattr(p, self.surface_role),
            "border": p.border if p.bordered else None,
            **self.shadow_args(p),
        }

    def body_box(self, w: int, h: int, p=None):
        p = p or self.theme.palette

        inset = self.inset
        shadow = S(p.shadow_offset)

        return (
            inset,
            inset,
            max(inset + 1, w - inset),
            max(inset + 1, h - inset - shadow),
        )

    # ------------------------------------------------------------------
    # Images/icons
    # ------------------------------------------------------------------

    def add_image(
        self,
        x,
        y,
        pil,
        anchor="nw",
        tags=()
    ):
        ph = photo(pil)
        self._refs.append(ph)

        return self.create_image(
            x,
            y,
            image=ph,
            anchor=anchor,
            tags=tags
        )

    def add_icon(
        self,
        name,
        x,
        y,
        size,
        color,
        anchor="center",
        tags=()
    ):
        return self.add_image(
            x,
            y,
            ui_icon(name, S(size), color),
            anchor=anchor,
            tags=tags
        )

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def redraw(self):
        self._redraw_job = None

        try:
            w = self.winfo_width()
            h = self.winfo_height()
        except tk.TclError:
            return

        if w < 40 or h < 40:
            return

        p = self.theme.palette

        self.delete("all")
        self._refs = []

        surface = render.surface(
            w,
            h,
            S(self.radius),
            page_bg=p.bg,
            inset=self.inset,
            **self.surface_args(p)
        )

        self.add_image(0, 0, surface)

        self.draw_content(w, h, p)

    def draw_content(self, w: int, h: int, p):
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Canvas button
# ─────────────────────────────────────────────────────────────────────────────

class CanvasButton(tk.Canvas):
    """Canvas based button."""

    def __init__(
        self,
        master,
        theme: ThemeManager,
        text: str = "",
        icon: str | None = None,
        command=None,
        style: str = "secondary",
        height: int = 44,
        padx: int = 18,
        min_width: int = 0,
        size: int = 15,
        icon_size: int = 18,
        bg_role: str = "bg",
        square: bool = False,
        tooltip: str | None = None
    ):
        self.theme = theme
        self.text = text
        self.icon = icon
        self.command = command
        self.style = style
        self.bg_role = bg_role
        self.icon_size = icon_size

        self._font = font(size, True)

        self._text_w = (
            self._font.measure(text)
            if text
            else 0
        )

        self._icon_w = S(icon_size) if icon else 0
        self._gap = S(8) if icon and text else 0

        self._height = S(height)

        self._width = (
            self._height
            if square
            else max(
                S(min_width),
                self._text_w
                + self._icon_w
                + self._gap
                + 2 * S(padx)
            )
        )

        super().__init__(
            master,
            width=self._width,
            height=self._height,
            bd=0,
            highlightthickness=0,
            bg=getattr(theme.palette, bg_role),
            cursor="hand2"
        )

        self._hover = False
        self._pressed = False
        self._enabled = True
        self._refs = []

        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)

        theme.subscribe(self._on_theme)

        self.redraw()

    def _on_theme(self, p):
        self.configure(bg=getattr(p, self.bg_role))
        self.redraw()

    def _set_hover(self, value):
        self._hover = value

        if not value:
            self._pressed = False

        self.redraw()

    def _press(self, _event):
        if self._enabled:
            self._pressed = True
            self.redraw()

    def _release(self, event):
        fire = (
            self._pressed
            and self._enabled
            and 0 <= event.x <= self._width
            and 0 <= event.y <= self._height
        )

        self._pressed = False
        self.redraw()

        if fire and self.command:
            self.command()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

        self.configure(
            cursor="hand2" if enabled else "arrow"
        )

        self.redraw()

    def set_icon(self, icon: str):
        self.icon = icon
        self.redraw()

    def _colors(self, p):
        hot = self._hover and self._enabled

        if self.style == "primary":
            fill = p.accent_hover if hot else p.accent
            fg = p.on_accent
            border = None

        elif self.style == "chip":
            fill = (
                mix(p.surface_alt, p.accent, 0.16)
                if hot
                else p.surface_alt
            )
            fg = p.text
            border = p.border if p.bordered else None

        elif self.style == "ghost":
            fill = p.surface_alt if hot else p.bg
            fg = p.text_muted
            border = None

        else:
            fill = p.surface_alt if hot else p.surface
            fg = p.text
            border = p.border

        if self._pressed:
            fill = mix(fill, p.text, 0.08)

        if not self._enabled:
            fill = mix(fill, p.bg, 0.45)
            fg = p.text_faint

        return fill, fg, border

    def redraw(self):
        p = self.theme.palette

        fill, fg, border = self._colors(p)

        self.delete("all")
        self._refs = []

        bg = getattr(p, self.bg_role)

        image = render.surface(
            self._width,
            self._height,
            self._height // 2,
            fill,
            bg,
            border=border,
            border_w=max(1, S(1))
        )

        ph = photo(image)
        self._refs.append(ph)

        self.create_image(
            0,
            0,
            image=ph,
            anchor="nw"
        )

        content_width = (
            self._icon_w
            + self._gap
            + self._text_w
        )

        x = (
            self._width
            - content_width
        ) // 2

        cy = self._height // 2

        if self.icon:
            icon_image = photo(
                ui_icon(
                    self.icon,
                    S(self.icon_size),
                    fg
                )
            )

            self._refs.append(icon_image)

            self.create_image(
                x + self._icon_w // 2,
                cy,
                image=icon_image,
                anchor="center"
            )

            x += self._icon_w + self._gap

        if self.text:
            self.create_text(
                x,
                cy,
                text=self.text,
                anchor="w",
                fill=fg,
                font=self._font
            )


# ─────────────────────────────────────────────────────────────────────────────
# Segmented control
# ─────────────────────────────────────────────────────────────────────────────

class Segmented(tk.Canvas):
    """°C / °F selector."""

    def __init__(
        self,
        master,
        theme: ThemeManager,
        options,
        value,
        command,
        height: int = 40,
        seg_width: int = 58
    ):
        self.options = list(options)
        self.value = value
        self.command = command

        self._height = S(height)
        self._segment_width = S(seg_width)
        self._width = (
            self._segment_width * len(self.options)
            + S(8)
        )

        super().__init__(
            master,
            width=self._width,
            height=self._height,
            bd=0,
            highlightthickness=0,
            bg=theme.palette.bg,
            cursor="hand2"
        )

        self.theme = theme
        self._refs = []
        self._font = font(14, True)

        self.bind(
            "<ButtonRelease-1>",
            self._click
        )

        theme.subscribe(
            lambda p: (
                self.configure(bg=p.bg),
                self.redraw()
            )
        )

        self.redraw()

    def _click(self, event):
        index = int(
            (event.x - S(4))
            // self._segment_width
        )

        if 0 <= index < len(self.options):
            self.select(
                self.options[index][0],
                notify=True
            )

    def select(self, value, notify=False):
        changed = value != self.value

        self.value = value
        self.redraw()

        if (
            notify
            and changed
            and self.command
        ):
            self.command(value)

    def redraw(self):
        p = self.theme.palette

        self.delete("all")
        self._refs = []

        track = photo(
            render.surface(
                self._width,
                self._height,
                self._height // 2,
                p.surface,
                p.bg,
                border=p.border,
                border_w=max(1, S(1))
            )
        )

        self._refs.append(track)

        self.create_image(
            0,
            0,
            image=track,
            anchor="nw"
        )

        for i, (value, label) in enumerate(self.options):
            x0 = S(4) + i * self._segment_width

            selected = value == self.value

            if selected:
                pill = photo(
                    render.pill(
                        self._segment_width,
                        self._height - S(8),
                        p.accent
                    )
                )

                self._refs.append(pill)

                self.create_image(
                    x0,
                    S(4),
                    image=pill,
                    anchor="nw"
                )

            self.create_text(
                x0 + self._segment_width // 2,
                self._height // 2,
                text=label,
                font=self._font,
                fill=(
                    p.on_accent
                    if selected
                    else p.text_muted
                )
            )


# ─────────────────────────────────────────────────────────────────────────────
# Search bar
# ─────────────────────────────────────────────────────────────────────────────

class SearchBar(tk.Canvas):
    """Large rounded search field."""

    def __init__(
        self,
        master,
        theme: ThemeManager,
        placeholder: str,
        on_submit,
        on_change=None,
        height: int = 54
    ):
        super().__init__(
            master,
            height=S(height),
            width=S(200),
            bd=0,
            highlightthickness=0,
            bg=theme.palette.bg
        )

        self.theme = theme
        self.placeholder = placeholder
        self.on_submit = on_submit
        self.on_change = on_change

        self._height = S(height)

        self._focused = False
        self._error = False
        self._busy = False
        self._placeholder_on = False

        self._refs = []

        self._angle = 0
        self._spin_job = None

        self.entry = tk.Entry(
            self,
            bd=0,
            highlightthickness=0,
            relief="flat",
            font=font(16),
            insertwidth=2
        )

        self._window = self.create_window(
            S(58),
            self._height // 2,
            window=self.entry,
            anchor="w"
        )

        self.entry.bind(
            "<FocusIn>",
            self._focus_in
        )

        self.entry.bind(
            "<FocusOut>",
            self._focus_out
        )

        self.entry.bind(
            "<Return>",
            lambda _e: self.on_submit()
        )

        self.entry.bind(
            "<KeyRelease>",
            self._key
        )

        self.bind(
            "<Button-1>",
            lambda _e: self.entry.focus_set()
        )

        self.bind(
            "<Configure>",
            lambda _e: self.redraw()
        )

        theme.subscribe(self._on_theme)

        self._show_placeholder()

    # ------------------------------------------------------------------
    # Text
    # ------------------------------------------------------------------

    def get_text(self) -> str:
        if self._placeholder_on:
            return ""

        return self.entry.get()

    def set_text(self, text: str):
        self._placeholder_on = False

        self.entry.delete(0, "end")
        self.entry.insert(0, text)

        self._style_entry()

    def clear(self):
        self.entry.delete(0, "end")

        if not self._focused:
            self._show_placeholder()

    def focus(self):
        self.entry.focus_set()

    def _show_placeholder(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, self.placeholder)

        self._placeholder_on = True

        self._style_entry()

    def _focus_in(self, _event):
        self._focused = True

        if self._placeholder_on:
            self.entry.delete(0, "end")
            self._placeholder_on = False

        self._style_entry()
        self.redraw()

    def _focus_out(self, _event):
        self._focused = False

        if not self.entry.get().strip():
            self._show_placeholder()

        self._style_entry()
        self.redraw()

    def _key(self, event):
        if event.keysym not in (
            "Return",
            "Tab",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R"
        ):
            if self.on_change:
                self.on_change()

    def set_error(self, value: bool):
        self._error = value
        self.redraw()

    # ------------------------------------------------------------------
    # Busy spinner
    # ------------------------------------------------------------------

    def set_busy(self, busy: bool):
        self._busy = busy

        self.redraw()

        if busy and self._spin_job is None:
            self._spin()

        elif not busy and self._spin_job is not None:
            try:
                self.after_cancel(self._spin_job)
            except tk.TclError:
                pass

            self._spin_job = None

    def _spin(self):
        if not self._busy:
            self._spin_job = None
            return

        self._angle = (
            self._angle - 14
        ) % 360

        try:
            self.itemconfigure(
                "spinner",
                start=self._angle
            )
        except tk.TclError:
            pass

        self._spin_job = self.after(
            30,
            self._spin
        )

    # ------------------------------------------------------------------
    # Entry colors
    # ------------------------------------------------------------------

    def _style_entry(self):
        p = self.theme.palette

        self.entry.configure(
            bg=p.surface,
            fg=(
                p.text_faint
                if self._placeholder_on
                else p.text
            ),
            insertbackground=p.text,
            selectbackground=p.accent,
            selectforeground=p.on_accent,
            disabledbackground=p.surface
        )

    def _on_theme(self, p):
        self.configure(bg=p.bg)

        self._style_entry()
        self.redraw()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def redraw(self):
        w = self.winfo_width()
        h = self.winfo_height()

        if w < 60 or h < 20:
            return

        p = self.theme.palette

        self.delete("bg")
        self._refs = []

        ring = (
            p.danger
            if self._error
            else (
                p.accent
                if self._focused
                else p.border
            )
        )

        image = render.surface(
            w,
            h,
            h // 2,
            p.surface,
            p.bg,
            inset=S(4),
            border=ring,
            border_w=(
                S(2)
                if (
                    self._focused
                    or self._error
                )
                else S(1)
            ),
            shadow_alpha=p.shadow_alpha // 2,
            shadow_blur=S(3),
            shadow_offset=S(1)
        )

        ph = photo(image)
        self._refs.append(ph)

        self.create_image(
            0,
            0,
            image=ph,
            anchor="nw",
            tags="bg"
        )

        search_icon = photo(
            ui_icon(
                "search",
                S(22),
                p.accent if self._focused
                else p.text_faint
            )
        )

        self._refs.append(search_icon)

        self.create_image(
            S(34),
            h // 2,
            image=search_icon,
            anchor="center",
            tags="bg"
        )

        right = S(56)

        self.coords(
            self._window,
            S(58),
            h // 2
        )

        self.itemconfigure(
            self._window,
            width=max(
                S(40),
                w - S(58) - right
            )
        )

        if self._busy:
            r = S(10)
            cx = w - S(34)

            self.create_oval(
                cx - r,
                h // 2 - r,
                cx + r,
                h // 2 + r,
                outline=p.border,
                width=S(3),
                tags="bg"
            )

            self.create_arc(
                cx - r,
                h // 2 - r,
                cx + r,
                h // 2 + r,
                start=self._angle,
                extent=100,
                style="arc",
                outline=p.accent,
                width=S(3),
                tags=("bg", "spinner")
            )

        self.tag_lower("bg")


# ─────────────────────────────────────────────────────────────────────────────
# Suggestion chips
# ─────────────────────────────────────────────────────────────────────────────

class ChipRow(tk.Frame):
    """Wrapping row of city suggestion buttons."""

    def __init__(
        self,
        master,
        theme: ThemeManager,
        on_pick
    ):
        super().__init__(
            master,
            bd=0,
            highlightthickness=0,
            height=S(34),
            bg=theme.palette.bg
        )

        self.theme = theme
        self.on_pick = on_pick
        self._widgets = []

        self.bind(
            "<Configure>",
            lambda _e: self._layout()
        )

        theme.subscribe(
            lambda p: self.configure(bg=p.bg)
        )

    def set_groups(self, groups):
        for widget in self._widgets:
            try:
                widget.destroy()
            except tk.TclError:
                pass

        self._widgets = []

        for label, icon, items in groups:
            if not items:
                continue

            label_widget = ThemedLabel(
                self,
                self.theme,
                label,
                fg="text_faint",
                font=font(12, True)
            )

            self._widgets.append(
                label_widget
            )

            for text, value in items:
                button = CanvasButton(
                    self,
                    self.theme,
                    text=text,
                    icon=icon,
                    command=lambda v=value: self.on_pick(v),
                    style="chip",
                    height=32,
                    padx=14,
                    size=13,
                    icon_size=13
                )

                self._widgets.append(button)

        self.after_idle(self._layout)

    def _layout(self):
        width = self.winfo_width()

        if width < 50:
            return

        gap = S(8)
        row_h = S(32)

        x = 0
        y = 0

        for widget in self._widgets:
            ww = widget.winfo_reqwidth()
            wh = widget.winfo_reqheight()

            if (
                x > 0
                and x + ww > width
            ):
                x = 0
                y += row_h + gap

            widget.place(
                x=x,
                y=y + max(0, (row_h - wh) // 2)
            )

            x += ww + gap

        needed = (
            y + row_h
            if self._widgets
            else 1
        )

        try:
            self.configure(height=needed)
        except tk.TclError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Scrollbar
# ─────────────────────────────────────────────────────────────────────────────

class MiniScrollbar(tk.Canvas):
    """Slim rounded scrollbar."""

    def __init__(
        self,
        master,
        theme: ThemeManager,
        command
    ):
        super().__init__(
            master,
            width=S(12),
            bd=0,
            highlightthickness=0,
            bg=theme.palette.bg
        )

        self.theme = theme
        self.command = command

        self._lo = 0.0
        self._hi = 1.0

        self.bind(
            "<Button-1>",
            self._drag
        )

        self.bind(
            "<B1-Motion>",
            self._drag
        )

        self.bind(
            "<Configure>",
            lambda _e: self.redraw()
        )

        theme.subscribe(
            lambda p: (
                self.configure(bg=p.bg),
                self.redraw()
            )
        )

    def set(self, lo, hi):
        self._lo = float(lo)
        self._hi = float(hi)
        self.redraw()

    def _drag(self, event):
        h = max(
            1,
            self.winfo_height()
        )

        span = self._hi - self._lo

        self.command(
            "moveto",
            max(
                0.0,
                min(
                    1.0 - span,
                    event.y / h - span / 2
                )
            )
        )

    def redraw(self):
        self.delete("all")

        h = self.winfo_height()

        if (
            self._hi - self._lo >= 0.999
            or h < 20
        ):
            return

        p = self.theme.palette

        x = self.winfo_width() // 2
        pad = S(4)

        top = self._lo * h + pad
        bottom = max(
            top + S(24),
            self._hi * h - pad
        )

        self.create_line(
            x,
            top,
            x,
            bottom,
            width=S(6),
            capstyle="round",
            fill=mix(
                p.text_faint,
                p.bg,
                0.35
            )
        )


# ─────────────────────────────────────────────────────────────────────────────
# Scroll frame
# ─────────────────────────────────────────────────────────────────────────────

class ScrollFrame(tk.Frame):
    """Vertical scrolling container whose inner frame always matches width."""

    def __init__(
        self,
        master,
        theme: ThemeManager
    ):
        super().__init__(
            master,
            bd=0,
            highlightthickness=0,
            bg=theme.palette.bg
        )

        self.theme = theme

        self.canvas = tk.Canvas(
            self,
            bd=0,
            highlightthickness=0,
            bg=theme.palette.bg,
            yscrollincrement=S(18)
        )

        self.bar = MiniScrollbar(
            self,
            theme,
            self.canvas.yview
        )

        self.canvas.configure(
            yscrollcommand=self.bar.set
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.bar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.columnconfigure(
            0,
            weight=1
        )

        self.rowconfigure(
            0,
            weight=1
        )

        # IMPORTANT:
        # Give the inner frame a real expandable width.
        self.inner = tk.Frame(
            self.canvas,
            bd=0,
            highlightthickness=0,
            bg=theme.palette.bg
        )

        self.inner.columnconfigure(
            0,
            weight=1
        )

        self._window = self.canvas.create_window(
            0,
            0,
            window=self.inner,
            anchor="nw"
        )

        self.inner.bind(
            "<Configure>",
            self._inner_configure
        )

        self.canvas.bind(
            "<Configure>",
            self._canvas_configure
        )

        for sequence in (
            "<MouseWheel>",
            "<Button-4>",
            "<Button-5>"
        ):
            self.bind_all(
                sequence,
                self._wheel,
                add="+"
            )

        theme.subscribe(
            self._on_theme
        )

    def _inner_configure(self, _event=None):
        try:
            self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        except tk.TclError:
            pass

    def _canvas_configure(self, event):
        width = max(
            1,
            event.width
        )

        try:
            # Set BOTH the embedded frame width and
            # the canvas window width.
            self.inner.configure(
                width=width
            )

            self.canvas.itemconfigure(
                self._window,
                width=width
            )
        except tk.TclError:
            pass

        self.after_idle(
            self._inner_configure
        )

    def _on_theme(self, p):
        for widget in (
            self,
            self.canvas,
            self.inner
        ):
            try:
                widget.configure(
                    bg=p.bg
                )
            except tk.TclError:
                pass

    def _scrollable(self):
        return (
            self.inner.winfo_reqheight()
            > self.canvas.winfo_height()
        )

    def _wheel(self, event):
        if not self._scrollable():
            return

        if getattr(event, "num", None) == 4:
            step = -1

        elif getattr(event, "num", None) == 5:
            step = 1

        else:
            step = (
                -1
                if event.delta > 0
                else 1
            )

        self.canvas.yview_scroll(
            step * 3,
            "units"
        )

    def scroll_top(self):
        try:
            self.canvas.yview_moveto(0)
        except tk.TclError:
            pass