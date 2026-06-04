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


DEFAULT_SCORING_RULES: Dict[str, Any] = {
    "thresholds": {
        "draft_now_min": 80,
        "watch_min": 65,
        "maybe_min": 50,
    },
    "weights": {
        "technical_fit": 20,
        "budget_fit": 15,
        "client_quality": 15,
        "clarity_of_scope": 10,
        "urgency_timing": 10,
        "portfolio_match": 10,
        "repeat_work_potential": 10,
        "communication_quality": 10,
    },
    "risk_penalties": {
        "unpaid_test_request": 25,
        "payment_rule_bypass": 25,
        "unrealistic_deadline": 20,
        "vague_fixed_low_budget": 20,
        "suspicious_payment": 15,
        "scope_creep_risk": 15,
        "easy_language_complex_work": 10,
        "unclear_deliverables": 10,
        "unsupported_tech_stack": 10,
        "free_consultation_request": 10,
    },
    "pricing": {
        "target_hourly_rate": 75,
        "minimum_project_value": 300,
        "risk_multiplier_low": 1.0,
        "risk_multiplier_medium": 1.25,
        "risk_multiplier_high": 1.5,
        "rush_multiplier": 1.25,
        "platform_fee_buffer": 0.10,
    },
}

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
        "quick_win_discount": 0.85,
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
    cfg["scoring_rules"] = load_scoring_rules()
    _enforce_safety(cfg)
    return cfg


def load_scoring_rules(path: Optional[str] = None) -> Dict[str, Any]:
    """Load scoring rules from TOML, falling back to example then hard defaults."""
    candidates = [
        path,
        "config/scoring_rules.toml",
        "config/scoring_rules.example.toml",
    ]
    base = _deep_merge({}, DEFAULT_SCORING_RULES)
    for candidate in candidates:
        if not candidate:
            continue
        p = Path(candidate)
        if p.exists():
            with open(p, "rb") as f:
                data = tomllib.load(f)
            return _deep_merge(base, data)
    return base


def _enforce_safety(cfg: Dict[str, Any]) -> None:
    for section, key, msg in _PROHIBITED:
        if cfg.get(section, {}).get(key, False):
            raise ConfigError(f"SAFETY VIOLATION: {msg}")
