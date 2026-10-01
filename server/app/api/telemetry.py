"""Telemetry API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.telemetry import Telemetry
from app.schemas.telemetry import (
    TelemetryCreate,
    TelemetryResponse,
    TelemetryQuery,
    TelemetryAggregated,
    TelemetryStats,
)
from app.services.database import (
    add_telemetry,
    get_telemetry,
    get_telemetry_for_node,
    get_telemetry_stats,
)

router = APIRouter()


@router.post("/", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    telemetry_data: TelemetryCreate,
    db: AsyncSession = Depends(get_db),
) -> TelemetryResponse:
    """
    Ingest telemetry data from an edge node.
    """
    try:
        telemetry = await add_telemetry(telemetry_data, db)
        return TelemetryResponse.from_orm(telemetry)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store telemetry: {str(e)}",
        )


@router.get("/", response_model=List[TelemetryResponse])
async def list_telemetry(
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[TelemetryResponse]:
    """
    List telemetry data with optional filters.
    """
    telemetry_list = await get_telemetry(node_id, start_time, end_time, limit, offset, db)
    return [TelemetryResponse.from_orm(t) for t in telemetry_list]


@router.get("/node/{node_id}", response_model=List[TelemetryResponse])
async def get_node_telemetry(
    node_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> List[TelemetryResponse]:
    """
    Get telemetry data for a specific node.
    """
    telemetry_list = await get_telemetry_for_node(node_id, start_time, end_time, db)
    if not telemetry_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry found for node {node_id}",
        )
    return [TelemetryResponse.from_orm(t) for t in telemetry_list]


@router.get("/stats/{node_id}", response_model=TelemetryStats)
async def get_telemetry_stats_endpoint(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> TelemetryStats:
    """
    Get aggregated statistics for a node.
    """
    try:
        stats = await get_telemetry_stats(node_id, db)
        return TelemetryStats(**stats)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/aggregated/{node_id}", response_model=TelemetryAggregated)
async def get_aggregated_telemetry(
    node_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    points: int = Query(50, ge=10, le=500, description="Number of data points to return"),
    db: AsyncSession = Depends(get_db),
) -> TelemetryAggregated:
    """
    Get aggregated telemetry data for charting.
    Returns sampled data points for the given time range.
    """
    from app.services.database import get_node_by_id

    node = await get_node_by_id(node_id, db)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )

    # Get all telemetry for the node
    telemetry_list = await get_telemetry(node_id, start_time, end_time, 1000, 0, db)

    if not telemetry_list:
        return TelemetryAggregated(
            node_id=node_id,
            timestamps=[],
            cpu_usage=[],
            memory_usage=[],
            temperature=[],
            load_1=[],
        )

    # Sample down to requested number of points
    step = max(1, len(telemetry_list) // points)
    sampled = telemetry_list[::step][:points]

    return TelemetryAggregated(
        node_id=node_id,
        timestamps=[int(t.timestamp.timestamp()) for t in sampled],
        cpu_usage=[t.cpu_usage for t in sampled],
        memory_usage=[t.memory_usage for t in sampled],
        temperature=[t.temperature for t in sampled],
        load_1=[t.load_1 for t in sampled],
    )