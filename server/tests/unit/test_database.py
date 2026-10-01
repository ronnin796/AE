"""Unit tests for database service layer"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.models.node import Node, NodeStatus
from app.models.telemetry import Telemetry
from app.schemas.node import NodeRegister, NodeUpdate, NodeResponse
from app.schemas.telemetry import TelemetryCreate


class TestNodeDatabase:
    """Tests for node database operations"""

    @pytest.mark.asyncio
    async def test_get_node_by_id_found(self, async_session: AsyncSession):
        """Test getting existing node by node_id"""
        # Create a node directly in the database
        node = Node(
            node_id="test-node",
            hostname="test-host",
            os="Linux",
            status=NodeStatus.ONLINE,
        )
        async_session.add(node)
        await async_session.commit()

        # Retrieve it
        result = await get_node_by_id("test-node", async_session)
        assert result is not None
        assert result.node_id == "test-node"
        assert result.hostname == "test-host"

    @pytest.mark.asyncio
    async def test_get_node_by_id_not_found(self, async_session: AsyncSession):
        """Test getting non-existent node returns None"""
        result = await get_node_by_id("non-existent", async_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_node(self, async_session: AsyncSession):
        """Test creating a new node"""
        register_data = NodeRegister(
            node_id="new-node",
            hostname="new-host",
            os="Linux",
            os_version="6.1",
            kernel_version="6.1.0",
            cpu_brand="Intel i7",
            cpu_cores=8,
            total_memory=16_000_000_000,
            version="0.1.0",
            arch="x86_64",
        )

        node = await create_node(register_data, async_session)
        assert node.node_id == "new-node"
        assert node.hostname == "new-host"
        assert node.status == NodeStatus.ONLINE
        assert node.id is not None

    @pytest.mark.asyncio
    async def test_update_node(self, async_session: AsyncSession):
        """Test updating node information"""
        # Create node first
        node = Node(
            node_id="update-test",
            hostname="old-host",
            os="Linux",
            status=NodeStatus.ONLINE,
        )
        async_session.add(node)
        await async_session.commit()

        # Update it
        update_data = NodeUpdate(hostname="new-host", cpu_cores=16)
        updated = await update_node("update-test", update_data, async_session)

        assert updated.hostname == "new-host"
        assert updated.cpu_cores == 16
        assert updated.node_id == "update-test"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_node_not_found(self, async_session: AsyncSession):
        """Test updating non-existent node raises ValueError"""
        update_data = NodeUpdate(hostname="new-host")
        with pytest.raises(ValueError, match="Node non-existent not found"):
            await update_node("non-existent", update_data, async_session)

    @pytest.mark.asyncio
    async def test_list_nodes_pagination(self, async_session: AsyncSession):
        """Test listing nodes with pagination"""
        # Create multiple nodes
        for i in range(5):
            node = Node(
                node_id=f"node-{i}",
                hostname=f"host-{i}",
                os="Linux",
                status=NodeStatus.ONLINE,
            )
            async_session.add(node)
        await async_session.commit()

        # Test page 1
        result = await list_nodes(page=1, page_size=2, db=async_session)
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert result["total"] == 5
        assert len(result["nodes"]) == 2

        # Test page 2
        result = await list_nodes(page=2, page_size=2, db=async_session)
        assert result["page"] == 2
        assert len(result["nodes"]) == 2

        # Test page 3 (last page)
        result = await list_nodes(page=3, page_size=2, db=async_session)
        assert result["page"] == 3
        assert len(result["nodes"]) == 1


class TestTelemetryDatabase:
    """Tests for telemetry database operations"""

    @pytest.mark.asyncio
    async def test_add_telemetry(self, async_session: AsyncSession):
        """Test adding telemetry data point"""
        # Create node first
        node = Node(
            node_id="telemetry-node",
            hostname="telemetry-host",
            os="Linux",
            status=NodeStatus.ONLINE,
        )
        async_session.add(node)
        await async_session.commit()

        # Add telemetry
        telemetry_data = TelemetryCreate(
            node_id="telemetry-node",
            timestamp=int(datetime.utcnow().timestamp()),
            cpu_usage=50.0,
            memory_usage=60.0,
            temperature=55.0,
        )

        telemetry = await add_telemetry(telemetry_data, async_session)
        assert telemetry.node_id == node.id  # FK to node
        assert telemetry.cpu_usage == 50.0
        assert telemetry.memory_usage == 60.0
        assert telemetry.temperature == 55.0

        # Verify node last_seen was updated
        await async_session.refresh(node)
        assert node.status == NodeStatus.ONLINE

    @pytest.mark.asyncio
    async def test_add_telemetry_node_not_found(self, async_session: AsyncSession):
        """Test adding telemetry for non-existent node raises ValueError"""
        telemetry_data = TelemetryCreate(
            node_id="non-existent",
            timestamp=int(datetime.utcnow().timestamp()),
            cpu_usage=50.0,
        )

        with pytest.raises(ValueError, match="Node non-existent not found"):
            await add_telemetry(telemetry_data, async_session)

    @pytest.mark.asyncio
    async def test_get_telemetry(self, async_session: AsyncSession):
        """Test getting telemetry with filters"""
        # Create node and telemetry
        node = Node(
            node_id="telemetry-node-2",
            hostname="host-2",
            os="Linux",
            status=NodeStatus.ONLINE,
        )
        async_session.add(node)
        await async_session.commit()

        # Add multiple telemetry points
        for i in range(3):
            tel = Telemetry(
                node_id=node.id,
                timestamp=datetime.utcnow(),
                cpu_usage=float(i * 10),
                memory_usage=50.0,
            )
            async_session.add(tel)
        await async_session.commit()

        # Get telemetry
        result = await get_telemetry(node_id="telemetry-node-2", limit=10, db=async_session)
        assert len(result) == 3
        assert all(t.node_id == node.id for t in result)

    @pytest.mark.asyncio
    async def test_get_telemetry_for_node(self, async_session: AsyncSession):
        """Test getting telemetry for specific node"""
        node = Node(
            node_id="telemetry-node-3",
            hostname="host-3",
            os="Linux",
            status=NodeStatus.ONLINE,
        )
        async_session.add(node)
        await async_session.commit()

        tel = Telemetry(
            node_id=node.id,
            timestamp=datetime.utcnow(),
            cpu_usage=75.0,
        )
        async_session.add(tel)
        await async_session.commit()

        result = await get_telemetry_for_node("telemetry-node-3", db=async_session)
        assert len(result) == 1
        assert result[0].cpu_usage == 75.0

    @pytest.mark.asyncio
    async def test_get_telemetry_stats(self, async_session: AsyncSession):
        """Test getting aggregated telemetry statistics"""
        node = Node(
            node_id="stats-node",
            hostname="stats-host",
            os="Linux",
            status=NodeStatus.ONLINE,
        )
        async_session.add(node)
        await async_session.commit()

        # Add telemetry with known values
        for cpu_val in [10.0, 20.0, 30.0, 40.0, 50.0]:
            tel = Telemetry(
                node_id=node.id,
                timestamp=datetime.utcnow(),
                cpu_usage=cpu_val,
                memory_usage=50.0,
                temperature=40.0 + cpu_val,
            )
            async_session.add(tel)
        await async_session.commit()

        stats = await get_telemetry_stats("stats-node", async_session)
        assert stats["node_id"] == "stats-node"
        assert stats["count"] == 5
        assert stats["avg_cpu"] == 30.0  # (10+20+30+40+50)/5
        assert stats["max_cpu"] == 50.0
        assert stats["avg_memory"] == 50.0
        assert stats["avg_temperature"] == 70.0  # (50+60+70+80+90)/5
        assert stats["max_temperature"] == 90.0

    @pytest.mark.asyncio
    async def test_get_telemetry_stats_node_not_found(self, async_session: AsyncSession):
        """Test getting stats for non-existent node raises ValueError"""
        with pytest.raises(ValueError, match="Node non-existent not found"):
            await get_telemetry_stats("non-existent", async_session)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])