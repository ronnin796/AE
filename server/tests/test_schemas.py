"""Unit tests for telemetry validation and schemas"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.telemetry import (
    TelemetryBase,
    TelemetryCreate,
    TelemetryResponse,
    TelemetryQuery,
    TelemetryAggregated,
    TelemetryStats,
)
from app.schemas.node import (
    NodeBase,
    NodeRegister,
    NodeRegisterResponse,
    NodeUpdate,
    NodeResponse,
    NodeListResponse,
    ServerConfig,
)


class TestTelemetrySchemas:
    """Tests for telemetry Pydantic schemas"""

    def test_telemetry_base_valid(self):
        """Test valid telemetry base data"""
        data = TelemetryBase(
            node_id="test-node",
            timestamp=int(datetime.utcnow().timestamp()),
            cpu_usage=45.5,
            memory_usage=60.0,
            temperature=55.0,
        )
        assert data.node_id == "test-node"
        assert data.cpu_usage == 45.5
        assert data.memory_usage == 60.0
        assert data.temperature == 55.0

    def test_telemetry_base_cpu_usage_validation(self):
        """Test CPU usage must be >= 0"""
        with pytest.raises(ValidationError) as exc_info:
            TelemetryBase(
                node_id="test-node",
                timestamp=int(datetime.utcnow().timestamp()),
                cpu_usage=-1.0,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_telemetry_base_memory_usage_bounds(self):
        """Test memory usage must be 0-100"""
        with pytest.raises(ValidationError):
            TelemetryBase(
                node_id="test-node",
                timestamp=int(datetime.utcnow().timestamp()),
                memory_usage=150.0,
            )

        with pytest.raises(ValidationError):
            TelemetryBase(
                node_id="test-node",
                timestamp=int(datetime.utcnow().timestamp()),
                memory_usage=-10.0,
            )

        # Valid bounds
        data = TelemetryBase(
            node_id="test-node",
            timestamp=int(datetime.utcnow().timestamp()),
            memory_usage=0.0,
        )
        assert data.memory_usage == 0.0

        data = TelemetryBase(
            node_id="test-node",
            timestamp=int(datetime.utcnow().timestamp()),
            memory_usage=100.0,
        )
        assert data.memory_usage == 100.0

    def test_telemetry_base_optional_fields(self):
        """Test optional fields can be omitted"""
        data = TelemetryBase(
            node_id="test-node",
            timestamp=int(datetime.utcnow().timestamp()),
        )
        assert data.cpu_usage is None
        assert data.memory_usage is None
        assert data.temperature is None
        assert data.cpu_per_core is None
        assert data.temperatures is None

    def test_telemetry_create_inherits_base(self):
        """Test TelemetryCreate inherits from TelemetryBase"""
        data = TelemetryCreate(
            node_id="test-node",
            timestamp=int(datetime.utcnow().timestamp()),
            cpu_usage=30.0,
        )
        assert isinstance(data, TelemetryBase)
        assert data.cpu_usage == 30.0

    def test_telemetry_query_defaults(self):
        """Test TelemetryQuery default values"""
        query = TelemetryQuery()
        assert query.node_id is None
        assert query.start_time is None
        assert query.end_time is None
        assert query.limit == 100
        assert query.offset == 0

    def test_telemetry_query_limit_bounds(self):
        """Test limit bounds"""
        with pytest.raises(ValidationError):
            TelemetryQuery(limit=0)
        with pytest.raises(ValidationError):
            TelemetryQuery(limit=1001)

        # Valid
        query = TelemetryQuery(limit=500)
        assert query.limit == 500

    def test_telemetry_aggregated_structure(self):
        """Test TelemetryAggregated structure"""
        aggregated = TelemetryAggregated(
            node_id="test-node",
            timestamps=[1000, 2000, 3000],
            cpu_usage=[10.0, 20.0, 30.0],
            memory_usage=[50.0, 55.0, 60.0],
            temperature=[40.0, 42.0, 45.0],
            load_1=[1.0, 1.2, 1.5],
        )
        assert aggregated.node_id == "test-node"
        assert len(aggregated.timestamps) == 3
        assert len(aggregated.cpu_usage) == 3

    def test_telemetry_stats_structure(self):
        """Test TelemetryStats structure"""
        stats = TelemetryStats(
            node_id="test-node",
            count=100,
            avg_cpu=25.5,
            max_cpu=80.0,
            avg_memory=60.0,
            max_memory=90.0,
            avg_temperature=55.0,
            max_temperature=70.0,
            latest_timestamp=int(datetime.utcnow().timestamp()),
        )
        assert stats.count == 100
        assert stats.avg_cpu == 25.5
        assert stats.max_cpu == 80.0


class TestNodeSchemas:
    """Tests for node Pydantic schemas"""

    def test_node_capabilities_defaults(self):
        """Test capabilities field defaults to None and accepts list of strings"""
        data = NodeBase(node_id="test-node", hostname="test-host")
        assert data.capabilities is None

        data2 = NodeBase(
            node_id="test-node",
            hostname="test-host",
            capabilities=["telemetry", "heartbeat", "inference"],
        )
        assert data2.capabilities == ["telemetry", "heartbeat", "inference"]

    def test_node_capabilities_json_string(self):
        """Test capabilities can be provided as a JSON string"""
        data = NodeBase(
            node_id="test-node",
            hostname="test-host",
            capabilities='["telemetry", "heartbeat"]',
        )
        assert data.capabilities == ["telemetry", "heartbeat"]

    def test_node_base_required_fields(self):
        """Test NodeBase required fields"""
        data = NodeBase(
            node_id="test-node",
            hostname="test-host",
        )
        assert data.node_id == "test-node"
        assert data.hostname == "test-host"
        assert data.os == "Linux"  # default

    def test_node_base_optional_fields(self):
        """Test NodeBase optional fields"""
        data = NodeBase(
            node_id="test-node",
            hostname="test-host",
            os_version="6.1",
            kernel_version="6.1.0",
            cpu_brand="Test CPU",
            cpu_cores=8,
            total_memory=16_000_000_000,
            version="0.1.0",
            arch="x86_64",
        )
        assert data.cpu_cores == 8
        assert data.total_memory == 16_000_000_000

    def test_node_base_cpu_cores_validation(self):
        """Test cpu_cores must be >= 1"""
        with pytest.raises(ValidationError):
            NodeBase(node_id="test", hostname="host", cpu_cores=0)

    def test_node_register_inherits_base(self):
        """Test NodeRegister inherits from NodeBase"""
        data = NodeRegister(node_id="test", hostname="host")
        assert isinstance(data, NodeBase)

    def test_node_register_response(self):
        """Test NodeRegisterResponse structure"""
        response = NodeRegisterResponse(
            success=True,
            node_id="test-node",
            assigned_id="1",
            message="Success",
            server_time=1234567890,
            config=ServerConfig(),
        )
        assert response.success is True
        assert response.config.heartbeat_interval == 10
        assert response.config.telemetry_interval == 2

    def test_server_config_defaults(self):
        """Test ServerConfig default values"""
        config = ServerConfig()
        assert config.heartbeat_interval == 10
        assert config.telemetry_interval == 2
        assert config.model_update_url is None

    def test_node_update_partial(self):
        """Test NodeUpdate allows partial updates"""
        update = NodeUpdate(hostname="new-host")
        assert update.hostname == "new-host"
        assert update.os_version is None
        assert update.cpu_cores is None

    def test_node_response_from_orm(self):
        """Test NodeResponse can be created from ORM model"""
        # This is mostly a structural test
        response = NodeResponse(
            id=1,
            node_id="test-node",
            hostname="test-host",
            os="Linux",
            status="online",
            last_seen=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert response.id == 1
        assert response.status == "online"

    def test_node_list_response(self):
        """Test NodeListResponse structure"""
        list_resp = NodeListResponse(
            nodes=[],
            total=0,
            page=1,
            page_size=20,
        )
        assert list_resp.total == 0
        assert list_resp.page == 1
        assert list_resp.page_size == 20


class TestTelemetryEdgeCases:
    """Edge case tests for telemetry"""

    def test_cpu_per_core_list(self):
        """Test cpu_per_core accepts list of floats"""
        data = TelemetryBase(
            node_id="test",
            timestamp=1234567890,
            cpu_per_core=[10.0, 20.0, 15.0, 25.0],
        )
        assert len(data.cpu_per_core) == 4
        assert data.cpu_per_core[0] == 10.0

    def test_temperatures_list(self):
        """Test temperatures accepts list of floats"""
        data = TelemetryBase(
            node_id="test",
            timestamp=1234567890,
            temperatures=[45.0, 50.0, 55.0],
        )
        assert len(data.temperatures) == 3

    def test_negative_temperature_allowed(self):
        """Test negative temperatures are allowed (valid for some sensors)"""
        data = TelemetryBase(
            node_id="test",
            timestamp=1234567890,
            temperature=-10.0,
        )
        assert data.temperature == -10.0

    def test_large_memory_values(self):
        """Test large memory values (bytes)"""
        data = TelemetryBase(
            node_id="test",
            timestamp=1234567890,
            memory_total=64_000_000_000,  # 64 GB
            memory_available=32_000_000_000,
            memory_used=32_000_000_000,
        )
        assert data.memory_total == 64_000_000_000