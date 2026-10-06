"""Input validation for the search field."""
from __future__ import annotations

import re

from errors import ValidationError

MAX_CITY_LENGTH = 100
_ALLOWED_PUNCTUATION = set(" .,'’-")


def validate_city(raw: str | None) -> str:
    """Return a cleaned city query or raise :class:`ValidationError`.

    Accepts unicode letters, spaces and ``. , ' -`` so inputs such as
    ``"São Paulo"``, ``"St. John's"`` or ``"Paris, FR"`` pass.
    """
    if raw is None or not raw.strip():
        raise ValidationError("Please enter a city name before searching.")

    city = re.sub(r"\s+", " ", raw.strip())

    if len(city) > MAX_CITY_LENGTH:
        raise ValidationError(f"City names can be at most {MAX_CITY_LENGTH} characters long.")

    bad = sorted({c for c in city if not (c.isalpha() or c in _ALLOWED_PUNCTUATION)})
    if bad:
        shown = " ".join(bad[:5])
        raise ValidationError(
            f"“{shown}” isn't allowed in a city name. Use letters, spaces, commas, hyphens or apostrophes."
        )

    if sum(c.isalpha() for c in city) < 2:
        raise ValidationError("Please enter at least two letters.")

    return city
