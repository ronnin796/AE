"""Unit tests for database service layer"""

import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.node import Node, NodeStatus
from app.models.telemetry import Telemetry
from app.services.database import (
    get_node_by_id,
    create_node,
    update_node,
    list_nodes,
    add_telemetry,
    get_telemetry,
    get_telemetry_for_node,
    get_telemetry_stats,
)
from app.schemas.node import NodeRegister, NodeUpdate
from app.schemas.telemetry import TelemetryCreate


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


@pytest.mark.asyncio
async def test_create_node(async_session):
    """Test creating a new node"""
    register_data = NodeRegister(
        node_id="test-node-001",
        hostname="test-host",
        os="Linux",
        os_version="6.1",
        kernel_version="6.1.0",
        cpu_brand="Test CPU",
        cpu_cores=4,
        total_memory=8_000_000_000,
        version="0.1.0",
        arch="x86_64",
    )

    node = await create_node(register_data, async_session)

    assert node.node_id == "test-node-001"
    assert node.hostname == "test-host"
    assert node.status == NodeStatus.ONLINE
    assert node.id is not None


@pytest.mark.asyncio
async def test_get_node_by_id(async_session):
    """Test retrieving a node by node_id"""
    register_data = NodeRegister(
        node_id="test-node-002",
        hostname="test-host-2",
        os="Linux",
        cpu_cores=8,
        total_memory=16_000_000_000,
    )
    await create_node(register_data, async_session)

    node = await get_node_by_id("test-node-002", async_session)

    assert node is not None
    assert node.node_id == "test-node-002"
    assert node.cpu_cores == 8


@pytest.mark.asyncio
async def test_get_node_by_id_not_found(async_session):
    """Test retrieving non-existent node returns None"""
    node = await get_node_by_id("non-existent", async_session)
    assert node is None


@pytest.mark.asyncio
async def test_update_node(async_session):
    """Test updating node information"""
    register_data = NodeRegister(
        node_id="test-node-003",
        hostname="old-host",
        os="Linux",
    )
    await create_node(register_data, async_session)

    update_data = NodeUpdate(
        hostname="new-host",
        cpu_brand="New CPU",
        cpu_cores=16,
    )

    updated_node = await update_node("test-node-003", update_data, async_session)

    assert updated_node.hostname == "new-host"
    assert updated_node.cpu_brand == "New CPU"
    assert updated_node.cpu_cores == 16


@pytest.mark.asyncio
async def test_update_node_not_found(async_session):
    """Test updating non-existent node raises ValueError"""
    update_data = NodeUpdate(hostname="new-host")
    with pytest.raises(ValueError, match="Node non-existent not found"):
        await update_node("non-existent", update_data, async_session)


@pytest.mark.asyncio
async def test_list_nodes(async_session):
    """Test listing nodes with pagination"""
    # Create multiple nodes
    for i in range(5):
        register_data = NodeRegister(
            node_id=f"test-node-list-{i}",
            hostname=f"host-{i}",
            os="Linux",
        )
        await create_node(register_data, async_session)

    result = await list_nodes(page=1, page_size=3, db=async_session)

    assert result["total"] == 5
    assert result["page"] == 1
    assert result["page_size"] == 3
    assert len(result["nodes"]) == 3


@pytest.mark.asyncio
async def test_add_telemetry(async_session):
    """Test adding telemetry data"""
    # First create a node
    register_data = NodeRegister(
        node_id="test-node-telemetry",
        hostname="telemetry-host",
        os="Linux",
        cpu_cores=4,
        total_memory=8_000_000_000,
    )
    await create_node(register_data, async_session)

    # Add telemetry
    telemetry_data = TelemetryCreate(
        node_id="test-node-telemetry",
        timestamp=int(datetime.utcnow().timestamp()),
        cpu_usage=45.5,
        memory_usage=60.2,
        memory_total=8_000_000_000,
        memory_available=3_200_000_000,
        memory_used=4_800_000_000,
        temperature=55.0,
        uptime=3600,
        load_1=1.5,
        load_5=1.2,
        load_15=1.0,
        processes_running=2,
        processes_total=150,
    )

    telemetry = await add_telemetry(telemetry_data, async_session)

    assert telemetry.node_id == 1  # node.id
    assert telemetry.cpu_usage == 45.5
    assert telemetry.memory_usage == 60.2
    assert telemetry.temperature == 55.0


@pytest.mark.asyncio
async def test_add_telemetry_node_not_found(async_session):
    """Test adding telemetry for non-existent node raises ValueError"""
    telemetry_data = TelemetryCreate(
        node_id="non-existent",
        timestamp=int(datetime.utcnow().timestamp()),
    )
    with pytest.raises(ValueError, match="Node non-existent not found"):
        await add_telemetry(telemetry_data, async_session)


@pytest.mark.asyncio
async def test_get_telemetry(async_session):
    """Test retrieving telemetry with filters"""
    # Create node
    register_data = NodeRegister(
        node_id="test-node-get-tel",
        hostname="tel-host",
        os="Linux",
    )
    await create_node(register_data, async_session)

    # Add multiple telemetry points
    base_time = int(datetime.utcnow().timestamp())
    for i in range(3):
        telemetry_data = TelemetryCreate(
            node_id="test-node-get-tel",
            timestamp=base_time + i * 10,
            cpu_usage=float(i * 10),
            memory_usage=50.0,
        )
        await add_telemetry(telemetry_data, async_session)

    # Get all telemetry
    telemetry_list = await get_telemetry(node_id="test-node-get-tel", limit=10, db=async_session)
    assert len(telemetry_list) == 3

    # Get with time filter
    telemetry_list = await get_telemetry(
        node_id="test-node-get-tel",
        start_time=datetime.fromtimestamp(base_time + 5),
        limit=10,
        db=async_session
    )
    assert len(telemetry_list) == 2


@pytest.mark.asyncio
async def test_get_telemetry_for_node(async_session):
    """Test get_telemetry_for_node convenience function"""
    register_data = NodeRegister(
        node_id="test-node-for-node",
        hostname="for-node-host",
        os="Linux",
    )
    await create_node(register_data, async_session)

    telemetry_data = TelemetryCreate(
        node_id="test-node-for-node",
        timestamp=int(datetime.utcnow().timestamp()),
        cpu_usage=25.0,
    )
    await add_telemetry(telemetry_data, async_session)

    telemetry_list = await get_telemetry_for_node("test-node-for-node", db=async_session)
    assert len(telemetry_list) == 1


@pytest.mark.asyncio
async def test_get_telemetry_stats(async_session):
    """Test getting aggregated telemetry statistics"""
    register_data = NodeRegister(
        node_id="test-node-stats",
        hostname="stats-host",
        os="Linux",
    )
    await create_node(register_data, async_session)

    # Add multiple telemetry points
    base_time = int(datetime.utcnow().timestamp())
    for i in range(5):
        telemetry_data = TelemetryCreate(
            node_id="test-node-stats",
            timestamp=base_time + i * 10,
            cpu_usage=float(i * 10),
            memory_usage=50.0 + i,
            temperature=40.0 + i,
        )
        await add_telemetry(telemetry_data, async_session)

    stats = await get_telemetry_stats("test-node-stats", db=async_session)

    assert stats["node_id"] == "test-node-stats"
    assert stats["count"] == 5
    assert stats["avg_cpu"] == 20.0  # (0+10+20+30+40)/5
    assert stats["max_cpu"] == 40.0
    assert stats["avg_memory"] == 52.0  # (50+51+52+53+54)/5
    assert stats["max_memory"] == 54.0
    assert stats["avg_temperature"] == 42.0  # (40+41+42+43+44)/5
    assert stats["max_temperature"] == 44.0
    assert stats["latest_timestamp"] is not None


@pytest.mark.asyncio
async def test_get_telemetry_stats_node_not_found(async_session):
    """Test getting stats for non-existent node raises ValueError"""
    with pytest.raises(ValueError, match="Node non-existent not found"):
        await get_telemetry_stats("non-existent", async_session)