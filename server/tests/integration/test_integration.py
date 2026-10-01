"""Integration tests for AetherEdge Part I

These tests require a running server and edge daemon.
Run with: pytest tests/integration/ -v
"""

import asyncio
import subprocess
import time
from pathlib import Path

import pytest
import pytest_asyncio
import httpx

from app.database import async_session_maker
from app.models.node import Node, NodeStatus
from sqlalchemy import delete
from app.models.telemetry import Telemetry


# Test configuration
SERVER_HOST = "127.0.0.1"
SERVER_HTTP_PORT = 8080
SERVER_TCP_PORT = 8081
BASE_URL = f"http://{SERVER_HOST}:{SERVER_HTTP_PORT}/api/v1"
EDGE_BINARY = Path(__file__).parent.parent.parent.parent / "edge" / "target" / "debug" / "aetheredge-edge"


async def clean_database():
    """Clean database (nodes and telemetry)"""
    from app.database import async_session_maker
    from app.models.node import Node
    from app.models.telemetry import Telemetry
    from sqlalchemy import delete
    
    # Use the server's session maker (which uses the main database file)
    async with async_session_maker() as db:
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()


# --- Node Registration Tests ---

@pytest.mark.asyncio
async def test_it001_single_node_registration(server_process):
    """IT-001: Single node registration via TCP protocol"""
    await clean_database()
    
    # Start edge node
    edge_proc = subprocess.Popen(
        [
            str(EDGE_BINARY),
            "--node-id", "it001-node-a",
            "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
            "--telemetry-interval", "2",
            "--no-heartbeat",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    try:
        await asyncio.sleep(3)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/")
            assert resp.status_code == 200
            data = resp.json()
            
            nodes = [n for n in data["nodes"] if n["node_id"] == "it001-node-a"]
            assert len(nodes) == 1
            assert nodes[0]["status"] == "online"
            assert nodes[0]["hostname"] is not None
            
    finally:
        edge_proc.terminate()
        edge_proc.wait(timeout=5)


@pytest.mark.asyncio
async def test_it002_multi_node_registration(server_process):
    """IT-002: Multiple independent node registrations"""
    await clean_database()
    
    edge_procs = []
    
    try:
        for node_id in ["it002-node-a", "it002-node-b"]:
            proc = subprocess.Popen(
                [
                    str(EDGE_BINARY),
                    "--node-id", node_id,
                    "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
                    "--telemetry-interval", "2",
                    "--no-heartbeat",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            edge_procs.append(proc)
        
        await asyncio.sleep(4)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/")
            assert resp.status_code == 200
            data = resp.json()
            
            node_ids = {n["node_id"] for n in data["nodes"]}
            assert "it002-node-a" in node_ids
            assert "it002-node-b" in node_ids
            
            # Both should be online
            for node in data["nodes"]:
                if node["node_id"] in ["it002-node-a", "it002-node-b"]:
                    assert node["status"] == "online"
                    
    finally:
        for proc in edge_procs:
            proc.terminate()
            proc.wait(timeout=5)


# --- Heartbeat Tests ---

@pytest.mark.asyncio
async def test_it003_heartbeat_updates_last_seen(server_process):
    """IT-003: Heartbeat updates node last_seen"""
    await clean_database()
    
    edge_proc = subprocess.Popen(
        [
            str(EDGE_BINARY),
            "--node-id", "it003-node-a",
            "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
            "--telemetry-interval", "10",
            "--no-telemetry",  # Disable telemetry to isolate heartbeat
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    try:
        await asyncio.sleep(3)  # Registration + first heartbeat
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/it003-node-a")
            assert resp.status_code == 200
            initial_last_seen = resp.json()["last_seen"]
        
        # Wait for another heartbeat (10s interval) + buffer
        await asyncio.sleep(15)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/it003-node-a")
            assert resp.status_code == 200
            updated_last_seen = resp.json()["last_seen"]
            assert updated_last_seen != initial_last_seen, f"last_seen not updated: {initial_last_seen} == {updated_last_seen}"
            
    finally:
        edge_proc.terminate()
        edge_proc.wait(timeout=5)


# --- Telemetry Transmission Tests ---

@pytest.mark.asyncio
async def test_it004_telemetry_pipeline(server_process):
    """IT-004: Full telemetry pipeline Linux -> Rust -> TCP -> DB -> Dashboard"""
    await clean_database()
    
    edge_proc = subprocess.Popen(
        [
            str(EDGE_BINARY),
            "--node-id", "it004-node-a",
            "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
            "--telemetry-interval", "1",
            "--no-heartbeat",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    try:
        # Wait for several telemetry samples
        await asyncio.sleep(5)
        
        # Check telemetry received via HTTP API
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/telemetry/node/it004-node-a?limit=10")
            assert resp.status_code == 200
            telemetry = resp.json()
            
            # Should have multiple samples
            assert len(telemetry) >= 3
            
            # Verify real data (not mocked)
            for sample in telemetry:
                assert sample["node_id"] == "it004-node-a"
                assert sample["cpu_usage"] is not None
                assert sample["memory_usage"] is not None
                assert sample["timestamp"] > 0
                # CPU usage should be realistic (0-100*core_count)
                assert 0 <= sample["cpu_usage"] <= 1600  # 16 cores max
                # Memory usage should be 0-100%
                assert 0 <= sample["memory_usage"] <= 100
                # Temperature should be reasonable
                if sample["temperature"] is not None:
                    assert -50 <= sample["temperature"] <= 150
                    
    finally:
        edge_proc.terminate()
        edge_proc.wait(timeout=5)


@pytest.mark.asyncio
async def test_it008_concurrent_nodes_telemetry(server_process):
    """IT-008: Concurrent nodes - telemetry correctly associated"""
    await clean_database()
    
    edge_procs = []
    
    try:
        # Start two edge nodes
        for node_id in ["it008-node-a", "it008-node-b"]:
            proc = subprocess.Popen(
                [
                    str(EDGE_BINARY),
                    "--node-id", node_id,
                    "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
                    "--telemetry-interval", "1",
                    "--no-heartbeat",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            edge_procs.append(proc)
        
        # Wait for telemetry
        await asyncio.sleep(5)
        
        # Check telemetry for each node separately
        async with httpx.AsyncClient() as client:
            for node_id in ["it008-node-a", "it008-node-b"]:
                resp = await client.get(f"{BASE_URL}/telemetry/node/{node_id}?limit=5")
                assert resp.status_code == 200
                telemetry = resp.json()
                
                assert len(telemetry) >= 3
                # All samples should belong to this node
                for sample in telemetry:
                    assert sample["node_id"] == node_id
                    
    finally:
        for proc in edge_procs:
            proc.terminate()
            proc.wait(timeout=5)


# --- Node Disconnection Tests ---

@pytest.mark.asyncio
async def test_it005_node_disconnection_detected(server_process):
    """IT-005: Server detects node disconnection after timeout"""
    await clean_database()
    
    edge_proc = subprocess.Popen(
        [
            str(EDGE_BINARY),
            "--node-id", "it005-node-a",
            "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
            "--telemetry-interval", "10",
            "--no-telemetry",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    try:
        # Wait for registration and a few heartbeats
        await asyncio.sleep(5)
        
        # Verify node is online
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/it005-node-a")
            assert resp.status_code == 200
            assert resp.json()["status"] == "online"
        
        # Stop the edge node
        edge_proc.terminate()
        edge_proc.wait(timeout=5)
        
        # Wait for heartbeat timeout - need to wait longer than the timeout
        await asyncio.sleep(15)
        
        # Call maintenance endpoint with 5s timeout
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/nodes/maintenance/mark-offline",
                params={"timeout_seconds": 5}
            )
            assert resp.status_code == 200
            result = resp.json()
            assert result["marked_offline"] >= 1
            
        await asyncio.sleep(2)
        
        # Verify node is now offline
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/it005-node-a")
            assert resp.status_code == 200
            assert resp.json()["status"] == "offline"
            
    finally:
        if edge_proc.poll() is None:
            edge_proc.terminate()
            edge_proc.wait(timeout=5)


# --- Node Reconnection Tests ---

@pytest.mark.asyncio
async def test_it006_node_reconnection(server_process):
    """IT-006: Stopped node can reconnect and become active"""
    await clean_database()
    
    # Start first instance
    edge_proc = subprocess.Popen(
        [
            str(EDGE_BINARY),
            "--node-id", "it006-node-a",
            "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
            "--telemetry-interval", "2",
            "--no-heartbeat",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    try:
        await asyncio.sleep(3)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/it006-node-a")
            assert resp.status_code == 200
            assert resp.json()["status"] == "online"
        
        # Stop first instance
        edge_proc.terminate()
        edge_proc.wait(timeout=5)
        
        # Mark offline via maintenance endpoint
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/nodes/maintenance/mark-offline",
                params={"timeout_seconds": 5}
            )
            assert resp.status_code == 200
        
        await asyncio.sleep(2)
        
        # Start second instance with same node_id
        edge_proc2 = subprocess.Popen(
            [
                str(EDGE_BINARY),
                "--node-id", "it006-node-a",
                "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
                "--telemetry-interval", "2",
                "--no-heartbeat",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        try:
            await asyncio.sleep(3)
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{BASE_URL}/nodes/it006-node-a")
                assert resp.status_code == 200
                assert resp.json()["status"] == "online"
                
        finally:
            edge_proc2.terminate()
            edge_proc2.wait(timeout=5)
            
    finally:
        if edge_proc.poll() is None:
            edge_proc.terminate()
            edge_proc.wait(timeout=5)


# --- Invalid Input Tests ---

@pytest.mark.asyncio
async def test_it007_malformed_registration_rejected(server_process):
    """IT-007: Server rejects malformed registration safely"""
    await clean_database()
    
    async with httpx.AsyncClient() as client:
        # Missing required fields
        resp = await client.post(f"{BASE_URL}/nodes/register", json={})
        assert resp.status_code == 422  # Validation error
        
        # Invalid cpu_cores (must be >= 1)
        resp = await client.post(f"{BASE_URL}/nodes/register", json={
            "node_id": "it007-invalid-cores",
            "hostname": "test-host",
            "cpu_cores": 0,
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_it007_malformed_telemetry_rejected(server_process):
    """IT-007: Server rejects malformed telemetry safely"""
    await clean_database()
    
    # Create a valid node first via HTTP API
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/nodes/register", json={
            "node_id": "it007-node-a",
            "hostname": "test-host",
            "os": "Linux",
        })
        assert resp.status_code == 201
    
    async with httpx.AsyncClient() as client:
        # Negative timestamp should be rejected by schema validation (ge=0)
        resp = await client.post(f"{BASE_URL}/telemetry/", json={
            "node_id": "it007-node-a",
            "timestamp": -1,
            "cpu_usage": 50.0,
        })
        assert resp.status_code == 422
        
        # Invalid memory_usage (must be 0-100)
        resp = await client.post(f"{BASE_URL}/telemetry/", json={
            "node_id": "it007-node-a",
            "timestamp": int(time.time()),
            "memory_usage": 150.0,
        })
        assert resp.status_code == 422