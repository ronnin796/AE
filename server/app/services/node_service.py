"""Node registration service"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.node import Node, NodeStatus
from app.schemas.node import NodeRegister, NodeRegisterResponse, ServerConfig, NodeUpdate
from app.services.database import create_node as db_create_node, get_node_by_id, update_node as db_update_node


async def register_node(register_data: NodeRegister, db: AsyncSession) -> NodeRegisterResponse:
    """Register a new node or update existing"""
    existing_node = await get_node_by_id(register_data.node_id, db)

    if existing_node:
        # Update existing node
        existing_node.hostname = register_data.hostname
        existing_node.os = register_data.os
        existing_node.os_version = register_data.os_version
        existing_node.kernel_version = register_data.kernel_version
        existing_node.cpu_brand = register_data.cpu_brand
        existing_node.cpu_cores = register_data.cpu_cores
        existing_node.total_memory = register_data.total_memory
        existing_node.version = register_data.version
        existing_node.arch = register_data.arch
        existing_node.status = NodeStatus.ONLINE
        existing_node.last_seen = datetime.utcnow()

        await db.commit()
        await db.refresh(existing_node)

        return NodeRegisterResponse(
            success=True,
            node_id=existing_node.node_id,
            assigned_id=str(existing_node.id),
            message="Node updated successfully",
            server_time=int(datetime.utcnow().timestamp()),
            config=ServerConfig(),
        )
    else:
        # Create new node
        node = await db_create_node(register_data, db)

        return NodeRegisterResponse(
            success=True,
            node_id=node.node_id,
            assigned_id=str(node.id),
            message="Node registered successfully",
            server_time=int(datetime.utcnow().timestamp()),
            config=ServerConfig(),
        )


async def update_node_status(node_id: str, status: NodeStatus, db: AsyncSession) -> Node:
    """Update node status"""
    node = await get_node_by_id(node_id, db)
    if not node:
        raise ValueError(f"Node {node_id} not found")

    node.status = status
    node.last_seen = datetime.utcnow()

    await db.commit()
    await db.refresh(node)
    return node


async def mark_offline_nodes(timeout_seconds: int = 30, db: AsyncSession = None) -> int:
    """Mark nodes as OFFLINE if they haven't sent heartbeat recently"""
    if db is None:
        from app.database import async_session_maker
        async with async_session_maker() as db:
            return await _mark_offline_nodes_internal(timeout_seconds, db)
    return await _mark_offline_nodes_internal(timeout_seconds, db)


async def _mark_offline_nodes_internal(timeout_seconds: int, db: AsyncSession) -> int:
    from datetime import timezone
    threshold = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

    result = await db.execute(
        select(Node).where(
            Node.status == NodeStatus.ONLINE,
            Node.last_seen < threshold,
        )
    )
    offline_nodes = result.scalars().all()

    count = 0
    for node in offline_nodes:
        node.status = NodeStatus.OFFLINE
        count += 1

    if count > 0:
        await db.commit()

    return count