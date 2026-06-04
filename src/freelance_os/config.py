"""Config loader with hard safety enforcement."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


class ConfigError(Exception):
    pass


SAFE_DEFAULTS: Dict[str, Any] = {
    "user": {
        "name": "User",
        "default_timezone": "UTC",
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
    "scoring": {
        "target_hourly_rate": 75,
        "minimum_project_value": 300,
        "risk_multiplier_low": 1.0,
        "risk_multiplier_medium": 1.25,
        "risk_multiplier_high": 1.5,
        "rush_multiplier": 1.25,
    },
}

_PROHIBITED = [
    ("safety", "allow_auto_submit",
     "allow_auto_submit=true is prohibited: automated proposal submission violates platform TOS"),
    ("safety", "allow_browser_automation",
     "allow_browser_automation=true is prohibited: stealth browser automation is forbidden"),
    ("safety", "allow_auto_message",
     "allow_auto_message=true is prohibited: automated messaging is forbidden"),
    ("safety", "allow_scraping",
     "allow_scraping=true is prohibited: authenticated scraping is forbidden"),
]


def _deep_merge(base: Dict, override: Dict) -> Dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg = _deep_merge({}, SAFE_DEFAULTS)
    if path:
        p = Path(path)
        if p.exists():
            with open(p, "rb") as f:
                user_cfg = tomllib.load(f)
            cfg = _deep_merge(cfg, user_cfg)
    _enforce_safety(cfg)
    return cfg


def _enforce_safety(cfg: Dict[str, Any]) -> None:
    for section, key, msg in _PROHIBITED:
        if cfg.get(section, {}).get(key, False):
            raise ConfigError(f"SAFETY VIOLATION: {msg}")
