from collections.abc import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Create the database engine only when persistence is used."""
    global _engine

    if _engine is None:
        database_url = get_settings().database_url
        if database_url is None:
            raise HTTPException(
                status_code=503,
                detail="Database is not configured. Set DATABASE_URL and run migrations.",
            )
        _engine = create_async_engine(database_url, pool_pre_ping=True)

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


async def check_database() -> bool:
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine() -> None:
    global _engine

    if _engine is not None:
        await _engine.dispose()
        _engine = None
