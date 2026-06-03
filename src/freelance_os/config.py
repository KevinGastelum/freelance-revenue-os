"""Configuration loader for Freelance Revenue OS."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


_SAFE_DEFAULTS = {
    "allow_browser_automation": False,
    "allow_auto_submit": False,
    "allow_auto_message": False,
    "allow_scraping": False,
    "require_human_approval": True,
}

_UNSAFE_FLAGS = {
    "allow_browser_automation",
    "allow_auto_submit",
    "allow_auto_message",
    "allow_scraping",
}


class UnsafeConfigError(ValueError):
    """Raised when a safety flag is set to an unsafe value."""


class Settings:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._validate_safety()

    def _validate_safety(self) -> None:
        safety = self._data.get("safety", {})
        for flag in _UNSAFE_FLAGS:
            value = safety.get(flag, _SAFE_DEFAULTS[flag])
            if value is True:
                raise UnsafeConfigError(
                    f"Safety violation: '{flag}' must not be true. "
                    "This system enforces the 'AI prepares, human commits' policy."
                )

    @property
    def user_name(self) -> str:
        return self._data.get("user", {}).get("name", "User")

    @property
    def target_hourly_rate(self) -> float:
        return float(self._data.get("user", {}).get("target_hourly_rate", 75))

    @property
    def minimum_project_value(self) -> float:
        return float(self._data.get("user", {}).get("minimum_project_value", 300))

    @property
    def client_work_dir(self) -> Path:
        return Path(self._data.get("paths", {}).get("client_work_dir", "./client-work"))

    @property
    def portfolio_file(self) -> Path:
        return Path(self._data.get("paths", {}).get("portfolio_file", "./config/portfolio.yaml"))

    @property
    def database_path(self) -> Path:
        return Path(self._data.get("paths", {}).get("database_path", "./data/freelance_os.sqlite"))

    @property
    def require_human_approval(self) -> bool:
        return bool(self._data.get("safety", {}).get("require_human_approval", True))


def load_settings(config_path: Path | None = None) -> Settings:
    if config_path is None:
        config_path = Path("config/settings.toml")

    if not config_path.exists():
        return Settings({})

    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    return Settings(data)


def load_portfolio(portfolio_path: Path | None = None) -> list[dict[str, Any]]:
    if portfolio_path is None:
        portfolio_path = Path("config/portfolio.yaml")

    if not portfolio_path.exists():
        return []

    with open(portfolio_path) as f:
        data = yaml.safe_load(f)

    if not data:
        return []
    return data.get("items", [])


def load_banned_phrases(phrases_path: Path | None = None) -> list[str]:
    if phrases_path is None:
        phrases_path = Path("config/banned_phrases.yaml")

    if not phrases_path.exists():
        return []

    with open(phrases_path) as f:
        data = yaml.safe_load(f)

    if not data:
        return []
    return data.get("phrases", [])


def load_scoring_rules(rules_path: Path | None = None) -> dict[str, Any]:
    if rules_path is None:
        rules_path = Path("config/scoring_rules.toml")

    if not rules_path.exists():
        return {}

    with open(rules_path, "rb") as f:
        return tomllib.load(f)
