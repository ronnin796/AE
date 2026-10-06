"""Node-related API endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.database import get_db
from app.models.node import Node, NodeStatus
from app.models.telemetry import Telemetry
from app.schemas.node import (
    NodeBase,
    NodeListResponse,
    NodeRegister,
    NodeRegisterResponse,
    NodeUpdate,
    NodeResponse,
    ServerConfig,
)
from app.schemas.telemetry import TelemetryLatest
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
from app.services.database import get_latest_telemetry_for_all_nodes, get_latest_telemetry_for_node, get_node_by_id

router = APIRouter()

logger = logging.getLogger(__name__)


async def _enrich_node_with_latest_telemetry(node: Node, db: AsyncSession, latest_telemetry_map: Dict[int, Telemetry] = None) -> NodeResponse:
    """Enrich a node with its latest telemetry data."""
    node_response = NodeResponse.from_orm(node)
    
    if latest_telemetry_map and node.id in latest_telemetry_map:
        telemetry = latest_telemetry_map[node.id]
        node_response.latest_telemetry = _telemetry_to_latest(telemetry, node.node_id)
    elif not latest_telemetry_map:
        # Fetch individually if no map provided
        telemetry = await get_latest_telemetry_for_node(node.node_id, db)
        if telemetry:
            node_response.latest_telemetry = _telemetry_to_latest(telemetry, node.node_id)
    
    return node_response


def _telemetry_to_latest(telemetry: Telemetry, node_id_str: str) -> TelemetryLatest:
    """Convert database Telemetry model to TelemetryLatest schema."""
    import json
    
    cpu_per_core = None
    if telemetry.cpu_per_core:
        try:
            cpu_per_core = json.loads(telemetry.cpu_per_core)
        except (json.JSONDecodeError, TypeError):
            cpu_per_core = None

    temperatures = None
    if telemetry.temperatures:
        try:
            temperatures = json.loads(telemetry.temperatures)
        except (json.JSONDecodeError, TypeError):
            temperatures = None

    # Calculate age in seconds - handle both naive and aware datetimes
    age_seconds = None
    if telemetry.timestamp:
        ts = telemetry.timestamp
        # If timestamp is naive, assume UTC
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_seconds = int((now - ts).total_seconds())

    return TelemetryLatest(
        node_id=node_id_str,
        timestamp=int(telemetry.timestamp.timestamp()),
        cpu_usage=telemetry.cpu_usage,
        cpu_per_core=cpu_per_core,
        memory_usage=telemetry.memory_usage,
        memory_total=telemetry.memory_total,
        memory_available=telemetry.memory_available,
        memory_used=telemetry.memory_used,
        temperature=telemetry.temperature,
        temperatures=temperatures,
        uptime=telemetry.uptime,
        load_1=telemetry.load_1,
        load_5=telemetry.load_5,
        load_15=telemetry.load_15,
        processes_running=telemetry.processes_running,
        processes_total=telemetry.processes_total,
        age_seconds=age_seconds,
    )


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
    return await _enrich_node_with_latest_telemetry(node, db)


@router.get("/", response_model=NodeListResponse)
async def list_nodes_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> NodeListResponse:
    """
    List all registered nodes with pagination.
    """
    from app.services.database import list_nodes, get_latest_telemetry_for_all_nodes
    
    # Get paginated nodes
    result = await list_nodes(page, page_size, db)
    
    # Get latest telemetry for all nodes in a single query
    latest_telemetry_map = await get_latest_telemetry_for_all_nodes(db)
    
    # Enrich nodes with latest telemetry
    enriched_nodes = []
    for node_response in result["nodes"]:
        # We need to get the node object to access its ID
        node_obj = await get_node_by_id(node_response.node_id, db)
        if node_obj:
            enriched = await _enrich_node_with_latest_telemetry(node_obj, db, latest_telemetry_map)
            enriched_nodes.append(enriched)
        else:
            enriched_nodes.append(node_response)
    
    return NodeListResponse(
        nodes=enriched_nodes,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/status/online", response_model=List[NodeResponse])
async def get_online_nodes_endpoint(
    db: AsyncSession = Depends(get_db),
) -> List[NodeResponse]:
    """
    Get list of currently online nodes.
    """
    nodes = await get_online_nodes(db)
    latest_telemetry_map = await get_latest_telemetry_for_all_nodes(db)
    enriched = []
    for node in nodes:
        enriched.append(await _enrich_node_with_latest_telemetry(node, db, latest_telemetry_map))
    return enriched


@router.get("/status/offline", response_model=List[NodeResponse])
async def get_offline_nodes_endpoint(
    db: AsyncSession = Depends(get_db),
) -> List[NodeResponse]:
    """
    Get list of offline nodes.
    """
    nodes = await get_offline_nodes(db)
    latest_telemetry_map = await get_latest_telemetry_for_all_nodes(db)
    enriched = []
    for node in nodes:
        enriched.append(await _enrich_node_with_latest_telemetry(node, db, latest_telemetry_map))
    return enriched


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


@router.get("/debug/events", response_model=dict)
async def debug_events(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """
    Debug endpoint: Get recent system events (registrations, heartbeats, telemetry, status changes).
    """
    from app.models.node import Node
    from app.models.telemetry import Telemetry
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, desc, func

    now = datetime.now(timezone.utc)
    events = []

    # Get recent node registrations/updates (last 24 hours)
    node_query = (
        select(Node)
        .where(Node.created_at >= now - timedelta(hours=24))
        .order_by(desc(Node.created_at))
        .limit(limit)
    )
    nodes_result = await db.execute(node_query)
    nodes = nodes_result.scalars().all()

    for node in nodes:
        events.append({
            "id": f"node_created_{node.id}",
            "timestamp": node.created_at.isoformat(),
            "type": "connect",
            "node_id": node.node_id,
            "message": f"Node registered: {node.hostname} ({node.node_id})",
        })

    # Get recent heartbeats (nodes with recent last_seen)
    hb_query = (
        select(Node)
        .where(Node.last_seen >= now - timedelta(hours=24))
        .order_by(desc(Node.last_seen))
        .limit(limit)
    )
    hb_result = await db.execute(hb_query)
    hb_nodes = hb_result.scalars().all()

    for node in hb_nodes:
        # Skip if we already added a connect event for this time
        if node.created_at != node.last_seen:
            events.append({
                "id": f"heartbeat_{node.id}_{int(node.last_seen.timestamp())}",
                "timestamp": node.last_seen.isoformat(),
                "type": "heartbeat",
                "node_id": node.node_id,
                "message": f"Heartbeat received from {node.hostname}",
            })

    # Get recent telemetry
    tel_query = (
        select(Telemetry)
        .where(Telemetry.timestamp >= now - timedelta(hours=24))
        .order_by(desc(Telemetry.timestamp))
        .limit(limit)
    )
    tel_result = await db.execute(tel_query)
    telemetry_list = tel_result.scalars().all()

    # Get node info for telemetry
    node_ids = {t.node_id for t in telemetry_list}
    node_map = {}
    if node_ids:
        node_q = select(Node).where(Node.id.in_(node_ids))
        node_r = await db.execute(node_q)
        node_map = {n.id: n for n in node_r.scalars().all()}

    for tel in telemetry_list:
        node = node_map.get(tel.node_id)
        if node:
            events.append({
                "id": f"telemetry_{tel.id}",
                "timestamp": tel.timestamp.isoformat(),
                "type": "telemetry",
                "node_id": node.node_id,
                "message": f"Telemetry: CPU={tel.cpu_usage:.1f}% MEM={tel.memory_usage:.1f}%" 
                          + (f" TEMP={tel.temperature:.1f}°C" if tel.temperature else ""),
            })

    # Get status changes (nodes that went offline)
    offline_query = (
        select(Node)
        .where(Node.status == "offline", Node.updated_at >= now - timedelta(hours=24))
        .order_by(desc(Node.updated_at))
        .limit(limit)
    )
    offline_result = await db.execute(offline_query)
    offline_nodes = offline_result.scalars().all()

    for node in offline_nodes:
        events.append({
            "id": f"disconnect_{node.id}",
            "timestamp": node.updated_at.isoformat(),
            "type": "disconnect",
            "node_id": node.node_id,
            "message": f"Node marked offline: {node.hostname}",
        })

    # Sort events by timestamp, newest first
    events.sort(key=lambda e: e["timestamp"], reverse=True)
    
    return {
        "events": events[:limit],
        "total": len(events),
    }