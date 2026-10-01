"""System test for AetherEdge Part I - End-to-End Edge Monitoring"""

import asyncio
import subprocess
import time
from pathlib import Path

import pytest
import pytest_asyncio
import httpx

from app.database import async_session_maker
from sqlalchemy import delete, select
from app.models.node import Node
from app.models.telemetry import Telemetry


# Test configuration
SERVER_HOST = "127.0.0.1"
SERVER_HTTP_PORT = 8080
SERVER_TCP_PORT = 8081
BASE_URL = f"http://{SERVER_HOST}:{SERVER_HTTP_PORT}/api/v1"
EDGE_BINARY = Path(__file__).parent.parent.parent.parent / "edge" / "target" / "debug" / "aetheredge-edge"


@pytest_asyncio.fixture(scope="function")
async def clean_database():
    """Clean database before each test"""
    async with async_session_maker() as db:
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()
    yield
    async with async_session_maker() as db:
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()


@pytest.mark.asyncio
async def test_st001_end_to_end_edge_monitoring(server_process, clean_database):
    """
    ST-001: End-to-End Edge Monitoring
    
    Test the complete Part I pipeline with 2 edge nodes running for 60 seconds:
    - 2 Rust edge daemons collect real Linux telemetry
    - Telemetry sent via TCP binary protocol to FastAPI server
    - Server stores telemetry in SQLite database
    - Dashboard (HTTP API) can query and display telemetry
    - Both nodes remain online throughout test
    """
    edge_procs = []
    
    try:
        # Start two edge nodes
        for node_id in ["st001-node-a", "st001-node-b"]:
            proc = subprocess.Popen(
                [
                    str(EDGE_BINARY),
                    "--node-id", node_id,
                    "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
                    "--telemetry-interval", "2",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            edge_procs.append(proc)
        
        # Wait for registration
        await asyncio.sleep(5)
        
        # Verify both nodes registered
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/")
            assert resp.status_code == 200
            nodes = resp.json()["nodes"]
            node_ids = {n["node_id"] for n in nodes}
            assert "st001-node-a" in node_ids
            assert "st001-node-b" in node_ids
            for node in nodes:
                if node["node_id"] in ["st001-node-a", "st001-node-b"]:
                    assert node["status"] == "online"
        
        # Run for 60 seconds, collecting telemetry
        test_duration = 60
        check_interval = 10
        checks = test_duration // check_interval
        
        telemetry_counts = {"st001-node-a": 0, "st001-node-b": 0}
        
        for i in range(checks):
            await asyncio.sleep(check_interval)
            
            # Check telemetry for each node
            async with httpx.AsyncClient() as client:
                for node_id in ["st001-node-a", "st001-node-b"]:
                    resp = await client.get(f"{BASE_URL}/telemetry/node/{node_id}?limit=50")
                    assert resp.status_code == 200
                    telemetry = resp.json()
                    telemetry_counts[node_id] = len(telemetry)
                    
                    # Verify telemetry has real data
                    for sample in telemetry:
                        assert sample["node_id"] == node_id
                        assert sample["cpu_usage"] is not None
                        assert sample["memory_usage"] is not None
                        assert 0 <= sample["cpu_usage"] <= 1600  # 16 cores max
                        assert 0 <= sample["memory_usage"] <= 100
                        assert sample["timestamp"] > 0
        
        # Verify both nodes collected telemetry throughout the test
        # With 2s interval over 60s, expect ~30 samples per node
        for node_id, count in telemetry_counts.items():
            assert count >= 20, f"Node {node_id} only collected {count} telemetry samples"
        
        # Verify both nodes still online at end
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/nodes/")
            assert resp.status_code == 200
            nodes = resp.json()["nodes"]
            for node in nodes:
                if node["node_id"] in ["st001-node-a", "st001-node-b"]:
                    assert node["status"] == "online", f"Node {node['node_id']} went offline"
        
        print(f"Telemetry collected: Node A={telemetry_counts['st001-node-a']}, Node B={telemetry_counts['st001-node-b']}")
        
    finally:
        for proc in edge_procs:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)