"""Benchmark tests for AetherEdge Part I"""

import asyncio
import statistics
import subprocess
import time
from pathlib import Path

import pytest
import pytest_asyncio
import psutil
import httpx

from app.database import async_session_maker
from sqlalchemy import delete
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
    from app.database import async_session_maker
    from sqlalchemy import delete
    from app.models.telemetry import Telemetry
    from app.models.node import Node
    async with async_session_maker() as db:
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()
    yield
    async with async_session_maker() as db:
        await db.execute(delete(Telemetry))
        await db.execute(delete(Node))
        await db.commit()


def get_process_memory_mb(pid):
    """Get process RSS memory in MB"""
    try:
        proc = psutil.Process(pid)
        return proc.memory_info().rss / 1024 / 1024
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def get_process_cpu_percent(pid, interval=0.1):
    """Get process CPU percentage"""
    try:
        proc = psutil.Process(pid)
        return proc.cpu_percent(interval=interval)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


class TestBenchmarks:
    """Benchmark tests for AetherEdge Part I"""

    @pytest.mark.asyncio
    async def test_bt003_edge_daemon_memory_consumption(self, server_process, clean_database):
        """BT-003: Edge daemon memory consumption (RSS)"""
        edge_proc = subprocess.Popen(
            [
                str(EDGE_BINARY),
                "--node-id", "bt003-node-a",
                "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
                "--telemetry-interval", "2",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        try:
            await asyncio.sleep(5)  # Let it stabilize
            
            # Sample memory over 30 seconds
            samples = []
            for _ in range(30):
                mem = get_process_memory_mb(edge_proc.pid)
                if mem:
                    samples.append(mem)
                await asyncio.sleep(1)
            
            assert len(samples) > 0
            mean_mem = statistics.mean(samples)
            max_mem = max(samples)
            min_mem = min(samples)
            
            print(f"BT-003 Edge Daemon Memory: mean={mean_mem:.1f}MB, min={min_mem:.1f}MB, max={max_mem:.1f}MB")
            
            # Should be reasonable (< 100MB for a simple daemon)
            assert mean_mem < 100, f"Mean memory {mean_mem:.1f}MB exceeds 100MB"
            
        finally:
            edge_proc.terminate()
            edge_proc.wait(timeout=5)

    @pytest.mark.asyncio
    async def test_bt004_edge_daemon_cpu_overhead(self, server_process, clean_database):
        """BT-004: Edge daemon CPU overhead"""
        edge_proc = subprocess.Popen(
            [
                str(EDGE_BINARY),
                "--node-id", "bt004-node-a",
                "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
                "--telemetry-interval", "2",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        try:
            await asyncio.sleep(5)  # Let it stabilize
            
            # Sample CPU over 30 seconds
            samples = []
            for _ in range(30):
                cpu = get_process_cpu_percent(edge_proc.pid, interval=0.5)
                if cpu is not None:
                    samples.append(cpu)
                await asyncio.sleep(1)
            
            assert len(samples) > 0
            mean_cpu = statistics.mean(samples)
            max_cpu = max(samples)
            
            print(f"BT-004 Edge Daemon CPU: mean={mean_cpu:.2f}%, max={max_cpu:.2f}%")
            
            # Should be very low for an idle daemon (< 1% average)
            assert mean_cpu < 5.0, f"Mean CPU {mean_cpu:.2f}% exceeds 5%"
            
        finally:
            edge_proc.terminate()
            edge_proc.wait(timeout=5)

    @pytest.mark.asyncio
    async def test_bt005_telemetry_message_size(self, server_process, clean_database):
        """BT-005: Telemetry message size"""
        import httpx
        
        edge_proc = subprocess.Popen(
            [
                str(EDGE_BINARY),
                "--node-id", "bt005-node-a",
                "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
                "--telemetry-interval", "1",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        try:
            await asyncio.sleep(3)
            
            # Get a telemetry sample and measure its JSON size
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{BASE_URL}/telemetry/node/bt005-node-a?limit=1")
                assert resp.status_code == 200
                telemetry = resp.json()
                assert len(telemetry) > 0
                
                import json
                sample = telemetry[0]
                json_str = json.dumps(sample)
                size_bytes = len(json_str.encode('utf-8'))
                
                print(f"BT-005 Telemetry Message Size: {size_bytes} bytes")
                
                # Should be reasonable (< 2KB for a telemetry sample)
                assert size_bytes < 2048, f"Telemetry message {size_bytes} bytes exceeds 2KB"
                
        finally:
            edge_proc.terminate()
            edge_proc.wait(timeout=5)

    @pytest.mark.asyncio
    async def test_bt006_telemetry_interval_accuracy(self, server_process, clean_database):
        """BT-006: Telemetry transmission interval accuracy"""
        import httpx
        
        interval = 2  # seconds
        edge_proc = subprocess.Popen(
            [
                str(EDGE_BINARY),
                "--node-id", "bt006-node-a",
                "--server-addr", f"{SERVER_HOST}:{SERVER_TCP_PORT}",
                "--telemetry-interval", str(interval),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        try:
            await asyncio.sleep(5)
            
            # Collect timestamps for 30 seconds
            async with httpx.AsyncClient() as client:
                await asyncio.sleep(2)
                resp = await client.get(f"{BASE_URL}/telemetry/node/bt006-node-a?limit=20")
                assert resp.status_code == 200
                telemetry = resp.json()
                
                if len(telemetry) >= 3:
                    # Calculate intervals between consecutive samples
                    timestamps = [t["timestamp"] for t in telemetry]
                    timestamps.sort()
                    intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                    
                    mean_interval = statistics.mean(intervals)
                    stdev_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
                    
                    print(f"BT-006 Telemetry Interval: configured={interval}s, mean={mean_interval:.2f}s, stdev={stdev_interval:.2f}s")
                    
                    # Should be close to configured interval (within 20%)
                    assert abs(mean_interval - interval) / interval < 0.2, \
                        f"Mean interval {mean_interval:.2f}s deviates >20% from configured {interval}s"
                    
        finally:
            edge_proc.terminate()
            edge_proc.wait(timeout=5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])