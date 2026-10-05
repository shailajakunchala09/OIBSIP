"""Emoji shortcode support."""
from __future__ import annotations

import re

SHORTCODES: dict[str, str] = {
    "smile": "😄", "heart": "❤️", "thumbsup": "👍", "laughing": "😆",
    "fire": "🔥", "rocket": "🚀", "wave": "👋", "joy": "😂",
    "ok_hand": "👌", "clap": "👏", "star": "⭐", "eyes": "👀",
    "tada": "🎉", "thinking": "🤔", "pray": "🙏", "100": "💯",
}

# Shown in the picker, in this order.
PICKER_ORDER = list(SHORTCODES)

_PATTERN = re.compile(r":([a-z0-9_]+):")


def convert_shortcodes(text: str) -> str:
    """Replace known :shortcodes: with Unicode emoji; unknown ones are left alone."""
    return _PATTERN.sub(lambda m: SHORTCODES.get(m.group(1), m.group(0)), text)
