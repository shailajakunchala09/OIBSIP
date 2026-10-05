"""SQLite storage layer. The server is the only process that opens the database."""
from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    created_at    INTEGER NOT NULL,
    last_seen     INTEGER
);
CREATE TABLE IF NOT EXISTS rooms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    description TEXT    NOT NULL DEFAULT '',
    created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at  INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS room_members (
    room_id   INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at INTEGER NOT NULL,
    PRIMARY KEY (room_id, user_id)
);
CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id    INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind       TEXT    NOT NULL DEFAULT 'user' CHECK (kind IN ('user', 'system')),
    body       TEXT    NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_room_id ON messages(room_id, id);
CREATE INDEX IF NOT EXISTS idx_members_user ON room_members(user_id);
"""


class DatabaseError(Exception):
    """Wraps sqlite3 errors so callers never see driver internals."""


class UsernameTaken(DatabaseError):
    pass


class RoomExists(DatabaseError):
    pass


class Database:
    def __init__(self, path: Path | str = config.DB_PATH) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        try:
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.executescript(SCHEMA)
            self._seed_default_rooms()
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- helpers ---------------------------------------------------------
    def _query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        try:
            with self._lock:
                return self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        try:
            with self._lock, self._conn:
                return self._conn.execute(sql, params)
        except sqlite3.IntegrityError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(str(exc)) from exc

    def _seed_default_rooms(self) -> None:
        now = int(time.time())
        with self._conn:
            for name, description in config.DEFAULT_ROOMS:
                self._conn.execute(
                    "INSERT OR IGNORE INTO rooms (name, description, created_at) VALUES (?, ?, ?)",
                    (name, description, now),
                )

    # -- users -----------------------------------------------------------
    def create_user(self, username: str, password_hash: str) -> dict[str, Any]:
        try:
            cur = self._execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, int(time.time())),
            )
        except sqlite3.IntegrityError as exc:
            raise UsernameTaken(username) from exc
        return self.get_user_by_id(cur.lastrowid)  # type: ignore[return-value]

    def get_user_by_name(self, username: str) -> dict[str, Any] | None:
        rows = self._query("SELECT * FROM users WHERE username = ?", (username,))
        return dict(rows[0]) if rows else None

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        rows = self._query("SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(rows[0]) if rows else None

    def touch_last_seen(self, user_id: int) -> None:
        self._execute("UPDATE users SET last_seen = ? WHERE id = ?", (int(time.time()), user_id))

    # -- rooms -----------------------------------------------------------
    def create_room(self, name: str, description: str, user_id: int) -> dict[str, Any]:
        try:
            cur = self._execute(
                "INSERT INTO rooms (name, description, created_by, created_at) VALUES (?, ?, ?, ?)",
                (name, description, user_id, int(time.time())),
            )
        except sqlite3.IntegrityError as exc:
            raise RoomExists(name) from exc
        return self.get_room(cur.lastrowid)  # type: ignore[return-value]

    def get_room(self, room_id: int) -> dict[str, Any] | None:
        rows = self._query("SELECT * FROM rooms WHERE id = ?", (room_id,))
        return dict(rows[0]) if rows else None

    def list_rooms(self) -> list[dict[str, Any]]:
        rows = self._query(
            """SELECT r.id, r.name, r.description,
                      (SELECT COUNT(*) FROM room_members m WHERE m.room_id = r.id) AS member_count
               FROM rooms r ORDER BY r.name COLLATE NOCASE"""
        )
        return [dict(r) for r in rows]

    # -- membership ------------------------------------------------------
    def add_member(self, room_id: int, user_id: int) -> bool:
        """Return True when the user was not a member before."""
        cur = self._execute(
            "INSERT OR IGNORE INTO room_members (room_id, user_id, joined_at) VALUES (?, ?, ?)",
            (room_id, user_id, int(time.time())),
        )
        return cur.rowcount == 1

    def remove_member(self, room_id: int, user_id: int) -> bool:
        cur = self._execute(
            "DELETE FROM room_members WHERE room_id = ? AND user_id = ?", (room_id, user_id)
        )
        return cur.rowcount == 1

    def is_member(self, room_id: int, user_id: int) -> bool:
        return bool(
            self._query(
                "SELECT 1 FROM room_members WHERE room_id = ? AND user_id = ?", (room_id, user_id)
            )
        )

    def room_ids_for_user(self, user_id: int) -> set[int]:
        rows = self._query("SELECT room_id FROM room_members WHERE user_id = ?", (user_id,))
        return {r["room_id"] for r in rows}

    def members(self, room_id: int) -> list[dict[str, Any]]:
        rows = self._query(
            """SELECT u.username, u.last_seen FROM room_members m
               JOIN users u ON u.id = m.user_id
               WHERE m.room_id = ? ORDER BY u.username COLLATE NOCASE""",
            (room_id,),
        )
        return [dict(r) for r in rows]

    # -- messages --------------------------------------------------------
    def add_message(self, room_id: int, user_id: int, body: str, kind: str = "user") -> dict[str, Any]:
        now = int(time.time())
        cur = self._execute(
            "INSERT INTO messages (room_id, user_id, kind, body, created_at) VALUES (?, ?, ?, ?, ?)",
            (room_id, user_id, kind, body, now),
        )
        rows = self._query(
            """SELECT m.id, m.kind, m.body AS text, m.created_at AS ts, u.username
               FROM messages m JOIN users u ON u.id = m.user_id WHERE m.id = ?""",
            (cur.lastrowid,),
        )
        return dict(rows[0])

    def recent_messages(self, room_id: int, limit: int = config.HISTORY_LIMIT) -> list[dict[str, Any]]:
        rows = self._query(
            """SELECT m.id, m.kind, m.body AS text, m.created_at AS ts, u.username
               FROM messages m JOIN users u ON u.id = m.user_id
               WHERE m.room_id = ? ORDER BY m.id DESC LIMIT ?""",
            (room_id, limit),
        )
        return [dict(r) for r in reversed(rows)]
