"""FastAPI server main entry point"""

import asyncio
import logging
from datetime import datetime

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


@app.get("/", summary="Root endpoint")
async def root() -> dict:
    return {"message": "AetherEdge Server is running", "version": "0.1.0"}


@app.get("/health", summary="Health check endpoint")
async def health() -> dict:
    return {"status": "ok", "uptime": 0}


@app.on_event("startup")
async def startup_event():
    """Initialize database and start TCP server on startup"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Start TCP server in background
    global tcp_server_task
    tcp_server_task = asyncio.create_task(start_tcp_server())
    logger.info("TCP server started")


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

    await close_db()
    logger.info("Database connections closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)