"""
password_generator.py
======================
Core, GUI-independent password generation logic for VaultForge.

Security notes
--------------
* Uses the ``secrets`` module exclusively for all randomness decisions
  (character choice AND shuffling). ``random`` is never imported or used
  anywhere in this module, because it is not cryptographically secure.
* Guarantees at least one character from every *selected* category,
  satisfying the "must contain every selected type" requirement, without
  making the guaranteed characters predictable in position (the final
  string is securely shuffled after assembly).
* Never logs, prints, or persists generated passwords anywhere.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from config import (
    AMBIGUOUS_CHARS,
    DIGITS,
    LOWERCASE,
    SYMBOLS,
    UPPERCASE,
)
from validators import validate_settings


@dataclass(frozen=True)
class GeneratorSettings:
    """Immutable snapshot of the options used to generate one password."""

    length: int
    use_upper: bool
    use_lower: bool
    use_digits: bool
    use_symbols: bool
    exclude_ambiguous: bool = False


class PasswordGenerationError(Exception):
    """Raised when a password cannot be generated from the given settings."""


def _build_category_pools(settings: GeneratorSettings) -> list[str]:
    """Return the list of character pools for every *selected* category.

    Ambiguous characters are stripped from each pool individually so a
    category is never accidentally emptied by the exclusion filter.
    """
    pools: list[str] = []

    def strip_ambiguous(pool: str) -> str:
        if not settings.exclude_ambiguous:
            return pool
        return "".join(ch for ch in pool if ch not in AMBIGUOUS_CHARS)

    if settings.use_upper:
        pools.append(strip_ambiguous(UPPERCASE))
    if settings.use_lower:
        pools.append(strip_ambiguous(LOWERCASE))
    if settings.use_digits:
        pools.append(strip_ambiguous(DIGITS))
    if settings.use_symbols:
        pools.append(strip_ambiguous(SYMBOLS))

    # Defensive check: ambiguous-character stripping should never be able to
    # empty a whole category pool given the current AMBIGUOUS_CHARS set, but
    # we guard against it explicitly rather than trusting that assumption.
    empty_pools = [p for p in pools if len(p) == 0]
    if empty_pools:
        raise PasswordGenerationError(
            "One of the selected character categories has no usable "
            "characters left after excluding ambiguous characters."
        )

    return pools


def generate_password(settings: GeneratorSettings) -> str:
    """Generate a single cryptographically secure password.

    Args:
        settings: The validated generator configuration to use.

    Returns:
        A password string of exactly ``settings.length`` characters that
        contains at least one character from every selected category.

    Raises:
        ValidationError: if the settings fail validation.
        PasswordGenerationError: if a password cannot be built from the
            resulting character pools (e.g. all pools ended up empty).
    """
    validate_settings(
        settings.length,
        settings.use_upper,
        settings.use_lower,
        settings.use_digits,
        settings.use_symbols,
    )

    pools = _build_category_pools(settings)
    combined_pool = "".join(pools)

    if not combined_pool:
        raise PasswordGenerationError("No characters available to build a password.")

    # Step 1: guarantee one securely-chosen character from every selected
    # category so the password always satisfies every chosen requirement.
    required_chars = [secrets.choice(pool) for pool in pools]

    # Step 2: fill the remaining length from the combined pool.
    remaining = settings.length - len(required_chars)
    if remaining < 0:
        # Should not happen because validate_length enforces a sane minimum,
        # but guard against a future misuse of this function directly.
        raise PasswordGenerationError(
            "Password length is too short for the number of selected "
            "character categories."
        )

    filler_chars = [secrets.choice(combined_pool) for _ in range(remaining)]

    password_chars = required_chars + filler_chars

    # Step 3: securely shuffle so the guaranteed characters are not always
    # clustered at the start of the string. secrets.SystemRandom() is backed
    # by os.urandom and is safe to use for shuffling, unlike random.shuffle.
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def contains_all_required_categories(password: str, settings: GeneratorSettings) -> bool:
    """Verify a generated password actually satisfies every selected rule.

    Used internally and by the test-suite as a defense-in-depth check —
    generation should always satisfy this, but we verify rather than assume.
    """
    if settings.use_upper and not any(c in UPPERCASE for c in password):
        return False
    if settings.use_lower and not any(c in LOWERCASE for c in password):
        return False
    if settings.use_digits and not any(c in DIGITS for c in password):
        return False
    if settings.use_symbols and not any(c in SYMBOLS for c in password):
        return False
    return True
