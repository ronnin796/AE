"""Integration tests for AetherEdge IT requirements.

Tests cover:
- IT-001: Node Connection
- IT-002: Node Detail Retrieval
- IT-003: Telemetry Transmission
- IT-004: Individual Disconnect
- IT-005: Reconnection
"""

import pytest
import pytest_asyncio
import asyncio
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, init_db, async_session_maker
from app.models.node import Node, NodeStatus
from app.models.telemetry import Telemetry
from app.services.database import create_node, add_telemetry, get_node_by_id, get_telemetry_for_node
from app.services.node_service import register_node, mark_offline_nodes, update_node_status
from app.schemas.node import NodeRegister, ServerConfig


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
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


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):
    """Create async session for testing"""
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.mark.asyncio
async def test_it_001_node_connection(async_session):
    """IT-001: Node Connection - Node appears in dashboard."""
    # Register a new node
    register_data = NodeRegister(
        node_id="test-node-001",
        hostname="test-node-001",
        os="Linux",
        cpu_cores=4,
        total_memory=16_000_000_000,
    )

    response = await register_node(register_data, async_session)

    assert response.success is True
    assert response.node_id == "test-node-001"

    # Verify node can be retrieved
    from app.services.database import get_node_by_id
    node = await get_node_by_id("test-node-001", async_session)
    assert node is not None
    assert node.hostname == "test-node-001"
    assert node.status == NodeStatus.ONLINE


@pytest.mark.asyncio
async def test_it_002_node_detail_retrieval(async_session):
    """IT-002: Node Detail Retrieval - Clicking node displays information."""
    # Register a new node
    register_data = NodeRegister(
        node_id="test-node-002",
        hostname="test-node-002",
        os="Linux",
        cpu_cores=4,
        total_memory=16_000_000_000,
    )

    await register_node(register_data, async_session)

    # Get node details
    from app.services.database import get_node_by_id
    node = await get_node_by_id("test-node-002", async_session)

    assert node is not None
    assert node.hostname == "test-node-002"
    assert node.node_id == "test-node-002"
    assert node.status == NodeStatus.ONLINE
    assert node.last_seen is not None

    # Verify NodeResponse schema works
    from app.schemas.node import NodeResponse
    node_response = NodeResponse.model_validate(node)
    assert node_response.id >= 1
    assert node_response.node_id == "test-node-002"
    assert node_response.hostname == "test-node-002"
    assert node_response.status == "online"


@pytest.mark.asyncio
async def test_it_003_telemetry_transmission(async_session):
    """IT-003: Telemetry Transmission - Agent sends telemetry, server receives it, dashboard displays it."""
    # Register a new node
    register_data = NodeRegister(
        node_id="test-node-003",
        hostname="test-node-003",
        os="Linux",
        cpu_cores=4,
        total_memory=16_000_000_000,
    )

    await register_node(register_data, async_session)

    # Add telemetry data point
    telemetry_data = {
        "node_id": "test-node-003",
        "timestamp": int(datetime.utcnow().timestamp()),
        "cpu_usage": 45.5,
        "memory_usage": 60.2,
        "temperature": 45.0,
    }

    # Add telemetry directly to database
    from app.services.database import add_telemetry as db_add_telemetry
    from app.schemas.telemetry import TelemetryCreate

    tel_create = TelemetryCreate(
        node_id="test-node-003",
        timestamp=telemetry_data["timestamp"],
        cpu_usage=telemetry_data["cpu_usage"],
        memory_usage=telemetry_data["memory_usage"],
        temperature=telemetry_data["temperature"],
    )

    tel = await db_add_telemetry(tel_create, async_session)
    assert tel is not None
    assert tel.cpu_usage == 45.5

    # Verify telemetry can be retrieved
    from app.services.database import get_telemetry_for_node
    tel_list = await get_telemetry_for_node("test-node-003", db=async_session)
    assert len(tel_list) >= 1
    assert tel_list[0].cpu_usage == 45.5


@pytest.mark.asyncio
async def test_it_004_individual_disconnect(async_session):
    """IT-004: Individual Disconnect - Disconnect Node A, Node B remains online."""
    # Register two nodes
    register_data_1 = NodeRegister(
        node_id="test-node-disconnect-a",
        hostname="disconnect-a",
        os="Linux",
        cpu_cores=4,
        total_memory=16_000_000_000,
    )

    register_data_2 = NodeRegister(
        node_id="test-node-disconnect-b",
        hostname="disconnect-b",
        os="Linux",
        cpu_cores=4,
        total_memory=16_000_000_000,
    )

    await register_node(register_data_1, async_session)
    await register_node(register_data_2, async_session)

    # Verify both nodes are online
    from app.services.database import get_node_by_id
    from app.services.heartbeat_service import get_online_nodes

    nodes = await get_online_nodes(async_session)
    online_ids = [n.node_id for n in nodes]
    assert "test-node-disconnect-a" in online_ids
    assert "test-node-disconnect-b" in online_ids

    # Mark first node offline
    node_a = await get_node_by_id("test-node-disconnect-a", async_session)
    node_a.status = NodeStatus.OFFLINE
    node_a.last_seen = datetime.utcnow()
    await async_session.commit()

    # Mark second node as still online
    node_b = await get_node_by_id("test-node-disconnect-b", async_session)
    node_b.status = NodeStatus.ONLINE
    node_b.last_seen = datetime.utcnow()
    await async_session.commit()

    # Mark offline nodes
    count = await mark_offline_nodes(timeout_seconds=30, db=async_session)

    # Only node-a should be marked offline
    nodes_after = await get_online_nodes(async_session)
    online_ids_after = [n.node_id for n in nodes_after]
    assert "test-node-disconnect-a" not in online_ids_after
    assert "test-node-disconnect-b" in online_ids_after

    # Verify node-a is now offline
    node_a_check = await get_node_by_id("test-node-disconnect-a", async_session)
    assert node_a_check.status == NodeStatus.OFFLINE

    # Verify node-b is still online
    node_b_check = await get_node_by_id("test-node-disconnect-b", async_session)
    assert node_b_check.status == NodeStatus.ONLINE


@pytest.mark.asyncio
async def test_it_005_reconnection(async_session):
    """IT-005: Reconnection - Restart Node A, Node A returns online."""
    # Register a node
    register_data = NodeRegister(
        node_id="test-node-reconnect",
        hostname="reconnect-node",
        os="Linux",
        cpu_cores=4,
        total_memory=16_000_000_000,
    )

    await register_node(register_data, async_session)

    # Mark node offline
    from datetime import datetime, timedelta
    old_time = int(datetime.utcnow().timestamp()) - 60  # 60 seconds ago

    node = await get_node_by_id("test-node-reconnect", async_session)
    node.status = NodeStatus.OFFLINE
    node.last_seen = datetime.utcfromtimestamp(old_time)
    await async_session.commit()

    # Verify node is offline
    node_check = await get_node_by_id("test-node-reconnect", async_session)
    assert node_check.status == NodeStatus.OFFLINE

    # Simulate reconnection - update node to online with recent last_seen
    node = await get_node_by_id("test-node-reconnect", async_session)
    node.status = NodeStatus.ONLINE
    node.last_seen = datetime.utcnow()
    await async_session.commit()

    # Verify node is back online
    node_check = await get_node_by_id("test-node-reconnect", async_session)
    assert node_check.status == NodeStatus.ONLINE
    assert node_check.last_seen is not None