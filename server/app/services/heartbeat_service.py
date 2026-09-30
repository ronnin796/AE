"""Heartbeat service for managing node liveness"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.node import Node, NodeStatus
from app.schemas.node import NodeRegisterResponse, ServerConfig
from app.services.database import get_node_by_id


async def send_heartbeat(node_id: str, db: AsyncSession) -> dict:
    """Process heartbeat from node"""
    node = await get_node_by_id(node_id, db)
    if not node:
        return {
            "success": False,
            "message": f"Node {node_id} not found",
        }

    # Update last_seen
    node.last_seen = datetime.utcnow()
    node.status = NodeStatus.ONLINE

    await db.commit()

    return {
        "success": True,
        "server_time": int(datetime.utcnow().timestamp()),
        "next_heartbeat_interval": 10,
        "commands": [],
    }


async def check_node_health(node_id: str, db: AsyncSession) -> dict:
    """Check if a node is healthy"""
    node = await get_node_by_id(node_id, db)
    if not node:
        return {
            "healthy": False,
            "reason": "Node not found",
        }

    timeout_seconds = 30
    if (datetime.utcnow() - node.last_seen).total_seconds() > timeout_seconds:
        node.status = NodeStatus.OFFLINE
        await db.commit()
        return {
            "healthy": False,
            "reason": "Heartbeat timeout",
            "last_seen": node.last_seen.isoformat(),
        }

    return {
        "healthy": True,
        "status": node.status.value,
        "last_seen": node.last_seen.isoformat(),
        "uptime_seconds": node.uptime if hasattr(node, 'uptime') else None,
    }


async def get_online_nodes(db: AsyncSession) -> list:
    """Get list of currently online nodes"""
    result = await db.execute(
        select(Node).where(Node.status == NodeStatus.ONLINE)
    )
    return result.scalars().all()


async def get_offline_nodes(db: AsyncSession) -> list:
    """Get list of offline nodes"""
    result = await db.execute(
        select(Node).where(Node.status == NodeStatus.OFFLINE)
    )
    return result.scalars().all()