"""Tests for the client's non-GUI core: ChatState and ChatClient (against a real server)."""
from __future__ import annotations

import queue
import socket
import time
import unittest
from datetime import date, datetime

from client.client import ChatClient
from client.state import (ChatState, day_label, describe_system_message, format_time,
                          last_seen_label)
from server.server import ChatServer


def wait_for(client: ChatClient, kind: str, timeout: float = 3.0) -> dict:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            frame = client.events.get(timeout=0.2)
        except queue.Empty:
            continue
        if frame["type"] == kind:
            return frame
    raise AssertionError(f"timed out waiting for {kind}")


class StateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = ChatState()
        rooms = [{"id": 1, "name": "General", "description": "", "member_count": 2, "online_count": 2, "joined": True},
                 {"id": 2, "name": "Python", "description": "", "member_count": 1, "online_count": 1, "joined": True}]
        self.state.apply({"type": "auth_ok", "request": "login", "token": "t",
                          "user": {"username": "alice", "created_at": 1}, "rooms": rooms})
        self.state.apply({"type": "joined", "room": rooms[0], "history": [], "members": []})

    def msg(self, room: int, user: str, text: str = "hi", kind: str = "user") -> dict:
        return {"type": "message", "room_id": room,
                "message": {"id": 1, "kind": kind, "text": text, "ts": 1_700_000_000, "username": user}}

    def test_unread_counts_only_other_rooms_and_other_users(self) -> None:
        self.state.apply(self.msg(2, "bobby"))
        self.state.apply(self.msg(2, "bobby"))
        self.state.apply(self.msg(2, "alice"))                     # own message
        self.state.apply(self.msg(2, "bobby", "joined", "system"))  # system messages do not count
        self.state.apply(self.msg(1, "bobby"))                     # active room
        self.assertEqual(self.state.unread, {1: 0, 2: 2})

    def test_opening_room_clears_unread_and_replaces_history(self) -> None:
        self.state.apply(self.msg(2, "bobby"))
        change = self.state.apply({"type": "joined", "room": self.state.rooms[2],
                                   "history": [self.msg(2, "bobby", "old")["message"]], "members": []})
        self.assertEqual((change.kind, change.new_member), ("room_opened", False))
        self.assertEqual(self.state.unread[2], 0)
        self.assertEqual([m["text"] for m in self.state.messages[2]], ["old"])
        self.assertEqual(self.state.active_room_id, 2)

    def test_message_flags(self) -> None:
        change = self.state.apply(self.msg(2, "bobby"))
        self.assertEqual((change.is_own, change.is_active), (False, False))
        change = self.state.apply(self.msg(1, "ALICE"))
        self.assertEqual((change.is_own, change.is_active), (True, True))

    def test_leaving_active_room(self) -> None:
        self.state.apply({"type": "left", "room_id": 1})
        self.assertIsNone(self.state.active_room_id)
        self.assertFalse(self.state.rooms[1]["joined"])
        self.assertNotIn(1, self.state.messages)

    def test_cache_is_capped(self) -> None:
        for i in range(600):
            self.state.apply(self.msg(1, "bobby", str(i)))
        self.assertEqual(len(self.state.messages[1]), 500)
        self.assertEqual(self.state.messages[1][-1]["text"], "599")

    def test_error_frame(self) -> None:
        change = self.state.apply({"type": "error", "message": "Nope", "request": "login", "code": "auth"})
        self.assertEqual((change.kind, change.text, change.request), ("error", "Nope", "login"))

    def test_formatting_helpers(self) -> None:
        ts = int(datetime(2026, 9, 29, 14, 35).timestamp())
        self.assertEqual(format_time(ts), "14:35")
        self.assertEqual(day_label(ts, today=date(2026, 9, 29)), "Today")
        self.assertEqual(day_label(ts, today=date(2026, 9, 30)), "Yesterday")
        self.assertEqual(day_label(ts, today=date(2026, 10, 5)), "Tuesday, 29 September 2026")
        self.assertEqual(last_seen_label(ts, now=datetime(2026, 9, 29, 18, 0)), "last seen 14:35")
        self.assertEqual(last_seen_label(None), "never seen online")
        sys_msg = {"username": "alice", "text": "joined"}
        self.assertEqual(describe_system_message(sys_msg, "Alice", "Python"), "You joined #Python")
        self.assertEqual(describe_system_message({"username": "bobby", "text": "left"}, "alice", "Python"),
                         "bobby left #Python")


class ClientNetworkTests(unittest.TestCase):
    def test_connect_register_chat_and_detect_server_loss(self) -> None:
        server = ChatServer("127.0.0.1", 0, ":memory:")
        port = server.start()
        client = ChatClient()
        try:
            client.connect_async("127.0.0.1", port)
            wait_for(client, "_connected")
            client.send("register", username="alice", password="correct-horse")
            ok = wait_for(client, "auth_ok")
            general = next(r["id"] for r in ok["rooms"] if r["name"] == "General")
            client.send("join_room", room_id=general)
            wait_for(client, "joined")
            client.send("send_message", room_id=general, text="hi :wave:")
            msgs = []
            end = time.monotonic() + 3
            while time.monotonic() < end and not any(m["message"]["text"] == "hi 👋" for m in msgs):
                try:
                    f = client.events.get(timeout=0.2)
                except queue.Empty:
                    continue
                if f["type"] == "message":
                    msgs.append(f)
            self.assertTrue(any(m["message"]["text"] == "hi 👋" for m in msgs))
            server.stop()
            lost = wait_for(client, "_disconnected")
            self.assertIn("closed", lost["reason"])
            self.assertFalse(client.connected)
            self.assertFalse(client.send("ping"))
        finally:
            client.close()
            server.stop()

    def test_connection_refused_message_is_friendly(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            free_port = probe.getsockname()[1]
        client = ChatClient()
        client.connect_async("127.0.0.1", free_port)
        failed = wait_for(client, "_connect_failed")
        self.assertIn("run_server.bat", failed["message"])
        self.assertNotIn("Traceback", failed["message"])

    def test_deliberate_close_is_silent(self) -> None:
        server = ChatServer("127.0.0.1", 0, ":memory:")
        port = server.start()
        client = ChatClient()
        try:
            client.connect_async("127.0.0.1", port)
            wait_for(client, "_connected")
            client.close()
            time.sleep(0.4)
            kinds = []
            while not client.events.empty():
                kinds.append(client.events.get()["type"])
            self.assertNotIn("_disconnected", kinds)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
