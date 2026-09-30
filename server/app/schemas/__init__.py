"""Schemas package"""
from app.schemas.node import (
    NodeBase,
    NodeCapabilities,
    NodeListResponse,
    NodeRegister,
    NodeRegisterResponse,
    NodeResponse,
    NodeUpdate,
    ServerConfig,
)
from app.schemas.telemetry import (
    TelemetryBase,
    TelemetryCreate,
    TelemetryQuery,
    TelemetryResponse,
    TelemetryAggregated,
    TelemetryStats,
)

__all__ = [
    "NodeBase",
    "NodeCapabilities",
    "NodeListResponse",
    "NodeRegister",
    "NodeRegisterResponse",
    "NodeResponse",
    "NodeUpdate",
    "ServerConfig",
    "TelemetryBase",
    "TelemetryCreate",
    "TelemetryQuery",
    "TelemetryResponse",
    "TelemetryAggregated",
    "TelemetryStats",
]