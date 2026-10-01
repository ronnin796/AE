"""Pytest configuration for integration tests"""

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.database import async_session_maker
from app.models.node import Node
from app.models.telemetry import Telemetry


@pytest_asyncio.fixture(scope="function")
async def clean_database():
    """Clean database before each test (uses main database for integration tests)"""
    print(f"[clean_database] Pre-test cleanup starting")
    async with async_session_maker() as db:
        result = await db.execute(select(Node))
        nodes_before = result.scalars().all()
        print(f"[clean_database] Nodes before cleanup: {len(nodes_before)}")
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()
        print(f"[clean_database] Pre-test cleanup done")
    yield
    print(f"[clean_database] Post-test cleanup starting")
    async with async_session_maker() as db:
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()
        print(f"[clean_database] Post-test cleanup done")