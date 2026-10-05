"""VANTA CHAT desktop client: application controller.

Run with:  python -m client.gui [--host 127.0.0.1] [--port 5050]

The controller owns the Tk root, the network client and the chat state. It turns
frames from the server into view updates, and view actions into frames.
"""
from __future__ import annotations

import argparse
import sys
import tkinter as tk
import traceback

from common.protocol import DEFAULT_HOST, DEFAULT_PORT

from .chat_view import ChatView
from .client import ChatClient
from .components import (LogoMark, RoundedButton, ToastManager, Toggle, ModalDialog,
                         ask_new_room, confirm, notify)
from .login_view import LoginView
from .settings import Settings
from .state import ChatState, Change
from .theme import font, theme

APP_NAME = "VANTA CHAT"
VERSION = "1.0.0"
POLL_MS = 40
MAX_RECONNECT_ATTEMPTS = 8
TOAST_PREVIEW = 90

SHORTCUTS = [
    ("Ctrl+K", "Find a room"),
    ("Ctrl+F", "Search messages in this room"),
    ("Ctrl+N", "Create a room"),
    ("Ctrl+E", "Emoji picker"),
    ("Ctrl+B", "Show or hide members"),
    ("Ctrl+,", "Settings"),
    ("Enter / Shift+Enter", "Send / new line"),
    ("Esc", "Clear the message box, or close search"),
]


class App:
    def __init__(self, host: str, port: int, splash_seconds: float = 2.2) -> None:
        self.host, self.port = host, port
        self.settings = Settings.load()
        theme.set_mode(self.settings.theme)

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.configure(bg=theme.c["bg"])
        self.root.minsize(980, 640)
        self._center(self.root, 1180, 760)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.report_callback_exception = self._on_callback_error

        self.client = ChatClient()
        self.state = ChatState()
        self.toasts = ToastManager(self.root)
        self.view: tk.Frame | None = None
        self.phase = "login"                 # login | chat | reconnecting | offline
        self._pending: tuple[str, str, str] | None = None   # mode, username, password (login only)
        self._attempts = 0
        self._retry_job: str | None = None
        self._resume_after: int | None = None
        self._closing = False

        self._bind_shortcuts()
        self.root.after(POLL_MS, self._poll)
        if splash_seconds > 0:
            self.root.withdraw()
            self._show_splash(splash_seconds)
        else:
            self._show_login()

    # ====================================================================
    # Startup
    # ====================================================================
    @staticmethod
    def _center(window: tk.Misc, width: int, height: int) -> None:
        x = max(0, (window.winfo_screenwidth() - width) // 2)
        y = max(0, (window.winfo_screenheight() - height) // 3)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def _show_splash(self, seconds: float) -> None:
        c = theme.c
        splash = tk.Toplevel(self.root, bg=c["sidebar"])
        splash.overrideredirect(True)
        self._center(splash, 460, 290)
        body = tk.Frame(splash, bg=c["sidebar"], highlightthickness=1, highlightbackground=c["border"])
        body.pack(fill="both", expand=True)
        LogoMark(body, 64, bg=c["sidebar"]).pack(pady=(48, 0))
        tk.Label(body, text=APP_NAME, bg=c["sidebar"], fg=c["text"], font=font(24, "bold")).pack(pady=(16, 0))
        tk.Label(body, text="Private conversations. Simple connection.", bg=c["sidebar"],
                 fg=c["text_dim"], font=font(10)).pack(pady=(4, 0))
        bar = tk.Canvas(body, width=260, height=4, bg=c["border"], highlightthickness=0, bd=0)
        bar.pack(pady=(34, 0))
        fill = bar.create_rectangle(0, 0, 0, 4, fill=c["accent"], width=0)
        tk.Label(body, text="Starting…", bg=c["sidebar"], fg=c["text_faint"], font=font(9)).pack(pady=(10, 0))
        splash.update()

        steps = max(1, int(seconds * 1000 / 30))

        def tick(step: int = 0) -> None:
            if step >= steps:
                splash.destroy()
                self.root.deiconify()
                self._show_login()
                return
            bar.coords(fill, 0, 0, 260 * step / steps, 4)
            splash.after(30, tick, step + 1)

        splash.after(30, tick)

    # ====================================================================
    # Screens
    # ====================================================================
    def _swap_view(self, view: tk.Frame) -> None:
        old, self.view = self.view, view
        view.pack(fill="both", expand=True)
        if old is not None:
            old.destroy()

    def _show_login(self, message: str = "") -> None:
        self.phase = "login"
        self.root.configure(bg=theme.c["bg"])
        view = LoginView(self.root, self._submit_login, f"{self.host}:{self.port}", self.settings.last_username)
        self._swap_view(view)
        if message:
            view.show_error(message)

    def _show_chat(self) -> None:
        self.phase = "chat"
        self.root.configure(bg=theme.c["bg"])
        self._swap_view(ChatView(self.root, self, self.state))

    @property
    def _chat(self) -> ChatView | None:
        return self.view if isinstance(self.view, ChatView) else None

    @property
    def _login(self) -> LoginView | None:
        return self.view if isinstance(self.view, LoginView) else None

    # ====================================================================
    # Login / logout
    # ====================================================================
    def _submit_login(self, mode: str, username: str, password: str) -> None:
        self._pending = (mode, username, password)
        if self._login:
            self._login.set_loading(True)
        self.client.connect_async(self.host, self.port)

    def _login_failed(self, message: str, field_name: str | None = None) -> None:
        self._pending = None
        self.client.close()
        login = self._login
        if not login:
            return
        login.set_loading(False)
        field = {"username": login.username, "password": login.password}.get(field_name or "")
        login.show_error(message, field)
        if field_name == "password":
            login.clear_password()

    def request_logout(self) -> None:
        if not confirm(self.root, "Log out?", "You will leave this session and return to the sign-in screen. "
                       "Your rooms and messages stay saved on the server.", "Log out"):
            return
        self._end_session()
        self._show_login()

    def _end_session(self) -> None:
        if self._retry_job:
            self.root.after_cancel(self._retry_job)
            self._retry_job = None
        self.client.send("logout")
        self.client.close()
        self.state.reset()
        self._pending = None
        self._attempts = 0

    def quit(self) -> None:
        if self._closing:
            return
        self._closing = True
        if self.state.username:
            self.client.send("logout")
        self.client.close()
        self.root.destroy()

    # ====================================================================
    # Event pump
    # ====================================================================
    def _poll(self) -> None:
        try:
            for _ in range(200):
                try:
                    frame = self.client.events.get_nowait()
                except Exception:       # queue.Empty
                    break
                try:
                    self._handle(frame)
                except Exception:
                    self._on_callback_error(*sys.exc_info())
        finally:
            if not self._closing:
                self.root.after(POLL_MS, self._poll)

    def _handle(self, frame: dict) -> None:
        kind = frame["type"]
        if kind == "_connected":
            return self._on_connected()
        if kind == "_connect_failed":
            return self._on_connect_failed(frame["message"])
        if kind == "_disconnected":
            return self._on_disconnected(frame["reason"])
        if self.phase == "login" and kind not in ("auth_ok", "error"):
            return                        # stray frame from a connection we no longer care about
        change = self.state.apply(frame)
        getattr(self, f"_when_{change.kind}", lambda c: None)(change)

    # -- connection events -------------------------------------------------
    def _on_connected(self) -> None:
        if self.phase == "reconnecting" and self.state.token:
            self.client.send("resume", token=self.state.token)
        elif self._pending:
            mode, username, password = self._pending
            self.client.send(mode, username=username, password=password)

    def _on_connect_failed(self, message: str) -> None:
        if self.phase == "reconnecting":
            return self._schedule_retry()
        self._login_failed(message)

    def _on_disconnected(self, reason: str) -> None:
        if self.phase == "login":
            return self._login_failed(reason)
        if self.phase == "chat":
            self._resume_after = self.state.active_room_id
            self._start_reconnect()

    # -- reconnect ---------------------------------------------------------
    def _start_reconnect(self) -> None:
        self.phase = "reconnecting"
        self._attempts = 0
        if self._chat:
            self._chat.set_connection("reconnecting")
        self._schedule_retry(first=True)

    def _schedule_retry(self, first: bool = False) -> None:
        if self._retry_job:
            return
        if self._attempts >= MAX_RECONNECT_ATTEMPTS:
            self.phase = "offline"
            if self._chat:
                self._chat.set_connection("offline")
                self._chat.flash("Could not reach the server. Click the status badge to try again.")
            return
        self._attempts += 1
        delay = 500 if first else min(1000 * self._attempts, 8000)
        self._retry_job = self.root.after(delay, self._retry)

    def _retry(self) -> None:
        self._retry_job = None
        if self.phase == "reconnecting":
            self.client.connect_async(self.host, self.port)

    def reconnect_now(self) -> None:
        if self.phase == "offline":
            self.phase = "reconnecting"
            self._attempts = 0
            if self._chat:
                self._chat.set_connection("reconnecting")
            self._schedule_retry(first=True)

    # ====================================================================
    # Frames -> views
    # ====================================================================
    def _when_auth(self, change: Change) -> None:
        if change.request == "resume":
            self.phase = "chat"
            self._attempts = 0
            if self._chat:
                self._chat.set_connection("connected")
                self._chat.refresh_rooms()
                self._chat.flash("Reconnected.")
            if self._resume_after is not None:      # reload history that may have arrived while offline
                self.client.send("join_room", room_id=self._resume_after)
                self._resume_after = None
            return
        self.settings.last_username = self.state.username
        self.settings.save()
        self._pending = None                        # the password is not kept past this point
        self._show_chat()
        first = next((r for r in self.state.rooms.values() if r["joined"]), None)
        if first:
            self.client.send("join_room", room_id=first["id"])

    def _when_rooms(self, change: Change) -> None:
        if self._chat:
            self._chat.refresh_rooms()

    def _when_room_opened(self, change: Change) -> None:
        if self._chat:
            self._chat.show_room()

    def _when_left(self, change: Change) -> None:
        if not self._chat:
            return
        if self.state.active_room:
            self._chat.refresh_rooms()
        else:
            self._chat.show_welcome()

    def _when_presence(self, change: Change) -> None:
        if self._chat and change.room_id == self.state.active_room_id:
            self._chat.render_members()
            self._chat.refresh_rooms()

    def _when_typing(self, change: Change) -> None:
        if self._chat and change.username and change.username.lower() != self.state.username.lower():
            self._chat.show_typing(change.room_id, change.username)

    def _when_message(self, change: Change) -> None:
        if self._chat:
            self._chat.on_message(change)
        message = change.message
        if message and message["kind"] == "user" and not change.is_own:
            self._maybe_notify(change.room_id, message)

    def _when_shutdown(self, change: Change) -> None:
        if self._chat:
            self._chat.flash("The server is shutting down. Trying to reconnect…")

    def _when_error(self, change: Change) -> None:
        text, request, code = change.text or "Something went wrong.", change.request, change.username
        if request in ("login", "register") and self.phase == "login":
            field = {"exists": "username", "auth": "password"}.get(code or "")
            if request == "register" and code == "validation":
                field = "username"
            return self._login_failed(text, field)
        if request == "resume":
            self._end_session()
            return self._show_login("Your session expired. Please sign in again.")
        if request == "create_room":
            return notify(self.root, "Could not create room", text, "error")
        if self._chat:
            self._chat.flash(text)

    # ====================================================================
    # Notifications
    # ====================================================================
    def _window_unfocused(self) -> bool:
        try:
            return self.root.focus_displayof() is None or self.root.state() == "iconic"
        except tk.TclError:
            return False

    def _maybe_notify(self, room_id: int, message: dict) -> None:
        if not self.settings.notifications or not self._window_unfocused():
            return
        preview = " ".join(message["text"].split())
        if len(preview) > TOAST_PREVIEW:
            preview = preview[:TOAST_PREVIEW - 1] + "…"
        self.toasts.show(f"New message in #{self.state.room_name(room_id)}", f"{message['username']}: {preview}",
                         on_click=lambda: self._bring_to_front(room_id))
        if self.settings.sound:
            self.root.bell()

    def _bring_to_front(self, room_id: int) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.open_room(room_id)

    # ====================================================================
    # Actions called by the views
    # ====================================================================
    def open_room(self, room_id: int) -> None:
        if room_id == self.state.active_room_id and self._chat:
            return self._chat.focus_composer()
        if not self.client.send("join_room", room_id=room_id) and self._chat:
            self._chat.flash("You are offline. Reconnecting…")

    def request_new_room(self) -> None:
        result = ask_new_room(self.root)
        if result and not self.client.send("create_room", name=result[0], description=result[1]) and self._chat:
            self._chat.flash("You are offline. Reconnecting…")

    def request_leave_room(self, room_id: int) -> None:
        name = self.state.room_name(room_id)
        if confirm(self.root, f"Leave #{name}?", "You can join again later from the room list. "
                   "Others will see that you left.", "Leave room", danger=True):
            self.client.send("leave_room", room_id=room_id)

    def send_message(self, room_id: int, text: str) -> bool:
        if self.client.send("send_message", room_id=room_id, text=text):
            return True
        if self._chat:
            self._chat.flash("Message not sent: you are offline.")
        return False

    def notify_typing(self, room_id: int | None) -> None:
        if room_id is not None:
            self.client.send("typing", room_id=room_id)

    # ====================================================================
    # Settings and About
    # ====================================================================
    def open_settings(self) -> None:
        dialog = ModalDialog(self.root, "Settings", width=440)
        c = theme.c
        draft = {"theme": self.settings.theme, "notifications": self.settings.notifications,
                 "sound": self.settings.sound}
        tk.Label(dialog.body, text="Settings", bg=c["surface"], fg=c["text"], font=font(14, "bold"),
                 anchor="w").pack(fill="x")

        tk.Label(dialog.body, text="Theme", bg=c["surface"], fg=c["text_dim"], font=font(9),
                 anchor="w").pack(fill="x", pady=(16, 6))
        theme_row = tk.Frame(dialog.body, bg=c["surface"])
        theme_row.pack(fill="x")
        buttons: dict[str, RoundedButton] = {}

        def pick(mode: str) -> None:
            draft["theme"] = mode
            for key, button in buttons.items():
                button.set_style("primary" if key == mode else "secondary")

        for mode, label in (("dark", "Dark"), ("light", "Light")):
            buttons[mode] = RoundedButton(theme_row, label, lambda m=mode: pick(m), width=100, height=34,
                                          style="primary" if draft["theme"] == mode else "secondary",
                                          bg=c["surface"])
            buttons[mode].pack(side="left", padx=(0, 8))

        def toggle_row(title: str, hint: str, key: str) -> None:
            row = tk.Frame(dialog.body, bg=c["surface"])
            row.pack(fill="x", pady=(16, 0))
            text = tk.Frame(row, bg=c["surface"])
            text.pack(side="left", fill="x", expand=True)
            tk.Label(text, text=title, bg=c["surface"], fg=c["text"], font=font(10, "bold"), anchor="w").pack(fill="x")
            tk.Label(text, text=hint, bg=c["surface"], fg=c["text_dim"], font=font(9), anchor="w").pack(fill="x")
            Toggle(row, draft[key], lambda value, k=key: draft.__setitem__(k, value), bg=c["surface"]).pack(side="right")

        toggle_row("Desktop notifications", "Show a pop-up for new messages while this window is in the background.",
                   "notifications")
        toggle_row("Notification sound", "Play a short beep with each pop-up.", "sound")

        def done() -> None:
            changed_theme = draft["theme"] != self.settings.theme
            self.settings.theme = draft["theme"]
            self.settings.notifications = draft["notifications"]
            self.settings.sound = draft["sound"]
            self.settings.save()
            dialog.close(True)
            if changed_theme:
                theme.set_mode(self.settings.theme)
                self._rebuild_view()

        dialog.add_buttons(("Cancel", "secondary", lambda: dialog.close(None)), ("Done", "primary", done))
        dialog.show()

    def _rebuild_view(self) -> None:
        self.root.configure(bg=theme.c["bg"])
        if self._chat:
            self._swap_view(ChatView(self.root, self, self.state))
        elif self._login:
            self._show_login()

    def open_about(self) -> None:
        dialog = ModalDialog(self.root, f"About {APP_NAME}", width=480)
        c = theme.c
        header = tk.Frame(dialog.body, bg=c["surface"])
        header.pack(fill="x")
        LogoMark(header, 44, bg=c["surface"]).pack(side="left")
        titles = tk.Frame(header, bg=c["surface"])
        titles.pack(side="left", padx=(14, 0))
        tk.Label(titles, text=APP_NAME, bg=c["surface"], fg=c["text"], font=font(15, "bold"), anchor="w").pack(fill="x")
        tk.Label(titles, text=f"Version {VERSION}", bg=c["surface"], fg=c["text_dim"], font=font(9),
                 anchor="w").pack(fill="x")
        about = (
            "Built by Kunchala Shailaja for the OASIS INFOBYTE Python Programming internship (Task 5: "
            "Chat Application). Python, Tkinter, socket, threading and SQLite, standard library only.\n\n"
            "This is a learning project for a trusted network. Passwords are stored as salted hashes, but "
            "messages are saved as plain text on the server and travel over unencrypted TCP."
        )
        tk.Label(dialog.body, text=about, bg=c["surface"], fg=c["text_dim"], font=font(10), anchor="w",
                 justify="left", wraplength=428).pack(fill="x", pady=(16, 0))
        tk.Label(dialog.body, text="Keyboard shortcuts", bg=c["surface"], fg=c["text"], font=font(10, "bold"),
                 anchor="w").pack(fill="x", pady=(18, 6))
        grid = tk.Frame(dialog.body, bg=c["surface"])
        grid.pack(fill="x")
        for row, (keys, action) in enumerate(SHORTCUTS):
            tk.Label(grid, text=keys, bg=c["surface"], fg=c["accent"], font=font(9, "bold"), anchor="w",
                     width=18).grid(row=row, column=0, sticky="w", pady=1)
            tk.Label(grid, text=action, bg=c["surface"], fg=c["text_dim"], font=font(9),
                     anchor="w").grid(row=row, column=1, sticky="w", pady=1)
        dialog.add_buttons(("Close", "primary", lambda: dialog.close(True)))
        dialog.show()

    # ====================================================================
    # Shortcuts and error handling
    # ====================================================================
    def _bind_shortcuts(self) -> None:
        actions = {
            "<Control-k>": lambda: self._chat and self._chat.focus_room_search(),
            "<Control-f>": lambda: self._chat and self._chat.toggle_search(),
            "<Control-n>": lambda: self._chat and self.request_new_room(),
            "<Control-e>": lambda: self._chat and self._chat.toggle_emoji_picker(),
            "<Control-b>": lambda: self._chat and self._chat.toggle_members(),
            "<Control-comma>": lambda: self.open_settings(),
        }
        for sequence, action in actions.items():
            def handler(event: tk.Event, action=action) -> str:
                if self.root.grab_current() is None:    # ignore while a dialog is open
                    self.root.after_idle(action)
                return "break"
            # Text and Entry have emacs-style defaults for these keys; override them explicitly.
            for tag in ("Text", "Entry", "all"):
                self.root.bind_class(tag, sequence, handler)
                self.root.bind_class(tag, sequence.replace("-k>", "-K>").replace("-f>", "-F>")
                                     .replace("-n>", "-N>").replace("-e>", "-E>").replace("-b>", "-B>"), handler)

    def _on_callback_error(self, exc_type, exc, tb) -> None:
        traceback.print_exception(exc_type, exc, tb)
        if self._chat:
            try:
                self._chat.flash("Something unexpected went wrong. Details are in the console.")
            except tk.TclError:
                pass

    def run(self) -> None:
        self.root.mainloop()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="VANTA CHAT desktop client")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"server address (default {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"server port (default {DEFAULT_PORT})")
    parser.add_argument("--splash-seconds", type=float, default=2.2,
                        help="how long to show the splash screen; 0 skips it")
    args = parser.parse_args(argv)
    App(args.host, args.port, args.splash_seconds).run()


if __name__ == "__main__":
    main()
