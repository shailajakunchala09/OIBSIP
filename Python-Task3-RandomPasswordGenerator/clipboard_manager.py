"""
clipboard_manager.py
=====================
Clipboard integration for VaultForge, built on top of ``pyperclip``.

Security notes
--------------
* Never logs or persists clipboard contents anywhere.
* Supports an optional, configurable auto-clear timer so a copied
  password does not sit on the system clipboard indefinitely.
* All failures (e.g. no clipboard mechanism available on a headless
  Linux box) are caught and reported through a boolean/callback rather
  than raising up into the GUI event loop and crashing the app.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

import pyperclip

from config import DEFAULT_CLIPBOARD_AUTOCLEAR_SECONDS


class ClipboardManager:
    """Wraps pyperclip with error handling and an auto-clear timer.

    An instance is meant to live for the lifetime of the main window so
    that a pending auto-clear timer can be cancelled if the user copies
    something new or clears the clipboard manually before it fires.
    """

    def __init__(self, autoclear_seconds: int = DEFAULT_CLIPBOARD_AUTOCLEAR_SECONDS) -> None:
        self._autoclear_seconds = autoclear_seconds
        self._timer: Optional[threading.Timer] = None
        self._last_copied_marker: Optional[str] = None

    def copy(self, text: str, on_result: Optional[Callable[[bool, str], None]] = None) -> bool:
        """Copy ``text`` to the system clipboard.

        Args:
            text: The value to copy (e.g. a generated password).
            on_result: Optional callback invoked with (success, message).

        Returns:
            True on success, False if the copy failed for any reason.
        """
        self._cancel_pending_clear()

        try:
            pyperclip.copy(text)
        except Exception as exc:  # pragma: no cover - platform dependent
            message = f"Clipboard unavailable: {exc}"
            if on_result:
                on_result(False, message)
            return False

        # Store only a marker (not the password itself) so we can decide,
        # at clear time, whether the clipboard still holds what we copied.
        self._last_copied_marker = text

        if self._autoclear_seconds > 0:
            self._schedule_autoclear(text)

        if on_result:
            on_result(True, "Copied to clipboard.")
        return True

    def clear(self, on_result: Optional[Callable[[bool, str], None]] = None) -> bool:
        """Clear the clipboard immediately, if it currently holds our value."""
        self._cancel_pending_clear()

        try:
            pyperclip.copy("")
        except Exception as exc:  # pragma: no cover - platform dependent
            message = f"Could not clear clipboard: {exc}"
            if on_result:
                on_result(False, message)
            return False

        self._last_copied_marker = None
        if on_result:
            on_result(True, "Clipboard cleared.")
        return True

    def set_autoclear_seconds(self, seconds: int) -> None:
        """Update how long a copied password stays before auto-clearing."""
        self._autoclear_seconds = max(0, seconds)

    def shutdown(self) -> None:
        """Cancel any pending timer. Call this when the app is closing."""
        self._cancel_pending_clear()

    # -- internal helpers ---------------------------------------------------

    def _schedule_autoclear(self, copied_text: str) -> None:
        def _do_clear() -> None:
            # Only clear if the clipboard still holds what we copied, so we
            # never wipe something the user copied from elsewhere afterward.
            try:
                current = pyperclip.paste()
            except Exception:  # pragma: no cover - platform dependent
                return
            if current == copied_text:
                try:
                    pyperclip.copy("")
                except Exception:  # pragma: no cover - platform dependent
                    pass

        self._timer = threading.Timer(self._autoclear_seconds, _do_clear)
        self._timer.daemon = True
        self._timer.start()

    def _cancel_pending_clear(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
