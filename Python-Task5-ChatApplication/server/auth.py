"""Password hashing. Validation rules live in common/validation.py (re-exported here)."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from common.validation import validate_password, validate_room_name, validate_username  # noqa: F401

from . import config


def hash_password(password: str, iterations: int = config.PBKDF2_ITERATIONS) -> str:
    """Return 'pbkdf2_sha256$iterations$salt_hex$hash_hex' using a fresh random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)
