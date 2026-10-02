"""Telemetry SQLAlchemy model"""

from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Telemetry(Base):
    """Telemetry data points from edge nodes"""
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to node
    node_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True,
    )

    # CPU metrics
    cpu_usage: Mapped[float] = mapped_column(Float, nullable=True)  # percentage
    cpu_per_core: Mapped[str] = mapped_column(String(1000), nullable=True)  # JSON array

    # Memory metrics
    memory_usage: Mapped[float] = mapped_column(Float, nullable=True)  # percentage
    memory_total: Mapped[int] = mapped_column(Integer, nullable=True)  # bytes
    memory_available: Mapped[int] = mapped_column(Integer, nullable=True)
    memory_used: Mapped[int] = mapped_column(Integer, nullable=True)

    # Temperature
    temperature: Mapped[float] = mapped_column(Float, nullable=True)  # Celsius
    temperatures: Mapped[str] = mapped_column(String(500), nullable=True)  # JSON array

    # System
    uptime: Mapped[int] = mapped_column(Integer, nullable=True)  # seconds
    load_1: Mapped[float] = mapped_column(Float, nullable=True)
    load_5: Mapped[float] = mapped_column(Float, nullable=True)
    load_15: Mapped[float] = mapped_column(Float, nullable=True)
    processes_running: Mapped[int] = mapped_column(Integer, nullable=True)
    processes_total: Mapped[int] = mapped_column(Integer, nullable=True)

    # Relationship
    node: Mapped["Node"] = relationship("Node", back_populates="telemetry")

    def __repr__(self) -> str:
        return f"<Telemetry(node_id={self.node_id}, timestamp={self.timestamp}, cpu={self.cpu_usage})>"