"""Input rules shared by the server (authoritative) and the client (instant feedback)."""
from __future__ import annotations

import re

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_]{3,20}")
ROOM_NAME_PATTERN = re.compile(r"[A-Za-z0-9_-]{2,24}")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_MESSAGE_LENGTH = 1000
MAX_DESCRIPTION_LENGTH = 80


def validate_username(username: str) -> str | None:
    """Return a human-friendly error message, or None when the value is acceptable."""
    if not username:
        return "Please enter a username."
    if not USERNAME_PATTERN.fullmatch(username):
        return "Usernames are 3-20 characters: letters, numbers and underscores only."
    return None


def validate_password(password: str) -> str | None:
    if not password:
        return "Please enter a password."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Password must be at most {MAX_PASSWORD_LENGTH} characters."
    return None


def validate_room_name(name: str) -> str | None:
    if not name:
        return "Please enter a room name."
    if not ROOM_NAME_PATTERN.fullmatch(name):
        return "Room names are 2-24 characters: letters, numbers, '-' and '_' only."
    return None
