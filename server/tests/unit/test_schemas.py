"""Unit tests for Pydantic schemas"""

import pytest
from datetime import datetime
from app.schemas.node import (
    NodeBase,
    NodeRegister,
    NodeRegisterResponse,
    NodeUpdate,
    NodeResponse,
    ServerConfig,
    NodeListResponse,
)
from app.schemas.telemetry import (
    TelemetryBase,
    TelemetryCreate,
    TelemetryResponse,
    TelemetryQuery,
    TelemetryAggregated,
    TelemetryStats,
)


class TestNodeSchemas:
    """Tests for node-related schemas"""

    def test_node_base_valid(self):
        """Test NodeBase with valid data"""
        node = NodeBase(
            node_id="test-node",
            hostname="test-host",
            os="Linux",
            os_version="6.1",
            kernel_version="6.1.0",
            cpu_brand="Intel i7",
            cpu_cores=8,
            total_memory=16_000_000_000,
            version="0.1.0",
            arch="x86_64",
        )
        assert node.node_id == "test-node"
        assert node.cpu_cores == 8

    def test_node_base_minimal(self):
        """Test NodeBase with only required fields"""
        node = NodeBase(
            node_id="test-node",
            hostname="test-host",
            os="Linux",
        )
        assert node.node_id == "test-node"
        assert node.os_version is None
        assert node.cpu_cores is None

    def test_node_register(self):
        """Test NodeRegister schema"""
        reg = NodeRegister(
            node_id="test-node",
            hostname="test-host",
            os="Linux",
            os_version="6.1",
            kernel_version="6.1.0",
            cpu_brand="AMD Ryzen",
            cpu_cores=16,
            total_memory=32_000_000_000,
            version="0.1.0",
            arch="x86_64",
        )
        assert reg.node_id == "test-node"

    def test_node_register_response(self):
        """Test NodeRegisterResponse schema"""
        resp = NodeRegisterResponse(
            success=True,
            node_id="test-node",
            assigned_id="1",
            message="Node registered successfully",
            server_time=1234567890,
            config=ServerConfig(
                heartbeat_interval=10,
                telemetry_interval=2,
                model_update_url=None,
            ),
        )
        assert resp.success is True
        assert resp.config.heartbeat_interval == 10

    def test_node_update(self):
        """Test NodeUpdate schema (partial update)"""
        update = NodeUpdate(hostname="new-host", cpu_cores=16)
        assert update.hostname == "new-host"
        assert update.cpu_cores == 16
        assert update.os_version is None  # Not provided

    def test_server_config(self):
        """Test ServerConfig schema"""
        config = ServerConfig(
            heartbeat_interval=10,
            telemetry_interval=2,
            model_update_url="http://example.com/model",
        )
        assert config.heartbeat_interval == 10
        assert config.model_update_url == "http://example.com/model"

    def test_node_capabilities(self):
        """Test capabilities field accepts list of strings and JSON string"""
        node = NodeBase(
            node_id="test-node",
            hostname="test-host",
            capabilities=["telemetry", "heartbeat", "inference"],
        )
        assert node.capabilities == ["telemetry", "heartbeat", "inference"]

        node2 = NodeBase(
            node_id="test-node",
            hostname="test-host",
            capabilities='["telemetry", "heartbeat"]',
        )
        assert node2.capabilities == ["telemetry", "heartbeat"]

    def test_node_list_response(self):
        """Test NodeListResponse schema"""
        resp = NodeListResponse(nodes=[], total=0, page=1, page_size=20)
        assert resp.total == 0
        assert resp.page == 1


class TestTelemetrySchemas:
    """Tests for telemetry-related schemas"""

    def test_telemetry_base_valid(self):
        """Test TelemetryBase with valid data"""
        tel = TelemetryBase(
            node_id="test-node",
            timestamp=1234567890,
            cpu_usage=45.5,
            cpu_per_core=[10.0, 20.0, 30.0, 40.0],
            memory_usage=60.0,
            memory_total=16_000_000_000,
            memory_available=6_400_000_000,
            memory_used=9_600_000_000,
            temperature=55.0,
            temperatures=[50.0, 55.0, 60.0],
            uptime=3600,
            load_1=1.5,
            load_5=1.2,
            load_15=1.0,
            processes_running=10,
            processes_total=200,
        )
        assert tel.cpu_usage == 45.5
        assert len(tel.cpu_per_core) == 4

    def test_telemetry_base_minimal(self):
        """Test TelemetryBase with only required fields"""
        tel = TelemetryBase(node_id="test-node", timestamp=1234567890)
        assert tel.node_id == "test-node"
        assert tel.cpu_usage is None
        assert tel.cpu_per_core is None

    def test_telemetry_create(self):
        """Test TelemetryCreate schema"""
        create = TelemetryCreate(
            node_id="test-node",
            timestamp=1234567890,
            cpu_usage=50.0,
        )
        assert create.node_id == "test-node"
        assert create.cpu_usage == 50.0

    def test_telemetry_query_defaults(self):
        """Test TelemetryQuery default values"""
        query = TelemetryQuery()
        assert query.limit == 100
        assert query.offset == 0
        assert query.node_id is None

    def test_telemetry_query_custom(self):
        """Test TelemetryQuery with custom values"""
        query = TelemetryQuery(
            node_id="test-node",
            limit=50,
            offset=10,
        )
        assert query.node_id == "test-node"
        assert query.limit == 50
        assert query.offset == 10

    def test_telemetry_aggregated(self):
        """Test TelemetryAggregated schema"""
        agg = TelemetryAggregated(
            node_id="test-node",
            timestamps=[1234567890, 1234567891],
            cpu_usage=[50.0, 55.0],
            memory_usage=[60.0, 62.0],
            temperature=[55.0, 56.0],
            load_1=[1.5, 1.6],
        )
        assert agg.node_id == "test-node"
        assert len(agg.timestamps) == 2
        assert len(agg.cpu_usage) == 2

    def test_telemetry_stats(self):
        """Test TelemetryStats schema"""
        stats = TelemetryStats(
            node_id="test-node",
            count=100,
            avg_cpu=45.5,
            max_cpu=90.0,
            avg_memory=60.0,
            max_memory=85.0,
            avg_temperature=55.0,
            max_temperature=70.0,
            latest_timestamp=1234567890,
        )
        assert stats.count == 100
        assert stats.avg_cpu == 45.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])