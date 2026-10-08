#!/bin/bash
# Script to test edge-server connection
cd /home/ronnin/Projects/AE_Edge

echo "=== Building edge daemon ==="
cargo build --bin aetheredge-edge --manifest-path edge/Cargo.toml 2>&1 | tail -2

echo ""
echo "=== Starting server ==="
cd /home/ronnin/Projects/AE_Edge/server
source .venv/bin/activate
python -m app.main &
SERVER_PID=$!
sleep 3

echo ""
echo "=== Testing edge client connection ==="
cd /home/ronnin/Projects/AE_Edge
timeout 5 ./edge/target/debug/aetheredge-edge --server-addr 127.0.0.1:8081 --node-id test-node-x 2>&1

echo ""
echo "=== Stopping server ==="
kill $SERVER_PID 2>/dev/null || true
