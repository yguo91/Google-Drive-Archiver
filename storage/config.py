"""Configuration management using JSON storage."""

import json
import os
import sys
from pathlib import Path
from typing import Any


def get_config_dir() -> Path:
    """Get the application config directory."""
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        config_dir = Path(appdata) / "DriveArchiver"
    else:
        config_dir = Path.home() / ".drive_archiver"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get the path to the config file."""
    return get_config_dir() / "config.json"


def get_token_path() -> Path:
    """Get the path to the OAuth token file."""
    return get_config_dir() / "token.json"


def get_credentials_path() -> Path:
    """Get the path to the OAuth credentials file.

    Checks bundled location (PyInstaller), then app directory, then config directory.
    """
    # Check bundled location first (PyInstaller .exe)
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "credentials.json"
        if bundled.exists():
            return bundled

    # Check app directory (for development)
    app_dir = Path(__file__).parent.parent
    app_creds = app_dir / "credentials.json"
    if app_creds.exists():
        return app_creds

    # Fall back to config directory
    return get_config_dir() / "credentials.json"


DEFAULT_CONFIG = {
    "drive": {
        "connected": False,
        "account_email": ""
    },
    "archive": {
        "path": ""
    },
    "rules": {
        "filter_mode": "size",
        "min_size_mb": 200,
        "before_date": "2020-01-01",
        "dry_run": True,
        "trash_after": True
    }
}


class Config:
    """Application configuration manager."""

    def __init__(self):
        self._data: dict = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file, or use defaults."""
        config_path = get_config_path()
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = DEFAULT_CONFIG.copy()
        else:
            self._data = self._deep_copy(DEFAULT_CONFIG)

        # Ensure all default keys exist
        self._merge_defaults()

    def save(self) -> None:
        """Save configuration to file."""
        config_path = get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def _merge_defaults(self) -> None:
        """Ensure all default keys exist in loaded config."""
        for key, value in DEFAULT_CONFIG.items():
            if key not in self._data:
                self._data[key] = self._deep_copy(value)
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in self._data[key]:
                        self._data[key][subkey] = subvalue

    def _deep_copy(self, obj: Any) -> Any:
        """Create a deep copy of a nested dict/list structure."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        return obj

    # Drive settings
    @property
    def is_connected(self) -> bool:
        return self._data["drive"]["connected"]

    @is_connected.setter
    def is_connected(self, value: bool) -> None:
        self._data["drive"]["connected"] = value

    @property
    def account_email(self) -> str:
        return self._data["drive"]["account_email"]

    @account_email.setter
    def account_email(self, value: str) -> None:
        self._data["drive"]["account_email"] = value

    # Archive settings
    @property
    def archive_path(self) -> str:
        return self._data["archive"]["path"]

    @archive_path.setter
    def archive_path(self, value: str) -> None:
        self._data["archive"]["path"] = value

    # Rules settings
    @property
    def filter_mode(self) -> str:
        return self._data["rules"]["filter_mode"]

    @filter_mode.setter
    def filter_mode(self, value: str) -> None:
        self._data["rules"]["filter_mode"] = value

    @property
    def min_size_mb(self) -> int:
        return self._data["rules"]["min_size_mb"]

    @min_size_mb.setter
    def min_size_mb(self, value: int) -> None:
        self._data["rules"]["min_size_mb"] = value

    @property
    def before_date(self) -> str:
        return self._data["rules"]["before_date"]

    @before_date.setter
    def before_date(self, value: str) -> None:
        self._data["rules"]["before_date"] = value

    @property
    def dry_run(self) -> bool:
        return self._data["rules"]["dry_run"]

    @dry_run.setter
    def dry_run(self, value: bool) -> None:
        self._data["rules"]["dry_run"] = value

    @property
    def trash_after(self) -> bool:
        return self._data["rules"]["trash_after"]

    @trash_after.setter
    def trash_after(self, value: bool) -> None:
        self._data["rules"]["trash_after"] = value

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._data = self._deep_copy(DEFAULT_CONFIG)
        self.save()
