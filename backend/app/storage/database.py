"""Database Connection and Session Management with SQLModel / SQLite."""

import os
from typing import Generator
from sqlmodel import Session, SQLModel, create_engine
from backend.app.core.config import settings

# In-memory SQLite for testing or file-based for local persistence
DATABASE_URL = settings.DATABASE_URL

# For SQLite, connect_args check_same_thread=False allows FastAPI multi-threaded requests
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
)


def init_db() -> None:
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    with Session(engine, expire_on_commit=False) as session:
        yield session
