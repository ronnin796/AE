"""Node-related API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.node import Node, NodeStatus
from app.schemas.node import (
    NodeBase,
    NodeCapabilities,
    NodeListResponse,
    NodeRegister,
    NodeRegisterResponse,
    NodeUpdate,
    NodeResponse,
    ServerConfig,
)
from app.services.node_service import (
    register_node,
    update_node_status,
    mark_offline_nodes,
)
from app.services.heartbeat_service import (
    send_heartbeat,
    check_node_health,
    get_online_nodes,
    get_offline_nodes,
)

router = APIRouter()


@router.post("/register", response_model=NodeRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_node_endpoint(
    register_data: NodeRegister,
    db: AsyncSession = Depends(get_db),
) -> NodeRegisterResponse:
    """
    Register a new edge node or update existing node information.
    """
    return await register_node(register_data, db)


@router.post("/{node_id}/heartbeat", response_model=dict)
async def heartbeat_endpoint(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Receive heartbeat from an edge node.
    """
    return await send_heartbeat(node_id, db)


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node_endpoint(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    """
    Get details of a specific node.
    """
    from app.services.database import get_node_by_id
    node = await get_node_by_id(node_id, db)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )
    return NodeResponse.from_orm(node)


@router.get("/", response_model=NodeListResponse)
async def list_nodes_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> NodeListResponse:
    """
    List all registered nodes with pagination.
    """
    from app.services.database import list_nodes
    result = await list_nodes(page, page_size, db)
    return result


@router.get("/status/online", response_model=List[NodeResponse])
async def get_online_nodes_endpoint(
    db: AsyncSession = Depends(get_db),
) -> List[NodeResponse]:
    """
    Get list of currently online nodes.
    """
    nodes = await get_online_nodes(db)
    return [NodeResponse.from_orm(node) for node in nodes]


@router.get("/status/offline", response_model=List[NodeResponse])
async def get_offline_nodes_endpoint(
    db: AsyncSession = Depends(get_db),
) -> List[NodeResponse]:
    """
    Get list of offline nodes.
    """
    nodes = await get_offline_nodes(db)
    return [NodeResponse.from_orm(node) for node in nodes]


@router.post("/{node_id}/status", response_model=NodeResponse)
async def update_node_status_endpoint(
    node_id: str,
    status: NodeStatus,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    """
    Manually update node status (for testing/admin).
    """
    node = await update_node_status(node_id, status, db)
    return NodeResponse.from_orm(node)


@router.post("/maintenance/mark-offline", response_model=dict)
async def mark_offline_nodes_endpoint(
    timeout_seconds: int = Query(30, ge=5),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Mark nodes as OFFLINE if they haven't sent heartbeat recently (maintenance task).
    """
    count = await mark_offline_nodes(timeout_seconds, db)
    return {
        "marked_offline": count,
        "message": f"Marked {count} nodes as OFFLINE",
    }