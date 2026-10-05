"""VANTA CHAT server: threaded TCP server speaking newline-delimited JSON."""
from __future__ import annotations

import argparse
import collections
import logging
import re
import secrets
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

from common.emoji import convert_shortcodes
from common.protocol import FrameReader, ProtocolError, encode
from common.validation import MAX_DESCRIPTION_LENGTH

from . import auth, config
from .database import Database, DatabaseError, RoomExists, UsernameTaken

log = logging.getLogger("vanta.server")

PUBLIC_REQUESTS = {"register", "login", "resume", "ping"}
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
RATE_LIMIT_MESSAGES = 10
RATE_LIMIT_WINDOW = 5.0
SERVER_ERROR = "Something went wrong on the server. Please try again."


class Session:
    """One connected client socket and its authentication state."""

    def __init__(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        self.sock = sock
        self.addr = addr
        self.username: str | None = None
        self.user_id: int | None = None
        self.joined: set[int] = set()
        self.closed = False
        self.graceful = False
        self._send_lock = threading.Lock()
        self._recent_sends: collections.deque[float] = collections.deque()

    def send(self, payload: dict[str, Any]) -> bool:
        if self.closed:
            return False
        try:
            with self._send_lock:
                self.sock.sendall(encode(payload))
            return True
        except OSError:
            self.close()
            return False

    def error(self, message: str, code: str = "error", request: str | None = None) -> None:
        self.send({"type": "error", "code": code, "message": message, "request": request})

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        for action in (lambda: self.sock.shutdown(socket.SHUT_RDWR), self.sock.close):
            try:
                action()
            except OSError:
                pass

    def allow_message(self) -> bool:
        now = time.monotonic()
        while self._recent_sends and now - self._recent_sends[0] > RATE_LIMIT_WINDOW:
            self._recent_sends.popleft()
        if len(self._recent_sends) >= RATE_LIMIT_MESSAGES:
            return False
        self._recent_sends.append(now)
        return True


class ChatServer:
    def __init__(self, host: str = config.HOST, port: int = config.PORT,
                 db_path: Path | str = config.DB_PATH) -> None:
        self.host = host
        self.port = port
        self.db = Database(db_path)
        self._lock = threading.RLock()
        self._online: dict[str, Session] = {}      # lower-case username -> session
        self._tokens: dict[str, int] = {}          # resume token -> user id
        self._listener: socket.socket | None = None
        self._running = False
        self._dummy_hash = auth.hash_password("not-a-real-password")
        self._handlers: dict[str, Callable[[Session, dict[str, Any]], None]] = {
            "register": self._on_register, "login": self._on_login, "resume": self._on_resume,
            "logout": self._on_logout, "ping": self._on_ping, "list_rooms": self._on_list_rooms,
            "create_room": self._on_create_room, "join_room": self._on_join_room,
            "leave_room": self._on_leave_room, "send_message": self._on_send_message,
            "typing": self._on_typing,
        }

    # -- lifecycle -------------------------------------------------------
    def start(self) -> int:
        """Bind and start accepting in a background thread. Returns the bound port."""
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if sys.platform != "win32":
            # On POSIX this allows quick restarts. On Windows the same option would let a second
            # server bind the same port, hiding the "already running" error, so it is skipped there.
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen(32)
        self._listener = listener
        self.port = listener.getsockname()[1]
        self._running = True
        threading.Thread(target=self._accept_loop, name="accept", daemon=True).start()
        log.info("VANTA CHAT server listening on %s:%d", self.host, self.port)
        return self.port

    def serve_forever(self, already_started: bool = False) -> None:
        if not already_started:
            self.start()
        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            log.info("Shutting down...")
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        if self._listener:
            try:
                self._listener.close()
            except OSError:
                pass
        with self._lock:
            sessions = list(self._online.values())
        for session in sessions:
            session.send({"type": "server_shutdown"})
            session.close()
        self.db.close()

    def _accept_loop(self) -> None:
        assert self._listener is not None
        while self._running:
            try:
                sock, addr = self._listener.accept()
            except OSError:
                break
            threading.Thread(target=self._serve_client, args=(sock, addr),
                             name=f"client-{addr[1]}", daemon=True).start()

    # -- per-client loop -------------------------------------------------
    def _serve_client(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        session = Session(sock, addr)
        sock.settimeout(config.IDLE_TIMEOUT_SECONDS)
        reader = FrameReader(sock)
        log.info("Connection from %s:%d", *addr)
        try:
            while not session.closed:
                frame = reader.read()
                if frame is None:
                    break
                self._dispatch(session, frame)
        except socket.timeout:
            log.info("Closing idle connection %s:%d", *addr)
        except ProtocolError as exc:
            session.error(str(exc), "protocol")
        except OSError:
            pass
        except Exception:  # last resort: never let a thread die silently
            log.exception("Unexpected error in client loop")
        finally:
            self._disconnect(session)

    def _dispatch(self, session: Session, frame: dict[str, Any]) -> None:
        kind = frame["type"]
        handler = self._handlers.get(kind)
        if handler is None:
            session.error("Unknown request.", "protocol", kind)
            return
        if kind not in PUBLIC_REQUESTS and session.user_id is None:
            session.error("Please sign in first.", "auth", kind)
            return
        try:
            handler(session, frame)
        except DatabaseError:
            log.exception("Database error while handling %r", kind)
            session.error("The server could not reach its database. Please try again.", "database", kind)
        except Exception:
            log.exception("Unexpected error while handling %r", kind)
            session.error(SERVER_ERROR, "server", kind)

    # -- authentication --------------------------------------------------
    def _on_register(self, session: Session, frame: dict[str, Any]) -> None:
        if session.user_id is not None:
            return session.error("You are already signed in.", "auth", "register")
        username = str(frame.get("username", "")).strip()
        password = str(frame.get("password", ""))
        problem = auth.validate_username(username) or auth.validate_password(password)
        if problem:
            return session.error(problem, "validation", "register")
        try:
            user = self.db.create_user(username, auth.hash_password(password))
        except UsernameTaken:
            return session.error("That username is already taken. Try another one.", "exists", "register")
        log.info("Registered user %s", user["username"])
        self._complete_login(session, user, request="register")

    def _on_login(self, session: Session, frame: dict[str, Any]) -> None:
        if session.user_id is not None:
            return session.error("You are already signed in.", "auth", "login")
        username = str(frame.get("username", "")).strip()
        password = str(frame.get("password", ""))
        if not username or not password:
            return session.error("Please enter your username and password.", "validation", "login")
        user = self.db.get_user_by_name(username)
        stored = user["password_hash"] if user else self._dummy_hash  # equalise timing
        if not auth.verify_password(password, stored) or not user:
            log.info("Failed login for %r", username[:20])
            return session.error("Incorrect username or password.", "auth", "login")
        self._complete_login(session, user, request="login")

    def _on_resume(self, session: Session, frame: dict[str, Any]) -> None:
        user_id = self._tokens.get(str(frame.get("token", "")))
        user = self.db.get_user_by_id(user_id) if user_id else None
        if not user:
            return session.error("Your session expired. Please sign in again.", "auth", "resume")
        self._complete_login(session, user, request="resume", takeover=True)

    def _complete_login(self, session: Session, user: dict[str, Any], request: str,
                        takeover: bool = False) -> None:
        key = user["username"].lower()
        with self._lock:
            existing = self._online.get(key)
            if existing and existing is not session:
                if not takeover:
                    return session.error("This account is already signed in on another window.",
                                         "auth", request)
                existing.close()
            for token, uid in list(self._tokens.items()):
                if uid == user["id"]:
                    del self._tokens[token]
            token = secrets.token_hex(24)
            self._tokens[token] = user["id"]
            session.user_id = user["id"]
            session.username = user["username"]
            session.joined = self.db.room_ids_for_user(user["id"])
            self._online[key] = session
        session.send({
            "type": "auth_ok", "request": request, "token": token,
            "user": {"username": user["username"], "created_at": user["created_at"]},
            "rooms": self._rooms_payload(session),
        })
        log.info("%s signed in (%s)", user["username"], request)
        self._broadcast_rooms()
        for room_id in session.joined:
            self._broadcast_presence(room_id)

    def _on_logout(self, session: Session, frame: dict[str, Any]) -> None:
        session.graceful = True
        with self._lock:
            for token, uid in list(self._tokens.items()):
                if uid == session.user_id:
                    del self._tokens[token]
        session.send({"type": "bye"})
        session.close()

    def _disconnect(self, session: Session) -> None:
        session.close()
        if session.username is None or not self._running:
            return
        key = session.username.lower()
        with self._lock:
            is_current = self._online.get(key) is session
            if is_current:
                del self._online[key]
        if not is_current:
            return
        try:
            self.db.touch_last_seen(session.user_id)  # type: ignore[arg-type]
        except DatabaseError:
            log.exception("Could not update last_seen")
        log.info("%s disconnected%s", session.username, "" if session.graceful else " (connection lost)")
        self._broadcast_rooms()
        for room_id in session.joined:
            self._broadcast_presence(room_id)

    def _on_ping(self, session: Session, frame: dict[str, Any]) -> None:
        session.send({"type": "pong"})

    # -- rooms -----------------------------------------------------------
    def _on_list_rooms(self, session: Session, frame: dict[str, Any]) -> None:
        session.send({"type": "rooms", "rooms": self._rooms_payload(session)})

    def _on_create_room(self, session: Session, frame: dict[str, Any]) -> None:
        name = str(frame.get("name", "")).strip().lstrip("#")
        description = _CONTROL_CHARS.sub("", str(frame.get("description", ""))).strip()[:MAX_DESCRIPTION_LENGTH]
        problem = auth.validate_room_name(name)
        if problem:
            return session.error(problem, "validation", "create_room")
        try:
            room = self.db.create_room(name, description, session.user_id)  # type: ignore[arg-type]
        except RoomExists:
            return session.error(f"A room named #{name} already exists.", "exists", "create_room")
        log.info("%s created #%s", session.username, room["name"])
        self._join(session, room["id"])

    def _on_join_room(self, session: Session, frame: dict[str, Any]) -> None:
        room_id = frame.get("room_id")
        if not isinstance(room_id, int) or self.db.get_room(room_id) is None:
            return session.error("That room is no longer available.", "not_found", "join_room")
        self._join(session, room_id)

    def _join(self, session: Session, room_id: int) -> None:
        """Make the user a member (if needed) and send them the room with its history."""
        user_id: int = session.user_id  # type: ignore[assignment]
        newly_joined = self.db.add_member(room_id, user_id)
        session.joined.add(room_id)
        if newly_joined:
            notice = self.db.add_message(room_id, user_id, "joined", kind="system")
            self._broadcast_room(room_id, {"type": "message", "room_id": room_id, "message": notice},
                                 exclude=session)
        room = next(r for r in self._rooms_payload(session) if r["id"] == room_id)
        session.send({
            "type": "joined", "room": room,
            "history": self.db.recent_messages(room_id),
            "members": self._members_payload(room_id),
            "new_member": newly_joined,
        })
        if newly_joined:
            self._broadcast_rooms()
            self._broadcast_presence(room_id)

    def _on_leave_room(self, session: Session, frame: dict[str, Any]) -> None:
        room_id = frame.get("room_id")
        if not isinstance(room_id, int) or room_id not in session.joined:
            return session.error("You are not in that room.", "not_found", "leave_room")
        self.db.remove_member(room_id, session.user_id)  # type: ignore[arg-type]
        session.joined.discard(room_id)
        notice = self.db.add_message(room_id, session.user_id, "left", kind="system")  # type: ignore[arg-type]
        self._broadcast_room(room_id, {"type": "message", "room_id": room_id, "message": notice})
        session.send({"type": "left", "room_id": room_id})
        self._broadcast_rooms()
        self._broadcast_presence(room_id)

    # -- messages --------------------------------------------------------
    def _on_send_message(self, session: Session, frame: dict[str, Any]) -> None:
        room_id = frame.get("room_id")
        if not isinstance(room_id, int) or room_id not in session.joined:
            return session.error("Join this room before sending messages.", "not_found", "send_message")
        text = _CONTROL_CHARS.sub("", str(frame.get("text", ""))).strip()
        if not text:
            return session.error("Type something before sending.", "validation", "send_message")
        if len(text) > config.MAX_MESSAGE_LENGTH:
            return session.error(f"Messages can be at most {config.MAX_MESSAGE_LENGTH} characters.",
                                 "validation", "send_message")
        if not session.allow_message():
            return session.error("You are sending messages too quickly. Slow down a little.",
                                 "rate", "send_message")
        message = self.db.add_message(room_id, session.user_id, convert_shortcodes(text))  # type: ignore[arg-type]
        self._broadcast_room(room_id, {"type": "message", "room_id": room_id, "message": message})

    def _on_typing(self, session: Session, frame: dict[str, Any]) -> None:
        room_id = frame.get("room_id")
        if isinstance(room_id, int) and room_id in session.joined:
            self._broadcast_room(room_id, {"type": "typing", "room_id": room_id,
                                           "username": session.username}, exclude=session)

    # -- payload builders and broadcasts ---------------------------------
    def _snapshot(self) -> list[Session]:
        with self._lock:
            return list(self._online.values())

    def _rooms_payload(self, session: Session) -> list[dict[str, Any]]:
        online_counts: collections.Counter[int] = collections.Counter()
        for other in self._snapshot():
            online_counts.update(other.joined)
        return [{**room, "online_count": online_counts[room["id"]], "joined": room["id"] in session.joined}
                for room in self.db.list_rooms()]

    def _members_payload(self, room_id: int) -> list[dict[str, Any]]:
        with self._lock:
            online = {name for name, s in self._online.items() if room_id in s.joined}
        return [{"username": m["username"], "last_seen": m["last_seen"],
                 "online": m["username"].lower() in online} for m in self.db.members(room_id)]

    def _broadcast_room(self, room_id: int, payload: dict[str, Any], exclude: Session | None = None) -> None:
        for session in self._snapshot():
            if session is not exclude and room_id in session.joined:
                session.send(payload)

    def _broadcast_presence(self, room_id: int) -> None:
        try:
            members = self._members_payload(room_id)
        except DatabaseError:
            log.exception("Could not build presence")
            return
        self._broadcast_room(room_id, {"type": "presence", "room_id": room_id, "members": members})

    def _broadcast_rooms(self) -> None:
        try:
            for session in self._snapshot():
                session.send({"type": "rooms", "rooms": self._rooms_payload(session)})
        except DatabaseError:
            log.exception("Could not broadcast rooms")


def main() -> None:
    parser = argparse.ArgumentParser(description="VANTA CHAT server")
    parser.add_argument("--host", default=config.HOST, help=f"interface to bind (default {config.HOST})")
    parser.add_argument("--port", type=int, default=config.PORT, help=f"port (default {config.PORT})")
    parser.add_argument("--db", default=str(config.DB_PATH), help="SQLite database file")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")
    try:
        server = ChatServer(args.host, args.port, args.db)
        server.start()
    except OSError as exc:
        log.error("Could not start the server on %s:%d (%s). Is another copy already running?",
                  args.host, args.port, exc.strerror or exc)
        raise SystemExit(1)
    except DatabaseError as exc:
        log.error("Could not open the database: %s", exc)
        raise SystemExit(1)
    print("\n  VANTA CHAT server  -  press Ctrl+C to stop\n")
    server.serve_forever(already_started=True)


if __name__ == "__main__":
    main()
