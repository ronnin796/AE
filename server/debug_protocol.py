#!/usr/bin/env python3
"""Debug script to see exactly what bytes are being sent/received"""

import msgpack
from app.protocol import MAGIC_BYTES, MAX_MESSAGE_SIZE, MessageType, Envelope, Register, encode_envelope

def debug_serialize():
    print("=== DEBUG: Creating test Register message ===")

    # Create a register message like the Rust client would
    register = Register(
        node_id="node-a",
        hostname="test-host",
        os="Linux",
        os_version="6.1",
        kernel_version="6.1.0",
        cpu_brand="Intel i7",
        cpu_cores=8,
        total_memory=16_000_000_000,
        version="0.1.0",
        arch="x86_64",
        capabilities=["telemetry", "heartbeat", "inference"]
    )

    print(f"Register object: {register}")
    register_payload = register.serialize()
    print(f"Register payload ({len(register_payload)} bytes): {register_payload.hex()}")

    # Create envelope
    envelope = Envelope(
        version=1,
        msg_type=MessageType.REGISTER,
        sequence=1,
        timestamp=1234567890,
        payload=register_payload
    )

    print(f"Envelope object: {envelope}")

    # Serialize envelope to MessagePack (what goes inside the framing)
    envelope_msgpack = envelope.serialize()
    print(f"Envelope MessagePack ({len(envelope_msgpack)} bytes): {envelope_msgpack.hex()}")

    # Unpack to see what we get
    unpacked = msgpack.unpackb(envelope_msgpack, raw=False)
    print(f"Unpacked envelope: {unpacked}")
    print(f"Type: {type(unpacked)}")
    if isinstance(unpacked, dict):
        print(f"'msg_type' value: {unpacked.get('msg_type')} (type: {type(unpacked.get('msg_type'))})")
    else:
        print(f"Not a dict! It's a {type(unpacked)}: {unpacked}")

    # Now apply the framing (what actually goes on the wire)
    framed_data = encode_envelope(envelope)
    print(f"Framed data ({len(framed_data)} bytes): {framed_data.hex()}")

    # Verify framing
    if framed_data[:4] == MAGIC_BYTES:
        print("✓ Magic bytes correct")
    else:
        print(f"✗ Magic bytes incorrect: {framed_data[:4].hex()} expected {MAGIC_BYTES.hex()}")

    length = int.from_bytes(framed_data[4:8], byteorder='big')
    print(f"Length field: {length} bytes")
    print(f"Actual payload length: {len(framed_data) - 8}")

    if length == len(framed_data) - 8:
        print("✓ Length matches payload")
    else:
        print("✗ Length mismatch")

    # Extract the inner payload (what Python server should get)
    inner_payload = framed_data[8:]
    print(f"Inner payload ({len(inner_payload)} bytes): {inner_payload.hex()}")

    # Try to unpack this inner payload
    try:
        inner_unpacked = msgpack.unpackb(inner_payload, raw=False)
        print(f"Inner unpacked: {inner_unpacked}")
        print(f"Type: {type(inner_unpacked)}")
        if isinstance(inner_unpacked, dict):
            print(f"✓ Inner payload is dict with msg_type: {inner_unpacked.get('msg_type')}")
        else:
            print(f"✗ Inner payload is {type(inner_unpacked)}: {inner_unpacked}")
    except Exception as e:
        print(f"✗ Failed to unpack inner payload: {e}")

if __name__ == "__main__":
    debug_serialize()