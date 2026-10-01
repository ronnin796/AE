"""Database configuration and session management"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# Use async SQLite driver for async operations
def get_database_url() -> str:
    """Get database URL with proper async SQLite driver"""
    url = settings.database_url

    # Replace sqlite:/// with sqlite+aiosqlite:/// for async support
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    return url


# Create async engine
engine = create_async_engine(
    get_database_url(),
    echo=settings.log_level == "debug",
    future=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Dependency for FastAPI
async def get_db() -> AsyncSession:
    """FastAPI dependency for database session"""
    async with get_session() as session:
        yield session