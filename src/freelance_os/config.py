import tomllib
from pathlib import Path
from typing import Any


class SafetyConfigError(Exception):
    pass


class Settings:
    def __init__(self, config_path: Path | None = None):
        self.config: dict[str, Any] = {}

        path = config_path or Path.home() / ".config" / "freelance-os" / "settings.toml"
        if path.exists():
            with open(path, "rb") as f:
                self.config = tomllib.load(f)

        self._validate_safety()

    def _validate_safety(self) -> None:
        safety = self.config.get("safety", {})
        prohibited = {
            "allow_browser_automation": "browser automation",
            "allow_auto_submit": "automated proposal submission",
            "allow_auto_message": "automated messaging",
            "allow_scraping": "authenticated scraping",
        }
        for key, label in prohibited.items():
            if safety.get(key) is True:
                raise SafetyConfigError(
                    f"Safety policy violation: '{key}' enables {label}, which is prohibited."
                )

    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.config
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key, default)
        return node


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
