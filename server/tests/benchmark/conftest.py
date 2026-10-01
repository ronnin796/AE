"""Pytest configuration for benchmark tests"""

import pytest
import pytest_asyncio
from sqlalchemy import delete

from app.database import async_session_maker
from app.models.node import Node
from app.models.telemetry import Telemetry


@pytest_asyncio.fixture(scope="function")
async def clean_database():
    """Clean database before each test"""
    async with async_session_maker() as db:
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()
    yield
    async with async_session_maker() as db:
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()