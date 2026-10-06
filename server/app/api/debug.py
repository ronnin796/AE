"""Debug API endpoints for system events and diagnostics"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.node import Node, NodeStatus
from app.models.telemetry import Telemetry
from app.schemas.node import NodeResponse

router = APIRouter(prefix="/debug", tags=["debug"])

logger = logging.getLogger(__name__)


@router.get("/events")
async def get_debug_events(
    limit: int = Query(100, ge=1, le=500),
    since: Optional[datetime] = Query(None),
    event_types: Optional[List[str]] = Query(None),
    node_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get system debug events from the database.
    Reconstructs events from node status changes, telemetry receipts, and heartbeats.
    """
    events = []
    
    # Build query for recent telemetry (represents telemetry events)
    telemetry_query = select(Telemetry).order_by(desc(Telemetry.timestamp)).limit(limit * 2)
    
    if since:
        telemetry_query = telemetry_query.where(Telemetry.timestamp >= since)
    if node_id:
        node = await db.execute(select(Node).where(Node.node_id == node_id))
        node_obj = node.scalar_one_or_none()
        if node_obj:
            telemetry_query = telemetry_query.where(Telemetry.node_id == node_obj.id)
    
    telemetry_result = await db.execute(telemetry_query)
    telemetry_list = telemetry_result.scalars().all()
    
    # Get node info for all telemetry
    node_ids = {t.node_id for t in telemetry_list}
    nodes = {}
    if node_ids:
        node_result = await db.execute(select(Node).where(Node.id.in_(node_ids)))
        nodes = {n.id: n for n in node_result.scalars().all()}
    
    for t in telemetry_list:
        node = nodes.get(t.node_id)
        if not node:
            continue
            
        events.append({
            "id": f"telemetry-{t.id}",
            "timestamp": t.timestamp.isoformat(),
            "type": "telemetry",
            "node_id": node.node_id,
            "message": f"Telemetry received: CPU={t.cpu_usage:.1f}% MEM={t.memory_usage:.1f}% Temp={t.temperature:.1f}°C" if t.cpu_usage is not None else "Telemetry received"
        })
    
    # Add node registration/heartbeat events from node table
    node_query = select(Node).order_by(desc(Node.created_at)).limit(limit)
    if since:
        node_query = node_query.where(Node.created_at >= since)
    if node_id:
        node_query = node_query.where(Node.node_id == node_id)
        
    node_result = await db.execute(node_query)
    node_list = node_result.scalars().all()
    
    for n in node_list:
        events.append({
            "id": f"register-{n.id}",
            "timestamp": n.created_at.isoformat(),
            "type": "connect",
            "node_id": n.node_id,
            "message": f"Node registered: {n.hostname} ({n.os} {n.os_version or ''})"
        })
        
        # Add heartbeat events based on status changes
        if n.status == NodeStatus.ONLINE:
            events.append({
                "id": f"heartbeat-{n.id}",
                "timestamp": n.last_seen.isoformat(),
                "type": "heartbeat",
                "node_id": n.node_id,
                "message": f"Heartbeat received - Node ONLINE"
            })
        elif n.status == NodeStatus.OFFLINE:
            events.append({
                "id": f"offline-{n.id}",
                "timestamp": n.last_seen.isoformat(),
                "type": "disconnect",
                "node_id": n.node_id,
                "message": f"Node marked OFFLINE (no heartbeat)"
            })
    
    # Sort all events by timestamp descending
    events.sort(key=lambda e: e["timestamp"], reverse=True)
    events = events[:limit]
    
    # Filter by event types if specified
    if event_types:
        events = [e for e in events if e["type"] in event_types]
    
    return {
        "events": events,
        "total": len(events),
        "filters": {
            "limit": limit,
            "since": since.isoformat() if since else None,
            "event_types": event_types,
            "node_id": node_id
        }
    }


@router.get("/stats")
async def get_debug_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get debug statistics about the system."""
    from sqlalchemy import func
    
    # Node counts by status
    node_counts = await db.execute(
        select(Node.status, func.count(Node.id))
        .group_by(Node.status)
    )
    status_counts = {str(status): count for status, count in node_counts.all()}
    
    # Telemetry stats
    total_telemetry = await db.execute(select(func.count(Telemetry.id)))
    telemetry_count = total_telemetry.scalar() or 0
    
    # Latest telemetry per node
    latest_per_node = await db.execute(
        select(Telemetry.node_id, func.max(Telemetry.timestamp).label("latest"))
        .group_by(Telemetry.node_id)
    )
    latest_times = {row[0]: row[1] for row in latest_per_node.all()}
    
    # Node to ID mapping
    node_map = {}
    nodes_result = await db.execute(select(Node))
    for n in nodes_result.scalars().all():
        node_map[n.id] = n.node_id
    
    latest_by_node_id = {node_map.get(k): v.isoformat() if v else None for k, v in latest_times.items() if k in node_map}
    
    return {
        "nodes": {
            "total": sum(status_counts.values()),
            "by_status": status_counts
        },
        "telemetry": {
            "total_points": telemetry_count,
            "latest_per_node": latest_by_node_id
        },
        "database": {
            "node_table_rows": sum(status_counts.values()),
            "telemetry_table_rows": telemetry_count
        }
    }


@router.get("/connections")
async def get_active_connections(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get information about active TCP connections."""
    from app.tcp_server import _connected_clients
    
    active = list(_connected_clients.keys())
    
    # Get node details for active connections
    nodes_info = {}
    if active:
        node_result = await db.execute(
            select(Node).where(Node.node_id.in_(active))
        )
        for n in node_result.scalars().all():
            nodes_info[n.node_id] = {
                "hostname": n.hostname,
                "status": n.status.value,
                "last_seen": n.last_seen.isoformat(),
                "tcp_connected": True
            }
    
    return {
        "active_connections": active,
        "count": len(active),
        "nodes": nodes_info
    }