"""Protocol definitions for AetherEdge binary protocol

Part I: Binary protocol handler for edge node communication
This provides MessagePack serialization matching the Rust edge daemon protocol.
Designed for extension in Part II with TLS, authentication, etc.

IMPORTANT: The Rust edge daemon serializes its structs as MessagePack *maps*
(keys = field names) and its `#[repr(u8)]` enums as single-element arrays
(e.g. msg_type 1 => [[1]]). All deserialize helpers below accept map-form data,
and enum fields are unwrapped from the list form rmp-serde produces.
"""

import msgpack
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class MessageType(Enum):
    REGISTER = 1
    REGISTER_RESPONSE = 2
    HEARTBEAT = 3
    HEARTBEAT_ACK = 4
    TELEMETRY = 5
    INFERENCE_REQUEST = 6
    INFERENCE_RESULT = 7
    ERROR = 255


# Protocol version
PROTOCOL_VERSION = 1

# Magic bytes for protocol identification
MAGIC_BYTES = b"AETH"

# Maximum message size (1 MB)
MAX_MESSAGE_SIZE = 1048576


def _get(data: Any, key: str, default=None) -> Any:
    """Fetch a field from a deserialized payload.

    rmp-serde (the Rust side) serializes named structs as MessagePack maps,
    so `data` is normally a dict. Return the default for list-form payloads.
    """
    if isinstance(data, dict):
        return data.get(key, default)
    return default


def _unwrap_enum_value(raw: Any) -> int:
    """Convert an enum field to its integer value.

    rmp-serde serializes `#[repr(u8)]` enums as a single-element array
    (e.g. `[[1]]` for Register). Accept int, nested list, or enum-name str.
    """
    if isinstance(raw, int):
        return raw
    if isinstance(raw, (list, tuple)) and len(raw) >= 1:
        return _unwrap_enum_value(raw[0])
    if isinstance(raw, str):
        for mt in MessageType:
            if mt.name.lower() == raw.lower():
                return mt.value
    raise ValueError(f"Cannot interpret enum value: {raw!r}")


@dataclass
class Register:
    """Node registration message"""
    node_id: str
    hostname: str
    os: str
    os_version: str
    kernel_version: str
    cpu_brand: str
    cpu_cores: int
    total_memory: int
    version: str
    arch: str
    capabilities: List[str] = field(default_factory=list)

    @classmethod
    def deserialize(cls, payload: bytes) -> 'Register':
        data = msgpack.unpackb(payload, raw=False)
        return cls(
            node_id=_get(data, 'node_id'),
            hostname=_get(data, 'hostname'),
            os=_get(data, 'os'),
            os_version=_get(data, 'os_version'),
            kernel_version=_get(data, 'kernel_version'),
            cpu_brand=_get(data, 'cpu_brand'),
            cpu_cores=_get(data, 'cpu_cores'),
            total_memory=_get(data, 'total_memory'),
            version=_get(data, 'version'),
            arch=_get(data, 'arch'),
            capabilities=_get(data, 'capabilities') or [],
        )

    def serialize(self) -> bytes:
        return msgpack.packb({
            'node_id': self.node_id,
            'hostname': self.hostname,
            'os': self.os,
            'os_version': self.os_version,
            'kernel_version': self.kernel_version,
            'cpu_brand': self.cpu_brand,
            'cpu_cores': self.cpu_cores,
            'total_memory': self.total_memory,
            'version': self.version,
            'arch': self.arch,
            'capabilities': self.capabilities,
        })


@dataclass
class ProtocolServerConfig:
    """Server configuration"""
    heartbeat_interval: int
    telemetry_interval: int
    model_update_url: Optional[str] = None

    @classmethod
    def deserialize(cls, payload: bytes) -> 'ProtocolServerConfig':
        data = msgpack.unpackb(payload, raw=False)
        return cls(
            heartbeat_interval=_get(data, 'heartbeat_interval'),
            telemetry_interval=_get(data, 'telemetry_interval'),
            model_update_url=_get(data, 'model_update_url'),
        )

    def serialize(self) -> dict:
        return {
            'heartbeat_interval': self.heartbeat_interval,
            'telemetry_interval': self.telemetry_interval,
            'model_update_url': self.model_update_url,
        }


# Backward-compatible alias
ServerConfig = ProtocolServerConfig


@dataclass
class RegisterResponse:
    """Registration response message"""
    success: bool
    node_id: str
    assigned_id: str
    message: str
    server_time: int
    config: Optional['ProtocolServerConfig'] = None

    @classmethod
    def deserialize(cls, payload: bytes) -> 'RegisterResponse':
        data = msgpack.unpackb(payload, raw=False)
        config_data = _get(data, 'config')
        config = None
        if config_data is not None:
            config = ProtocolServerConfig.deserialize(
                msgpack.packb(config_data)
            )
        return cls(
            success=_get(data, 'success'),
            node_id=_get(data, 'node_id'),
            assigned_id=_get(data, 'assigned_id'),
            message=_get(data, 'message'),
            server_time=_get(data, 'server_time'),
            config=config,
        )

    def serialize(self) -> bytes:
        return msgpack.packb({
            'success': self.success,
            'node_id': self.node_id,
            'assigned_id': self.assigned_id,
            'message': self.message,
            'server_time': self.server_time,
            'config': self.config.serialize() if self.config else None,
        })


@dataclass
class Heartbeat:
    """Heartbeat message"""
    node_id: str
    timestamp: int
    status: str
    uptime: int

    @classmethod
    def deserialize(cls, payload: bytes) -> 'Heartbeat':
        data = msgpack.unpackb(payload, raw=False)
        # status is a Rust enum; rmp-serde sends it as [[1]] or as int
        status_raw = _get(data, 'status')
        if isinstance(status_raw, (list, tuple)):
            status_raw = status_raw[0] if status_raw else 'online'
        return cls(
            node_id=_get(data, 'node_id'),
            timestamp=_get(data, 'timestamp'),
            status=str(status_raw),
            uptime=_get(data, 'uptime'),
        )

    def serialize(self) -> bytes:
        return msgpack.packb({
            'node_id': self.node_id,
            'timestamp': self.timestamp,
            'status': self.status,
            'uptime': self.uptime,
        })


@dataclass
class HeartbeatAck:
    """Heartbeat acknowledgment"""
    node_id: str
    server_time: int
    next_heartbeat_interval: int
    commands: List[str] = field(default_factory=list)

    @classmethod
    def deserialize(cls, payload: bytes) -> 'HeartbeatAck':
        data = msgpack.unpackb(payload, raw=False)
        return cls(
            node_id=_get(data, 'node_id'),
            server_time=_get(data, 'server_time'),
            next_heartbeat_interval=_get(data, 'next_heartbeat_interval') or 0,
            commands=_get(data, 'commands') or [],
        )

    def serialize(self) -> bytes:
        return msgpack.packb({
            'node_id': self.node_id,
            'server_time': self.server_time,
            'next_heartbeat_interval': self.next_heartbeat_interval,
            'commands': self.commands,
        })


@dataclass
class Telemetry:
    """Telemetry message (edge -> server)"""
    node_id: str
    timestamp: int
    cpu_usage: Optional[float] = None
    cpu_per_core: Optional[List[float]] = None
    memory_usage: Optional[float] = None
    memory_total: Optional[int] = None
    memory_available: Optional[int] = None
    memory_used: Optional[int] = None
    temperature: Optional[float] = None
    temperatures: Optional[List[float]] = None
    uptime: Optional[int] = None
    load_1: Optional[float] = None
    load_5: Optional[float] = None
    load_15: Optional[float] = None
    processes_running: Optional[int] = None
    processes_total: Optional[int] = None

    @classmethod
    def deserialize(cls, payload: bytes) -> 'Telemetry':
        data = msgpack.unpackb(payload, raw=False)
        return cls(
            node_id=_get(data, 'node_id'),
            timestamp=_get(data, 'timestamp'),
            cpu_usage=_get(data, 'cpu_usage'),
            cpu_per_core=_get(data, 'cpu_per_core'),
            memory_usage=_get(data, 'memory_usage'),
            memory_total=_get(data, 'memory_total'),
            memory_available=_get(data, 'memory_available'),
            memory_used=_get(data, 'memory_used'),
            temperature=_get(data, 'temperature'),
            temperatures=_get(data, 'temperatures'),
            uptime=_get(data, 'uptime'),
            load_1=_get(data, 'load_1'),
            load_5=_get(data, 'load_5'),
            load_15=_get(data, 'load_15'),
            processes_running=_get(data, 'processes_running'),
            processes_total=_get(data, 'processes_total'),
        )


@dataclass
class Error:
    """Error message"""
    code: int
    message: str
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def deserialize(cls, payload: bytes) -> 'Error':
        data = msgpack.unpackb(payload, raw=False)
        return cls(
            code=_get(data, 'code'),
            message=_get(data, 'message'),
            details=_get(data, 'details'),
        )

    def serialize(self) -> bytes:
        return msgpack.packb({
            'code': self.code,
            'message': self.message,
            'details': self.details,
        })


@dataclass
class Envelope:
    """Envelope wrapping all protocol messages"""
    version: int
    msg_type: MessageType
    sequence: int
    timestamp: int
    payload: bytes

    def serialize(self) -> bytes:
        """Serialize envelope to MessagePack"""
        data = {
            'version': self.version,
            'msg_type': self.msg_type.value,
            'sequence': self.sequence,
            'timestamp': self.timestamp,
            'payload': self.payload,
        }
        return msgpack.packb(data)

    @classmethod
    def deserialize(cls, data: bytes) -> 'Envelope':
        """Deserialize MessagePack bytes to envelope.

        Accepts both map form ({version, msg_type, sequence, timestamp, payload})
        and array form ([version, msg_type, sequence, timestamp, payload]).
        """
        unpacked = msgpack.unpackb(data, raw=False)

        if isinstance(unpacked, dict):
            # Dictionary format: {version: ..., msg_type: ..., ...}
            payload = unpacked['payload']
            # msgpack unpacks byte arrays as list of ints; convert back to bytes
            if isinstance(payload, list):
                payload = bytes(payload)
            return cls(
                version=unpacked['version'],
                msg_type=MessageType(_unwrap_enum_value(unpacked['msg_type'])),
                sequence=unpacked['sequence'],
                timestamp=unpacked['timestamp'],
                payload=payload,
            )
        elif isinstance(unpacked, (list, tuple)) and len(unpacked) >= 5:
            # Array format: [version, msg_type, sequence, timestamp, payload]
            payload = unpacked[4]
            if isinstance(payload, list):
                payload = bytes(payload)
            return cls(
                version=unpacked[0],
                msg_type=MessageType(_unwrap_enum_value(unpacked[1])),
                sequence=unpacked[2],
                timestamp=unpacked[3],
                payload=payload,
            )
        else:
            raise ValueError(
                f"Invalid envelope data format: expected dict or list of 5 elements, "
                f"got {type(unpacked)}"
            )


def encode_envelope(envelope: Envelope) -> bytes:
    """Encode envelope for network transmission with magic bytes and length prefix"""
    payload = envelope.serialize()

    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError(f"Message exceeds maximum size: {len(payload)} > {MAX_MESSAGE_SIZE}")

    # Prepend magic bytes and length
    buf = bytearray()
    buf.extend(MAGIC_BYTES)
    buf.extend((len(payload)).to_bytes(4, byteorder='big'))
    buf.extend(payload)

    return bytes(buf)


def decode_envelope(data: bytes) -> Envelope:
    """Decode envelope from network bytes (magic + length + envelope)"""
    if len(data) < 8:
        raise ValueError("Message too short for header")

    # Verify magic bytes
    if data[0:4] != MAGIC_BYTES:
        raise ValueError(f"Invalid magic bytes: {data[:4]}")

    # Read payload length
    length = int.from_bytes(data[4:8], byteorder='big')

    if len(data) < 8 + length:
        raise ValueError(f"Message truncated: expected {length} bytes, got {len(data) - 8}")

    # Extract the envelope payload (the MessagePack-encoded envelope)
    envelope_bytes = data[8:8 + length]

    return Envelope.deserialize(envelope_bytes)
