"""Unit tests for node registration service"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.node import Node, NodeStatus
from app.services.node_service import (
    register_node,
    update_node_status,
    mark_offline_nodes,
)
from app.schemas.node import NodeRegister, ServerConfig


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
async def test_register_new_node(async_session):
    """Test registering a new node"""
    register_data = NodeRegister(
        node_id="test-node-new",
        hostname="new-host",
        os="Linux",
        os_version="6.1",
        kernel_version="6.1.0",
        cpu_brand="Test CPU",
        cpu_cores=8,
        total_memory=16_000_000_000,
        version="0.1.0",
        arch="x86_64",
    )

    response = await register_node(register_data, async_session)

    assert response.success is True
    assert response.node_id == "test-node-new"
    assert response.assigned_id is not None
    assert response.message == "Node registered successfully"
    assert response.server_time > 0
    assert response.config is not None
    assert isinstance(response.config, ServerConfig)


@pytest.mark.asyncio
async def test_register_existing_node_updates(async_session):
    """Test registering existing node updates its information"""
    # Register first time
    register_data = NodeRegister(
        node_id="test-node-existing",
        hostname="old-host",
        os="Linux",
        cpu_cores=4,
        total_memory=8_000_000_000,
    )
    await register_node(register_data, async_session)

    # Register again with updated info
    updated_data = NodeRegister(
        node_id="test-node-existing",
        hostname="new-host",
        os="Linux",
        os_version="6.2",
        kernel_version="6.2.0",
        cpu_brand="Updated CPU",
        cpu_cores=16,
        total_memory=32_000_000_000,
        version="0.2.0",
        arch="x86_64",
    )

    response = await register_node(updated_data, async_session)

    assert response.success is True
    assert response.message == "Node updated successfully"

    # Verify node was updated
    from app.services.database import get_node_by_id
    node = await get_node_by_id("test-node-existing", async_session)
    assert node.hostname == "new-host"
    assert node.os_version == "6.2"
    assert node.cpu_brand == "Updated CPU"
    assert node.cpu_cores == 16
    assert node.total_memory == 32_000_000_000
    assert node.version == "0.2.0"
    assert node.status == NodeStatus.ONLINE


@pytest.mark.asyncio
async def test_update_node_status(async_session):
    """Test manually updating node status"""
    register_data = NodeRegister(
        node_id="test-node-status",
        hostname="status-host",
        os="Linux",
    )
    await register_node(register_data, async_session)

    # Update to DEGRADED
    node = await update_node_status("test-node-status", NodeStatus.DEGRADED, async_session)
    assert node.status == NodeStatus.DEGRADED
    assert node.last_seen is not None

    # Update to MAINTENANCE
    node = await update_node_status("test-node-status", NodeStatus.MAINTENANCE, async_session)
    assert node.status == NodeStatus.MAINTENANCE


@pytest.mark.asyncio
async def test_update_node_status_not_found(async_session):
    """Test updating status of non-existent node raises ValueError"""
    with pytest.raises(ValueError, match="Node non-existent not found"):
        await update_node_status("non-existent", NodeStatus.OFFLINE, async_session)


@pytest.mark.asyncio
async def test_mark_offline_nodes(async_session):
    """Test marking nodes offline based on timeout"""
    from app.services.database import get_node_by_id

    # Create nodes with different last_seen times (timezone-aware UTC)
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(seconds=60)  # 60 seconds ago
    recent_time = now - timedelta(seconds=5)  # 5 seconds ago

    # Node 1: old last_seen (should be marked offline with 30s timeout)
    node1 = Node(
        node_id="test-node-old",
        hostname="old-host",
        os="Linux",
        status=NodeStatus.ONLINE,
        last_seen=old_time,
    )
    async_session.add(node1)

    # Node 2: recent last_seen (should stay online)
    node2 = Node(
        node_id="test-node-recent",
        hostname="recent-host",
        os="Linux",
        status=NodeStatus.ONLINE,
        last_seen=recent_time,
    )
    async_session.add(node2)

    # Node 3: already offline (should not be counted)
    node3 = Node(
        node_id="test-node-offline",
        hostname="offline-host",
        os="Linux",
        status=NodeStatus.OFFLINE,
        last_seen=old_time,
    )
    async_session.add(node3)

    await async_session.commit()

    # Mark offline with 30 second timeout
    count = await mark_offline_nodes(timeout_seconds=30, db=async_session)

    assert count == 1  # Only node1 should be marked offline

    # Verify node1 is now offline
    node1_check = await get_node_by_id("test-node-old", async_session)
    assert node1_check.status == NodeStatus.OFFLINE

    # Verify node2 is still online
    node2_check = await get_node_by_id("test-node-recent", async_session)
    assert node2_check.status == NodeStatus.ONLINE

    # Verify node3 unchanged
    node3_check = await get_node_by_id("test-node-offline", async_session)
    assert node3_check.status == NodeStatus.OFFLINE


@pytest.mark.asyncio
async def test_mark_offline_nodes_custom_timeout(async_session):
    """Test mark_offline_nodes with custom timeout"""
    from app.services.database import get_node_by_id

    # Create node with last_seen 100 seconds ago (timezone-aware UTC)
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(seconds=100)
    node = Node(
        node_id="test-node-custom-timeout",
        hostname="custom-timeout-host",
        os="Linux",
        status=NodeStatus.ONLINE,
        last_seen=old_time,
    )
    async_session.add(node)
    await async_session.commit()

    # With 200s timeout, should NOT be marked offline
    count = await mark_offline_nodes(timeout_seconds=200, db=async_session)
    assert count == 0

    node_check = await get_node_by_id("test-node-custom-timeout", async_session)
    assert node_check.status == NodeStatus.ONLINE

    # With 50s timeout, SHOULD be marked offline
    count = await mark_offline_nodes(timeout_seconds=50, db=async_session)
    assert count == 1

    node_check = await get_node_by_id("test-node-custom-timeout", async_session)
    assert node_check.status == NodeStatus.OFFLINE