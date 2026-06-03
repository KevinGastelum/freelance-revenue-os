import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

_DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "freelance-os"

_engine = None


def _db_path() -> Path:
    env = os.environ.get("FREELANCE_OS_DB")
    if env:
        return Path(env)
    return _DEFAULT_DATA_DIR / "freelance_os.sqlite"


def get_engine():
    global _engine
    if _engine is None:
        path = _db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{path}")
        _ensure_tables(_engine)
    return _engine


def reset_engine() -> None:
    """Reset the cached engine. Call in tests after changing FREELANCE_OS_DB."""
    global _engine
    _engine = None


def _ensure_tables(eng) -> None:
    from . import models  # noqa: F401 — registers SQLModel table metadata
    SQLModel.metadata.create_all(eng)


def create_all() -> None:
    """Idempotently create all tables. Safe to call multiple times."""
    _ensure_tables(get_engine())


def get_session() -> Session:
    return Session(get_engine())
