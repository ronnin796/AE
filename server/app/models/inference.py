"""Inference metrics SQLAlchemy model"""

from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InferenceMetrics(Base):
    """Inference metrics from edge nodes"""
    __tablename__ = "inference_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to node
    node_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request metadata
    request_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    model_path: Mapped[str] = mapped_column(String(1024), nullable=True)

    # Input/output metadata
    input_shape: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    output_shape: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    output: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of floats

    # Performance metrics
    inference_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 0=failed, 1=success
    error: Mapped[str] = mapped_column(Text, nullable=True)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Relationship
    node: Mapped["Node"] = relationship("Node", back_populates="inference_metrics")

    def __repr__(self) -> str:
        return f"<InferenceMetrics(node_id={self.node_id}, model_id={self.model_id}, latency_ms={self.inference_time_ms})>"


# Add back-populates to Node model
def _patch_node_relationship():
    from app.models.node import Node
    Node.inference_metrics = relationship("InferenceMetrics", back_populates="node")


_patch_node_relationship()