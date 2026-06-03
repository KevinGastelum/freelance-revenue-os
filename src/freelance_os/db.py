from sqlmodel import SQLModel, create_engine, Session


def get_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}")


def create_tables(engine) -> int:
    """Import all models so they register with SQLModel metadata, then create tables."""
    from freelance_os import models as _models  # noqa: F401
    SQLModel.metadata.create_all(engine)
    return len(SQLModel.metadata.tables)


def get_session(engine) -> Session:
    return Session(engine)
