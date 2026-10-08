"""Node SQLAlchemy model"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NodeStatus(str, PyEnum):
    """Node status enumeration"""
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class Node(Base):
    """Edge node registry"""
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    os: Mapped[str] = mapped_column(String(100), nullable=False)
    os_version: Mapped[str] = mapped_column(String(100), nullable=True)
    kernel_version: Mapped[str] = mapped_column(String(100), nullable=True)
    cpu_brand: Mapped[str] = mapped_column(String(255), nullable=True)
    cpu_cores: Mapped[int] = mapped_column(Integer, nullable=True)
    total_memory: Mapped[int] = mapped_column(Integer, nullable=True)  # bytes
    version: Mapped[str] = mapped_column(String(50), nullable=True)
    arch: Mapped[str] = mapped_column(String(20), nullable=True)
    capabilities: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON object

    status: Mapped[NodeStatus] = mapped_column(
        Enum(NodeStatus),
        default=NodeStatus.OFFLINE,
        nullable=False,
        index=True,
    )

    # Server-pushed configuration intervals
    heartbeat_interval: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    telemetry_interval: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to telemetry
    telemetry: Mapped[list["Telemetry"]] = relationship(
        "Telemetry",
        back_populates="node",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Relationship to inference metrics
    inference_metrics: Mapped[list["InferenceMetrics"]] = relationship(
        "InferenceMetrics",
        back_populates="node",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Node(node_id={self.node_id}, hostname={self.hostname}, status={self.status})>"