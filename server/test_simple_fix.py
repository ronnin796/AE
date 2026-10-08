"""Simple test to verify schema fixes"""
import json
from app.schemas.node import NodeBase
from app.schemas.telemetry import TelemetryCreate

# Test NodeBase schema with JSON strings
node_base = NodeBase(
    node_id="test-node",
    hostname="test-host",
    os="Linux",
    capabilities='["telemetry", "heartbeat"]',  # JSON string
    tags='{"env": "test", "region": "us-west"}'  # JSON string
)

print(f"Node ID: {node_base.node_id}")
print(f"Hostname: {node_base.hostname}")
print(f"Capabilities: {node_base.capabilities}")
print(f"Tags: {node_base.tags}")

# Test that validation works
assert node_base.capabilities == ["telemetry", "heartbeat"]
assert node_base.tags == {"env": "test", "region": "us-west"}

print("\nTest passed! NodeBase schema correctly parses JSON strings.")

# Test telemetry create
from app.schemas.telemetry import TelemetryCreate
telemetry = TelemetryCreate(
    node_id="test-node",
    timestamp=1234567890,
    cpu_usage=45.5,
    memory_usage=60.2,
    temperature=45.0
)

print(f"\nTelemetry test - Node ID: {telemetry.node_id}, CPU: {telemetry.cpu_usage}%")
print("\nAll tests passed successfully!")