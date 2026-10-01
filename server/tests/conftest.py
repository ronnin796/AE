"""Pytest configuration and fixtures"""

import asyncio
import sys
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import delete

from app.database import Base, async_session_maker
from app.models.node import Node
from app.models.telemetry import Telemetry
from app.config import settings


# Use in-memory SQLite for unit tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for unit tests"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncSession:
    """Create async session for unit tests"""
    async_session_maker_local = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker_local() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def server_process():
    """Start the FastAPI server for integration tests"""
    # Ensure database is initialized
    from app.database import init_db
    await init_db()
    
    # Start server
    import os
    import subprocess
    from pathlib import Path
    
    # Use the current Python interpreter to run uvicorn
    python_exe = sys.executable
    server_dir = Path(__file__).parent.parent.parent / "server"
    
    # Create log file for server output
    log_file = server_dir / "test_server.log"
    log_f = open(log_file, "w")
    
    env = {
        **os.environ,
        "PYTHONPATH": str(server_dir),
    }
    
    proc = subprocess.Popen(
        [
            python_exe, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8080",
            "--log-level", "warning"
        ],
        cwd=server_dir,
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )
    
    # Wait for server to start
    import httpx
    for _ in range(30):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://127.0.0.1:8080/health", timeout=1.0)
                if resp.status_code == 200:
                    break
        except Exception:
            pass
        await asyncio.sleep(0.5)
    else:
        proc.terminate()
        log_f.close()
        with open(log_file, "r") as f:
            log_content = f.read()
        pytest.fail(f"Server failed to start. Log: {log_content}")
    
    yield proc
    
    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    log_f.close()


@pytest.fixture(autouse=True)
def override_settings_unit_tests(monkeypatch, request):
    """Override settings for unit tests only (not integration tests)"""
    # Skip for integration tests (tests in integration directory)
    if "integration" in str(request.node.fspath):
        return
    monkeypatch.setattr(settings, "database_url", TEST_DATABASE_URL)
    monkeypatch.setattr(settings, "host", "127.0.0.1")
    monkeypatch.setattr(settings, "port", 8080)
    monkeypatch.setattr(settings, "cors_origins", ["*"])