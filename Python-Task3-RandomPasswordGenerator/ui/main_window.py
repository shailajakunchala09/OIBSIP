
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from clipboard_manager import ClipboardManager
from config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_TAGLINE,
    CUSTOM_PRESET_NAME,
    DEFAULT_CLIPBOARD_AUTOCLEAR_SECONDS,
    DEFAULT_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    PRESETS,
)
from history import HistoryEntry, SessionHistory
from password_generator import (
    GeneratorSettings,
    PasswordGenerationError,
    generate_password,
)
from strength_analyzer import analyze_password, strength_to_fraction
from ui.theme import get_palette
from validators import ValidationError


STRENGTH_COLOR_KEY = {
    "Weak": "strength_weak",
    "Medium": "strength_medium",
    "Strong": "strength_strong",
    "Very Strong": "strength_very_strong",
}


class MainWindow:
    """Final reliable VaultForge desktop dashboard."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.theme_name = "dark"
        self.palette = get_palette(self.theme_name)

        self.history = SessionHistory()
        self.clipboard = ClipboardManager(
            DEFAULT_CLIPBOARD_AUTOCLEAR_SECONDS
        )

        self.current_password = ""
        self.password_visible = True

        self.length_var = tk.IntVar(
            value=DEFAULT_PASSWORD_LENGTH
        )
        self.use_upper_var = tk.BooleanVar(value=True)
        self.use_lower_var = tk.BooleanVar(value=True)
        self.use_digits_var = tk.BooleanVar(value=True)
        self.use_symbols_var = tk.BooleanVar(value=True)
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)
        self.autoclear_var = tk.IntVar(
            value=DEFAULT_CLIPBOARD_AUTOCLEAR_SECONDS
        )
        self.preset_var = tk.StringVar(value="Strong")

        self._updating_length = False
        self._applying_preset = False
        self._history_rows: list[tk.Widget] = []
        self._checkbox_cards: list[tuple[tk.Frame, tk.Checkbutton]] = []

        self._configure_root()
        self._configure_styles()
        self._build_header()
        self._build_scroll_area()
        self._build_blocks()
        self._build_footer()
        self._bind_events()

        self._apply_preset("Strong")
        self._refresh_all()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ================================================================
    # ROOT / STYLE
    # ================================================================

    def _configure_root(self) -> None:
        self.root.title(
            f"{APP_NAME} — {APP_SUBTITLE}"
        )
        self.root.geometry("1240x900")
        self.root.minsize(860, 620)
        self.root.configure(
            bg=self.palette.app_bg
        )

    def _configure_styles(self) -> None:
        self.style = ttk.Style(self.root)

        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self._apply_ttk_palette()

    def _apply_ttk_palette(self) -> None:
        p = self.palette

        self.style.configure(
            "VF.TCombobox",
            fieldbackground=p.card_bg_alt,
            background=p.card_bg_alt,
            foreground=p.text_primary,
            arrowcolor=p.text_secondary,
            bordercolor=p.border,
            lightcolor=p.card_bg_alt,
            darkcolor=p.card_bg_alt,
            padding=(8, 7),
        )

        self.style.configure(
            "VF.Horizontal.TScale",
            background=p.card_bg,
            troughcolor=p.border,
            lightcolor=p.accent,
            darkcolor=p.accent,
        )

        self.root.option_add(
            "*TCombobox*Listbox.background",
            p.card_bg_alt,
        )
        self.root.option_add(
            "*TCombobox*Listbox.foreground",
            p.text_primary,
        )
        self.root.option_add(
            "*TCombobox*Listbox.selectBackground",
            p.accent,
        )
        self.root.option_add(
            "*TCombobox*Listbox.selectForeground",
            p.text_on_accent,
        )

    # ================================================================
    # HEADER
    # ================================================================

    def _build_header(self) -> None:
        p = self.palette

        self.header = tk.Frame(
            self.root,
            bg=p.card_bg,
            highlightthickness=1,
            highlightbackground=p.border,
        )
        self.header.pack(
            fill="x",
            padx=16,
            pady=(14, 9),
        )

        self.brand = tk.Frame(
            self.header,
            bg=p.card_bg,
        )
        self.brand.pack(
            side="left",
            padx=14,
            pady=10,
        )

        self.logo = tk.Label(
            self.brand,
            text="VF",
            bg=p.accent,
            fg=p.text_on_accent,
            font=("Segoe UI", 12, "bold"),
            width=4,
            pady=8,
        )
        self.logo.pack(
            side="left",
            padx=(0, 11),
        )

        self.title_box = tk.Frame(
            self.brand,
            bg=p.card_bg,
        )
        self.title_box.pack(
            side="left",
            anchor="w",
        )

        self.title_label = tk.Label(
            self.title_box,
            text=APP_NAME,
            bg=p.card_bg,
            fg=p.text_primary,
            font=("Segoe UI", 23, "bold"),
        )
        self.title_label.pack(
            anchor="w"
        )

        self.subtitle_label = tk.Label(
            self.title_box,
            text=f"{APP_SUBTITLE}  ·  {APP_TAGLINE}",
            bg=p.card_bg,
            fg=p.text_secondary,
            font=("Segoe UI", 8),
        )
        self.subtitle_label.pack(
            anchor="w",
            pady=(1, 0),
        )

        self.header_right = tk.Frame(
            self.header,
            bg=p.card_bg,
        )
        self.header_right.pack(
            side="right",
            padx=14,
            pady=10,
        )

        self.security_label = tk.Label(
            self.header_right,
            text="● SECURITY-FIRST",
            bg=p.card_bg,
            fg=p.success,
            font=("Segoe UI", 8, "bold"),
        )
        self.security_label.pack(
            side="right",
            padx=(15, 0),
        )

        self.theme_area = tk.Frame(
            self.header_right,
            bg=p.card_bg,
        )
        self.theme_area.pack(
            side="right"
        )

        tk.Label(
            self.theme_area,
            text="THEME",
            bg=p.card_bg,
            fg=p.text_muted,
            font=("Segoe UI", 7, "bold"),
        ).pack(
            side="left",
            padx=(0, 7),
        )

        self.dark_btn = tk.Button(
            self.theme_area,
            text="Dark",
            command=lambda: self._set_theme("dark"),
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 8, "bold"),
            padx=10,
            pady=6,
        )
        self.dark_btn.pack(
            side="left"
        )

        self.light_btn = tk.Button(
            self.theme_area,
            text="Light",
            command=lambda: self._set_theme("light"),
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 8, "bold"),
            padx=10,
            pady=6,
        )
        self.light_btn.pack(
            side="left",
            padx=(4, 0),
        )

        self._refresh_theme_buttons()

    def _refresh_theme_buttons(self) -> None:
        p = self.palette

        self.dark_btn.configure(
            bg=p.accent if self.theme_name == "dark" else p.card_bg_alt,
            fg=p.text_on_accent if self.theme_name == "dark" else p.text_secondary,
            activebackground=p.accent,
            activeforeground=p.text_on_accent,
        )

        self.light_btn.configure(
            bg=p.accent if self.theme_name == "light" else p.card_bg_alt,
            fg=p.text_on_accent if self.theme_name == "light" else p.text_secondary,
            activebackground=p.accent,
            activeforeground=p.text_on_accent,
        )

    # ================================================================
    # SCROLL AREA
    # ================================================================

    def _build_scroll_area(self) -> None:
        p = self.palette

        self.shell = tk.Frame(
            self.root,
            bg=p.app_bg,
        )
        self.shell.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=(0, 6),
        )

        self.canvas = tk.Canvas(
            self.shell,
            bg=p.app_bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.scrollbar = tk.Scrollbar(
            self.shell,
            orient="vertical",
            command=self.canvas.yview,
            width=13,
            relief="flat",
            bd=0,
            bg=p.card_bg_alt,
            activebackground=p.accent,
            troughcolor=p.app_bg,
        )
        self.scrollbar.pack(
            side="right",
            fill="y",
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.content = tk.Frame(
            self.canvas,
            bg=p.app_bg,
        )

        self.content_window = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw",
        )

        self.content.bind(
            "<Configure>",
            self._update_scroll_region,
        )

        self.canvas.bind(
            "<Configure>",
            self._resize_content_window,
        )

    def _update_scroll_region(self, _event=None) -> None:
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def _resize_content_window(
        self,
        event,
    ) -> None:
        self.canvas.itemconfigure(
            self.content_window,
            width=event.width,
        )

    def _bind_events(self) -> None:
        self.root.bind(
            "<Control-Return>",
            lambda _event: self.on_generate(),
        )
        self.root.bind(
            "<Control-r>",
            lambda _event: self.on_regenerate(),
        )
        self.root.bind(
            "<Control-R>",
            lambda _event: self.on_regenerate(),
        )
        self.root.bind(
            "<Control-l>",
            lambda _event: self.length_spin.focus_set(),
        )
        self.root.bind(
            "<Control-L>",
            lambda _event: self.length_spin.focus_set(),
        )
        self.root.bind(
            "<Escape>",
            lambda _event: self._clear_transient_status(),
        )

        self.root.bind_all(
            "<MouseWheel>",
            self._on_mousewheel,
            add="+",
        )
        self.root.bind_all(
            "<Button-4>",
            lambda _event: self.canvas.yview_scroll(-3, "units"),
            add="+",
        )
        self.root.bind_all(
            "<Button-5>",
            lambda _event: self.canvas.yview_scroll(3, "units"),
            add="+",
        )

        self.length_var.trace_add(
            "write",
            lambda *_args: self._on_length_var_changed(),
        )

    def _on_mousewheel(self, event) -> None:
        delta = getattr(
            event,
            "delta",
            0,
        )
        if delta:
            self.canvas.yview_scroll(
                int(-delta / 120),
                "units",
            )

    # ================================================================
    # BLOCK HELPER
    # ================================================================

    def _make_block(
        self,
        number: str,
        title: str,
        subtitle: str,
    ) -> tuple[tk.Frame, tk.Frame]:

        p = self.palette

        block = tk.Frame(
            self.content,
            bg=p.card_bg,
            highlightthickness=1,
            highlightbackground=p.border,
        )
        block.pack(
            fill="x",
            pady=(0, 10),
        )

        heading = tk.Frame(
            block,
            bg=p.card_bg,
        )
        heading.pack(
            fill="x",
            padx=18,
            pady=(14, 8),
        )

        tk.Label(
            heading,
            text=number,
            bg=p.accent,
            fg=p.text_on_accent,
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=4,
        ).pack(
            side="left"
        )

        text_box = tk.Frame(
            heading,
            bg=p.card_bg,
        )
        text_box.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10,
        )

        tk.Label(
            text_box,
            text=title,
            bg=p.card_bg,
            fg=p.text_primary,
            font=("Segoe UI", 18, "bold"),
        ).pack(
            anchor="w"
        )

        tk.Label(
            text_box,
            text=subtitle,
            bg=p.card_bg,
            fg=p.text_muted,
            font=("Segoe UI", 8),
        ).pack(
            anchor="w",
            pady=(1, 0),
        )

        body = tk.Frame(
            block,
            bg=p.card_bg,
        )
        body.pack(
            fill="x",
            padx=18,
            pady=(0, 17),
        )

        return block, body

    def _field_label(
        self,
        parent: tk.Widget,
        text: str,
    ) -> None:

        tk.Label(
            parent,
            text=text,
            bg=parent["bg"],
            fg=self.palette.text_secondary,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
            pady=(5, 4),
        )

    def _build_blocks(self) -> None:
        """Build all dashboard sections in the required order."""
        self._build_generator_block()
        self._build_password_block()
        self._build_security_block()
        self._build_history_block()

    def _button(
        self,
        parent: tk.Widget,
        text: str,
        command,
        primary: bool = False,
    ) -> tk.Button:
        """Create a consistent VaultForge action button."""
        p = self.palette

        normal_bg = p.accent if primary else p.card_bg_alt
        normal_fg = p.text_on_accent if primary else p.text_primary
        hover_bg = p.accent if primary else p.border

        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=normal_bg,
            fg=normal_fg,
            activebackground=hover_bg,
            activeforeground=(
                p.text_on_accent if primary else p.text_primary
            ),
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=p.accent if primary else p.border,
            highlightcolor=p.accent,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=7,
        )

        button._vf_primary = primary
        button._vf_normal_bg = normal_bg
        button._vf_hover_bg = hover_bg

        button.bind(
            "<Enter>",
            lambda _event: button.configure(
                bg=button._vf_hover_bg
            ),
        )

        button.bind(
            "<Leave>",
            lambda _event: button.configure(
                bg=button._vf_normal_bg
            ),
        )

        return button

    def _refresh_button(self, button: tk.Button) -> None:
        """Refresh an action button after a theme change."""
        p = self.palette
        primary = getattr(button, "_vf_primary", False)

        normal_bg = p.accent if primary else p.card_bg_alt
        normal_fg = p.text_on_accent if primary else p.text_primary
        hover_bg = p.accent if primary else p.border

        button.configure(
            bg=normal_bg,
            fg=normal_fg,
            activebackground=hover_bg,
            activeforeground=(
                p.text_on_accent if primary else p.text_primary
            ),
            highlightbackground=p.accent if primary else p.border,
            highlightcolor=p.accent,
        )

        button._vf_normal_bg = normal_bg
        button._vf_hover_bg = hover_bg

    # ================================================================
    # 01 GENERATOR CONTROLS
    # ================================================================

    def _build_generator_block(self) -> None:
        _block, body = self._make_block(
            "01",
            "Generator Controls",
            "Configure password length, character groups and security options.",
        )

        top = tk.Frame(
            body,
            bg=body["bg"],
        )
        top.pack(
            fill="x",
        )

        top.columnconfigure(
            0,
            weight=1,
            uniform="top",
        )
        top.columnconfigure(
            1,
            weight=1,
            uniform="top",
        )

        left = tk.Frame(
            top,
            bg=top["bg"],
        )
        left.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10),
        )

        right = tk.Frame(
            top,
            bg=top["bg"],
        )
        right.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(10, 0),
        )

        self._field_label(
            left,
            "PASSWORD PRESET",
        )

        self.preset_combo = ttk.Combobox(
            left,
            textvariable=self.preset_var,
            values=(
                list(PRESETS.keys())
                + [CUSTOM_PRESET_NAME]
            ),
            state="readonly",
            style="VF.TCombobox",
            font=("Segoe UI", 9),
        )
        self.preset_combo.pack(
            fill="x",
        )

        self.preset_combo.bind(
            "<<ComboboxSelected>>",
            self._on_preset_selected,
        )

        self._field_label(
            left,
            "PASSWORD LENGTH",
        )

        length_line = tk.Frame(
            left,
            bg=left["bg"],
        )
        length_line.pack(
            fill="x",
        )

        self.length_scale = ttk.Scale(
            length_line,
            from_=MIN_PASSWORD_LENGTH,
            to=MAX_PASSWORD_LENGTH,
            orient="horizontal",
            style="VF.Horizontal.TScale",
            command=self._on_length_changed,
        )
        self.length_scale.pack(
            side="left",
            fill="x",
            expand=True,
            pady=8,
        )

        self.length_value_label = tk.Label(
            length_line,
            text=str(
                self.length_var.get()
            ),
            bg=length_line["bg"],
            fg=self.palette.accent,
            font=("Consolas", 14, "bold"),
            width=4,
        )
        self.length_value_label.pack(
            side="right",
        )

        length_footer = tk.Frame(
            left,
            bg=left["bg"],
        )
        length_footer.pack(
            fill="x",
        )

        tk.Label(
            length_footer,
            text=f"Minimum {MIN_PASSWORD_LENGTH}",
            bg=length_footer["bg"],
            fg=self.palette.text_muted,
            font=("Segoe UI", 7),
        ).pack(
            side="left",
        )

        tk.Label(
            length_footer,
            text=f"Maximum {MAX_PASSWORD_LENGTH}",
            bg=length_footer["bg"],
            fg=self.palette.text_muted,
            font=("Segoe UI", 7),
        ).pack(
            side="right",
        )

        self.length_spin = tk.Spinbox(
            length_footer,
            from_=MIN_PASSWORD_LENGTH,
            to=MAX_PASSWORD_LENGTH,
            textvariable=self.length_var,
            width=6,
            justify="center",
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            bg=self.palette.card_bg_alt,
            fg=self.palette.text_primary,
            buttonbackground=self.palette.card_bg_alt,
            highlightthickness=1,
            highlightbackground=self.palette.border,
            highlightcolor=self.palette.accent,
        )
        self.length_spin.pack(
            side="right",
            padx=10,
        )

        self._field_label(
            right,
            "SECURITY OPTIONS",
        )

        ambiguous = self._checkbox_card(
            right,
            self.exclude_ambiguous_var,
            "Exclude ambiguous characters",
            "Avoid visually similar characters such as 0, O, 1 and l.",
        )
        ambiguous.pack(
            fill="x",
        )

        auto = tk.Frame(
            right,
            bg=self.palette.card_bg_alt,
            highlightthickness=1,
            highlightbackground=self.palette.border,
        )
        auto.pack(
            fill="x",
            pady=(8, 0),
        )

        auto_text = tk.Frame(
            auto,
            bg=auto["bg"],
        )
        auto_text.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10,
            pady=8,
        )

        tk.Label(
            auto_text,
            text="Clipboard auto-clear",
            bg=auto_text["bg"],
            fg=self.palette.text_primary,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
        )

        tk.Label(
            auto_text,
            text="0 disables automatic clearing",
            bg=auto_text["bg"],
            fg=self.palette.text_muted,
            font=("Segoe UI", 7),
        ).pack(
            anchor="w",
        )

        self.autoclear_spin = tk.Spinbox(
            auto,
            from_=0,
            to=300,
            increment=5,
            textvariable=self.autoclear_var,
            width=7,
            justify="center",
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            bg=self.palette.card_bg_alt,
            fg=self.palette.text_primary,
            buttonbackground=self.palette.card_bg_alt,
            highlightthickness=1,
            highlightbackground=self.palette.border,
            highlightcolor=self.palette.accent,
            command=self._on_autoclear_changed,
        )
        self.autoclear_spin.pack(
            side="right",
            padx=10,
        )

        self._field_label(
            body,
            "CHARACTER TYPES",
        )

        type_grid = tk.Frame(
            body,
            bg=body["bg"],
        )
        type_grid.pack(
            fill="x",
        )

        for column in range(4):
            type_grid.columnconfigure(
                column,
                weight=1,
                uniform="types",
            )

        options = [
            (
                self.use_upper_var,
                "A–Z · Uppercase",
                "Capital letters",
            ),
            (
                self.use_lower_var,
                "a–z · Lowercase",
                "Small letters",
            ),
            (
                self.use_digits_var,
                "0–9 · Numbers",
                "Numeric digits",
            ),
            (
                self.use_symbols_var,
                "!@#$ · Symbols",
                "Special characters",
            ),
        ]

        for index, (
            variable,
            title,
            description,
        ) in enumerate(options):

            card = self._checkbox_card(
                type_grid,
                variable,
                title,
                description,
            )

            card.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=3,
            )

        tk.Label(
            body,
            text=(
                "At least two character types "
                "must be selected."
            ),
            bg=body["bg"],
            fg=self.palette.text_muted,
            font=("Segoe UI", 7),
        ).pack(
            anchor="w",
            pady=(5, 0),
        )

    def _checkbox_card(
        self,
        parent: tk.Widget,
        variable: tk.BooleanVar,
        title: str,
        description: str,
    ) -> tk.Frame:

        p = self.palette

        card = tk.Frame(
            parent,
            bg=p.card_bg_alt,
            highlightthickness=1,
            highlightbackground=p.border,
        )

        text = tk.Frame(
            card,
            bg=p.card_bg_alt,
        )
        text.pack(
            side="left",
            fill="both",
            expand=True,
            padx=9,
            pady=7,
        )

        tk.Label(
            text,
            text=title,
            bg=p.card_bg_alt,
            fg=p.text_primary,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
        )

        tk.Label(
            text,
            text=description,
            bg=p.card_bg_alt,
            fg=p.text_muted,
            font=("Segoe UI", 7),
        ).pack(
            anchor="w",
        )

        checkbox = tk.Checkbutton(
            card,
            variable=variable,
            command=self._on_settings_changed,
            bg=p.card_bg_alt,
            activebackground=p.card_bg_alt,
            selectcolor=p.accent,
            fg=p.text_primary,
            bd=0,
            highlightthickness=0,
            relief="flat",
            cursor="hand2",
        )

        checkbox.pack(
            side="right",
            padx=10,
        )

        self._checkbox_cards.append(
            (card, checkbox)
        )

        return card

    # ================================================================
    # 02 GENERATED PASSWORD
    # ================================================================

    def _build_password_block(self) -> None:
        _block, body = self._make_block(
            "02",
            "Generated Password",
            "Generate, inspect, copy and manage your secure credential.",
        )

        state_row = tk.Frame(
            body,
            bg=body["bg"],
        )
        state_row.pack(
            fill="x",
        )

        self.password_state = tk.Label(
            state_row,
            text="READY",
            bg=state_row["bg"],
            fg=self.palette.success,
            font=("Segoe UI", 8, "bold"),
        )
        self.password_state.pack(
            side="right",
        )

        self.password_box = tk.Frame(
            body,
            bg=self.palette.card_bg_alt,
            highlightthickness=1,
            highlightbackground=self.palette.accent,
        )
        self.password_box.pack(
            fill="x",
            pady=(7, 7),
        )

        self.password_row = tk.Frame(
            self.password_box,
            bg=self.password_box["bg"],
        )
        self.password_row.pack(
            fill="x",
            padx=14,
            pady=14,
        )

        self.password_display = tk.Label(
            self.password_row,
            text="Click Generate Password",
            bg=self.password_row["bg"],
            fg=self.palette.text_muted,
            font=("Consolas", 18, "bold"),
            anchor="w",
        )
        self.password_display.pack(
            side="left",
            fill="x",
            expand=True,
        )

        self.eye_btn = self._button(
            self.password_row,
            "Hide",
            self.on_toggle_visibility,
        )
        self.eye_btn.pack(
            side="right",
        )

        self.status_label = tk.Label(
            body,
            text="No password generated yet.",
            bg=body["bg"],
            fg=self.palette.text_muted,
            font=("Segoe UI", 8),
        )
        self.status_label.pack(
            anchor="w",
            pady=(0, 7),
        )

        actions = tk.Frame(
            body,
            bg=body["bg"],
        )
        actions.pack(
            fill="x",
            pady=(0, 9),
        )

        self.generate_btn = self._button(
            actions,
            "Generate Password",
            self.on_generate,
            primary=True,
        )
        self.generate_btn.pack(
            side="left",
        )

        self.regenerate_btn = self._button(
            actions,
            "Regenerate",
            self.on_regenerate,
        )
        self.regenerate_btn.pack(
            side="left",
            padx=(7, 0),
        )

        self.copy_btn = self._button(
            actions,
            "Copy to Clipboard",
            self.on_copy,
        )
        self.copy_btn.pack(
            side="left",
            padx=(7, 0),
        )

        self.clear_clipboard_btn = self._button(
            actions,
            "Clear Clipboard",
            self.on_clear_clipboard,
        )
        self.clear_clipboard_btn.pack(
            side="left",
            padx=(7, 0),
        )

        self.reset_btn = self._button(
            actions,
            "Reset",
            self.on_reset,
        )
        self.reset_btn.pack(
            side="right",
        )

        self.clear_btn = self._button(
            actions,
            "Clear",
            self.on_clear,
        )
        self.clear_btn.pack(
            side="right",
            padx=(0, 7),
        )

        self.strength_box = tk.Frame(
            body,
            bg=self.palette.card_bg_alt,
            highlightthickness=1,
            highlightbackground=self.palette.border,
        )
        self.strength_box.pack(
            fill="x",
            pady=(0, 9),
        )

        self.strength_header = tk.Frame(
            self.strength_box,
            bg=self.strength_box["bg"],
        )
        self.strength_header.pack(
            fill="x",
            padx=12,
            pady=(9, 4),
        )

        tk.Label(
            self.strength_header,
            text="PASSWORD STRENGTH",
            bg=self.strength_header["bg"],
            fg=self.palette.text_secondary,
            font=("Segoe UI", 7, "bold"),
        ).pack(
            side="left",
        )

        self.strength_text_label = tk.Label(
            self.strength_header,
            text="—",
            bg=self.strength_header["bg"],
            fg=self.palette.text_secondary,
            font=("Segoe UI", 9, "bold"),
        )
        self.strength_text_label.pack(
            side="right",
        )

        self.strength_canvas = tk.Canvas(
            self.strength_box,
            height=18,
            bg=self.strength_box["bg"],
            bd=0,
            highlightthickness=0,
        )
        self.strength_canvas.pack(
            fill="x",
            padx=12,
            pady=(0, 9),
        )

        tk.Label(
            body,
            text="REQUIREMENT CHECKLIST",
            bg=body["bg"],
            fg=self.palette.text_secondary,
            font=("Segoe UI", 8, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 4),
        )

        checklist = tk.Frame(
            body,
            bg=body["bg"],
        )
        checklist.pack(
            fill="x",
        )

        self.req_dots: dict[str, tk.Label] = {}

        items = [
            ("length", "Minimum length satisfied"),
            ("upper", "Uppercase included"),
            ("lower", "Lowercase included"),
            ("digits", "Number included"),
            ("symbols", "Symbol included"),
            ("rules", "Selected character rules satisfied"),
        ]

        for key, text in items:

            row = tk.Frame(
                checklist,
                bg=checklist["bg"],
            )
            row.pack(
                fill="x",
                pady=2,
            )

            dot = tk.Label(
                row,
                text="○",
                width=2,
                bg=row["bg"],
                fg=self.palette.text_muted,
                font=("Segoe UI", 10, "bold"),
            )
            dot.pack(
                side="left"
            )

            tk.Label(
                row,
                text=text,
                bg=row["bg"],
                fg=self.palette.text_secondary,
                font=("Segoe UI", 8),
            ).pack(
                side="left"
            )

            self.req_dots[key] = dot

    # ================================================================
    # 03 SECURITY ANALYSIS
    # ================================================================

    def _build_security_block(self) -> None:
        _block, body = self._make_block(
            "03",
            "Security Analysis",
            "Live metrics and security guidance for the generated password.",
        )

        metrics_frame = tk.Frame(
            body,
            bg=body["bg"],
        )
        metrics_frame.pack(
            fill="x",
        )

        metrics_frame.columnconfigure(
            0,
            weight=1,
            uniform="metrics",
        )
        metrics_frame.columnconfigure(
            1,
            weight=1,
            uniform="metrics",
        )

        self.analysis_labels: dict[str, tk.Label] = {}

        metrics = [
            ("length", "Character Count"),
            ("categories", "Character Categories"),
            ("pool", "Character Pool Size"),
            ("entropy", "Estimated Entropy"),
            ("strength", "Overall Strength"),
        ]

        for index, (
            key,
            title,
        ) in enumerate(metrics):

            row = tk.Frame(
                metrics_frame,
                bg=self.palette.card_bg_alt,
                highlightthickness=1,
                highlightbackground=self.palette.border,
            )

            row.grid(
                row=index // 2,
                column=index % 2,
                sticky="ew",
                padx=3,
                pady=3,
            )

            tk.Label(
                row,
                text=title,
                bg=row["bg"],
                fg=self.palette.text_secondary,
                font=("Segoe UI", 8),
            ).pack(
                side="left",
                padx=11,
                pady=10,
            )

            value = tk.Label(
                row,
                text="—",
                bg=row["bg"],
                fg=self.palette.text_primary,
                font=("Segoe UI", 9, "bold"),
            )

            value.pack(
                side="right",
                padx=11,
            )

            self.analysis_labels[key] = value

        self.categories_box = self._info_box(
            body,
            "SELECTED CATEGORIES",
        )

        self.categories_label = tk.Label(
            self.categories_box,
            text="—",
            bg=self.categories_box["bg"],
            fg=self.palette.text_primary,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.categories_label.pack(
            fill="x",
            padx=11,
            pady=(0, 9),
        )

        self.tips_box = self._info_box(
            body,
            "SECURITY TIPS",
        )

        self.tips_label = tk.Label(
            self.tips_box,
            text=(
                "Generate a password to see "
                "personalized security tips."
            ),
            bg=self.tips_box["bg"],
            fg=self.palette.text_secondary,
            font=("Segoe UI", 8),
            justify="left",
            anchor="w",
        )
        self.tips_label.pack(
            fill="x",
            padx=11,
            pady=(0, 9),
        )

        self.policy_box = self._info_box(
            body,
            "SECURITY POLICY",
        )

        tk.Label(
            self.policy_box,
            text=(
                "Generation uses Python's secure secrets module. "
                "Session history is not persisted to disk."
            ),
            bg=self.policy_box["bg"],
            fg=self.palette.text_secondary,
            font=("Segoe UI", 8),
            justify="left",
            anchor="w",
        ).pack(
            fill="x",
            padx=11,
            pady=(0, 9),
        )

    def _info_box(
        self,
        parent: tk.Widget,
        title: str,
    ) -> tk.Frame:

        box = tk.Frame(
            parent,
            bg=self.palette.card_bg_alt,
            highlightthickness=1,
            highlightbackground=self.palette.border,
        )

        box.pack(
            fill="x",
            pady=3,
        )

        tk.Label(
            box,
            text=title,
            bg=box["bg"],
            fg=self.palette.accent,
            font=("Segoe UI", 7, "bold"),
        ).pack(
            anchor="w",
            padx=11,
            pady=(9, 3),
        )

        return box

    # ================================================================
    # 04 HISTORY
    # ================================================================

    def _build_history_block(self) -> None:
        _block, body = self._make_block(
            "04",
            "Recent Generation History",
            "The latest five generated passwords are kept for this session only.",
        )

        header = tk.Frame(
            body,
            bg=body["bg"],
        )

        header.pack(
            fill="x",
        )

        self.clear_history_btn = self._button(
            header,
            "Clear History",
            self.on_clear_history,
        )

        self.clear_history_btn.pack(
            side="right",
        )

        self.history_list_frame = tk.Frame(
            body,
            bg=body["bg"],
        )

        self.history_list_frame.pack(
            fill="x",
            pady=(8, 0),
        )

        self.history_empty_label = tk.Label(
            self.history_list_frame,
            text=(
                "No passwords generated yet this session."
            ),
            bg=self.history_list_frame["bg"],
            fg=self.palette.text_muted,
            font=("Segoe UI", 8),
        )

        self.history_empty_label.pack(
            anchor="w",
        )

    # ================================================================
    # FOOTER
    # ================================================================

    def _build_footer(self) -> None:
        self.footer = tk.Frame(
            self.root,
            bg=self.palette.app_bg,
        )

        self.footer.pack(
            fill="x",
            padx=20,
            pady=(0, 7),
        )

        self.footer_shortcuts = tk.Label(
            self.footer,
            text=(
                "Ctrl+Enter Generate  ·  "
                "Ctrl+R Regenerate  ·  "
                "Ctrl+L Focus Length  ·  "
                "Esc Clear Status"
            ),
            bg=self.footer["bg"],
            fg=self.palette.text_muted,
            font=("Consolas", 7),
        )

        self.footer_shortcuts.pack(
            side="left",
        )

        self.footer_brand = tk.Label(
            self.footer,
            text="VAULTFORGE · SECURE PASSWORD STUDIO",
            bg=self.footer["bg"],
            fg=self.palette.text_muted,
            font=("Segoe UI", 7, "bold"),
        )

        self.footer_brand.pack(
            side="right",
        )

    # ================================================================
    # SETTINGS
    # ================================================================

    def _current_settings(self) -> GeneratorSettings:
        return GeneratorSettings(
            length=int(
                self.length_var.get()
            ),
            use_upper=self.use_upper_var.get(),
            use_lower=self.use_lower_var.get(),
            use_digits=self.use_digits_var.get(),
            use_symbols=self.use_symbols_var.get(),
            exclude_ambiguous=self.exclude_ambiguous_var.get(),
        )

    def _on_preset_selected(
        self,
        _event=None,
    ) -> None:

        name = self.preset_var.get()

        if name != CUSTOM_PRESET_NAME:
            self._apply_preset(
                name
            )

    def _apply_preset(
        self,
        name: str,
    ) -> None:

        preset = PRESETS.get(
            name
        )

        if preset is None:
            return

        self._applying_preset = True

        try:
            self.length_var.set(
                preset.length
            )
            self.use_upper_var.set(
                preset.use_upper
            )
            self.use_lower_var.set(
                preset.use_lower
            )
            self.use_digits_var.set(
                preset.use_digits
            )
            self.use_symbols_var.set(
                preset.use_symbols
            )
            self.exclude_ambiguous_var.set(
                preset.exclude_ambiguous
            )
            self.preset_var.set(
                name
            )

        finally:
            self._applying_preset = False

        self._refresh_checklist_from_settings()

    def _on_settings_changed(
        self,
    ) -> None:

        if not self._applying_preset:
            self.preset_var.set(
                CUSTOM_PRESET_NAME
            )

        self._refresh_checklist_from_settings()

    def _on_length_changed(
        self,
        _value=None,
    ) -> None:

        if self._updating_length:
            return

        try:
            value = int(
                round(
                    float(
                        self.length_scale.get()
                    )
                )
            )
        except (
            tk.TclError,
            ValueError,
        ):
            return

        self._updating_length = True

        try:
            self.length_var.set(
                value
            )

        finally:
            self._updating_length = False

    def _on_length_var_changed(
        self,
    ) -> None:

        try:
            value = int(
                self.length_var.get()
            )
        except (
            tk.TclError,
            ValueError,
        ):
            return

        if hasattr(
            self,
            "length_value_label",
        ):
            self.length_value_label.configure(
                text=str(value)
            )

        if (
            hasattr(
                self,
                "length_scale",
            )
            and not self._updating_length
        ):
            self._updating_length = True

            try:
                self.length_scale.set(
                    value
                )

            finally:
                self._updating_length = False

        if not self._applying_preset:
            self.preset_var.set(
                CUSTOM_PRESET_NAME
            )

        if hasattr(
            self,
            "req_dots",
        ):
            self._refresh_checklist_from_settings()

    def _on_autoclear_changed(
        self,
    ) -> None:

        try:
            seconds = int(
                self.autoclear_var.get()
            )
        except (
            tk.TclError,
            ValueError,
        ):
            seconds = (
                DEFAULT_CLIPBOARD_AUTOCLEAR_SECONDS
            )

        self.clipboard.set_autoclear_seconds(
            seconds
        )

    # ================================================================
    # ACTIONS
    # ================================================================

    def on_generate(
        self,
    ) -> None:

        try:
            settings = self._current_settings()
            password = generate_password(
                settings
            )

        except ValidationError as exc:
            self._show_error(
                str(exc)
            )
            return

        except PasswordGenerationError as exc:
            self._show_error(
                str(exc)
            )
            return

        except Exception as exc:
            self._show_error(
                (
                    "Unexpected error while generating "
                    f"a password: {exc}"
                )
            )
            return

        self.current_password = password
        self.password_visible = True

        report = analyze_password(
            password
        )

        self._render_password()
        self._render_analysis(
            report
        )
        self._refresh_checklist_from_password(
            password,
            settings
        )

        self.history.add(
            password,
            report.strength,
        )

        self._render_history()

        copied = self.clipboard.copy(
            password,
            on_result=self._on_clipboard_result,
        )

        if copied:
            self._set_status(
                "Password generated and copied to clipboard.",
                self.palette.success,
            )
        else:
            self._set_status(
                "Password generated. Clipboard copy failed.",
                self.palette.warning,
            )

    def on_regenerate(
        self,
    ) -> None:

        self.on_generate()

    def on_toggle_visibility(
        self,
    ) -> None:

        self.password_visible = (
            not self.password_visible
        )

        self._render_password()

    def on_copy(
        self,
    ) -> None:

        if not self.current_password:
            self._show_error(
                "Generate a password before copying."
            )
            return

        self.clipboard.copy(
            self.current_password,
            on_result=self._on_clipboard_result,
        )

    def on_clear_clipboard(
        self,
    ) -> None:

        self.clipboard.clear(
            on_result=self._on_clipboard_result,
        )

    def on_reset(
        self,
    ) -> None:

        self._apply_preset(
            "Strong"
        )

        self.current_password = ""
        self.password_visible = True

        self._render_password()
        self._render_analysis(None)
        self._refresh_checklist_from_settings()

        self._set_status(
            "Settings reset to the Strong preset.",
            self.palette.info,
        )

    def on_clear(
        self,
    ) -> None:

        self.current_password = ""
        self.password_visible = True

        self._render_password()
        self._render_analysis(None)

        self._set_status(
            "Password cleared from view.",
            self.palette.text_muted,
        )

    def on_clear_history(
        self,
    ) -> None:

        self.history.clear()
        self._render_history()

        self._set_status(
            "Session history cleared.",
            self.palette.text_muted,
        )

    def _on_clipboard_result(
        self,
        success: bool,
        message: str,
    ) -> None:

        self._set_status(
            message,
            (
                self.palette.success
                if success
                else self.palette.danger
            ),
        )

    # ================================================================
    # RENDERING
    # ================================================================

    def _render_password(
        self,
    ) -> None:

        if not self.current_password:

            self.password_display.configure(
                text="Click Generate Password",
                fg=self.palette.text_muted,
            )

            self.eye_btn.configure(
                text="Hide"
            )

            self.password_state.configure(
                text="READY",
                fg=self.palette.success,
            )

            return

        if self.password_visible:

            self.password_display.configure(
                text=self.current_password,
                fg=self.palette.text_primary,
            )

            self.eye_btn.configure(
                text="Hide"
            )

        else:

            self.password_display.configure(
                text=(
                    "•"
                    * len(
                        self.current_password
                    )
                ),
                fg=self.palette.text_primary,
            )

            self.eye_btn.configure(
                text="Show"
            )

    def _render_analysis(
        self,
        report,
    ) -> None:

        if report is None:

            for label in self.analysis_labels.values():
                label.configure(
                    text="—"
                )

            self.strength_text_label.configure(
                text="—",
                fg=self.palette.text_secondary,
            )

            self.categories_label.configure(
                text="—"
            )

            self.tips_label.configure(
                text=(
                    "Generate a password to see "
                    "personalized security tips."
                )
            )

            self.password_state.configure(
                text="READY",
                fg=self.palette.success,
            )

            self._draw_strength_bar(
                0.0,
                self.palette.border,
            )

            return

        self.analysis_labels[
            "length"
        ].configure(
            text=str(
                report.length
            )
        )

        self.analysis_labels[
            "categories"
        ].configure(
            text=str(
                report.category_count
            )
        )

        self.analysis_labels[
            "pool"
        ].configure(
            text=(
                f"{report.pool_size} characters"
            )
        )

        self.analysis_labels[
            "entropy"
        ].configure(
            text=(
                f"~{report.entropy_bits:.1f} bits"
            )
        )

        self.analysis_labels[
            "strength"
        ].configure(
            text=report.strength
        )

        color_key = STRENGTH_COLOR_KEY.get(
            report.strength,
            "strength_weak",
        )

        color = getattr(
            self.palette,
            color_key,
        )

        self.strength_text_label.configure(
            text=report.strength,
            fg=color,
        )

        self._draw_strength_bar(
            strength_to_fraction(
                report.strength
            ),
            color,
        )

        self.password_state.configure(
            text="GENERATED",
            fg=color,
        )

        categories = []

        if self.use_upper_var.get():
            categories.append(
                "Uppercase"
            )

        if self.use_lower_var.get():
            categories.append(
                "Lowercase"
            )

        if self.use_digits_var.get():
            categories.append(
                "Numbers"
            )

        if self.use_symbols_var.get():
            categories.append(
                "Symbols"
            )

        self.categories_label.configure(
            text=(
                " · ".join(
                    categories
                )
                if categories
                else "None selected"
            )
        )

        tips = getattr(
            report,
            "tips",
            None,
        ) or []

        self.tips_label.configure(
            text=(
                "\n".join(
                    f"• {tip}"
                    for tip in tips
                )
                if tips
                else "No additional security tips."
            )
        )

    def _draw_strength_bar(
        self,
        fraction: float,
        color: str,
    ) -> None:

        canvas = self.strength_canvas

        canvas.delete(
            "all"
        )

        width = max(
            350,
            canvas.winfo_width()
        )

        height = 14

        canvas.create_rectangle(
            0,
            2,
            width,
            height + 2,
            fill=self.palette.border,
            outline="",
        )

        fraction = max(
            0.0,
            min(
                float(fraction),
                1.0,
            ),
        )

        fill_width = (
            width
            * fraction
        )

        if fill_width > 0:

            canvas.create_rectangle(
                0,
                2,
                fill_width,
                height + 2,
                fill=color,
                outline="",
            )

        for marker in (
            0.33,
            0.66,
        ):

            x = width * marker

            canvas.create_line(
                x,
                1,
                x,
                height + 3,
                fill=self.palette.app_bg,
                width=2,
            )

    # ================================================================
    # CHECKLIST
    # ================================================================

    def _refresh_checklist_from_settings(
        self,
    ) -> None:

        if not hasattr(
            self,
            "req_dots",
        ):
            return

        try:
            length_ok = (
                int(
                    self.length_var.get()
                )
                >= MIN_PASSWORD_LENGTH
            )
        except (
            tk.TclError,
            ValueError,
        ):
            length_ok = False

        selected_count = sum(
            [
                self.use_upper_var.get(),
                self.use_lower_var.get(),
                self.use_digits_var.get(),
                self.use_symbols_var.get(),
            ]
        )

        self._set_dot(
            "length",
            length_ok,
        )

        self._set_dot(
            "upper",
            self.use_upper_var.get(),
        )

        self._set_dot(
            "lower",
            self.use_lower_var.get(),
        )

        self._set_dot(
            "digits",
            self.use_digits_var.get(),
        )

        self._set_dot(
            "symbols",
            self.use_symbols_var.get(),
        )

        self._set_dot(
            "rules",
            selected_count >= 2,
        )

    def _refresh_checklist_from_password(
        self,
        password: str,
        settings: GeneratorSettings,
    ) -> None:

        from config import (
            DIGITS,
            LOWERCASE,
            SYMBOLS,
            UPPERCASE,
        )

        self._set_dot(
            "length",
            len(password) >= MIN_PASSWORD_LENGTH,
        )

        self._set_dot(
            "upper",
            settings.use_upper
            and any(
                c in UPPERCASE
                for c in password
            ),
        )

        self._set_dot(
            "lower",
            settings.use_lower
            and any(
                c in LOWERCASE
                for c in password
            ),
        )

        self._set_dot(
            "digits",
            settings.use_digits
            and any(
                c in DIGITS
                for c in password
            ),
        )

        self._set_dot(
            "symbols",
            settings.use_symbols
            and any(
                c in SYMBOLS
                for c in password
            ),
        )

        self._set_dot(
            "rules",
            sum(
                [
                    settings.use_upper,
                    settings.use_lower,
                    settings.use_digits,
                    settings.use_symbols,
                ]
            )
            >= 2,
        )

    def _set_dot(
        self,
        key: str,
        ok: bool,
    ) -> None:

        dot = self.req_dots[
            key
        ]

        dot.configure(
            text=(
                "●"
                if ok
                else "○"
            ),
            fg=(
                self.palette.success
                if ok
                else self.palette.text_muted
            ),
        )

    # ================================================================
    # HISTORY
    # ================================================================

    def _render_history(
        self,
    ) -> None:

        for row in self._history_rows:
            row.destroy()

        self._history_rows.clear()

        entries = self.history.entries

        if not entries:

            self.history_empty_label.pack(
                anchor="w"
            )

            return

        self.history_empty_label.pack_forget()

        for entry in entries:

            row = self._build_history_row(
                entry
            )

            row.pack(
                fill="x",
                pady=3,
            )

            self._history_rows.append(
                row
            )

    def _build_history_row(
        self,
        entry: HistoryEntry,
    ) -> tk.Frame:

        row = tk.Frame(
            self.history_list_frame,
            bg=self.palette.card_bg_alt,
            highlightthickness=1,
            highlightbackground=self.palette.border,
        )

        text_var = tk.StringVar(
            value=(
                entry.password
                if entry.revealed
                else entry.masked()
            )
        )

        text_label = tk.Label(
            row,
            textvariable=text_var,
            bg=row["bg"],
            fg=self.palette.text_primary,
            font=(
                "Consolas",
                9,
                "bold",
            ),
            anchor="w",
        )

        text_label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=11,
            pady=8,
        )

        tk.Label(
            row,
            text=(
                f"{entry.strength} · "
                f"{entry.timestamp_label()}"
            ),
            bg=row["bg"],
            fg=self.palette.text_muted,
            font=(
                "Segoe UI",
                7,
            ),
        ).pack(
            side="left",
            padx=7,
        )

        def toggle_reveal() -> None:
            entry.revealed = not entry.revealed

            text_var.set(
                entry.password
                if entry.revealed
                else entry.masked()
            )

            reveal_btn.configure(
                text=(
                    "Hide"
                    if entry.revealed
                    else "Show"
                )
            )

        reveal_btn = self._button(
            row,
            "Show",
            toggle_reveal,
        )

        reveal_btn.pack(
            side="right",
            padx=5,
            pady=5,
        )

        remove_btn = self._button(
            row,
            "Remove",
            lambda: self._remove_history_entry(
                entry
            ),
        )

        remove_btn.pack(
            side="right",
            padx=(5, 0),
            pady=5,
        )

        return row

    def _remove_history_entry(
        self,
        entry: HistoryEntry,
    ) -> None:

        self.history.remove(
            entry
        )

        self._render_history()

    # ================================================================
    # STATUS
    # ================================================================

    def _set_status(
        self,
        message: str,
        color: Optional[str] = None,
    ) -> None:

        self.status_label.configure(
            text=message,
            fg=(
                color
                or self.palette.text_muted
            ),
        )

    def _clear_transient_status(
        self,
    ) -> None:

        self.status_label.configure(
            text="",
            fg=self.palette.text_muted,
        )

    def _show_error(
        self,
        message: str,
    ) -> None:

        self._set_status(
            message,
            self.palette.danger,
        )

        try:
            messagebox.showerror(
                f"{APP_NAME} — Error",
                message,
            )
        except Exception:
            pass

    # ================================================================
    # THEME
    # ================================================================

    def _set_theme(self, name: str) -> None:
        """Switch between the complete Dark and Light palettes."""
        if name not in ("dark", "light"):
            return

        old_palette = self.palette

        if name == self.theme_name:
            self._refresh_theme_buttons()
            return

        self.theme_name = name
        self.palette = get_palette(name)

        self._apply_ttk_palette()

        self._repaint_theme(
            old_palette,
            self.palette,
        )

        self._refresh_theme_buttons()

        # Restore dynamic content after recoloring.
        self._render_password()

        if self.current_password:
            self._render_analysis(
                analyze_password(
                    self.current_password
                )
            )
        else:
            self._render_analysis(None)

        self._refresh_checklist_from_settings()
        self._render_history()

    def _repaint_theme(
        self,
        old,
        new,
    ) -> None:
        """Repaint every Tk widget by translating semantic colors."""

        self.root.configure(
            bg=new.app_bg
        )

        self._repaint_widget(
            self.root,
            old,
            new,
        )

        # Explicitly repaint important top-level widgets.
        self.header.configure(
            bg=new.card_bg,
            highlightbackground=new.border,
        )

        self.brand.configure(
            bg=new.card_bg
        )

        self.title_box.configure(
            bg=new.card_bg
        )

        self.header_right.configure(
            bg=new.card_bg
        )

        self.theme_area.configure(
            bg=new.card_bg
        )

        self.logo.configure(
            bg=new.accent,
            fg=new.text_on_accent,
        )

        self.title_label.configure(
            bg=new.card_bg,
            fg=new.text_primary,
        )

        self.subtitle_label.configure(
            bg=new.card_bg,
            fg=new.text_secondary,
        )

        self.security_label.configure(
            bg=new.card_bg,
            fg=new.success,
        )

        self.shell.configure(
            bg=new.app_bg
        )

        self.canvas.configure(
            bg=new.app_bg
        )

        self.content.configure(
            bg=new.app_bg
        )

        self.footer.configure(
            bg=new.app_bg
        )

        self.footer_shortcuts.configure(
            bg=new.app_bg,
            fg=new.text_muted,
        )

        self.footer_brand.configure(
            bg=new.app_bg,
            fg=new.text_muted,
        )

        # Password display.
        self.password_box.configure(
            bg=new.card_bg_alt,
            highlightbackground=new.accent,
        )

        self.password_row.configure(
            bg=new.card_bg_alt
        )

        self.password_display.configure(
            bg=new.card_bg_alt
        )

        # Strength section.
        self.strength_box.configure(
            bg=new.card_bg_alt,
            highlightbackground=new.border,
        )

        self.strength_header.configure(
            bg=new.card_bg_alt
        )

        self.strength_canvas.configure(
            bg=new.card_bg_alt
        )

        # Security information boxes.
        self.categories_box.configure(
            bg=new.card_bg_alt,
            highlightbackground=new.border,
        )

        self.tips_box.configure(
            bg=new.card_bg_alt,
            highlightbackground=new.border,
        )

        self.policy_box.configure(
            bg=new.card_bg_alt,
            highlightbackground=new.border,
        )

        # Character/security checkboxes.
        for card, checkbox in self._checkbox_cards:
            card.configure(
                bg=new.card_bg_alt,
                highlightbackground=new.border,
            )

            checkbox.configure(
                bg=new.card_bg_alt,
                activebackground=new.card_bg_alt,
                selectcolor=new.accent,
                fg=new.text_primary,
            )

        # Regular buttons.
        for button in (
            self.generate_btn,
            self.regenerate_btn,
            self.copy_btn,
            self.clear_clipboard_btn,
            self.clear_btn,
            self.reset_btn,
            self.eye_btn,
            self.clear_history_btn,
        ):
            self._refresh_button(
                button
            )

    def _repaint_widget(
        self,
        widget: tk.Widget,
        old,
        new,
    ) -> None:
        """Translate old semantic palette colors into the new palette."""

        try:
            options = widget.keys()

            if "bg" in options:
                current_bg = widget.cget("bg")

                if current_bg == old.app_bg:
                    widget.configure(
                        bg=new.app_bg
                    )

                elif current_bg == old.card_bg:
                    widget.configure(
                        bg=new.card_bg
                    )

                elif current_bg == old.card_bg_alt:
                    widget.configure(
                        bg=new.card_bg_alt
                    )

                elif current_bg == old.border:
                    widget.configure(
                        bg=new.border
                    )

            if "highlightbackground" in options:
                current_highlight = widget.cget(
                    "highlightbackground"
                )

                if current_highlight == old.border:
                    widget.configure(
                        highlightbackground=new.border
                    )

                elif current_highlight == old.accent:
                    widget.configure(
                        highlightbackground=new.accent
                    )

            if "fg" in options:
                current_fg = widget.cget("fg")

                if current_fg == old.text_primary:
                    widget.configure(
                        fg=new.text_primary
                    )

                elif current_fg == old.text_secondary:
                    widget.configure(
                        fg=new.text_secondary
                    )

                elif current_fg == old.text_muted:
                    widget.configure(
                        fg=new.text_muted
                    )

                elif current_fg == old.text_on_accent:
                    widget.configure(
                        fg=new.text_on_accent
                    )

                elif current_fg == old.accent:
                    widget.configure(
                        fg=new.accent
                    )

                elif current_fg == old.success:
                    widget.configure(
                        fg=new.success
                    )

                elif current_fg == old.warning:
                    widget.configure(
                        fg=new.warning
                    )

                elif current_fg == old.danger:
                    widget.configure(
                        fg=new.danger
                    )

        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self._repaint_widget(
                child,
                old,
                new,
            )

    def _refresh_button(
        self,
        button: tk.Button,
    ) -> None:
        """Apply current palette to a standard VaultForge button."""

        p = self.palette

        primary = getattr(
            button,
            "_vf_primary",
            False,
        )

        normal_bg = (
            p.accent
            if primary
            else p.card_bg_alt
        )

        normal_fg = (
            p.text_on_accent
            if primary
            else p.text_primary
        )

        hover_bg = (
            p.accent
            if primary
            else p.border
        )

        button.configure(
            bg=normal_bg,
            fg=normal_fg,
            activebackground=hover_bg,
            activeforeground=(
                p.text_on_accent
                if primary
                else p.text_primary
            ),
            highlightbackground=(
                p.accent
                if primary
                else p.border
            ),
            highlightcolor=p.accent,
        )

        button._vf_normal_bg = normal_bg
        button._vf_hover_bg = hover_bg

    def _refresh_theme_buttons(self) -> None:
        """Update Dark/Light buttons so the selected mode is obvious."""

        p = self.palette

        self.dark_btn.configure(
            bg=(
                p.accent
                if self.theme_name == "dark"
                else p.card_bg_alt
            ),
            fg=(
                p.text_on_accent
                if self.theme_name == "dark"
                else p.text_secondary
            ),
            activebackground=p.accent,
            activeforeground=p.text_on_accent,
        )

        self.light_btn.configure(
            bg=(
                p.accent
                if self.theme_name == "light"
                else p.card_bg_alt
            ),
            fg=(
                p.text_on_accent
                if self.theme_name == "light"
                else p.text_secondary
            ),
            activebackground=p.accent,
            activeforeground=p.text_on_accent,
        )

    # ================================================================
    # INIT REFRESH
    # ================================================================

    def _refresh_all(
        self,
    ) -> None:

        self._render_password()
        self._render_analysis(None)
        self._refresh_checklist_from_settings()
        self._render_history()

        self.length_scale.set(
            self.length_var.get()
        )

        self.length_value_label.configure(
            text=str(
                self.length_var.get()
            )
        )

    # ================================================================
    # CLOSE
    # ================================================================

    def _on_close(
        self,
    ) -> None:

        try:
            self.clipboard.shutdown()
        finally:
            self.root.destroy()
