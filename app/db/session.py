"""Database connection and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.logging import get_logger
from app.models.article import Base

logger = get_logger(__name__)

# Convert sync PostgreSQL URL to async
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine (lazy initialization to avoid import errors)
engine = None
AsyncSessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global engine
    if engine is None:
        engine = create_async_engine(
            database_url,
            echo=settings.debug,
            poolclass=StaticPool if "sqlite" in database_url else None,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
    return engine


def get_session_local():
    """Get or create the session factory."""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False
        )
    return AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    session_local = get_session_local()
    async with session_local() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables."""
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


async def drop_tables() -> None:
    """Drop all database tables."""
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise
