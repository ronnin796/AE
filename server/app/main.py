"""FastAPI server main entry point"""

from datetime import datetime
from typing import Optional

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

import logging
import uvicorn

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


@app.get("/", summary="Root endpoint")
async def root() -> dict:
    return {"message": "AetherEdge Server is running", "version": "0.1.0"}


@app.get("/health", summary="Health check endpoint")
async def health() -> dict:
    return {"status": "ok", "uptime": 0}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)