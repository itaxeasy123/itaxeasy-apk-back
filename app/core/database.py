from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def get_database_url() -> str:
    """
    Converts standard postgresql:// URLs to asyncpg format.
    """
    url = settings.DATABASE_URL
    
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://")
        
    return url


DATABASE_URL = get_database_url()

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10 if not settings.is_local else 5,
    max_overflow=20 if not settings.is_local else 10,
    pool_timeout=30,
)

# Async session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to yield an async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
