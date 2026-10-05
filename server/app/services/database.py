"""Database service layer for nodes and telemetry"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.node import Node, NodeStatus
from app.models.telemetry import Telemetry
from app.schemas.node import NodeRegister, NodeUpdate, NodeResponse, NodeListResponse
from app.schemas.telemetry import TelemetryCreate, TelemetryQuery, TelemetryAggregated, TelemetryStats


def _utcnow() -> datetime:
    """Return current time as timezone-aware UTC."""
    return datetime.now(timezone.utc)


async def get_node_by_id(node_id: str, db: AsyncSession) -> Optional[Node]:
    """Get node by node_id"""
    result = await db.execute(select(Node).where(Node.node_id == node_id))
    return result.scalar_one_or_none()


async def create_node(register_data: NodeRegister, db: AsyncSession) -> Node:
    """Create a new node from registration data"""
    import json
    capabilities_json = None
    if register_data.capabilities:
        capabilities_json = json.dumps(register_data.capabilities)

    tags_json = None
    if register_data.tags:
        tags_json = json.dumps(register_data.tags)

    node = Node(
        node_id=register_data.node_id,
        hostname=register_data.hostname,
        os=register_data.os,
        os_version=register_data.os_version,
        kernel_version=register_data.kernel_version,
        cpu_brand=register_data.cpu_brand,
        cpu_cores=register_data.cpu_cores,
        total_memory=register_data.total_memory,
        version=register_data.version,
        arch=register_data.arch,
        capabilities=capabilities_json,
        tags=tags_json,
        status=NodeStatus.ONLINE,
        # Defaults will be set by model, but can be overridden by callers
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node


async def update_node(node_id: str, update_data: NodeUpdate, db: AsyncSession) -> Node:
    """Update node information"""
    node = await get_node_by_id(node_id, db)
    if not node:
        raise ValueError(f"Node {node_id} not found")

    update_dict = update_data.model_dump(exclude_unset=True)

    # Handle tags specially - serialize to JSON string
    if 'tags' in update_dict:
        import json
        tags_value = update_dict.pop('tags')
        if tags_value is not None:
            node.tags = json.dumps(tags_value)
        else:
            node.tags = None

    for key, value in update_dict.items():
        setattr(node, key, value)

    await db.commit()
    await db.refresh(node)
    return node


async def list_nodes(page: int = 1, page_size: int = 20, db: AsyncSession = None) -> Dict[str, Any]:
    """List nodes with pagination"""
    if db is None:
        from app.database import async_session_maker
        async with async_session_maker() as db:
            return await _list_nodes_internal(page, page_size, db)
    return await _list_nodes_internal(page, page_size, db)


async def _list_nodes_internal(page: int, page_size: int, db: AsyncSession) -> Dict[str, Any]:
    """Internal implementation of list_nodes"""
    offset = (page - 1) * page_size

    # Count total
    total_result = await db.execute(select(func.count(Node.id)))
    total = total_result.scalar() or 0

    # Get paginated nodes
    result = await db.execute(
        select(Node)
        .order_by(desc(Node.created_at))
        .offset(offset)
        .limit(page_size)
    )
    nodes = result.scalars().all()

    return {
        "nodes": [NodeResponse.from_orm(n) for n in nodes],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# Telemetry services
async def add_telemetry(telemetry_data: TelemetryCreate, db: AsyncSession) -> Telemetry:
    """Add telemetry data point"""
    # Find node
    node = await get_node_by_id(telemetry_data.node_id, db)
    if not node:
        raise ValueError(f"Node {telemetry_data.node_id} not found")

    telemetry = Telemetry(
        node_id=node.id,
        timestamp=datetime.fromtimestamp(telemetry_data.timestamp),
        cpu_usage=telemetry_data.cpu_usage,
        cpu_per_core=str(telemetry_data.cpu_per_core) if telemetry_data.cpu_per_core else None,
        memory_usage=telemetry_data.memory_usage,
        memory_total=telemetry_data.memory_total,
        memory_available=telemetry_data.memory_available,
        memory_used=telemetry_data.memory_used,
        temperature=telemetry_data.temperature,
        temperatures=str(telemetry_data.temperatures) if telemetry_data.temperatures else None,
        uptime=telemetry_data.uptime,
        load_1=telemetry_data.load_1,
        load_5=telemetry_data.load_5,
        load_15=telemetry_data.load_15,
        processes_running=telemetry_data.processes_running,
        processes_total=telemetry_data.processes_total,
    )
    db.add(telemetry)

    # Update node last_seen and status
    node.last_seen = _utcnow()
    node.status = NodeStatus.ONLINE

    await db.commit()
    await db.refresh(telemetry)
    return telemetry


async def get_telemetry(
    node_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = None,
) -> List[Telemetry]:
    """Get telemetry data with filters"""
    if db is None:
        from app.database import async_session_maker
        async with async_session_maker() as db:
            return await _get_telemetry_internal(node_id, start_time, end_time, limit, offset, db)
    return await _get_telemetry_internal(node_id, start_time, end_time, limit, offset, db)


async def _get_telemetry_internal(
    node_id: Optional[str],
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    limit: int,
    offset: int,
    db: AsyncSession,
) -> List[Telemetry]:
    query = select(Telemetry).options(selectinload(Telemetry.node))

    if node_id:
        node = await get_node_by_id(node_id, db)
        if node:
            query = query.where(Telemetry.node_id == node.id)

    if start_time:
        query = query.where(Telemetry.timestamp >= start_time)
    if end_time:
        query = query.where(Telemetry.timestamp <= end_time)

    query = query.order_by(desc(Telemetry.timestamp)).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def get_telemetry_for_node(
    node_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = None,
) -> List[Telemetry]:
    """Get telemetry for a specific node"""
    return await get_telemetry(node_id, start_time, end_time, limit=1000, offset=0, db=db)


async def get_telemetry_stats(node_id: str, db: AsyncSession = None) -> Dict[str, Any]:
    """Get aggregated statistics for a node"""
    if db is None:
        from app.database import async_session_maker
        async with async_session_maker() as db:
            return await _get_telemetry_stats_internal(node_id, db)
    return await _get_telemetry_stats_internal(node_id, db)


async def _get_telemetry_stats_internal(node_id: str, db: AsyncSession) -> Dict[str, Any]:
    node = await get_node_by_id(node_id, db)
    if not node:
        raise ValueError(f"Node {node_id} not found")

    # Get basic stats
    result = await db.execute(
        select(
            func.count(Telemetry.id),
            func.avg(Telemetry.cpu_usage),
            func.max(Telemetry.cpu_usage),
            func.avg(Telemetry.memory_usage),
            func.max(Telemetry.memory_usage),
            func.avg(Telemetry.temperature),
            func.max(Telemetry.temperature),
            func.max(Telemetry.timestamp),
        ).where(Telemetry.node_id == node.id)
    )
    row = result.one()

    return {
        "node_id": node_id,
        "count": row[0] or 0,
        "avg_cpu": row[1],
        "max_cpu": row[2],
        "avg_memory": row[3],
        "max_memory": row[4],
        "avg_temperature": row[5],
        "max_temperature": row[6],
        "latest_timestamp": int(row[7].timestamp()) if row[7] else None,
    }