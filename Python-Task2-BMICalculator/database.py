"""
All SQLite access lives here so the desktop app and the Flask app talk
to the same schema through the same functions instead of writing raw
queries in two places.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import List, Optional

from config import DB_PATH, DATA_DIR


class DatabaseError(Exception):
    """Raised for any storage failure, wrapping the underlying
    sqlite3 error so callers never need to catch sqlite3 directly."""


def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    try:
        with _connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bmi_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    height REAL NOT NULL,
                    bmi REAL NOT NULL,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
                """
            )
            conn.commit()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not set up the database: {exc}") from exc


@contextmanager
def _connect(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def add_user(name: str, db_path: str = DB_PATH) -> int:
    try:
        with _connect(db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO users (name) VALUES (?)", (name,)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # name already taken - fetch and return the existing id instead
        # of treating this as a hard failure
        existing = get_user_by_name(name, db_path)
        if existing:
            return existing["id"]
        raise DatabaseError(f"A user named '{name}' already exists")
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not add user: {exc}") from exc


def get_user_by_name(name: str, db_path: str = DB_PATH) -> Optional[sqlite3.Row]:
    try:
        with _connect(db_path) as conn:
            return conn.execute(
                "SELECT * FROM users WHERE name = ?", (name,)
            ).fetchone()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not look up user: {exc}") from exc


def get_users(db_path: str = DB_PATH) -> List[sqlite3.Row]:
    try:
        with _connect(db_path) as conn:
            return conn.execute("SELECT * FROM users ORDER BY name").fetchall()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not load users: {exc}") from exc


def add_record(
    user_id: int, weight: float, height: float, bmi: float, category: str,
    db_path: str = DB_PATH,
) -> int:
    try:
        with _connect(db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO bmi_records (user_id, weight, height, bmi, category)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, weight, height, bmi, category),
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not save the record: {exc}") from exc


def get_records(user_id: int, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    try:
        with _connect(db_path) as conn:
            return conn.execute(
                """
                SELECT * FROM bmi_records
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id,),
            ).fetchall()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not load history: {exc}") from exc


def delete_record(record_id: int, db_path: str = DB_PATH) -> bool:
    try:
        with _connect(db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM bmi_records WHERE id = ?", (record_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not delete record: {exc}") from exc


def get_stats(user_id: int, db_path: str = DB_PATH) -> dict:
    """Small summary used on both the desktop analytics tab and the
    web analytics page - latest/previous/highest/lowest BMI plus count."""
    records = get_records(user_id, db_path)
    if not records:
        return {
            "latest": None,
            "previous": None,
            "highest": None,
            "lowest": None,
            "count": 0,
        }

    bmi_values = [row["bmi"] for row in records]
    return {
        "latest": records[0]["bmi"],
        "previous": records[1]["bmi"] if len(records) > 1 else None,
        "highest": max(bmi_values),
        "lowest": min(bmi_values),
        "count": len(records),
    }
