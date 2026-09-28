"""
validators.py
==============
Pure, GUI-independent validation functions for VaultForge.

Every function here raises ``ValidationError`` with a clear,
human-readable message on failure, and returns ``None`` (implicitly)
on success. Keeping validation separate from the GUI means it can be
unit-tested directly and reused if the GUI layer ever changes.
"""

from __future__ import annotations

from config import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


class ValidationError(Exception):
    """Raised when user-supplied generator settings are invalid."""


def validate_length(length: int, min_len: int = MIN_PASSWORD_LENGTH,
                     max_len: int = MAX_PASSWORD_LENGTH) -> None:
    """Ensure the requested password length is a sane integer in range.

    Raises:
        ValidationError: if length is not an int, or out of range.
    """
    if not isinstance(length, int) or isinstance(length, bool):
        raise ValidationError("Password length must be a whole number.")

    if length < min_len:
        raise ValidationError(
            f"Password length must be at least {min_len} characters."
        )

    if length > max_len:
        raise ValidationError(
            f"Password length cannot exceed {max_len} characters."
        )


def validate_character_selection(use_upper: bool, use_lower: bool,
                                  use_digits: bool, use_symbols: bool) -> None:
    """Ensure at least two character categories have been selected.

    Raises:
        ValidationError: if fewer than two categories are selected.
    """
    selected_count = sum([use_upper, use_lower, use_digits, use_symbols])

    if selected_count == 0:
        raise ValidationError(
            "Select at least two character types (e.g. uppercase and numbers)."
        )

    if selected_count == 1:
        raise ValidationError(
            "At least two character types must be selected for a secure password."
        )


def validate_settings(length: int, use_upper: bool, use_lower: bool,
                       use_digits: bool, use_symbols: bool) -> None:
    """Run all validations required before generating a password.

    Raises:
        ValidationError: on any invalid setting, with a specific message.
    """
    validate_length(length)
    validate_character_selection(use_upper, use_lower, use_digits, use_symbols)
