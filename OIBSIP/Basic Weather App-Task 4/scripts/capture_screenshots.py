"""Capture the README screenshots from the *real* running SkyPulse app.

Usage (from the project folder, with a valid key in .env and internet access):

    python scripts/capture_screenshots.py [--city London] [--error-city Zzxqwvv]

It launches the application, drives it through each state using the real
OpenWeatherMap API, and saves 01…09 PNGs into ./screenshots. Requires Pillow's
ImageGrab (Windows/macOS, or Linux with an X display).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import ImageGrab  # noqa: E402

from app import _enable_hidpi  # noqa: E402
from config import SCREENSHOT_DIR, load_settings  # noqa: E402
from storage import Preferences  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


def grab(win, widget=None, name="shot.png", pad=0):
    win.update()
    time.sleep(0.25)
    if widget is None:
        widget = win
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    box = (x - pad, y - pad, x + widget.winfo_width() + pad, y + widget.winfo_height() + pad)
    image = ImageGrab.grab(bbox=box)
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    image.save(SCREENSHOT_DIR / name)
    print("saved", name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="London", help="city used for the dashboard shots")
    ap.add_argument("--error-city", default="Zzxqwvv", help="a name the API will not find")
    args = ap.parse_args()

    _enable_hidpi()
    settings = load_settings()
    if not settings.has_api_key:
        sys.exit("Set OPENWEATHER_API_KEY in .env first — screenshots must come from live data.")

    # isolated preferences so your own favourites don't appear in the images
    import tempfile
    prefs = Preferences(Path(tempfile.mkdtemp()) / "preferences.json")
    prefs.theme = "dark"
    win = MainWindow(settings, prefs=prefs)
    win.attributes("-topmost", True)
    sh = win.winfo_screenheight()
    win.geometry(f"{int(win.winfo_screenwidth() * 0.86)}x{min(int(sh * 0.94), 1100)}+20+10")
    win.update()
    dash = win.dashboard

    win.search_bar.set_text(args.city)
    win.search()
    win.wait_idle()
    if win.report is None:
        sys.exit(f"Search failed: {getattr(win.error.err, 'message', 'unknown error')}")

    grab(win, win, "08-dark-theme.png")
    grab(win, win, "01-dashboard.png")
    grab(win, dash.hero, "02-current-weather.png", pad=6)
    grab(win, dash.hour_frame, "03-hourly-forecast.png", pad=6)
    grab(win, dash.day_frame, "04-five-day-forecast.png", pad=6)

    win.set_units("imperial")
    win.update()
    grab(win, win, "05-unit-toggle.png")
    win.set_units("metric")

    win.toggle_theme()
    win.update()
    grab(win, win, "07-light-theme.png")
    win.toggle_theme()

    win.search_bar.set_text(args.error_city)
    win.search()
    win.wait_idle()
    grab(win, win, "06-error-state.png")

    win.use_my_location()
    win.wait_idle()
    if not win.dashboard.winfo_ismapped():
        print("Location detection failed here — 09-location-detection.png not captured.")
    else:
        grab(win, win, "09-location-detection.png")
    win.destroy()


if __name__ == "__main__":
    main()
