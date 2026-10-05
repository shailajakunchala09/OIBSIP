"""Reusable Tkinter widgets: rounded buttons, fields, avatars, dialogs, toasts."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from common.validation import validate_room_name, MAX_DESCRIPTION_LENGTH

from .theme import EMOJI_FONT, avatar_color, font, theme


def rounded_polygon(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float,
                    radius: float, **options) -> int:
    r = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **options)


class LogoMark(tk.Canvas):
    """The VANTA mark: an accent rounded square holding a speech bubble."""

    def __init__(self, parent: tk.Misc, size: int = 36, bg: str | None = None) -> None:
        super().__init__(parent, width=size, height=size, bg=bg or theme.c["bg"], highlightthickness=0, bd=0)
        s = size
        rounded_polygon(self, 0, 0, s, s, s * 0.28, fill=theme.c["accent"], outline="")
        rounded_polygon(self, s * 0.24, s * 0.26, s * 0.76, s * 0.62, s * 0.12, fill="#FFFFFF", outline="")
        self.create_polygon(s * 0.36, s * 0.60, s * 0.36, s * 0.78, s * 0.54, s * 0.60, fill="#FFFFFF", outline="")


class RoundedButton(tk.Canvas):
    """Canvas-drawn button with hover, pressed and disabled states."""

    STYLES = {
        "primary": ("accent", "accent_hover", "accent_press", "accent_text"),
        "secondary": ("surface_alt", "border", "border", "text"),
        "danger": ("danger", "danger", "danger", "accent_text"),
        "ghost": (None, "hover", "surface_alt", "text_dim"),
    }

    def __init__(self, parent: tk.Misc, text: str, command: Callable[[], None] | None = None,
                 style: str = "primary", width: int = 120, height: int = 38, radius: int = 10,
                 bg: str | None = None, size: int = 10, anchor: str = "center") -> None:
        self._bg = bg or theme.c["bg"]
        super().__init__(parent, width=width, height=height, bg=self._bg, highlightthickness=0, bd=0,
                         cursor="hand2")
        self._label_text, self._command, self._style = text, command, style
        self._radius, self._font, self._anchor = radius, font(size, "bold"), anchor
        self._enabled, self._hovered, self._pressed = True, False, False
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_text(self, text: str) -> None:
        self._label_text = text
        self._redraw()

    def set_style(self, style: str) -> None:
        self._style = style
        self._redraw()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._redraw()

    def _set_hover(self, hovered: bool) -> None:
        self._hovered = hovered
        if not hovered:
            self._pressed = False
        self._redraw()

    def _on_press(self, event: tk.Event) -> None:
        if self._enabled:
            self._pressed = True
            self._redraw()

    def _on_release(self, event: tk.Event) -> None:
        was_pressed, self._pressed = self._pressed, False
        self._redraw()
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        if self._enabled and was_pressed and inside and self._command:
            self._command()

    def _redraw(self) -> None:
        c = theme.c
        self.delete("all")
        width = self.winfo_width() if self.winfo_width() > 1 else int(float(self["width"]))
        height = self.winfo_height() if self.winfo_height() > 1 else int(float(self["height"]))
        base, hover, press, text_key = self.STYLES[self._style]
        if not self._enabled:
            fill, text_color = c["surface_alt"], c["text_faint"]
        else:
            key = press if self._pressed else hover if self._hovered else base
            fill = c[key] if key else self._bg
            text_color = c["text"] if (self._style == "ghost" and self._hovered) else c[text_key]
        if fill != self._bg:
            rounded_polygon(self, 1, 1, width - 1, height - 1, self._radius, fill=fill, outline="")
        if self._anchor == "w":
            self.create_text(14, height // 2, text=self._label_text, fill=text_color, font=self._font, anchor="w")
        else:
            self.create_text(width // 2, height // 2, text=self._label_text, fill=text_color, font=self._font)


class Toggle(tk.Canvas):
    """On/off switch."""

    def __init__(self, parent: tk.Misc, value: bool, command: Callable[[bool], None] | None = None,
                 bg: str | None = None) -> None:
        super().__init__(parent, width=44, height=24, bg=bg or theme.c["surface"], highlightthickness=0,
                         bd=0, cursor="hand2")
        self.value, self._command = value, command
        self.bind("<Button-1>", self._flip)
        self._redraw()

    def _flip(self, event: tk.Event | None = None) -> None:
        self.value = not self.value
        self._redraw()
        if self._command:
            self._command(self.value)

    def _redraw(self) -> None:
        c = theme.c
        self.delete("all")
        rounded_polygon(self, 1, 2, 43, 22, 10, fill=c["accent"] if self.value else c["border"], outline="")
        x = 32 if self.value else 12
        self.create_oval(x - 8, 4, x + 8, 20, fill="#FFFFFF", outline="")


class Field(tk.Frame):
    """Labelled text input with focus ring, error state and optional show/hide toggle."""

    def __init__(self, parent: tk.Misc, label: str, secret: bool = False, bg: str | None = None) -> None:
        c = theme.c
        bg = bg or c["surface"]
        super().__init__(parent, bg=bg)
        self._input_bg, self._focused, self._error = c["input_bg"], False, False
        tk.Label(self, text=label, bg=bg, fg=c["text_dim"], font=font(9), anchor="w").pack(fill="x")
        self._border = tk.Frame(self, bg=c["border"], padx=1, pady=1)
        self._border.pack(fill="x", pady=(5, 0))
        inner = tk.Frame(self._border, bg=self._input_bg)
        inner.pack(fill="x")
        self.var = tk.StringVar()
        self.entry = tk.Entry(inner, textvariable=self.var, bg=self._input_bg, fg=c["text"],
                              insertbackground=c["text"], relief="flat", bd=0, highlightthickness=0,
                              font=font(11), show="•" if secret else "",
                              disabledbackground=self._input_bg, disabledforeground=c["text_faint"])
        self.entry.pack(side="left", fill="x", expand=True, padx=(12, 6), pady=10)
        if secret:
            self._toggle = tk.Label(inner, text="Show", bg=self._input_bg, fg=c["text_dim"],
                                    font=font(9), cursor="hand2")
            self._toggle.pack(side="right", padx=(0, 12))
            self._toggle.bind("<Button-1>", self._toggle_visibility)
        self.entry.bind("<FocusIn>", lambda e: self._set_focus(True))
        self.entry.bind("<FocusOut>", lambda e: self._set_focus(False))
        self.entry.bind("<Key>", lambda e: self.set_error(False) if self._error else None, add="+")

    def _toggle_visibility(self, event: tk.Event) -> None:
        hidden = self.entry.cget("show") != ""
        self.entry.configure(show="" if hidden else "•")
        self._toggle.configure(text="Hide" if hidden else "Show")

    def _set_focus(self, focused: bool) -> None:
        self._focused = focused
        self._paint()

    def _paint(self) -> None:
        c = theme.c
        self._border.configure(bg=c["danger"] if self._error else c["accent"] if self._focused else c["border"])

    def set_error(self, error: bool) -> None:
        self._error = error
        self._paint()

    def set_enabled(self, enabled: bool) -> None:
        self.entry.configure(state="normal" if enabled else "disabled")

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str) -> None:
        self.var.set(value)

    def focus(self) -> None:
        self.entry.focus_set()


class SearchBox(tk.Frame):
    """Compact search input with placeholder; calls on_change(text) as the user types."""

    def __init__(self, parent: tk.Misc, placeholder: str, on_change: Callable[[str], None],
                 bg: str | None = None, on_escape: Callable[[], None] | None = None) -> None:
        c = theme.c
        super().__init__(parent, bg=c["border"], padx=1, pady=1)
        self._placeholder, self._on_change, self._showing_placeholder = placeholder, on_change, True
        inner = tk.Frame(self, bg=c["input_bg"])
        inner.pack(fill="x")
        self.entry = tk.Entry(inner, bg=c["input_bg"], fg=c["text_faint"], insertbackground=c["text"],
                              relief="flat", bd=0, highlightthickness=0, font=font(10))
        self.entry.pack(side="left", fill="x", expand=True, padx=10, pady=7)
        self.entry.insert(0, placeholder)
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.entry.bind("<KeyRelease>", lambda e: on_change(self.get()))
        if on_escape:
            self.entry.bind("<Escape>", lambda e: on_escape())

    def _focus_in(self, event: tk.Event) -> None:
        self.configure(bg=theme.c["accent"])
        if self._showing_placeholder:
            self.entry.delete(0, "end")
            self.entry.configure(fg=theme.c["text"])
            self._showing_placeholder = False

    def _focus_out(self, event: tk.Event) -> None:
        self.configure(bg=theme.c["border"])
        if not self.entry.get():
            self._show_placeholder()

    def _show_placeholder(self) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, self._placeholder)
        self.entry.configure(fg=theme.c["text_faint"])
        self._showing_placeholder = True

    def get(self) -> str:
        return "" if self._showing_placeholder else self.entry.get().strip()

    def clear(self) -> None:
        if not self._showing_placeholder:
            self._show_placeholder()
        self._on_change("")

    def focus(self) -> None:
        self.entry.focus_set()


class Avatar(tk.Canvas):
    """Circle with the user's initial; optional presence dot."""

    def __init__(self, parent: tk.Misc, name: str, size: int = 36, status: str | None = None,
                 bg: str | None = None) -> None:
        bg = bg or theme.c["sidebar"]
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
        self.create_oval(1, 1, size - 1, size - 1, fill=avatar_color(name), outline="")
        self.create_text(size / 2, size / 2, text=name[:1].upper(), fill="#FFFFFF", font=font(max(8, size // 3), "bold"))
        if status:
            d = max(8, size // 3.2)
            color = theme.c["success"] if status == "online" else theme.c["text_faint"]
            self.create_oval(size - d - 1, size - d - 1, size - 1, size - 1, fill=color, outline=bg, width=2)


class Badge(tk.Canvas):
    """Unread-count pill. Draws nothing when the count is zero."""

    def __init__(self, parent: tk.Misc, count: int = 0, bg: str | None = None) -> None:
        super().__init__(parent, width=30, height=18, bg=bg or theme.c["sidebar"], highlightthickness=0, bd=0)
        if count > 0:
            rounded_polygon(self, 1, 1, 29, 17, 8, fill=theme.c["accent"], outline="")
            self.create_text(15, 9, text="99+" if count > 99 else str(count), fill="#FFFFFF", font=font(8, "bold"))


class ThinScrollbar(tk.Canvas):
    """Slim themed scrollbar (the native one ignores colours on Windows)."""

    def __init__(self, parent: tk.Misc, command: Callable[..., None], bg: str | None = None) -> None:
        super().__init__(parent, width=10, bg=bg or theme.c["bg"], highlightthickness=0, bd=0)
        self._command, self._first, self._last, self._grab = command, 0.0, 1.0, 0.0
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)

    def set(self, first: str, last: str) -> None:
        self._first, self._last = float(first), float(last)
        self._redraw()

    def _thumb(self) -> tuple[float, float]:
        height = max(1, self.winfo_height())
        top, bottom = self._first * height, self._last * height
        if bottom - top < 28:
            bottom = top + 28
        return top, min(bottom, height)

    def _redraw(self) -> None:
        self.delete("all")
        if self._last - self._first >= 0.999:
            return
        top, bottom = self._thumb()
        rounded_polygon(self, 2, top + 1, 8, bottom - 1, 3, fill=theme.c["border"], outline="")

    def _press(self, event: tk.Event) -> None:
        top, bottom = self._thumb()
        height = max(1, self.winfo_height())
        if top <= event.y <= bottom:
            self._grab = event.y - top
        else:
            self._grab = (bottom - top) / 2
            self._command("moveto", (event.y - self._grab) / height)

    def _drag(self, event: tk.Event) -> None:
        self._command("moveto", (event.y - self._grab) / max(1, self.winfo_height()))


class ScrollFrame(tk.Frame):
    """Vertically scrolling container. Put children into `.body`."""

    def __init__(self, parent: tk.Misc, bg: str) -> None:
        super().__init__(parent, bg=bg)
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._scrollbar = ThinScrollbar(self, self._canvas.yview, bg=bg)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self._canvas, bg=bg)
        window = self._canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfigure(window, width=e.width))
        self.bind_all("<MouseWheel>", self._on_wheel, add="+")

    def _on_wheel(self, event: tk.Event) -> None:
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
            while widget is not None and widget is not self:
                widget = widget.master
            if widget is self and self.body.winfo_height() > self._canvas.winfo_height():
                self._canvas.yview_scroll(int(-event.delta / 120), "units")
        except (tk.TclError, KeyError):
            pass        # the widget was destroyed (e.g. after a theme switch)


class ModalDialog(tk.Toplevel):
    """Themed modal window centred over its parent. Subclass or fill `.body`."""

    def __init__(self, parent: tk.Misc, title: str, width: int = 420) -> None:
        super().__init__(parent, bg=theme.c["surface"])
        self.withdraw()
        self._parent = parent.winfo_toplevel()
        self.title(title)
        self.resizable(False, False)
        self.transient(self._parent)
        self.result = None
        self._width = width
        self.body = tk.Frame(self, bg=theme.c["surface"], padx=26, pady=22)
        self.body.pack(fill="both", expand=True)
        self.bind("<Escape>", lambda e: self.close(None))
        self.protocol("WM_DELETE_WINDOW", lambda: self.close(None))

    def add_buttons(self, *buttons: tuple[str, str, Callable[[], None]]) -> None:
        row = tk.Frame(self.body, bg=theme.c["surface"])
        row.pack(fill="x", pady=(22, 0))
        for text, style, command in reversed(buttons):
            RoundedButton(row, text, command, style=style, width=104, height=36,
                          bg=theme.c["surface"]).pack(side="right", padx=(8, 0))

    def show(self):
        self.update_idletasks()
        height = self.winfo_reqheight()
        x = self._parent.winfo_rootx() + (self._parent.winfo_width() - self._width) // 2
        y = self._parent.winfo_rooty() + (self._parent.winfo_height() - height) // 3
        self.geometry(f"{self._width}x{height}+{max(0, x)}+{max(0, y)}")
        self.deiconify()
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.focus_set()
        self.wait_window()
        return self.result

    def close(self, result=None) -> None:
        self.result = result
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


def _heading(dialog: ModalDialog, title: str, message: str, color: str | None = None) -> None:
    c = theme.c
    tk.Label(dialog.body, text=title, bg=c["surface"], fg=color or c["text"], font=font(14, "bold"),
             anchor="w").pack(fill="x")
    tk.Label(dialog.body, text=message, bg=c["surface"], fg=c["text_dim"], font=font(10), anchor="w",
             justify="left", wraplength=dialog._width - 56).pack(fill="x", pady=(8, 0))


def confirm(parent: tk.Misc, title: str, message: str, confirm_text: str = "Confirm",
            danger: bool = False) -> bool:
    dialog = ModalDialog(parent, title)
    _heading(dialog, title, message)
    dialog.add_buttons(("Cancel", "secondary", lambda: dialog.close(False)),
                       (confirm_text, "danger" if danger else "primary", lambda: dialog.close(True)))
    dialog.bind("<Return>", lambda e: dialog.close(True))
    return bool(dialog.show())


def notify(parent: tk.Misc, title: str, message: str, kind: str = "info") -> None:
    dialog = ModalDialog(parent, title)
    _heading(dialog, title, message, theme.c["danger"] if kind == "error" else None)
    dialog.add_buttons(("OK", "primary", lambda: dialog.close(True)))
    dialog.bind("<Return>", lambda e: dialog.close(True))
    dialog.show()


def ask_new_room(parent: tk.Misc) -> tuple[str, str] | None:
    dialog = ModalDialog(parent, "Create room")
    c = theme.c
    tk.Label(dialog.body, text="Create a room", bg=c["surface"], fg=c["text"], font=font(14, "bold"),
             anchor="w").pack(fill="x")
    tk.Label(dialog.body, text="Rooms are visible to everyone on this server.", bg=c["surface"],
             fg=c["text_dim"], font=font(10), anchor="w").pack(fill="x", pady=(4, 14))
    name = Field(dialog.body, "Room name")
    name.pack(fill="x")
    description = Field(dialog.body, f"Description (optional, up to {MAX_DESCRIPTION_LENGTH} characters)")
    description.pack(fill="x", pady=(12, 0))
    error = tk.Label(dialog.body, text="", bg=c["surface"], fg=c["danger"], font=font(9), anchor="w")
    error.pack(fill="x", pady=(10, 0))

    def submit() -> None:
        value = name.get().strip().lstrip("#")
        problem = validate_room_name(value)
        if problem:
            error.configure(text=problem)
            name.set_error(True)
            return
        dialog.close((value, description.get().strip()))

    dialog.add_buttons(("Cancel", "secondary", lambda: dialog.close(None)), ("Create", "primary", submit))
    dialog.bind("<Return>", lambda e: submit())
    dialog.after(80, name.focus)
    return dialog.show()


class ToastManager:
    """Small always-on-top popups in the screen corner; they work while the app is unfocused."""

    WIDTH, HEIGHT, MARGIN, MAX_VISIBLE = 330, 78, 16, 3

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._toasts: list[tk.Toplevel] = []

    def show(self, title: str, body: str, on_click: Callable[[], None] | None = None,
             duration_ms: int = 5000) -> None:
        c = theme.c
        while len(self._toasts) >= self.MAX_VISIBLE:
            self._dismiss(self._toasts[0])
        toast = tk.Toplevel(self._root, bg=c["border"])
        toast.overrideredirect(True)
        try:
            toast.attributes("-topmost", True)
        except tk.TclError:
            pass
        card = tk.Frame(toast, bg=c["surface"])
        card.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Frame(card, bg=c["accent"], width=4).pack(side="left", fill="y")
        text = tk.Frame(card, bg=c["surface"])
        text.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        tk.Label(text, text=title, bg=c["surface"], fg=c["text"], font=font(10, "bold"), anchor="w").pack(fill="x")
        tk.Label(text, text=body, bg=c["surface"], fg=c["text_dim"], font=font(10, family=EMOJI_FONT),
                 anchor="w", justify="left", wraplength=self.WIDTH - 50).pack(fill="x", pady=(3, 0))

        def clicked(event: tk.Event) -> None:
            self._dismiss(toast)
            if on_click:
                on_click()

        for widget in (toast, card, text, *text.winfo_children()):
            widget.bind("<Button-1>", clicked)
        self._toasts.append(toast)
        self._restack()
        toast.after(duration_ms, lambda: self._dismiss(toast))

    def _dismiss(self, toast: tk.Toplevel) -> None:
        if toast in self._toasts:
            self._toasts.remove(toast)
            toast.destroy()
            self._restack()

    def _restack(self) -> None:
        screen_w, screen_h = self._root.winfo_screenwidth(), self._root.winfo_screenheight()
        for index, toast in enumerate(reversed(self._toasts)):
            x = screen_w - self.WIDTH - self.MARGIN
            y = screen_h - 64 - (index + 1) * (self.HEIGHT + 10)
            toast.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
