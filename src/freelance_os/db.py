"""Database engine and session helpers."""

from pathlib import Path
from typing import Generator, Optional

from sqlmodel import Session, SQLModel, create_engine


def get_engine(db_path: str = "data/freelance_os.sqlite"):
    """Return a SQLAlchemy engine for the given SQLite path."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def create_tables(engine=None, db_path: str = "data/freelance_os.sqlite"):
    """Create all tables (idempotent — safe to call repeatedly)."""
    from sqlalchemy import text
    import freelance_os.models  # noqa: F401

    if engine is None:
        engine = get_engine(db_path)
    SQLModel.metadata.create_all(engine)

    # Migrate existing DBs: add category column if absent (old rows -> 'OTHER').
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE lead ADD COLUMN category VARCHAR NOT NULL DEFAULT 'OTHER'"))
            conn.commit()
        except Exception:
            pass  # Column already exists

    return engine


def drop_tables(engine):
    """Drop all tables — destructive, requires explicit call."""
    import freelance_os.models  # noqa: F401

    SQLModel.metadata.drop_all(engine)


def get_session(engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
