"""
config.py
=========
Central configuration for VaultForge - Secure Password Studio.

Holds character sets, length limits, preset definitions, and other
constants shared across the application. Keeping this in one place
avoids magic strings/numbers scattered through the codebase.
"""

from __future__ import annotations

import string
from dataclasses import dataclass

# --------------------------------------------------------------------------
# Character pools
# --------------------------------------------------------------------------

LOWERCASE: str = string.ascii_lowercase
UPPERCASE: str = string.ascii_uppercase
DIGITS: str = string.digits
SYMBOLS: str = "!@#$%^&*()-_=+[]{}|;:,.<>?/~"

# Characters that are commonly confused with one another when displayed in
# certain fonts (zero vs capital O, lowercase l vs capital I vs one, etc.).
AMBIGUOUS_CHARS: str = "0O1lI|`'\"iL"

# --------------------------------------------------------------------------
# Length constraints
# --------------------------------------------------------------------------

MIN_PASSWORD_LENGTH: int = 8
MAX_PASSWORD_LENGTH: int = 128
DEFAULT_PASSWORD_LENGTH: int = 16

# --------------------------------------------------------------------------
# History
# --------------------------------------------------------------------------

MAX_HISTORY_ENTRIES: int = 5

# --------------------------------------------------------------------------
# Clipboard
# --------------------------------------------------------------------------

DEFAULT_CLIPBOARD_AUTOCLEAR_SECONDS: int = 30

# --------------------------------------------------------------------------
# Presets
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PasswordPreset:
    """A named, pre-configured combination of generator settings."""

    name: str
    length: int
    use_upper: bool
    use_lower: bool
    use_digits: bool
    use_symbols: bool
    exclude_ambiguous: bool
    description: str = ""


PRESETS: dict[str, PasswordPreset] = {
    "Quick Secure": PasswordPreset(
        name="Quick Secure",
        length=12,
        use_upper=True,
        use_lower=True,
        use_digits=True,
        use_symbols=False,
        exclude_ambiguous=True,
        description="Fast, everyday-strength password for low-risk accounts.",
    ),
    "Strong": PasswordPreset(
        name="Strong",
        length=16,
        use_upper=True,
        use_lower=True,
        use_digits=True,
        use_symbols=True,
        exclude_ambiguous=True,
        description="Balanced strength suited to most sensitive accounts.",
    ),
    "Maximum Security": PasswordPreset(
        name="Maximum Security",
        length=24,
        use_upper=True,
        use_lower=True,
        use_digits=True,
        use_symbols=True,
        exclude_ambiguous=False,
        description="Maximum entropy for critical or high-value accounts.",
    ),
}

CUSTOM_PRESET_NAME = "Custom"

# --------------------------------------------------------------------------
# Strength thresholds (bits of entropy)
# --------------------------------------------------------------------------

ENTROPY_WEAK_MAX: float = 35.0
ENTROPY_MEDIUM_MAX: float = 60.0
ENTROPY_STRONG_MAX: float = 80.0
# Anything above ENTROPY_STRONG_MAX is considered "Very Strong".

# --------------------------------------------------------------------------
# Application metadata
# --------------------------------------------------------------------------

APP_NAME: str = "VaultForge"
APP_SUBTITLE: str = "Secure Password Studio"
APP_TAGLINE: str = "Generate stronger credentials with confidence."
APP_VERSION: str = "1.0.0"
