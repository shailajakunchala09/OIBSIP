"""Server configuration constants."""
from pathlib import Path

from common.protocol import DEFAULT_HOST as HOST, DEFAULT_PORT as PORT  # noqa: F401
from common.validation import MAX_DESCRIPTION_LENGTH, MAX_MESSAGE_LENGTH  # noqa: F401

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "vanta_chat.db"

HISTORY_LIMIT = 100          # messages sent when a room is opened
IDLE_TIMEOUT_SECONDS = 45    # clients ping every 15 s; silence beyond this = dead

PBKDF2_ITERATIONS = 200_000

DEFAULT_ROOMS = [
    ("General", "Everyone starts here. Say hello."),
    ("Python", "Questions, snippets and code reviews."),
    ("Technology", "Gadgets, tools and tech news."),
    ("Random", "Anything that does not fit elsewhere."),
]
