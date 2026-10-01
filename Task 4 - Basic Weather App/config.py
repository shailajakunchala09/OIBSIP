"""Application configuration.

The OpenWeatherMap API key is read from the ``OPENWEATHER_API_KEY`` environment
variable (optionally loaded from a local ``.env`` file). It is never stored in
source code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ICON_DIR = ASSETS_DIR / "weather_icons"
SCREENSHOT_DIR = BASE_DIR / "screenshots"

APP_NAME = "SkyPulse"
APP_TITLE = "SkyPulse – Smart Weather Dashboard"
APP_TAGLINE = "Real-time weather intelligence"
APP_VERSION = "1.0.0"

API_KEY_ENV = "OPENWEATHER_API_KEY"
PLACEHOLDER_KEYS = {"", "your_api_key_here", "your-api-key-here", "changeme", "none"}

DEFAULT_CITIES = ("London", "Tokyo", "New York", "Sydney")


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the weather service."""

    api_key: str
    base_url: str = "https://api.openweathermap.org/data/2.5"
    timeout: tuple = (5.0, 10.0)  # (connect, read) seconds

    @property
    def has_api_key(self) -> bool:
        return self.api_key.strip().lower() not in PLACEHOLDER_KEYS


def load_settings(env_file: Path | str | None = None) -> Settings:
    """Load settings from ``.env`` (if present) and the process environment."""
    load_dotenv(env_file or BASE_DIR / ".env")
    return Settings(api_key=os.getenv(API_KEY_ENV, "").strip())
