"""
Tests for heartbeat timeout detection and offline marking.

These tests verify the background heartbeat monitor mechanism that marks nodes
OFFLINE when they stop sending heartbeats.

Root cause being tested: The heartbeat monitor task was never started during
FastAPI startup, so the dashboard continued showing nodes as ONLINE indefinitely
even after the edge process was killed.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.node import Node, NodeStatus
from app.services.database import get_node_by_id
from app.services.node_service import mark_offline_nodes


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_engine():
    """Create async engine for testing"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create async session for testing"""
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


def _make_node(node_id: str, status: NodeStatus, last_seen_offset: timedelta) -> Node:
    """Helper to create a Node with a last_seen relative to now (timezone-aware)."""
    now = datetime.now(timezone.utc)
    return Node(
        node_id=node_id,
        hostname=f"{node_id}-host",
        os="Linux",
        status=status,
        last_seen=now - last_seen_offset,
    )


@pytest.mark.asyncio
async def test_heartbeat_keeps_node_online(async_session):
    """Test 1 — Heartbeat keeps node online.

    A node that has recently sent a heartbeat (last_seen within timeout)
    should remain ONLINE after mark_offline_nodes runs.
    """
    # Node sent heartbeat 5 seconds ago (within 30s timeout)
    node = _make_node("node-heartbeat-ok", NodeStatus.ONLINE, timedelta(seconds=5))
    async_session.add(node)
    await async_session.commit()

    # Run the timeout check
    count = await mark_offline_nodes(timeout_seconds=30, db=async_session)

    # No nodes should be marked offline
    assert count == 0

    # Verify node is still ONLINE
    checked = await get_node_by_id("node-heartbeat-ok", async_session)
    assert checked.status == NodeStatus.ONLINE


@pytest.mark.asyncio
async def test_heartbeat_timeout_marks_node_offline(async_session):
    """Test 2 — Heartbeat timeout marks node offline.

    A node whose last_seen is older than the timeout threshold should be
    marked OFFLINE by mark_offline_nodes.
    """
    # Node last sent heartbeat 35 seconds ago (past 30s timeout)
    node = _make_node("node-heartbeat-timeout", NodeStatus.ONLINE, timedelta(seconds=35))
    async_session.add(node)
    await async_session.commit()

    # Run the timeout check with 30s threshold
    count = await mark_offline_nodes(timeout_seconds=30, db=async_session)

    # Exactly 1 node should be marked offline
    assert count == 1

    # Verify the node is now OFFLINE in the database
    checked = await get_node_by_id("node-heartbeat-timeout", async_session)
    assert checked.status == NodeStatus.OFFLINE


@pytest.mark.asyncio
async def test_node_reconnect_marks_online(async_session):
    """Test 3 — Node reconnects and becomes ONLINE again.

    After being marked OFFLINE due to heartbeat timeout, a node that
    re-registers should return to ONLINE state.
    """
    # Start with an offline node
    node = _make_node("node-reconnect", NodeStatus.OFFLINE, timedelta(seconds=100))
    async_session.add(node)
    await async_session.commit()

    # Simulate reconnection: update status to ONLINE with fresh last_seen
    from app.services.node_service import update_node_status
    updated = await update_node_status("node-reconnect", NodeStatus.ONLINE, async_session)
    assert updated.status == NodeStatus.ONLINE
    assert updated.last_seen is not None

    # Running timeout check should NOT re-mark it offline
    count = await mark_offline_nodes(timeout_seconds=30, db=async_session)
    assert count == 0

    checked = await get_node_by_id("node-reconnect", async_session)
    assert checked.status == NodeStatus.ONLINE


@pytest.mark.asyncio
async def test_multiple_nodes_independent(async_session):
    """Test 5 — Multiple nodes are handled independently.

    One dead node must not affect other nodes. A mix of recently-active
    and stale nodes should only have the stale ones marked offline.
    """
    # Node A: recently seen (within timeout)
    node_a = _make_node("node-multi-alive", NodeStatus.ONLINE, timedelta(seconds=3))
    async_session.add(node_a)

    # Node B: stale heartbeat (past timeout)
    node_b = _make_node("node-multi-dead", NodeStatus.ONLINE, timedelta(seconds=45))
    async_session.add(node_b)

    # Node C: another recently seen node
    node_c = _make_node("node-multi-alive-2", NodeStatus.ONLINE, timedelta(seconds=1))
    async_session.add(node_c)

    await async_session.commit()

    # Run timeout check
    count = await mark_offline_nodes(timeout_seconds=30, db=async_session)

    # Only node B should be marked offline
    assert count == 1

    # Verify independent status
    node_a_check = await get_node_by_id("node-multi-alive", async_session)
    assert node_a_check.status == NodeStatus.ONLINE

    node_b_check = await get_node_by_id("node-multi-dead", async_session)
    assert node_b_check.status == NodeStatus.OFFLINE

    node_c_check = await get_node_by_id("node-multi-alive-2", async_session)
    assert node_c_check.status == NodeStatus.ONLINE


@pytest.mark.asyncio
async def test_api_returns_offline_status(async_session):
    """Test 4 — API reflects database status.

    After timeout detection marks a node OFFLINE, the API should report
    OFFLINE status. This verifies the full chain: heartbeat timeout →
    database update → API response.
    """
    from app.schemas.node import NodeResponse

    # Create a stale node
    node = _make_node("node-api-check", NodeStatus.ONLINE, timedelta(seconds=40))
    async_session.add(node)
    await async_session.commit()

    # Run timeout detection
    await mark_offline_nodes(timeout_seconds=30, db=async_session)

    # Simulate what the API endpoint does: fetch node and serialize to NodeResponse
    checked = await get_node_by_id("node-api-check", async_session)
    response = NodeResponse.from_orm(checked)

    # The API should reflect the OFFLINE status from the database
    assert response.status == "offline"
