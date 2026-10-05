"""Integration tests: a real ChatServer on a random port, real sockets, real SQLite."""
from __future__ import annotations

import queue
import socket
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Callable

from common.protocol import FrameReader, encode
from server.server import ChatServer

PASSWORD = "correct-horse"


class TestClient:
    """Minimal scripted client that collects every frame the server sends."""

    def __init__(self, port: int) -> None:
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=5)
        self.frames: queue.Queue[dict[str, Any]] = queue.Queue()
        self.seen: list[dict[str, Any]] = []
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        reader = FrameReader(self.sock)
        try:
            while (frame := reader.read()) is not None:
                self.frames.put(frame)
        except (OSError, ValueError):
            pass

    def send(self, **payload: Any) -> None:
        self.sock.sendall(encode(payload))

    def wait(self, predicate: Callable[[dict[str, Any]], bool], timeout: float = 3.0) -> dict[str, Any]:
        end = timeout
        while True:
            try:
                frame = self.frames.get(timeout=end)
            except queue.Empty:
                raise AssertionError("Timed out waiting for expected frame; saw "
                                     f"{[f['type'] for f in self.seen[-8:]]}") from None
            self.seen.append(frame)
            if predicate(frame):
                return frame

    def expect(self, kind: str, timeout: float = 3.0, **match: Any) -> dict[str, Any]:
        return self.wait(lambda f: f["type"] == kind and all(f.get(k) == v for k, v in match.items()), timeout)

    def expect_silence(self, kind: str, window: float = 0.4) -> None:
        end = window
        while True:
            try:
                frame = self.frames.get(timeout=end)
            except queue.Empty:
                return
            self.seen.append(frame)
            if frame["type"] == kind:
                raise AssertionError(f"Unexpected {kind} frame: {frame}")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class ServerTestCase(unittest.TestCase):
    db_path: Path | str = ":memory:"

    def setUp(self) -> None:
        self.server = ChatServer("127.0.0.1", 0, self.db_path)
        self.port = self.server.start()
        self.clients: list[TestClient] = []

    def tearDown(self) -> None:
        for client in self.clients:
            client.close()
        self.server.stop()

    def connect(self) -> TestClient:
        client = TestClient(self.port)
        self.clients.append(client)
        return client

    def register(self, username: str, password: str = PASSWORD) -> tuple[TestClient, dict[str, Any]]:
        client = self.connect()
        client.send(type="register", username=username, password=password)
        return client, client.expect("auth_ok")

    @staticmethod
    def room_id(auth_ok: dict[str, Any], name: str) -> int:
        return next(r["id"] for r in auth_ok["rooms"] if r["name"] == name)


class AuthTests(ServerTestCase):
    def test_register_then_login(self) -> None:
        client, ok = self.register("alice")
        self.assertEqual(ok["user"]["username"], "alice")
        self.assertEqual([r["name"] for r in ok["rooms"]], ["General", "Python", "Random", "Technology"])
        client.send(type="logout")
        client.expect("bye")
        second = self.connect()
        second.send(type="login", username="ALICE", password=PASSWORD)   # usernames are case-insensitive
        self.assertEqual(second.expect("auth_ok")["user"]["username"], "alice")

    def test_validation_and_friendly_errors(self) -> None:
        c = self.connect()
        for payload, fragment in [
            ({"username": "", "password": PASSWORD}, "username"),
            ({"username": "ab", "password": PASSWORD}, "3-20"),
            ({"username": "bad name!", "password": PASSWORD}, "letters"),
            ({"username": "carol", "password": ""}, "password"),
            ({"username": "carol", "password": "short"}, "at least"),
        ]:
            c.send(type="register", **payload)
            self.assertIn(fragment, c.expect("error", request="register")["message"])

    def test_duplicate_username(self) -> None:
        self.register("alice")
        c = self.connect()
        c.send(type="register", username="Alice", password=PASSWORD)
        self.assertEqual(c.expect("error")["code"], "exists")

    def test_wrong_password_and_unknown_user_look_identical(self) -> None:
        self.register("alice")
        c = self.connect()
        c.send(type="login", username="alice", password="wrong-password")
        wrong = c.expect("error")["message"]
        c.send(type="login", username="nobody", password="wrong-password")
        unknown = c.expect("error")["message"]
        self.assertEqual(wrong, unknown)

    def test_requests_before_login_are_rejected(self) -> None:
        c = self.connect()
        c.send(type="send_message", room_id=1, text="hi")
        self.assertEqual(c.expect("error")["code"], "auth")

    def test_second_login_of_same_account_is_refused(self) -> None:
        self.register("alice")
        c = self.connect()
        c.send(type="login", username="alice", password=PASSWORD)
        self.assertIn("already signed in", c.expect("error")["message"])

    def test_resume_with_token_takes_over_old_connection(self) -> None:
        old, ok = self.register("alice")
        fresh = self.connect()
        fresh.send(type="resume", token=ok["token"])
        self.assertEqual(fresh.expect("auth_ok")["user"]["username"], "alice")
        fresh.send(type="resume", token="bogus")
        self.assertEqual(fresh.expect("error")["request"], "resume")

    def test_malformed_input_does_not_crash_server(self) -> None:
        c = self.connect()
        c.sock.sendall(b"this is not json\n")
        self.assertEqual(c.expect("error")["code"], "protocol")
        d, _ = self.register("alice")   # server still works
        d.send(type="join_room", room_id="nope")
        self.assertEqual(d.expect("error")["code"], "not_found")


class PasswordStorageTests(unittest.TestCase):
    def test_passwords_are_salted_hashes_not_plaintext(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.db"
            server = ChatServer("127.0.0.1", 0, path)
            port = server.start()
            clients = []
            for name in ("alice", "bobby"):
                c = TestClient(port)
                clients.append(c)
                c.send(type="register", username=name, password=PASSWORD)
                c.expect("auth_ok")
            server.stop()
            for c in clients:
                c.close()
            rows = sqlite3.connect(path).execute("SELECT password_hash FROM users").fetchall()
            hashes = [r[0] for r in rows]
            self.assertEqual(len(hashes), 2)
            for stored in hashes:
                self.assertTrue(stored.startswith("pbkdf2_sha256$200000$"))
                self.assertNotIn(PASSWORD, stored)
            self.assertNotEqual(hashes[0].split("$")[3], hashes[1].split("$")[3])   # unique salts


class ChatTests(ServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.alice, ok_a = self.register("alice")
        self.bob, ok_b = self.register("bobby")
        self.general = self.room_id(ok_a, "General")
        self.python = self.room_id(ok_a, "Python")

    def join(self, client: TestClient, room_id: int) -> dict[str, Any]:
        client.send(type="join_room", room_id=room_id)
        return client.expect("joined")

    def test_realtime_message_with_timestamp_and_emoji(self) -> None:
        self.join(self.alice, self.general)
        self.join(self.bob, self.general)
        self.alice.send(type="send_message", room_id=self.general, text="Hello Bob :smile: :nope:")
        got = self.bob.wait(lambda f: f["type"] == "message" and f["message"]["kind"] == "user")
        self.assertEqual(got["message"]["username"], "alice")
        self.assertEqual(got["message"]["text"], "Hello Bob 😄 :nope:")   # unknown shortcode untouched
        self.assertIsInstance(got["message"]["ts"], int)
        echo = self.alice.wait(lambda f: f["type"] == "message" and f["message"]["kind"] == "user")
        self.assertEqual(echo["message"]["id"], got["message"]["id"])

    def test_all_requested_shortcodes_convert(self) -> None:
        from common.emoji import convert_shortcodes
        text = ":smile::heart::thumbsup::laughing::fire::rocket::wave::joy::ok_hand::clap::star::eyes:"
        self.assertEqual(convert_shortcodes(text), "😄❤️👍😆🔥🚀👋😂👌👏⭐👀")

    def test_rooms_are_isolated(self) -> None:
        self.join(self.alice, self.general)
        self.join(self.bob, self.python)
        self.alice.send(type="send_message", room_id=self.general, text="general only")
        self.alice.expect("message", room_id=self.general)
        self.bob.expect_silence("message")

    def test_history_is_loaded_in_order_when_joining(self) -> None:
        self.join(self.alice, self.general)
        for i in range(3):
            self.alice.send(type="send_message", room_id=self.general, text=f"msg {i}")
            self.alice.expect("message", room_id=self.general)
        joined = self.join(self.bob, self.general)
        texts = [m["text"] for m in joined["history"] if m["kind"] == "user"]
        self.assertEqual(texts, ["msg 0", "msg 1", "msg 2"])
        self.assertTrue(joined["new_member"])

    def test_join_and_leave_system_messages(self) -> None:
        self.join(self.alice, self.general)
        self.join(self.bob, self.general)
        note = self.alice.expect("message", room_id=self.general)
        self.assertEqual((note["message"]["kind"], note["message"]["text"], note["message"]["username"]),
                         ("system", "joined", "bobby"))
        self.bob.send(type="leave_room", room_id=self.general)
        self.bob.expect("left")
        left = self.alice.expect("message", room_id=self.general)
        self.assertEqual((left["message"]["kind"], left["message"]["text"]), ("system", "left"))
        self.bob.send(type="send_message", room_id=self.general, text="ghost")
        self.assertEqual(self.bob.expect("error")["code"], "not_found")

    def test_create_room_rules(self) -> None:
        self.alice.send(type="create_room", name="Chess-Club", description="Openings and endgames")
        joined = self.alice.expect("joined")
        self.assertEqual(joined["room"]["name"], "Chess-Club")
        self.assertEqual(joined["room"]["member_count"], 1)
        self.bob.expect("rooms", timeout=3)
        self.alice.send(type="create_room", name="chess-club")
        self.assertEqual(self.alice.expect("error", request="create_room")["code"], "exists")
        self.alice.send(type="create_room", name="no spaces")
        self.assertEqual(self.alice.expect("error", request="create_room")["code"], "validation")

    def test_message_validation(self) -> None:
        self.join(self.alice, self.general)
        self.alice.send(type="send_message", room_id=self.general, text="   ")
        self.assertIn("Type something", self.alice.expect("error")["message"])
        self.alice.send(type="send_message", room_id=self.general, text="x" * 1001)
        self.assertIn("at most", self.alice.expect("error")["message"])

    def test_rate_limit(self) -> None:
        self.join(self.alice, self.general)
        for i in range(12):
            self.alice.send(type="send_message", room_id=self.general, text=f"spam {i}")
        self.assertEqual(self.alice.expect("error", request="send_message")["code"], "rate")

    def test_typing_goes_to_others_only(self) -> None:
        self.join(self.alice, self.general)
        self.join(self.bob, self.general)
        self.alice.send(type="typing", room_id=self.general)
        self.assertEqual(self.bob.expect("typing")["username"], "alice")
        self.alice.expect_silence("typing")

    def test_abrupt_disconnect_updates_presence_and_server_survives(self) -> None:
        self.join(self.alice, self.general)
        self.join(self.bob, self.general)
        self.alice.wait(lambda f: f["type"] == "presence" and all(m["online"] for m in f["members"])
                        and len(f["members"]) == 2)
        self.bob.sock.close()      # no logout, no goodbye
        pres = self.alice.wait(lambda f: f["type"] == "presence"
                               and any(m["username"] == "bobby" and not m["online"] for m in f["members"]))
        bobby = next(m for m in pres["members"] if m["username"] == "bobby")
        self.assertIsNotNone(bobby["last_seen"])
        self.alice.send(type="send_message", room_id=self.general, text="still here")
        self.assertEqual(self.alice.expect("message", room_id=self.general)["message"]["text"], "still here")

    def test_many_clients_receive_broadcast(self) -> None:
        extras = [self.register(f"user{i}")[0] for i in range(8)]
        everyone = [self.alice, self.bob, *extras]
        for c in everyone:
            self.join(c, self.general)
        self.alice.send(type="send_message", room_id=self.general, text="roll call")
        for c in everyone:
            c.wait(lambda f: f["type"] == "message" and f["message"]["text"] == "roll call")


class PersistenceTests(unittest.TestCase):
    def test_messages_and_membership_survive_server_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "persist.db"
            server = ChatServer("127.0.0.1", 0, path)
            port = server.start()
            alice = TestClient(port)
            alice.send(type="register", username="alice", password=PASSWORD)
            ok = alice.expect("auth_ok")
            room = next(r["id"] for r in ok["rooms"] if r["name"] == "General")
            alice.send(type="join_room", room_id=room)
            alice.expect("joined")
            alice.send(type="send_message", room_id=room, text="remember me :rocket:")
            alice.expect("message", room_id=room)
            alice.close()
            server.stop()

            server = ChatServer("127.0.0.1", 0, path)
            port = server.start()
            again = TestClient(port)
            again.send(type="login", username="alice", password=PASSWORD)
            ok = again.expect("auth_ok")
            self.assertTrue(next(r for r in ok["rooms"] if r["id"] == room)["joined"])
            again.send(type="join_room", room_id=room)
            history = again.expect("joined")["history"]
            self.assertIn("remember me 🚀", [m["text"] for m in history])
            again.close()
            server.stop()


if __name__ == "__main__":
    unittest.main()
