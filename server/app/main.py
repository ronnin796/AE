"""FastAPI server main entry point"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from .database import async_session_maker, get_db, init_db, close_db
from .models.node import Node, NodeStatus
from .models.telemetry import Telemetry
from .schemas.node import (
    NodeBase,
    NodeRegister,
    NodeRegisterResponse,
    NodeUpdate,
    ServerConfig,
    NodeResponse,
    NodeListResponse,
)
from .schemas.telemetry import (
    TelemetryCreate,
    TelemetryResponse,
    TelemetryQuery,
    TelemetryAggregated,
    TelemetryStats,
)
from .api import nodes, telemetry
from .tcp_server import start_tcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("aetheredge-server")

# Create FastAPI app
app = FastAPI(
    title="AetherEdge Server",
    description="FastAPI backend for AetherEdge distributed edge AI system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(nodes.router, prefix="/api/v1/nodes", tags=["nodes"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])

# Track TCP server task
tcp_server_task: asyncio.Task = None

# Track heartbeat monitor task
heartbeat_monitor_task: asyncio.Task = None


@app.get("/", summary="Root endpoint")
async def root() -> dict:
    return {"message": "AetherEdge Server is running", "version": "0.1.0"}


@app.get("/health", summary="Health check endpoint")
async def health() -> dict:
    return {"status": "ok", "uptime": 0}


async def start_heartbeat_monitor():
    """Start heartbeat monitoring task that checks node health periodically"""
    logger.info("Starting heartbeat monitor task...")

    async def monitor():
        while True:
            try:
                # Check all online nodes for heartbeat timeout
                from app.database import async_session_maker
                async with async_session_maker() as db:
                    from app.services.node_service import mark_offline_nodes
                    # Mark nodes offline if they haven't sent heartbeat in 30 seconds (default timeout)
                    count = await mark_offline_nodes(30, db)
                    if count > 0:
                        logger.info(f"Marked {count} nodes as OFFLINE due to heartbeat timeout")

                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    global heartbeat_monitor_task
    heartbeat_monitor_task = asyncio.create_task(monitor())
    logger.info("Heartbeat monitor task started")


@app.on_event("startup")
async def startup_event():
    """Initialize database and start TCP server on startup"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Start TCP server in background
    global tcp_server_task
    tcp_server_task = asyncio.create_task(start_tcp_server())

    # Start heartbeat monitor in background
    global heartbeat_monitor_task
    heartbeat_monitor_task = asyncio.create_task(start_heartbeat_monitor())

    # Give the TCP server a moment to start and bind to the port
    await asyncio.sleep(0.5)

    logger.info("TCP server started")
    logger.info("Heartbeat monitor started")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections and stop TCP server on shutdown"""
    logger.info("Shutting down...")

    # Stop TCP server
    if tcp_server_task and not tcp_server_task.done():
        tcp_server_task.cancel()
        try:
            await tcp_server_task
        except asyncio.CancelledError:
            pass
        logger.info("TCP server stopped")

    # Stop heartbeat monitor
    if heartbeat_monitor_task and not heartbeat_monitor_task.done():
        heartbeat_monitor_task.cancel()
        try:
            await heartbeat_monitor_task
        except asyncio.CancelledError:
            pass
        logger.info("Heartbeat monitor stopped")

    await close_db()
    logger.info("Database connections closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)