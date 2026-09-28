"""
app.py
======
Entry point for VaultForge - Secure Password Studio.

Run with:
    python app.py

This module only wires up the Tk root window and the MainWindow
controller; all business logic lives in the dedicated modules
(password_generator, strength_analyzer, validators, clipboard_manager,
history) so it can be tested independently of the GUI.
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

from ui.main_window import MainWindow


def main() -> int:
    root = tk.Tk()
    try:
        MainWindow(root)
    except Exception as exc:  # pragma: no cover - top-level safety net
        # Never let a startup error crash silently with no feedback.
        try:
            messagebox.showerror("VaultForge — Startup Error", str(exc))
        except Exception:
            print(f"VaultForge failed to start: {exc}", file=sys.stderr)
        return 1

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
