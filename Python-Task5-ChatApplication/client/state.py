"""Client-side chat state: pure Python, no Tkinter, fully unit-testable."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

MESSAGE_CACHE_LIMIT = 500


def format_time(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M")


def same_day(a: int, b: int) -> bool:
    return datetime.fromtimestamp(a).date() == datetime.fromtimestamp(b).date()


def day_label(ts: int, today: date | None = None) -> str:
    day = datetime.fromtimestamp(ts).date()
    today = today or date.today()
    if day == today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    return day.strftime("%A, %d %B %Y")


def last_seen_label(ts: int | None, now: datetime | None = None) -> str:
    if not ts:
        return "never seen online"
    seen = datetime.fromtimestamp(ts)
    now = now or datetime.now()
    if seen.date() == now.date():
        return f"last seen {seen:%H:%M}"
    if seen.date() == now.date() - timedelta(days=1):
        return f"last seen yesterday {seen:%H:%M}"
    return f"last seen {seen:%d %b}"


def describe_system_message(message: dict[str, Any], me: str, room_name: str) -> str:
    actor = "You" if message["username"].lower() == me.lower() else message["username"]
    verb = message["text"]                       # 'joined' or 'left'
    return f"{actor} {verb} #{room_name}"


@dataclass
class Change:
    """What a server frame did to the state; the GUI reacts to this."""
    kind: str
    room_id: int | None = None
    message: dict[str, Any] | None = None
    username: str | None = None
    text: str | None = None
    request: str | None = None
    is_own: bool = False
    is_active: bool = False
    new_member: bool = False


class ChatState:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.username = ""
        self.created_at = 0
        self.token = ""
        self.rooms: dict[int, dict[str, Any]] = {}
        self.messages: dict[int, list[dict[str, Any]]] = {}
        self.members: dict[int, list[dict[str, Any]]] = {}
        self.unread: dict[int, int] = {}
        self.active_room_id: int | None = None

    @property
    def active_room(self) -> dict[str, Any] | None:
        return self.rooms.get(self.active_room_id) if self.active_room_id is not None else None

    def room_name(self, room_id: int) -> str:
        return self.rooms.get(room_id, {}).get("name", "unknown")

    def apply(self, frame: dict[str, Any]) -> Change:
        handler = getattr(self, f"_on_{frame['type']}", None)
        return handler(frame) if handler else Change("ignored")

    # -- frame handlers --------------------------------------------------
    def _on_auth_ok(self, f: dict[str, Any]) -> Change:
        self.username = f["user"]["username"]
        self.created_at = f["user"]["created_at"]
        self.token = f["token"]
        self.rooms = {r["id"]: r for r in f["rooms"]}
        return Change("auth", request=f.get("request"))

    def _on_rooms(self, f: dict[str, Any]) -> Change:
        self.rooms = {r["id"]: r for r in f["rooms"]}
        for room_id in [rid for rid in self.unread if rid not in self.rooms or not self.rooms[rid]["joined"]]:
            self.unread.pop(room_id, None)
        return Change("rooms")

    def _on_joined(self, f: dict[str, Any]) -> Change:
        room = f["room"]
        self.rooms[room["id"]] = room
        self.messages[room["id"]] = list(f["history"])
        self.members[room["id"]] = f["members"]
        self.unread[room["id"]] = 0
        self.active_room_id = room["id"]
        return Change("room_opened", room_id=room["id"], new_member=bool(f.get("new_member")))

    def _on_left(self, f: dict[str, Any]) -> Change:
        room_id = f["room_id"]
        self.messages.pop(room_id, None)
        self.members.pop(room_id, None)
        self.unread.pop(room_id, None)
        if room_id in self.rooms:
            self.rooms[room_id] = {**self.rooms[room_id], "joined": False}
        if self.active_room_id == room_id:
            self.active_room_id = None
        return Change("left", room_id=room_id)

    def _on_message(self, f: dict[str, Any]) -> Change:
        room_id, message = f["room_id"], f["message"]
        cache = self.messages.setdefault(room_id, [])
        cache.append(message)
        del cache[:-MESSAGE_CACHE_LIMIT]
        is_own = message["username"].lower() == self.username.lower()
        is_active = room_id == self.active_room_id
        if message["kind"] == "user" and not is_own and not is_active:
            self.unread[room_id] = self.unread.get(room_id, 0) + 1
        return Change("message", room_id=room_id, message=message, is_own=is_own, is_active=is_active)

    def _on_presence(self, f: dict[str, Any]) -> Change:
        self.members[f["room_id"]] = f["members"]
        return Change("presence", room_id=f["room_id"])

    def _on_typing(self, f: dict[str, Any]) -> Change:
        return Change("typing", room_id=f["room_id"], username=f["username"])

    def _on_error(self, f: dict[str, Any]) -> Change:
        return Change("error", text=f["message"], request=f.get("request"), username=f.get("code"))

    def _on_bye(self, f: dict[str, Any]) -> Change:
        return Change("bye")

    def _on_server_shutdown(self, f: dict[str, Any]) -> Change:
        return Change("shutdown")

    def _on_pong(self, f: dict[str, Any]) -> Change:
        return Change("ignored")
