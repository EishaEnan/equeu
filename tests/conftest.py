from __future__ import annotations

import os
import pathlib

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


# Repo root: .../eQueue
ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION_001 = ROOT / "db" / "migrations" / "001_create_jobs_table.sql"


def _db_url() -> str:
    """
    Example:
      export DATABASE_URL_TEST="postgresql+asyncpg://postgres:postgres@localhost:5432/equeue_test"
    """
    url = os.getenv("DATABASE_URL_TEST")
    if not url:
        raise RuntimeError(
            "DATABASE_URL_TEST not set. "
            "Example: postgresql+asyncpg://postgres:postgres@localhost:5432/equeue_test"
        )
    return url


@pytest.fixture
def engine() -> AsyncEngine:
    """
    Function-scoped engine + NullPool prevents asyncpg connections from being reused
    across event loops created by pytest-anyio.
    """
    return create_async_engine(_db_url(), poolclass=NullPool)


async def _apply_migration(conn: AsyncConnection) -> None:
    """
    Executes the full migration script using the raw asyncpg connection,
    which supports multi-statement scripts (DO $$ ... $$; functions, triggers, etc.).
    """
    sql = MIGRATION_001.read_text()

    raw = await conn.get_raw_connection()
    # driver_connection is the underlying asyncpg.Connection
    await raw.driver_connection.execute(sql)


@pytest.fixture
async def db_conn(engine: AsyncEngine) -> AsyncConnection:
    """
    Provides a connection wrapped in a transaction for each test.
    We apply migrations inside the transaction and roll back afterward
    for isolation.
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            await _apply_migration(conn)
            yield conn
        finally:
            await trans.rollback()
            # Dispose ensures any resources are fully released per test.
            await engine.dispose()


@pytest.fixture
async def session(db_conn: AsyncConnection) -> AsyncSession:
    """
    AsyncSession bound to the same connection/transaction used by db_conn,
    so all repo operations are isolated and rollback cleanly.
    """
    async_session = sessionmaker(
        bind=db_conn,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session() as s:
        yield s
