"""
history.py
==========
Session-only password history for VaultForge.

IMPORTANT: This module keeps history purely in process memory (a Python
list). Nothing here is ever written to disk, a database, or any other
persistent store. History is lost the moment the application exits, by
design, per the OASIS Task 3 requirement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from config import MAX_HISTORY_ENTRIES


@dataclass
class HistoryEntry:
    """One in-memory record of a generated password."""

    password: str
    strength: str
    created_at: datetime = field(default_factory=datetime.now)
    revealed: bool = False

    def masked(self) -> str:
        """Return a fixed-width masked representation for display."""
        return "•" * min(len(self.password), 24)

    def timestamp_label(self) -> str:
        return self.created_at.strftime("%H:%M:%S")


class SessionHistory:
    """In-memory, fixed-size history of the most recent generated passwords.

    Only the most recent ``MAX_HISTORY_ENTRIES`` entries are kept; older
    entries are dropped automatically. Nothing is ever persisted.
    """

    def __init__(self, max_entries: int = MAX_HISTORY_ENTRIES) -> None:
        self._max_entries = max_entries
        self._entries: list[HistoryEntry] = []

    @property
    def entries(self) -> list[HistoryEntry]:
        """Most-recent-first view of current history entries."""
        return list(self._entries)

    def add(self, password: str, strength: str) -> HistoryEntry:
        """Record a newly generated password at the front of the history."""
        entry = HistoryEntry(password=password, strength=strength)
        self._entries.insert(0, entry)
        del self._entries[self._max_entries:]
        return entry

    def remove(self, entry: HistoryEntry) -> None:
        """Remove a single entry from history, if present."""
        if entry in self._entries:
            self._entries.remove(entry)

    def clear(self) -> None:
        """Discard all history entries immediately."""
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
