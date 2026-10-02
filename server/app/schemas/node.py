"""Node Pydantic schemas for API"""

import json
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


class NodeBase(BaseModel):
    """Base node schema"""
    node_id: str = Field(..., min_length=1, max_length=64)
    hostname: str = Field(..., min_length=1, max_length=255)
    os: str = Field(default="Linux", max_length=100)
    os_version: Optional[str] = Field(default=None, max_length=100)
    kernel_version: Optional[str] = Field(default=None, max_length=100)
    cpu_brand: Optional[str] = Field(default=None, max_length=255)
    cpu_cores: Optional[int] = Field(default=None, ge=1)
    total_memory: Optional[int] = Field(default=None, ge=0)
    version: Optional[str] = Field(default=None, max_length=50)
    arch: Optional[str] = Field(default=None, max_length=20)
    capabilities: Optional[List[str]] = None
    tags: Optional[dict[str, str]] = None

    @field_validator('capabilities', mode='before')
    @classmethod
    def parse_capabilities(cls, v):
        """Parse capabilities from JSON string if needed"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return None
            except (json.JSONDecodeError, TypeError):
                return None
        return v

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v):
        """Parse tags from JSON string if needed"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
                return None
            except (json.JSONDecodeError, TypeError):
                return None
        return v


class NodeRegister(NodeBase):
    """Schema for node registration request"""
    pass


class NodeRegisterResponse(BaseModel):
    """Schema for node registration response"""
    success: bool
    node_id: str
    assigned_id: Optional[str] = None
    message: str
    server_time: int
    config: Optional["ServerConfig"] = None


class ServerConfig(BaseModel):
    """Server configuration pushed to node"""
    heartbeat_interval: int = Field(default=10, ge=1)
    telemetry_interval: int = Field(default=2, ge=1)
    model_update_url: Optional[str] = None


class NodeUpdate(BaseModel):
    """Schema for node updates"""
    hostname: Optional[str] = Field(default=None, max_length=255)
    os_version: Optional[str] = Field(default=None, max_length=100)
    kernel_version: Optional[str] = Field(default=None, max_length=100)
    cpu_brand: Optional[str] = Field(default=None, max_length=255)
    cpu_cores: Optional[int] = Field(default=None, ge=1)
    total_memory: Optional[int] = Field(default=None, ge=0)
    version: Optional[str] = Field(default=None, max_length=50)
    tags: Optional[dict[str, str]] = None


class NodeResponse(NodeBase):
    """Schema for node response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
    heartbeat_interval: int
    telemetry_interval: int


class NodeListResponse(BaseModel):
    """Schema for paginated node list"""
    nodes: list[NodeResponse]
    total: int
    page: int
    page_size: int


# Update forward references
NodeRegisterResponse.model_rebuild()
