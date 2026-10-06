"""SkyPulse – Smart Weather Dashboard (OASIS INFOBYTE Python Programming Internship, Task 4)."""
from __future__ import annotations

import ctypes
import logging
import sys


def _enable_hidpi() -> None:
    """Ask Windows for real pixels so text stays crisp on scaled displays."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    _enable_hidpi()
    from config import load_settings
    from ui.main_window import MainWindow

    MainWindow(load_settings()).mainloop()


if __name__ == "__main__":
    main()
