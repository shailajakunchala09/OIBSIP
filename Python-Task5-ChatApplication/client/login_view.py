"""Login / registration screen."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from common.validation import validate_password, validate_username

from .components import Field, LogoMark, RoundedButton
from .theme import font, theme

COPY = {
    "login": {"title": "Welcome back", "subtitle": "Sign in to continue to your rooms.",
              "button": "Sign in", "switch_prompt": "New here?", "switch_action": "Create an account"},
    "register": {"title": "Create your account", "subtitle": "Pick a username and a password to get started.",
                 "button": "Create account", "switch_prompt": "Already registered?", "switch_action": "Sign in"},
}


class LoginView(tk.Frame):
    def __init__(self, parent: tk.Misc, on_submit: Callable[[str, str, str], None],
                 server_label: str, last_username: str = "") -> None:
        c = theme.c
        super().__init__(parent, bg=c["bg"])
        self._on_submit = on_submit
        self.mode = "login"
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_brand_panel()
        self._build_form(server_label)
        self.username.set(last_username)
        self._apply_mode()
        self.after(120, self.password.focus if last_username else self.username.focus)

    # -- layout ----------------------------------------------------------
    def _build_brand_panel(self) -> None:
        c = theme.c
        panel = tk.Frame(self, bg=c["sidebar"], width=430)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.pack_propagate(False)
        center = tk.Frame(panel, bg=c["sidebar"])
        center.place(relx=0.5, rely=0.46, anchor="center")
        LogoMark(center, 56, bg=c["sidebar"]).pack(anchor="w")
        tk.Label(center, text="VANTA CHAT", bg=c["sidebar"], fg=c["text"], font=font(26, "bold")).pack(anchor="w", pady=(18, 0))
        tk.Label(center, text="Private conversations. Simple connection.", bg=c["sidebar"],
                 fg=c["text_dim"], font=font(11)).pack(anchor="w", pady=(4, 28))
        for line in ("Rooms for every topic", "History that is still there tomorrow",
                     "Alerts when the window is in the background"):
            row = tk.Frame(center, bg=c["sidebar"])
            row.pack(anchor="w", pady=4)
            tk.Label(row, text="●", bg=c["sidebar"], fg=c["accent"], font=font(7)).pack(side="left")
            tk.Label(row, text=line, bg=c["sidebar"], fg=c["text_dim"], font=font(10)).pack(side="left", padx=(10, 0))
        tk.Label(panel, text="A local learning project. Messages are not end-to-end encrypted.",
                 bg=c["sidebar"], fg=c["text_faint"], font=font(8)).place(relx=0.5, rely=1.0, y=-22, anchor="s")

    def _build_form(self, server_label: str) -> None:
        c = theme.c
        side = tk.Frame(self, bg=c["bg"])
        side.grid(row=0, column=1, sticky="nsew")
        card = tk.Frame(side, bg=c["surface"], padx=36, pady=32, highlightthickness=1,
                        highlightbackground=c["border"], highlightcolor=c["border"])
        card.place(relx=0.5, rely=0.5, anchor="center", width=420)
        self._title = tk.Label(card, bg=c["surface"], fg=c["text"], font=font(18, "bold"), anchor="w")
        self._title.pack(fill="x")
        self._subtitle = tk.Label(card, bg=c["surface"], fg=c["text_dim"], font=font(10), anchor="w")
        self._subtitle.pack(fill="x", pady=(4, 22))
        self.username = Field(card, "Username")
        self.username.pack(fill="x")
        self.password = Field(card, "Password", secret=True)
        self.password.pack(fill="x", pady=(14, 0))
        self.confirm = Field(card, "Confirm password", secret=True)
        self.status = tk.Label(card, text="", bg=c["surface"], fg=c["danger"], font=font(9), anchor="w",
                               justify="left", wraplength=340)
        self.status.pack(fill="x", pady=(12, 0))
        self.submit_button = RoundedButton(card, "Sign in", self._submit, width=348, height=42, bg=c["surface"], size=11)
        self.submit_button.pack(fill="x", pady=(14, 0))
        switch = tk.Frame(card, bg=c["surface"])
        switch.pack(pady=(18, 0))
        self._switch_prompt = tk.Label(switch, bg=c["surface"], fg=c["text_dim"], font=font(10))
        self._switch_prompt.pack(side="left")
        self._switch_action = tk.Label(switch, bg=c["surface"], fg=c["accent"], font=font(10, "bold"), cursor="hand2")
        self._switch_action.pack(side="left", padx=(6, 0))
        self._switch_action.bind("<Button-1>", lambda e: self._toggle_mode())
        tk.Label(side, text=f"Server  {server_label}", bg=c["bg"], fg=c["text_faint"], font=font(9)).place(
            relx=0.5, rely=1.0, y=-22, anchor="s")
        for field in (self.username, self.password, self.confirm):
            field.entry.bind("<Return>", lambda e: self._submit())

    # -- behaviour -------------------------------------------------------
    def _toggle_mode(self) -> None:
        self.mode = "register" if self.mode == "login" else "login"
        self._apply_mode()
        self.username.focus()

    def _apply_mode(self) -> None:
        copy = COPY[self.mode]
        self._title.configure(text=copy["title"])
        self._subtitle.configure(text=copy["subtitle"])
        self.submit_button.set_text(copy["button"])
        self._switch_prompt.configure(text=copy["switch_prompt"])
        self._switch_action.configure(text=copy["switch_action"])
        if self.mode == "register":
            self.confirm.pack(fill="x", pady=(14, 0), before=self.status)
        else:
            self.confirm.pack_forget()
        self.show_error("")

    def _submit(self) -> None:
        if not self.submit_button.enabled:
            return
        username, password = self.username.get().strip(), self.password.get()
        if self.mode == "login":
            if not username:
                return self.show_error("Please enter your username.", self.username)
            if not password:
                return self.show_error("Please enter your password.", self.password)
        else:
            if (problem := validate_username(username)):
                return self.show_error(problem, self.username)
            if (problem := validate_password(password)):
                return self.show_error(problem, self.password)
            if password != self.confirm.get():
                return self.show_error("The two passwords do not match.", self.confirm)
        self.show_error("")
        self._on_submit(self.mode, username, password)

    def show_error(self, message: str, field: Field | None = None) -> None:
        for each in (self.username, self.password, self.confirm):
            each.set_error(False)
        self.status.configure(text=message, fg=theme.c["danger"])
        if message and field:
            field.set_error(True)
            field.focus()

    def set_loading(self, loading: bool) -> None:
        busy_text = "Signing in…" if self.mode == "login" else "Creating account…"
        self.submit_button.set_text(busy_text if loading else COPY[self.mode]["button"])
        self.submit_button.set_enabled(not loading)
        for field in (self.username, self.password, self.confirm):
            field.set_enabled(not loading)
        if loading:
            self.status.configure(text="Connecting to the server…", fg=theme.c["text_dim"])

    def clear_password(self) -> None:
        self.password.set("")
        self.confirm.set("")
