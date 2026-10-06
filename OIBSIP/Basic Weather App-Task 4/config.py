import os
import sys
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv


# ---------------------------------------------------------
# Application information
# ---------------------------------------------------------

APP_NAME = "SkyPulse"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Your Weather, At a Glance"
APP_TITLE = f"{APP_NAME} - {APP_TAGLINE}"

DEFAULT_CITIES = [
    "Hyderabad",
    "Bengaluru",
    "Mumbai",
    "Delhi",
    "Chennai",
    "Kolkata",
]


# ---------------------------------------------------------
# Application directory
# ---------------------------------------------------------

def get_app_directory() -> Path:
    """Return the folder where the application is running."""

    if getattr(sys, "frozen", False):
        # Running as a PyInstaller EXE
        return Path(sys.executable).resolve().parent

    # Running normally with Python
    return Path(__file__).resolve().parent


APP_DIR = get_app_directory()

# Weather icon directory
ICON_DIR = APP_DIR / "assets" / "icons"


# ---------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------

# Load .env from the same folder as the application.
# This works both for normal Python execution and PyInstaller EXE.
ENV_FILE = APP_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)

OPENWEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY",
    ""
).strip()

# Compatibility alias
API_KEY = OPENWEATHER_API_KEY


# ---------------------------------------------------------
# Application settings
# ---------------------------------------------------------

@dataclass
class Settings:
    """Application runtime settings."""

    api_key: str = OPENWEATHER_API_KEY

    base_url: str = "https://api.openweathermap.org/data/2.5"

    timeout: float = 10.0

    app_name: str = APP_NAME

    app_version: str = APP_VERSION

    app_title: str = APP_TITLE

    @property
    def has_api_key(self) -> bool:
        """Return True when an API key is configured."""
        return bool(self.api_key and self.api_key.strip())


# ---------------------------------------------------------
# Settings loader
# ---------------------------------------------------------

def load_settings() -> Settings:
    """Load application settings."""

    return Settings(
        api_key=OPENWEATHER_API_KEY,
        base_url="https://api.openweathermap.org/data/2.5",
        timeout=10.0,
        app_name=APP_NAME,
        app_version=APP_VERSION,
        app_title=APP_TITLE,
    )