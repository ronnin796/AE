"""Node-related API endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models.node import Node, NodeStatus
from app.schemas.node import (
    NodeBase,
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
from app.tcp_server import send_command_to_node, _connected_clients

router = APIRouter()

logger = logging.getLogger(__name__)


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


@router.get("/debug/registry", response_model=dict)
async def debug_node_registry(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Debug endpoint: Inspect the persistent node registry and active TCP connections.
    Returns both persistent nodes and currently connected nodes.
    """
    from app.services.database import list_nodes
    from app.tcp_server import _connected_clients
    
    # Get all persistent nodes
    result = await list_nodes(page=1, page_size=1000, db=db)
    
    # Get active TCP connections
    active_connections = list(_connected_clients.keys())
    
    # Build response with connection status
    nodes_with_status = []
    for node in result["nodes"]:
        node_dict = node.model_dump() if hasattr(node, 'model_dump') else node.dict()
        node_dict["tcp_connected"] = node_dict["node_id"] in active_connections
        nodes_with_status.append(node_dict)
    
    return {
        "persistent_nodes": nodes_with_status,
        "total_persistent": result["total"],
        "active_tcp_connections": active_connections,
        "active_count": len(active_connections),
    }


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


@router.post("/{node_id}/command", response_model=dict)
async def send_node_command(
    node_id: str,
    command: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Send a command to a node via TCP connection.
    Supported commands: shutdown, reboot, update_telemetry_interval, update_heartbeat_interval
    """
    from app.services.database import get_node_by_id
    
    node = await get_node_by_id(node_id, db)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )
    
    cmd_type = command.get("command")
    params = command.get("params", {})
    
    if cmd_type not in ["shutdown", "reboot", "update_telemetry_interval", "update_heartbeat_interval"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown command: {cmd_type}",
        )
    
    # Send command via TCP (background task)
    background_tasks.add_task(send_command_to_node, node_id, cmd_type, params)
    
    return {
        "success": True,
        "node_id": node_id,
        "command": cmd_type,
        "message": f"Command {cmd_type} queued for node {node_id}",
    }


@router.post("/{node_id}/shutdown", response_model=dict)
async def shutdown_node(
    node_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Send shutdown command to a node.
    """
    from app.services.database import get_node_by_id
    
    node = await get_node_by_id(node_id, db)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )
    
    background_tasks.add_task(send_command_to_node, node_id, "shutdown", {})
    
    return {
        "success": True,
        "node_id": node_id,
        "message": f"Shutdown command sent to node {node_id}",
    }


@router.post("/{node_id}/disconnect", response_model=dict)
async def disconnect_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Disconnect a node by closing its TCP connection.
    This forces the node to reconnect on its next heartbeat/telemetry interval.
    """
    from app.services.database import get_node_by_id
    from app.tcp_server import _connected_clients, send_command_to_node
    
    node = await get_node_by_id(node_id, db)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )
    
    # Close the TCP connection if it exists
    writer = _connected_clients.get(node_id)
    disconnected = False
    if writer:
        try:
            # Send shutdown command first
            await send_command_to_node(node_id, "shutdown", {})
            # Close the connection
            writer.close()
            await writer.wait_closed()
            logger.info(f"Disconnected node {node_id} via TCP")
            disconnected = True
        except Exception as e:
            logger.error(f"Error disconnecting node {node_id}: {e}")
    
    # Update node status in database
    node.status = NodeStatus.OFFLINE
    await db.commit()
    
    return {
        "success": True,
        "node_id": node_id,
        "message": f"Node {node_id} disconnected" + (" (TCP connection closed)" if disconnected else " (no active TCP connection)"),
    }


@router.post("/{node_id}/reconnect", response_model=dict)
async def reconnect_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Mark a node as ready for reconnection.
    The agent will automatically reconnect on its next interval.
    """
    from app.services.database import get_node_by_id
    
    node = await get_node_by_id(node_id, db)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )
    
    # Just mark as offline - the agent will re-register on next connection
    node.status = NodeStatus.OFFLINE
    await db.commit()
    
    return {
        "success": True,
        "node_id": node_id,
        "message": f"Node {node_id} marked for reconnection",
    }


@router.delete("/{node_id}", response_model=dict)
async def delete_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete a node permanently from the registry.
    If the node is currently connected via TCP, its connection will be closed first.
    """
    from app.services.database import get_node_by_id
    from app.tcp_server import _connected_clients, send_command_to_node
    
    node = await get_node_by_id(node_id, db)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found",
        )
    
    # Close TCP connection if active
    writer = _connected_clients.get(node_id)
    if writer:
        try:
            # Send shutdown command first
            await send_command_to_node(node_id, "shutdown", {})
            # Close the connection
            writer.close()
            await writer.wait_closed()
            logger.info(f"Closed TCP connection for node {node_id} during deletion")
        except Exception as e:
            logger.warning(f"Error closing connection for node {node_id} during deletion: {e}")
    
    # Delete from database (cascades to telemetry due to CASCADE on foreign key)
    await db.delete(node)
    await db.commit()
    
    return {
        "success": True,
        "node_id": node_id,
        "message": f"Node {node_id} deleted permanently",
    }