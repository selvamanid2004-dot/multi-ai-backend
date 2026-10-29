from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.database.base import Base

# Engine configured for asynchronous execution
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session per request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initializes database tables and performs safe column migrations on startup.
    """
    from sqlalchemy import text
    # Import all models to ensure metadata registration
    import app.database.models  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Automatic schema evolution: safely add new columns if they do not yet exist
        new_columns = [
            ("research_tasks", "task_type", "VARCHAR(50) DEFAULT 'RESEARCH'"),
            ("research_tasks", "document_filename", "VARCHAR(255)"),
            ("research_tasks", "document_summary", "JSON"),
            ("research_tasks", "strategic_projections", "JSON"),
            ("research_tasks", "visual_diagrams", "JSON"),
            ("research_tasks", "audit_dossier", "JSON"),
        ]
        for table, col, col_type in new_columns:
            try:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
            except Exception:
                # Column already present
                pass

