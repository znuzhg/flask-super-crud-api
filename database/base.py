from __future__ import annotations

import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

from config.settings import settings

logger = logging.getLogger(__name__)


Base = declarative_base()


_engine = None
SessionLocal = None
db_session = None


def init_engine(database_url: str | None = None):
    global _engine, SessionLocal, db_session
    url = database_url or settings.DATABASE_URL
    engine_kwargs = {"future": True}
    if url.startswith("sqlite"):
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False} if ":memory:" in url else {},
            "pool_pre_ping": True,
        })
    else:
        engine_kwargs.update({
            "pool_pre_ping": True,
            "pool_recycle": 1800,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
        })
    _engine = create_engine(url, **engine_kwargs)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    db_session = scoped_session(SessionLocal)
    logger.info("SQLAlchemy engine initialized")
    return _engine


def init_db():
    # Import models to ensure they are registered on Base.metadata
    from models.user import User  # noqa: F401
    Base.metadata.create_all(bind=_engine)


def get_session():
    if db_session is None:
        raise RuntimeError("Database not initialized. Call init_engine() first.")
    return db_session


def remove_session() -> None:
    if db_session is not None:
        try:
            db_session.remove()
        except OperationalError:
            # On teardown, ignore transient DB issues
            pass
