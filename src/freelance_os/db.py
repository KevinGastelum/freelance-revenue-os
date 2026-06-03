"""Database setup and session management."""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from freelance_os import models as _models  # noqa: F401 — ensures table metadata is registered


_engine = None


def get_engine(db_path: Path | None = None):
    global _engine
    if _engine is None:
        if db_path is None:
            db_path = Path("data/freelance_os.sqlite")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return _engine


def init_db(db_path: Path | None = None) -> None:
    engine = get_engine(db_path)
    SQLModel.metadata.create_all(engine)


def reset_engine() -> None:
    """Reset engine (used in tests to switch to a different DB path)."""
    global _engine
    _engine = None


def get_session(db_path: Path | None = None) -> Session:
    engine = get_engine(db_path)
    return Session(engine)
