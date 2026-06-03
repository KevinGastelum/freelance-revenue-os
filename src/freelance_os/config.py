import copy
import tomllib
from pathlib import Path


DEFAULT_CONFIG: dict = {
    "user": {
        "name": "",
        "default_timezone": "America/Chicago",
        "target_hourly_rate": 75,
        "minimum_project_value": 300,
    },
    "paths": {
        "client_work_dir": "./client-work",
        "portfolio_file": "./config/portfolio.yaml",
        "database_path": "./data/freelance_os.sqlite",
    },
    "safety": {
        "allow_browser_automation": False,
        "allow_auto_submit": False,
        "allow_auto_message": False,
        "allow_scraping": False,
        "require_human_approval": True,
    },
}

_UNSAFE_FLAGS = [
    "allow_auto_submit",
    "allow_browser_automation",
    "allow_auto_message",
    "allow_scraping",
]


class SafetyConfigError(Exception):
    """Raised when a configuration enables prohibited automation."""


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def validate_safety(config: dict) -> None:
    """Raise SafetyConfigError if any prohibited automation flag is enabled."""
    safety = config.get("safety", {})
    for flag in _UNSAFE_FLAGS:
        if safety.get(flag, False) is True:
            raise SafetyConfigError(
                f"Safety violation: '{flag}' is set to true in configuration. "
                "This setting is prohibited by the project safety policy. "
                "See docs/SAFETY_POLICY.md for the full policy. "
                "AI prepares; the human commits all platform actions."
            )


def load_config(config_path=None) -> dict:
    """
    Load configuration from a TOML file, merged over safe defaults.

    If config_path is None or the path does not exist, safe defaults are used.
    Always enforces the safety policy — raises SafetyConfigError if any
    prohibited automation flag is enabled.
    """
    config = copy.deepcopy(DEFAULT_CONFIG)

    if config_path is not None:
        path = Path(config_path)
        if path.exists():
            with open(path, "rb") as f:
                user_config = tomllib.load(f)
            config = _deep_merge(config, user_config)

    validate_safety(config)
    return config
