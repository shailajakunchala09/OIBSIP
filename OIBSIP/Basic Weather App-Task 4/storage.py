"""Lightweight persistence: favourites/theme/unit on disk, recent searches in memory."""
from __future__ import annotations

import json
import os
from pathlib import Path

from units import UnitSystem

MAX_RECENTS = 5
MAX_FAVORITES = 8


def default_prefs_path() -> Path:
    """~/.skypulse/preferences.json (outside the repo, so it is never committed)."""
    return Path(os.environ.get("SKYPULSE_HOME", Path.home() / ".skypulse")) / "preferences.json"


def city_key(name: str, country: str = "") -> str:
    return f"{name.strip().lower()}|{country.strip().lower()}"


def city_query(name: str, country: str = "") -> str:
    """'London' + 'GB' -> 'London,GB', which OpenWeatherMap resolves unambiguously."""
    return f"{name},{country}" if country else name


class SearchHistory:
    """Most-recent-first list of searched cities for the current session."""

    def __init__(self, limit: int = MAX_RECENTS):
        self.limit = limit
        self._items: list[dict] = []

    def add(self, name: str, country: str = "") -> None:
        key = city_key(name, country)
        self._items = [i for i in self._items if city_key(i["name"], i["country"]) != key]
        self._items.insert(0, {"name": name, "country": country})
        del self._items[self.limit:]

    def items(self) -> list[dict]:
        return list(self._items)


class Preferences:
    """Persisted user preferences. Corrupt or missing files fall back to defaults."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else default_prefs_path()
        self.units = UnitSystem.METRIC
        self.theme = "dark"
        self.favorites: list[dict] = []
        self.load()

    def load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("preferences must be an object")
        except (OSError, ValueError):
            return
        self.units = UnitSystem.parse(data.get("units"))
        self.theme = data.get("theme") if data.get("theme") in ("dark", "light") else "dark"
        favs = data.get("favorites", [])
        self.favorites = [
            {"name": str(f["name"]), "country": str(f.get("country", ""))}
            for f in favs if isinstance(f, dict) and f.get("name")
        ][:MAX_FAVORITES]

    def save(self) -> bool:
        payload = {"units": self.units.value, "theme": self.theme, "favorites": self.favorites}
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.path)
            return True
        except OSError:
            return False  # persistence is best-effort; the app keeps working

    def is_favorite(self, name: str, country: str = "") -> bool:
        key = city_key(name, country)
        return any(city_key(f["name"], f["country"]) == key for f in self.favorites)

    def toggle_favorite(self, name: str, country: str = "") -> bool:
        """Toggle and return the new state (True = now a favourite)."""
        key = city_key(name, country)
        if self.is_favorite(name, country):
            self.favorites = [f for f in self.favorites if city_key(f["name"], f["country"]) != key]
            state = False
        else:
            self.favorites.insert(0, {"name": name, "country": country})
            del self.favorites[MAX_FAVORITES:]
            state = True
        self.save()
        return state
