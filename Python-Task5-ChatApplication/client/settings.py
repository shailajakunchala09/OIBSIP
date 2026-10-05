"""Small JSON-backed user settings. Never stores passwords or tokens."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SETTINGS_PATH = Path.home() / ".vanta_chat" / "settings.json"


@dataclass
class Settings:
    theme: str = "dark"
    notifications: bool = True
    sound: bool = False
    last_username: str = ""

    @classmethod
    def load(cls, path: Path = SETTINGS_PATH) -> "Settings":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**known)
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self, path: Path = SETTINGS_PATH) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError:
            pass        # settings are a convenience; failing to save is not worth an error dialog
