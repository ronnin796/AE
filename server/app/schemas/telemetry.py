"""Telemetry Pydantic schemas for API"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class TelemetryBase(BaseModel):
    """Base telemetry schema"""
    node_id: str = Field(..., min_length=1, max_length=64)
    timestamp: int = Field(..., ge=0)
    cpu_usage: Optional[float] = Field(default=None, ge=0.0)
    cpu_per_core: Optional[list[float]] = None
    memory_usage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    memory_total: Optional[int] = Field(default=None, ge=0)
    memory_available: Optional[int] = Field(default=None, ge=0)
    memory_used: Optional[int] = Field(default=None, ge=0)
    temperature: Optional[float] = None
    temperatures: Optional[list[float]] = None
    uptime: Optional[int] = Field(default=None, ge=0)
    load_1: Optional[float] = None
    load_5: Optional[float] = None
    load_15: Optional[float] = None
    processes_running: Optional[int] = Field(default=None, ge=0)
    processes_total: Optional[int] = Field(default=None, ge=0)


class TelemetryCreate(TelemetryBase):
    """Schema for creating telemetry entry"""
    pass


class TelemetryResponse(TelemetryBase):
    """Schema for telemetry response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime] = None


class TelemetryQuery(BaseModel):
    """Query parameters for telemetry"""
    node_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class TelemetryAggregated(BaseModel):
    """Aggregated telemetry for charts"""
    node_id: str
    timestamps: list[int]
    cpu_usage: list[Optional[float]]
    memory_usage: list[Optional[float]]
    temperature: list[Optional[float]]
    load_1: list[Optional[float]]


class TelemetryStats(BaseModel):
    """Telemetry statistics for a node"""
    node_id: str
    count: int
    avg_cpu: Optional[float] = None
    max_cpu: Optional[float] = None
    avg_memory: Optional[float] = None
    max_memory: Optional[float] = None
    avg_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    latest_timestamp: Optional[int] = None


class TelemetrySummary(BaseModel):
    """Telemetry summary for all nodes"""
    nodes: Dict[str, TelemetryStats]


class TelemetryLatest(BaseModel):
    """Latest telemetry for a node"""
    node_id: str
    timestamp: int
    cpu_usage: Optional[float] = None
    cpu_per_core: Optional[list[float]] = None
    memory_usage: Optional[float] = None
    memory_total: Optional[int] = None
    memory_available: Optional[int] = None
    memory_used: Optional[int] = None
    temperature: Optional[float] = None
    temperatures: Optional[list[float]] = None
    uptime: Optional[int] = None
    load_1: Optional[float] = None
    load_5: Optional[float] = None
    load_15: Optional[float] = None
    processes_running: Optional[int] = None
    processes_total: Optional[int] = None
    age_seconds: Optional[int] = None