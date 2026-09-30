# AetherEdge Communication — Protocol Documentation

## Overview

The AetherEdge communication protocol enables lightweight, reliable messaging between edge nodes and the central server. Designed for constrained environments with minimal overhead.

---

## 📦 Protocol Design

### MessagePack Serialization

**Choice**: MessagePack over TCP

**Why MessagePack?**
1. **Compact**: 3-5× smaller than JSON
2. **Fast**: Zero-copy deserialization in Rust
3. **Schema evolution**: Add fields without breaking clients
4. **Binary-safe**: Handles arbitrary byte data
5. **Cross-language**: Libraries for Rust, Python, JavaScript

**Alternative Considered**: CBOR, Protobuf
- CBOR: Good but larger payloads
- Protobuf: Requires `.proto` files and code generation overhead

### Envelope Format

```
[4 bytes magic: "AETH"]
[4 bytes payload length: big-endian u32]
[payload: serialized MessagePack message]
```

**Magic Bytes**: "AETH" identifies AetherEdge protocol
**Length**: Big-endian u32 for payload size
**Payload**: MessagePack serialized message

### Message Types

| Type | Value | Direction | Description |
|------|-------|-----------|-------------|
| Register | 1 | Edge → Server | Node registration |
| RegisterResponse | 2 | Server → Edge | Registration result |
| Heartbeat | 3 | Edge → Server | Liveness check |
| HeartbeatAck | 4 | Server → Edge | Acknowledgment |
| Telemetry | 5 | Edge → Server | System metrics |
| InferenceResult | 7 | Edge → Server | AI output |
| Error | 255 | Either | Error reporting |

---

## 🏗️ Implementation

### Rust Side

```rust
// Serialize message
let payload = serialize(&message)?;

// Create envelope
let envelope = Envelope {
    version: PROTOCOL_VERSION,
    msg_type: MessageType::Register,
    sequence: next_sequence(),
    timestamp: current_time(),
    payload,
};

// Send over TCP
send_message(&mut stream, &envelope)?;
```

### Python Side (FastAPI)

```python
# Receive message
payload = await read_exact(8)  # Magic + length
msg_type, seq, timestamp, payload = parse_envelope(payload)

# Deserialize based on type
match msg_type:
    case MessageType.Register:
        node_info = Register(**payload)
    case MessageType.Telemetry:
        telemetry = Telemetry(**payload)
```

---

## 🔄 Message Flows

### Node Registration

```text
Edge Node                            Server
    │                                    │
    │── REGISTER ────────────────────────→│
    │    (node_id, hostname, os, ...)    │
    │                                    │
    │←── REGISTER_RESPONSE ──────────────│
    │    (success, assigned_id, config)  │
    │                                    │
    │── HEARTBEAT ──────────────────────→│ (every 10s)
    │    (node_id, timestamp)            │
    │                                    │
    │←── HEARTBEAT_ACK ─────────────────│
    │    (next_interval, commands)       │
```

### Telemetry Transmission

```text
Edge Node                            Server
    │                                    │
    │── TELEMETRY ──────────────────────→│ (every 2s)
    │    (node_id, cpu, memory, temp)    │
    │                                    │
    │←── ACK ───────────────────────────│
    │                                    │
    │   Database: INSERT telemetry       │
    │   Dashboard: Update charts         │
```

---

## ⚙️ Configuration

### CLI Options

```
--server-addr <HOST:PORT>          # Server address (default: 127.0.0.1:8080)
--telemetry-interval <SECONDS>     # Collection interval (default: 2)
--heartbeat-interval <SECONDS>     # Heartbeat interval (default: 10)
--no-telemetry                        # Disable telemetry
--no-heartbeat                        # Disable heartbeat
```

### Environment Variables

```
AETHEREDGE_SERVER_ADDR=127.0.0.1:8080
AETHEREDGE_TELEMETRY_INTERVAL=2
AETHEREDGE_HEARTBEAT_INTERVAL=10
AETHEREDGE_NO_TELEMETRY=false
AETHEREDGE_NO_HEARTBEAT=false
```

---

## 🛠️ Error Handling

### Common Errors

| Error | Cause | Action |
|-------|-------|--------|
| Connection refused | Server not running | Retry with backoff |
| Timeout | Server overloaded | Reduce collection frequency |
| Invalid magic | Wrong protocol | Verify server version |
| Serialization error | Schema mismatch | Check message format |

### Retry Strategy

```rust
async fn send_with_retry<T>(
    stream: &mut TcpStream,
    message: &Message,
    max_retries: u32,
) -> Result<()> {
    for attempt in 0..max_retries {
        match send_message(stream, message).await {
            Ok(_) => return Ok(()),
            Err(e) if attempt < max_retries - 1 => {
                let delay = Duration::from_secs(2u64.pow(attempt));
                tokio::time::sleep(delay).await;
            }
            Err(e) => return Err(e),
        }
    }
    unreachable!()
}
```

---

## 📈 Performance

### Message Size Comparison

| Format | Typical Size | Overhead |
|--------|-------------|----------|
| JSON | ~1-2 KB | High (text) |
| MessagePack | ~300-500 bytes | Low (binary) |
| Protobuf | ~200-400 bytes | Lowest (binary) |

### Latency

- **Serialization**: < 1 ms (MessagePack)
- **TCP transmission**: < 10 ms (local network)
- **Total round-trip**: < 20 ms

---

## 🔄 Part II Extensions

### Planned Improvements

1. **TLS/SSL**: Encrypt all communications
2. **Message acknowledgment**: Explicit ACK/NACK
3. **Compression**: Built-in compression support
4. **Schema versioning**: Handle protocol upgrades
5. **Multiplexing**: Multiple message types over single connection

---

## 📚 References

- MessagePack: https://msgpack.org/
- TCP: https://en.wikipedia.org/wiki/Transmission_Control_Protocol
- Rust Tokio: https://tokio.rs/

---

*Document generated: 2026-09-30*