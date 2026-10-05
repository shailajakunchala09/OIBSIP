"""Main chat dashboard: sidebar, message log, composer and members panel."""
from __future__ import annotations

import time
import tkinter as tk
from typing import TYPE_CHECKING

from common.emoji import PICKER_ORDER, SHORTCODES
from common.validation import MAX_MESSAGE_LENGTH

from .components import (Avatar, Badge, LogoMark, RoundedButton, ScrollFrame, SearchBox, ThinScrollbar)
from .state import ChatState, Change, day_label, describe_system_message, format_time, last_seen_label, same_day
from .theme import EMOJI_FONT, avatar_color, font, theme

if TYPE_CHECKING:
    from .gui import App

SIDEBAR_WIDTH = 280
MEMBERS_WIDTH = 250
GROUP_WINDOW_SECONDS = 300
TYPING_SEND_INTERVAL = 2.0
TYPING_DISPLAY_MS = 3500

STATUS_STYLES = {
    "connected": ("● Connected", "success", "Online"),
    "reconnecting": ("● Reconnecting…", "warning", "Reconnecting…"),
    "offline": ("● Offline - click to retry", "danger", "Offline"),
}


class ChatView(tk.Frame):
    def __init__(self, parent: tk.Misc, app: "App", state: ChatState) -> None:
        super().__init__(parent, bg=theme.c["bg"])
        self.app, self.state = app, state
        self._connection = "connected"
        self._room_filter = ""
        self._query = ""
        self._members_visible = True
        self._typing_users: dict[str, str] = {}
        self._last_typing_sent = 0.0
        self._hover_id: int | None = None
        self._msg_index: dict[int, tuple[str, int, str, bool]] = {}
        self._banner_after: str | None = None
        self._emoji_window: tk.Toplevel | None = None
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._build_members_panel()
        self.set_connection("connected")
        self.show_room() if state.active_room else self.show_welcome()

    # ====================================================================
    # Layout
    # ====================================================================
    def _build_sidebar(self) -> None:
        c = theme.c
        side = tk.Frame(self, bg=c["sidebar"], width=SIDEBAR_WIDTH)
        side.grid(row=0, column=0, sticky="nsew")
        side.pack_propagate(False)
        tk.Frame(side, bg=c["border"], width=1).pack(side="right", fill="y")

        brand = tk.Frame(side, bg=c["sidebar"])
        brand.pack(fill="x", padx=20, pady=(20, 14))
        LogoMark(brand, 30, bg=c["sidebar"]).pack(side="left")
        tk.Label(brand, text="VANTA CHAT", bg=c["sidebar"], fg=c["text"], font=font(13, "bold")).pack(side="left", padx=(10, 0))

        self._profile = tk.Frame(side, bg=c["surface"], padx=12, pady=10)
        self._profile.pack(fill="x", padx=14)
        self._avatar_slot = tk.Frame(self._profile, bg=c["surface"])
        self._avatar_slot.pack(side="left")
        identity = tk.Frame(self._profile, bg=c["surface"])
        identity.pack(side="left", padx=(12, 0))
        tk.Label(identity, text=self.state.username, bg=c["surface"], fg=c["text"], font=font(11, "bold"),
                 anchor="w").pack(fill="x")
        self._profile_status = tk.Label(identity, bg=c["surface"], fg=c["text_dim"], font=font(9), anchor="w")
        self._profile_status.pack(fill="x")

        search = SearchBox(side, "Search rooms", self._on_room_filter, on_escape=self._clear_room_filter)
        search.pack(fill="x", padx=14, pady=(14, 6))
        self._room_search = search

        header = tk.Frame(side, bg=c["sidebar"])
        header.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(header, text="ROOMS", bg=c["sidebar"], fg=c["text_faint"], font=font(8, "bold")).pack(side="left")

        footer = tk.Frame(side, bg=c["sidebar"])
        footer.pack(side="bottom", fill="x", padx=14, pady=(8, 16))
        RoundedButton(footer, "+  New room", self.app.request_new_room, width=250, height=38,
                      bg=c["sidebar"]).pack(fill="x")
        row = tk.Frame(footer, bg=c["sidebar"])
        row.pack(fill="x", pady=(8, 0))
        RoundedButton(row, "Settings", self.app.open_settings, style="ghost", width=100, height=32, bg=c["sidebar"],
                      size=9).pack(side="left")
        RoundedButton(row, "About", self.app.open_about, style="ghost", width=70, height=32, bg=c["sidebar"],
                      size=9).pack(side="left")
        RoundedButton(row, "Log out", self.app.request_logout, style="ghost", width=80, height=32, bg=c["sidebar"],
                      size=9).pack(side="right")

        self._room_list = ScrollFrame(side, c["sidebar"])
        self._room_list.pack(fill="both", expand=True, padx=(8, 4), pady=(6, 0))

    def _build_main(self) -> None:
        c = theme.c
        self._stack = tk.Frame(self, bg=c["bg"])
        self._stack.grid(row=0, column=1, sticky="nsew")
        self._stack.rowconfigure(0, weight=1)
        self._stack.columnconfigure(0, weight=1)
        self._welcome = tk.Frame(self._stack, bg=c["bg"])
        self._room_panel = tk.Frame(self._stack, bg=c["bg"])
        for panel in (self._welcome, self._room_panel):
            panel.grid(row=0, column=0, sticky="nsew")
        self._build_welcome()
        self._build_room_panel()

    def _build_welcome(self) -> None:
        c = theme.c
        center = tk.Frame(self._welcome, bg=c["bg"])
        center.place(relx=0.5, rely=0.45, anchor="center")
        LogoMark(center, 64).pack()
        tk.Label(center, text=f"Welcome, {self.state.username}", bg=c["bg"], fg=c["text"],
                 font=font(20, "bold")).pack(pady=(20, 6))
        tk.Label(center, text="Choose a room in the sidebar to join the conversation,\nor start a new one of your own.",
                 bg=c["bg"], fg=c["text_dim"], font=font(11), justify="center").pack()
        buttons = tk.Frame(center, bg=c["bg"])
        buttons.pack(pady=(24, 0))
        RoundedButton(buttons, "Create a room", self.app.request_new_room, width=140, height=40).pack(side="left", padx=5)
        RoundedButton(buttons, "Search rooms", self.focus_room_search, style="secondary", width=140, height=40).pack(side="left", padx=5)
        tk.Label(center, text="Tip: Ctrl+K searches rooms, Ctrl+N creates one.", bg=c["bg"], fg=c["text_faint"],
                 font=font(9)).pack(pady=(26, 0))

    def _build_room_panel(self) -> None:
        c = theme.c
        panel = self._room_panel
        # -- header ------------------------------------------------------
        self._header = tk.Frame(panel, bg=c["bg"])
        self._header.pack(side="top", fill="x", padx=24, pady=(16, 10))
        titles = tk.Frame(self._header, bg=c["bg"])
        titles.pack(side="left")
        self._title = tk.Label(titles, bg=c["bg"], fg=c["text"], font=font(16, "bold"), anchor="w")
        self._title.pack(fill="x")
        self._description = tk.Label(titles, bg=c["bg"], fg=c["text_dim"], font=font(9), anchor="w")
        self._description.pack(fill="x")
        controls = tk.Frame(self._header, bg=c["bg"])
        controls.pack(side="right")
        self._pill = tk.Label(controls, bg=c["bg"], font=font(9, "bold"), cursor="hand2")
        self._pill.pack(side="right", padx=(14, 0))
        self._pill.bind("<Button-1>", lambda e: self.app.reconnect_now() if self._connection != "connected" else None)
        for text, command, width in (("Leave", self._leave, 62), ("Members", self.toggle_members, 82),
                                     ("Search", self.toggle_search, 70)):
            RoundedButton(controls, text, command, style="ghost", width=width, height=32, size=9).pack(side="right", padx=2)
        counts = tk.Frame(controls, bg=c["bg"])
        counts.pack(side="right", padx=(0, 12))
        self._members_label = tk.Label(counts, bg=c["bg"], fg=c["text_dim"], font=font(9), anchor="e")
        self._members_label.pack(fill="x")
        self._online_label = tk.Label(counts, bg=c["bg"], fg=c["success"], font=font(9), anchor="e")
        self._online_label.pack(fill="x")
        tk.Frame(panel, bg=c["border"], height=1).pack(side="top", fill="x")

        # -- message search bar (hidden until Ctrl+F) --------------------
        self._search_bar = tk.Frame(panel, bg=c["bg"])
        self._message_search = SearchBox(self._search_bar, "Search messages in this room", self._on_message_search,
                                         on_escape=self.close_search)
        self._message_search.pack(side="left", fill="x", expand=True)
        self._search_count = tk.Label(self._search_bar, bg=c["bg"], fg=c["text_dim"], font=font(9))
        self._search_count.pack(side="left", padx=12)
        close = tk.Label(self._search_bar, text="✕", bg=c["bg"], fg=c["text_dim"], font=font(11), cursor="hand2")
        close.pack(side="left")
        close.bind("<Button-1>", lambda e: self.close_search())

        # -- composer (packed bottom-up so the log gets the remaining space)
        self._build_composer(panel)

        # -- message log ---------------------------------------------------
        holder = tk.Frame(panel, bg=c["bg"])
        holder.pack(side="top", fill="both", expand=True)
        self._log_holder = holder
        self.log = tk.Text(holder, bg=c["bg"], fg=c["text"], bd=0, highlightthickness=0, wrap="word", padx=24, pady=8,
                           cursor="arrow", state="disabled", font=font(11), insertwidth=0, spacing2=2,
                           selectbackground=c["accent"], selectforeground="#FFFFFF",
                           inactiveselectbackground=c["border"])
        scrollbar = ThinScrollbar(holder, self.log.yview, bg=c["bg"])
        self.log.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0, 4))
        self.log.pack(side="left", fill="both", expand=True)
        self._configure_tags()
        self.log.bind("<Motion>", self._on_motion)
        self.log.bind("<Leave>", lambda e: self._set_hover(None))
        self.log.bind("<Button-3>", self._on_right_click)
        self.log.bind("<Button-2>", self._on_right_click)
        self.log.bind("<Button-1>", lambda e: self.log.focus_set())
        self.log.bind("<Key>", self._on_log_key)

        self._empty = tk.Frame(holder, bg=c["bg"])
        self._empty_title = tk.Label(self._empty, bg=c["bg"], fg=c["text"], font=font(14, "bold"))
        self._empty_title.pack()
        self._empty_text = tk.Label(self._empty, bg=c["bg"], fg=c["text_dim"], font=font(10), justify="center")
        self._empty_text.pack(pady=(6, 0))
        self._jump = RoundedButton(holder, "New messages  ↓", self._jump_to_bottom, width=150, height=32, radius=16,
                                   bg=c["bg"], size=9)

    def _build_composer(self, panel: tk.Frame) -> None:
        c = theme.c
        card = tk.Frame(panel, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"],
                        highlightcolor=c["accent"])
        card.pack(side="bottom", fill="x", padx=24, pady=(0, 18))
        self._typing_label = tk.Label(panel, bg=c["bg"], fg=c["text_dim"], font=font(9, "italic"), anchor="w", height=1)
        self._typing_label.pack(side="bottom", fill="x", padx=26, pady=(2, 4))
        self._banner = tk.Label(panel, bg=c["danger"], fg="#FFFFFF", font=font(10), anchor="w", padx=14, pady=7)

        top = tk.Frame(card, bg=c["surface"])
        top.pack(fill="x")
        self.input = tk.Text(top, height=1, wrap="word", bg=c["surface"], fg=c["text"], insertbackground=c["text"],
                             bd=0, highlightthickness=0, font=font(11), padx=14, pady=12, undo=True,
                             selectbackground=c["accent"], selectforeground="#FFFFFF")
        self.input.pack(side="left", fill="x", expand=True)
        self._placeholder = tk.Label(self.input, bg=c["surface"], fg=c["text_faint"], font=font(11))
        self._placeholder.place(x=14, y=12)
        self._placeholder.bind("<Button-1>", lambda e: self.input.focus_set())
        buttons = tk.Frame(top, bg=c["surface"])
        buttons.pack(side="right", padx=(0, 10), pady=6)
        self._emoji_button = RoundedButton(buttons, "☺", self.toggle_emoji_picker, style="ghost", width=40, height=36,
                                           bg=c["surface"], size=14)
        self._emoji_button.pack(side="left", padx=(0, 6))
        self._send_button = RoundedButton(buttons, "Send", self._send, width=76, height=36, bg=c["surface"])
        self._send_button.pack(side="left")

        bottom = tk.Frame(card, bg=c["surface"])
        bottom.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(bottom, text="Enter to send  ·  Shift+Enter for a new line  ·  :smile: becomes 😄", bg=c["surface"],
                 fg=c["text_faint"], font=font(8)).pack(side="left")
        self._counter = tk.Label(bottom, bg=c["surface"], fg=c["text_faint"], font=font(8))
        self._counter.pack(side="right")

        self.input.bind("<Return>", self._on_enter)
        self.input.bind("<Shift-Return>", lambda e: None)
        self.input.bind("<Escape>", lambda e: self._clear_input())
        self.input.bind("<KeyRelease>", self._on_input_changed)
        self.input.bind("<<Paste>>", lambda e: self.after_idle(self._on_input_changed))
        self._sync_input()

    def _build_members_panel(self) -> None:
        c = theme.c
        self._members_panel = tk.Frame(self, bg=c["sidebar"], width=MEMBERS_WIDTH)
        self._members_panel.grid(row=0, column=2, sticky="nsew")
        self._members_panel.pack_propagate(False)
        tk.Frame(self._members_panel, bg=c["border"], width=1).pack(side="left", fill="y")
        header = tk.Frame(self._members_panel, bg=c["sidebar"])
        header.pack(fill="x", padx=18, pady=(22, 6))
        tk.Label(header, text="MEMBERS", bg=c["sidebar"], fg=c["text_faint"], font=font(8, "bold")).pack(side="left")
        tk.Label(self._members_panel,
                 text="Messages are stored unencrypted on the server and are not end-to-end encrypted.",
                 bg=c["sidebar"], fg=c["text_faint"], font=font(8), wraplength=MEMBERS_WIDTH - 40, justify="left"
                 ).pack(side="bottom", anchor="w", padx=18, pady=(0, 18))
        self._members_list = ScrollFrame(self._members_panel, c["sidebar"])
        self._members_list.pack(fill="both", expand=True, padx=(10, 4))

    def _configure_tags(self) -> None:
        c, log = theme.c, self.log
        log.tag_configure("date", justify="center", foreground=c["text_dim"], background=c["surface_alt"],
                          font=font(8, "bold"), spacing1=18, spacing3=10)
        log.tag_configure("system", justify="center", foreground=c["text_faint"], font=font(9, "italic"),
                          spacing1=8, spacing3=8)
        log.tag_configure("other_head", spacing1=12, spacing3=1, rmargin=140)
        log.tag_configure("other_body", rmargin=140, spacing3=2)
        log.tag_configure("own_head", justify="right", spacing1=12, spacing3=1, lmargin1=140, lmargin2=140)
        log.tag_configure("own_body", justify="right", background=c["own_bubble"], foreground=c["own_text"],
                          lmargin1=140, lmargin2=140, spacing3=2)
        log.tag_configure("grouped", spacing1=1)
        log.tag_configure("name_own", foreground=c["text_dim"], font=font(9, "bold"))
        log.tag_configure("time", foreground=c["text_faint"], font=font(8))
        log.tag_configure("hover", background=c["hover"])
        log.tag_configure("hl", background=c["warning"], foreground="#111111")
        log.tag_raise("hl")

    # ====================================================================
    # Rooms (sidebar)
    # ====================================================================
    def _on_room_filter(self, text: str) -> None:
        self._room_filter = text.lower()
        self.refresh_rooms()

    def _clear_room_filter(self) -> None:
        self._room_search.clear()
        self.focus_composer()

    def refresh_rooms(self) -> None:
        body = self._room_list.body
        for child in body.winfo_children():
            child.destroy()
        rooms = sorted(self.state.rooms.values(), key=lambda r: r["name"].lower())
        visible = [r for r in rooms if self._room_filter in r["name"].lower()]
        joined = [r for r in visible if r["joined"]]
        others = [r for r in visible if not r["joined"]]
        for title, group in (("YOUR ROOMS", joined), ("BROWSE", others)):
            if group:
                tk.Label(body, text=title, bg=theme.c["sidebar"], fg=theme.c["text_faint"], font=font(8, "bold"),
                         anchor="w").pack(fill="x", padx=12, pady=(12, 4))
                for room in group:
                    self._room_row(body, room)
        if not visible:
            tk.Label(body, text=f'No rooms match "{self._room_filter}"', bg=theme.c["sidebar"],
                     fg=theme.c["text_dim"], font=font(10)).pack(padx=12, pady=24)
        self._update_header()

    def _room_row(self, parent: tk.Frame, room: dict) -> None:
        c = theme.c
        active = room["id"] == self.state.active_room_id
        base = c["surface_alt"] if active else c["sidebar"]
        row = tk.Frame(parent, bg=base, cursor="hand2")
        row.pack(fill="x", pady=1)
        bar = tk.Frame(row, bg=c["accent"] if active else base, width=3)
        bar.pack(side="left", fill="y")
        hash_label = tk.Label(row, text="#", bg=base, fg=c["accent"] if active else c["text_faint"], font=font(12, "bold"))
        hash_label.pack(side="left", padx=(10, 0), pady=8)
        name = tk.Label(row, text=room["name"], bg=base, anchor="w", font=font(10, "bold" if active else ""),
                        fg=c["text"] if room["joined"] else c["text_dim"])
        name.pack(side="left", padx=(6, 0), fill="x", expand=True)
        unread = self.state.unread.get(room["id"], 0)
        if room["joined"]:
            tail: tk.Widget = Badge(row, unread, bg=base)
        else:
            tail = tk.Label(row, text="Join", bg=base, fg=c["text_faint"], font=font(8, "bold"))
        tail.pack(side="right", padx=(0, 10))
        widgets = [row, hash_label, name, tail]

        def paint(color: str) -> None:
            for widget in widgets:
                widget.configure(bg=color)
            bar.configure(bg=c["accent"] if active else color)

        for widget in (*widgets, bar):
            widget.bind("<Button-1>", lambda e, rid=room["id"]: self.app.open_room(rid))
            if not active:
                widget.bind("<Enter>", lambda e: paint(c["hover"]))
                widget.bind("<Leave>", lambda e: paint(base))

    # ====================================================================
    # Header, members, connection status
    # ====================================================================
    def _update_header(self) -> None:
        room = self.state.active_room
        if not room:
            return
        self._title.configure(text=f"#  {room['name']}")
        self._description.configure(text=room["description"] or "No description yet.")
        self._members_label.configure(text=f"{room['member_count']} member{'s' if room['member_count'] != 1 else ''}")
        self._online_label.configure(text=f"● {room['online_count']} online")

    def render_members(self) -> None:
        c = theme.c
        body = self._members_list.body
        for child in body.winfo_children():
            child.destroy()
        members = self.state.members.get(self.state.active_room_id or -1, [])
        for member in sorted(members, key=lambda m: (not m["online"], m["username"].lower())):
            row = tk.Frame(body, bg=c["sidebar"])
            row.pack(fill="x", padx=8, pady=5)
            Avatar(row, member["username"], 32, "online" if member["online"] else "offline").pack(side="left")
            text = tk.Frame(row, bg=c["sidebar"])
            text.pack(side="left", padx=(10, 0))
            you = "  (you)" if member["username"].lower() == self.state.username.lower() else ""
            tk.Label(text, text=member["username"] + you, bg=c["sidebar"], fg=c["text"] if member["online"] else c["text_dim"],
                     font=font(10, "bold"), anchor="w").pack(fill="x")
            status = "online now" if member["online"] else last_seen_label(member.get("last_seen"))
            tk.Label(text, text=status, bg=c["sidebar"], fg=c["success"] if member["online"] else c["text_faint"],
                     font=font(8), anchor="w").pack(fill="x")

    def set_connection(self, status: str) -> None:
        c = theme.c
        self._connection = status
        label, color_key, profile_text = STATUS_STYLES[status]
        self._pill.configure(text=label, fg=c[color_key])
        self._profile_status.configure(text=profile_text, fg=c[color_key] if status != "connected" else c["text_dim"])
        for child in self._avatar_slot.winfo_children():
            child.destroy()
        Avatar(self._avatar_slot, self.state.username, 40, "online" if status == "connected" else "offline",
               bg=c["surface"]).pack()
        self._set_composer_enabled(status == "connected" and self.state.active_room is not None)

    def toggle_members(self) -> None:
        self._members_visible = not self._members_visible
        if self._members_visible:
            self._members_panel.grid()
        else:
            self._members_panel.grid_remove()

    # ====================================================================
    # Switching between the welcome screen and a room
    # ====================================================================
    def show_welcome(self) -> None:
        self._welcome.tkraise()
        self._members_panel.grid_remove()
        self.refresh_rooms()
        self._set_composer_enabled(False)

    def show_room(self) -> None:
        room = self.state.active_room
        if not room:
            return self.show_welcome()
        self._room_panel.tkraise()
        if self._members_visible:
            self._members_panel.grid()
        self._clear_typing()
        self.close_search()
        self._placeholder.configure(text=f"Message #{room['name']}")
        self.refresh_rooms()
        self.render_messages()
        self.render_members()
        self._set_composer_enabled(self._connection == "connected")
        self.focus_composer()

    # ====================================================================
    # Message log
    # ====================================================================
    def render_messages(self) -> None:
        room_id = self.state.active_room_id
        messages = self.state.messages.get(room_id, []) if room_id is not None else []
        query = self._query.lower()
        shown = [m for m in messages if not query or (m["kind"] == "user" and query in m["text"].lower())]
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self._msg_index.clear()
        self._hover_id = None
        previous = None
        for message in shown:
            self._insert_message(message, previous, query)
            previous = message
        self.log.configure(state="disabled")
        self._search_count.configure(text=f"{sum(m['kind'] == 'user' for m in shown)} found" if query else "")
        self._update_empty_state(shown, messages)
        self._jump.place_forget()
        self.log.yview_moveto(1.0)
        self.after_idle(lambda: self.log.yview_moveto(1.0))

    def _insert_message(self, message: dict, previous: dict | None, query: str = "") -> None:
        log, room_name = self.log, self.state.room_name(self.state.active_room_id or -1)
        if previous is None or not same_day(previous["ts"], message["ts"]):
            log.insert("end", f"  {day_label(message['ts'])}  ", "date")
            log.insert("end", "\n")
        if message["kind"] == "system":
            log.insert("end", describe_system_message(message, self.state.username, room_name) + "\n", "system")
            return
        own = message["username"].lower() == self.state.username.lower()
        grouped = (previous is not None and previous["kind"] == "user" and previous["username"] == message["username"]
                   and same_day(previous["ts"], message["ts"]) and message["ts"] - previous["ts"] < GROUP_WINDOW_SECONDS)
        start = log.index("end-1c")
        if not grouped:
            self._insert_header(message, own)
        body_tag = "own_body" if own else "other_body"
        text = f"\u00a0\u00a0{message['text']}\u00a0\u00a0" if own else message["text"]
        body_start = log.index("end-1c")
        log.insert("end", text, (body_tag, "grouped") if grouped else (body_tag,))
        body_end = log.index("end-1c")
        log.insert("end", "\n")
        log.tag_add(f"msg_{message['id']}", start, log.index("end-1c"))
        self._msg_index[message["id"]] = (message["username"], message["ts"], message["text"], own)
        if query:
            self._highlight(body_start, body_end, query)

    def _insert_header(self, message: dict, own: bool) -> None:
        log = self.log
        stamp = format_time(message["ts"])
        if own:
            log.insert("end", "You", ("own_head", "name_own"))
            log.insert("end", f"  {stamp}", ("own_head", "time"))
        else:
            user_tag = f"user_{message['username'].lower()}"
            log.tag_configure(user_tag, foreground=avatar_color(message["username"]), font=font(10, "bold"))
            log.insert("end", message["username"], ("other_head", user_tag))
            log.insert("end", f"  {stamp}", ("other_head", "time"))
        log.insert("end", "\n")

    def _highlight(self, start: str, end: str, query: str) -> None:
        index = start
        while True:
            index = self.log.search(query, index, stopindex=end, nocase=True)
            if not index:
                return
            stop = f"{index}+{len(query)}c"
            self.log.tag_add("hl", index, stop)
            index = stop

    def on_message(self, change: Change) -> None:
        message = change.message
        if change.room_id != self.state.active_room_id or message is None:
            self.refresh_rooms()
            return
        self._drop_typing(message["username"])
        if self._query:
            self.render_messages()
            return
        at_bottom = self.log.yview()[1] >= 0.97
        messages = self.state.messages[change.room_id]
        previous = messages[-2] if len(messages) > 1 else None
        self.log.configure(state="normal")
        self._insert_message(message, previous)
        self.log.configure(state="disabled")
        self._update_empty_state(messages, messages)
        if at_bottom or change.is_own:
            self.log.yview_moveto(1.0)
        elif message["kind"] == "user":
            self._jump.place(relx=0.5, rely=1.0, y=-14, anchor="s")

    def _jump_to_bottom(self) -> None:
        self.log.yview_moveto(1.0)
        self._jump.place_forget()

    def _update_empty_state(self, shown: list[dict], all_messages: list[dict]) -> None:
        room = self.state.active_room
        if self._query and not any(m["kind"] == "user" for m in shown):
            self._empty_title.configure(text="No matches")
            self._empty_text.configure(text=f'Nothing in #{room["name"] if room else ""} matches "{self._query}".')
        elif not any(m["kind"] == "user" for m in all_messages):
            self._empty_title.configure(text=f"It's quiet in #{room['name'] if room else ''}")
            self._empty_text.configure(text="Be the first to say something.\nTry :wave: or :rocket:")
        else:
            self._empty.place_forget()
            return
        self._empty.place(relx=0.5, rely=0.5, anchor="center")

    # -- hover, copy, and key handling in the log ------------------------
    def _message_at(self, event: tk.Event) -> int | None:
        for tag in self.log.tag_names(self.log.index(f"@{event.x},{event.y}")):
            if tag.startswith("msg_"):
                return int(tag[4:])
        return None

    def _on_motion(self, event: tk.Event) -> None:
        message_id = self._message_at(event)
        if message_id is not None and self._msg_index.get(message_id, ("", 0, "", True))[3]:
            message_id = None           # own messages already have their own tint
        self._set_hover(message_id)

    def _set_hover(self, message_id: int | None) -> None:
        if message_id == self._hover_id:
            return
        self.log.tag_remove("hover", "1.0", "end")
        self._hover_id = message_id
        if message_id is not None:
            ranges = self.log.tag_ranges(f"msg_{message_id}")
            if ranges:
                self.log.tag_add("hover", ranges[0], ranges[1])

    def _on_right_click(self, event: tk.Event) -> None:
        message_id = self._message_at(event)
        if message_id is None or message_id not in self._msg_index:
            return
        sender, ts, text, _ = self._msg_index[message_id]
        c = theme.c
        menu = tk.Menu(self, tearoff=0, bg=c["surface"], fg=c["text"], activebackground=c["accent"],
                       activeforeground="#FFFFFF", bd=0, font=font(10))
        menu.add_command(label="Copy message", command=lambda: self._copy(text))
        menu.add_command(label="Copy with sender and time", command=lambda: self._copy(f"[{format_time(ts)}] {sender}: {text}"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)

    def _on_log_key(self, event: tk.Event) -> str | None:
        """Typing while the log has focus goes to the composer instead of being lost."""
        if event.char and event.char.isprintable() and not (event.state & 0x4):
            if str(self.input.cget("state")) == "normal":
                self.input.focus_set()
                self.input.insert("end", event.char)
                self._on_input_changed()
            return "break"
        return None

    # ====================================================================
    # Composer
    # ====================================================================
    def _set_composer_enabled(self, enabled: bool) -> None:
        self.input.configure(state="normal" if enabled else "disabled")
        self._send_button.set_enabled(enabled)
        self._emoji_button.set_enabled(enabled)
        if not enabled:
            self._placeholder.configure(text="Reconnecting…" if self._connection == "reconnecting"
                                        else "Offline - messages cannot be sent" if self._connection == "offline"
                                        else "Select a room to start chatting")
        elif self.state.active_room:
            self._placeholder.configure(text=f"Message #{self.state.active_room['name']}")
        self._sync_input()

    def focus_composer(self) -> None:
        if str(self.input.cget("state")) == "normal":
            self.input.focus_set()

    def _on_enter(self, event: tk.Event) -> str:
        self._send()
        return "break"

    def _send(self) -> None:
        room_id = self.state.active_room_id
        text = self.input.get("1.0", "end").strip()
        if room_id is None or not text or str(self.input.cget("state")) != "normal":
            return
        if len(text) > MAX_MESSAGE_LENGTH:
            return self.flash(f"That message is {len(text) - MAX_MESSAGE_LENGTH} characters too long.")
        if self.app.send_message(room_id, text):
            self._clear_input()
            self._last_typing_sent = 0.0
        else:
            self.flash("You are not connected. Your message was not sent.")

    def _clear_input(self) -> None:
        self.input.delete("1.0", "end")
        self._on_input_changed()

    def _on_input_changed(self, event: tk.Event | None = None) -> None:
        self._sync_input()
        is_typing_key = event is None or event.keysym not in ("Return", "Escape", "Shift_L", "Shift_R", "Control_L",
                                                              "Control_R", "Alt_L", "Alt_R", "Left", "Right", "Up", "Down")
        content = self.input.get("1.0", "end").strip()
        now = time.monotonic()
        if content and is_typing_key and now - self._last_typing_sent > TYPING_SEND_INTERVAL and self.state.active_room_id:
            self._last_typing_sent = now
            self.app.notify_typing(self.state.active_room_id)

    def _sync_input(self) -> None:
        content = self.input.get("1.0", "end-1c")
        if content:
            self._placeholder.place_forget()
        else:
            self._placeholder.place(x=14, y=12)
        length = len(content.strip())
        color = theme.c["danger"] if length > MAX_MESSAGE_LENGTH else theme.c["warning"] if length > MAX_MESSAGE_LENGTH * 0.9 else theme.c["text_faint"]
        self._counter.configure(text=f"{length} / {MAX_MESSAGE_LENGTH}", fg=color)
        try:
            lines = self.input.count("1.0", "end-1c", "displaylines")
            self.input.configure(height=max(1, min(5, lines[0] if lines else 1)))
        except tk.TclError:
            pass

    # -- emoji picker -----------------------------------------------------
    def toggle_emoji_picker(self) -> None:
        if self._emoji_window is not None:
            return self._close_emoji_picker()
        if str(self.input.cget("state")) != "normal":
            return
        c = theme.c
        window = tk.Toplevel(self, bg=c["border"])
        window.overrideredirect(True)
        try:
            window.attributes("-topmost", True)
        except tk.TclError:
            pass
        card = tk.Frame(window, bg=c["surface"])
        card.pack(padx=1, pady=1)
        grid = tk.Frame(card, bg=c["surface"])
        grid.pack(padx=8, pady=(8, 2))
        caption = tk.Label(card, text="Type :name: to use a shortcode", bg=c["surface"], fg=c["text_faint"], font=font(8))
        caption.pack(pady=(0, 8))
        for index, code in enumerate(PICKER_ORDER):
            glyph = SHORTCODES[code]
            cell = tk.Label(grid, text=glyph, font=font(16, family=EMOJI_FONT), bg=c["surface"], fg=c["text"], width=2,
                            cursor="hand2")
            cell.grid(row=index // 4, column=index % 4, padx=2, pady=2)
            cell.bind("<Enter>", lambda e, w=cell, n=code: (w.configure(bg=c["hover"]), caption.configure(text=f":{n}:")))
            cell.bind("<Leave>", lambda e, w=cell: w.configure(bg=c["surface"]))
            cell.bind("<Button-1>", lambda e, g=glyph: self._insert_emoji(g))
        window.update_idletasks()
        x = self._emoji_button.winfo_rootx() - window.winfo_reqwidth() + self._emoji_button.winfo_width()
        y = self._emoji_button.winfo_rooty() - window.winfo_reqheight() - 8
        window.geometry(f"+{max(0, x)}+{max(0, y)}")
        window.bind("<Escape>", lambda e: self._close_emoji_picker())
        window.bind("<FocusOut>", lambda e: self.after(150, self._close_emoji_picker))
        window.focus_force()
        self._emoji_window = window

    def _close_emoji_picker(self) -> None:
        window, self._emoji_window = self._emoji_window, None
        if window is not None:
            try:
                window.destroy()
            except tk.TclError:
                pass

    def _insert_emoji(self, glyph: str) -> None:
        self._close_emoji_picker()
        self.input.insert("insert", glyph)
        self.input.focus_set()
        self._on_input_changed()

    # ====================================================================
    # Search, typing indicator, banners, shortcuts
    # ====================================================================
    def toggle_search(self) -> None:
        if not self.state.active_room:
            return
        if self._search_bar.winfo_ismapped():
            self.close_search()
        else:
            self._search_bar.pack(side="top", fill="x", padx=24, pady=(10, 0), after=self._header)
            self._message_search.focus()

    def close_search(self) -> None:
        if self._search_bar.winfo_ismapped():
            self._search_bar.pack_forget()
        if self._query:
            self._message_search.clear()      # its callback resets the query and re-renders
        self.focus_composer()

    def _on_message_search(self, text: str) -> None:
        self._query = text
        self.render_messages()

    def focus_room_search(self) -> None:
        self._room_search.focus()

    def show_typing(self, room_id: int, username: str) -> None:
        if room_id != self.state.active_room_id:
            return
        self._drop_typing(username, refresh=False)
        self._typing_users[username] = self.after(TYPING_DISPLAY_MS, lambda: self._drop_typing(username))
        self._refresh_typing_label()

    def _drop_typing(self, username: str, refresh: bool = True) -> None:
        after_id = self._typing_users.pop(username, None)
        if after_id:
            self.after_cancel(after_id)
        if refresh:
            self._refresh_typing_label()

    def _clear_typing(self) -> None:
        for username in list(self._typing_users):
            self._drop_typing(username, refresh=False)
        self._refresh_typing_label()

    def _refresh_typing_label(self) -> None:
        names = list(self._typing_users)
        text = ("" if not names else f"{names[0]} is typing…" if len(names) == 1
                else f"{names[0]} and {names[1]} are typing…" if len(names) == 2 else "Several people are typing…")
        self._typing_label.configure(text=text)

    def flash(self, text: str) -> None:
        """Show a short, non-blocking error banner above the composer."""
        if self._banner_after:
            self.after_cancel(self._banner_after)
        self._banner.configure(text=text)
        self._banner.pack(side="bottom", fill="x", padx=24, pady=(0, 6), before=self._typing_label)
        self._banner_after = self.after(4000, self._hide_banner)

    def _hide_banner(self) -> None:
        self._banner_after = None
        self._banner.pack_forget()

    def _leave(self) -> None:
        if self.state.active_room_id is not None:
            self.app.request_leave_room(self.state.active_room_id)

    def destroy(self) -> None:
        self._close_emoji_picker()
        for after_id in [*self._typing_users.values(), self._banner_after]:
            if after_id:
                try:
                    self.after_cancel(after_id)
                except tk.TclError:
                    pass
        super().destroy()
