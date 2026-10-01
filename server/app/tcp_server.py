#!/usr/bin/env python3
"""Simple TCP server for AetherEdge binary protocol handling

Part I: Binary protocol handler for edge node communication
This provides an alternative to HTTP APIs for Rust edge nodes.
Designed for extension in Part II with TLS, authentication, etc.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.models.node import Node, NodeStatus
from app.schemas.node import NodeRegister

from app.protocol import (
    PROTOCOL_VERSION, MAGIC_BYTES, MAX_MESSAGE_SIZE,
    MessageType, Envelope, Register, RegisterResponse,
    Heartbeat, HeartbeatAck, Telemetry as ProtocolTelemetry,
    ServerConfig as ProtocolServerConfig,
    Error, ServerCommand, encode_envelope, decode_envelope
)

from app.services.database import create_node, get_node_by_id, add_telemetry
from app.schemas.telemetry import TelemetryCreate
from datetime import datetime

logger = logging.getLogger(__name__)


class SimpleTCPServer:
    """Simple TCP server for handling edge node binary protocol"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8081):
        self.host = host
        self.port = port
        self.server: Optional[asyncio.AbstractServer] = None
        self.running = False

    async def start(self):
        """Start the TCP server"""
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        self.running = True
        addr = self.server.sockets[0].getsockname()
        logger.info(f"TCP server started on {addr}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        """Stop the TCP server"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a client connection"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {client_addr}")

        node_id = None
        try:
            # Start heartbeat task
            hb_task = asyncio.create_task(self.send_heartbeat_periodically(writer))

            # Handle messages
            while self.running:
                # Read message using the new read_message method
                envelope = await self.read_message(reader)
                if envelope is None:
                    break

                # Process message
                response = await self.process_message(envelope)
                if response:
                    await self.write_message(writer, response)
                
                # Track node_id from register message
                if envelope.msg_type == MessageType.REGISTER and node_id is None:
                    try:
                        register_data = Register.deserialize(envelope.payload)
                        node_id = register_data.node_id
                        _connected_clients[node_id] = writer
                        logger.info(f"Registered client {node_id} for command sending")
                    except Exception as e:
                        logger.error(f"Failed to track node_id: {e}")

        except asyncio.IncompleteReadError:
            logger.info(f"Client {client_addr} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            if node_id and node_id in _connected_clients:
                del _connected_clients[node_id]
            hb_task.cancel()
            try:
                await hb_task
            except asyncio.CancelledError:
                pass
            writer.close()
            await writer.wait_closed()
            logger.info(f"Connection closed for {client_addr}")

    async def send_heartbeat_periodically(self, writer: asyncio.StreamWriter):
        """Send periodic heartbeat acknowledgment to client"""
        while self.running:
            await asyncio.sleep(30)  # Send every 30 seconds
            try:
                # Create heartbeat acknowledgment
                response = self.create_heartbeat_ack()
                await self.write_message(writer, response)
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")
                break

    async def read_message(self, reader: asyncio.StreamReader) -> Optional[Envelope]:
        """Read and decode a message from the stream"""
        try:
            # Read magic bytes
            magic = await reader.readexactly(4)
            if magic != MAGIC_BYTES:
                logger.warning(f"Invalid magic bytes: {magic}")
                return None

            # Read message length
            length_bytes = await reader.readexactly(4)
            length = int.from_bytes(length_bytes, byteorder='big')

            if length > MAX_MESSAGE_SIZE:
                logger.warning(f"Message too large: {length}")
                return None

            # Read full message (magic + length + payload) for decode_envelope
            full_message = magic + length_bytes + await reader.readexactly(length)
            return decode_envelope(full_message)

        except asyncio.IncompleteReadError:
            logger.info("Client disconnected")
            return None
        except Exception as e:
            import traceback
            logger.error(f"Error reading message: {e}\n{traceback.format_exc()}")
            return None

    async def write_message(self, writer: asyncio.StreamWriter, envelope: Envelope):
        """Send a message to the client"""
        try:
            data = encode_envelope(envelope)
            writer.write(data)
            await writer.drain()
        except Exception as e:
            logger.error(f"Error writing message: {e}")

    async def process_message(self, envelope: Envelope) -> Optional[Envelope]:
        """Process a received message and return response"""
        try:
            if envelope.msg_type == MessageType.REGISTER:
                return await self.handle_register(envelope)
            elif envelope.msg_type == MessageType.HEARTBEAT:
                return await self.handle_heartbeat(envelope)
            elif envelope.msg_type == MessageType.TELEMETRY:
                return await self.handle_telemetry(envelope)
            else:
                logger.warning(f"Unknown message type: {envelope.msg_type}")
                return self.create_error_response(envelope, 255, "Unknown message type")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self.create_error_response(envelope, 500, str(e))

    async def handle_heartbeat(self, envelope: Envelope) -> Optional[Envelope]:
        """Handle heartbeat from edge node"""
        try:
            # Deserialize heartbeat message
            heartbeat_data = Heartbeat.deserialize(envelope.payload)
            logger.debug(f"Heartbeat received from node {heartbeat_data.node_id}")

            # Update node last_seen in database
            async with async_session_maker() as db:
                node = await get_node_by_id(heartbeat_data.node_id, db)
                if node:
                    node.last_seen = datetime.utcnow()
                    node.status = NodeStatus.ONLINE
                    await db.commit()

            # Create heartbeat acknowledgment
            return self.create_heartbeat_ack()

        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
            return self.create_error_response(envelope, 500, str(e))

    async def handle_telemetry(self, envelope: Envelope) -> Optional[Envelope]:
        """Handle telemetry data from edge node"""
        try:
            # Deserialize telemetry message
            telemetry_data = ProtocolTelemetry.deserialize(envelope.payload)
            logger.debug(f"Telemetry received from node {telemetry_data.node_id}")

            # Store telemetry in database
            async with async_session_maker() as db:
                telemetry_create = TelemetryCreate(
                    node_id=telemetry_data.node_id,
                    timestamp=telemetry_data.timestamp,
                    cpu_usage=telemetry_data.cpu_usage,
                    cpu_per_core=telemetry_data.cpu_per_core,
                    memory_usage=telemetry_data.memory_usage,
                    memory_total=telemetry_data.memory_total,
                    memory_available=telemetry_data.memory_available,
                    memory_used=telemetry_data.memory_used,
                    temperature=telemetry_data.temperature,
                    temperatures=telemetry_data.temperatures,
                    uptime=telemetry_data.uptime,
                    load_1=telemetry_data.load_1,
                    load_5=telemetry_data.load_5,
                    load_15=telemetry_data.load_15,
                    processes_running=telemetry_data.processes_running,
                    processes_total=telemetry_data.processes_total,
                )
                await add_telemetry(telemetry_create, db)

            # Create telemetry acknowledgment
            return self.create_telemetry_ack(envelope.sequence)

        except Exception as e:
            logger.error(f"Error handling telemetry: {e}")
            return self.create_error_response(envelope, 500, str(e))

    async def handle_register(self, envelope: Envelope) -> Optional[Envelope]:
        """Handle node registration request"""
        try:
            # Get database session
            async with async_session_maker() as db:
                # Deserialize register message
                register_data = Register.deserialize(envelope.payload)

                logger.info(f"Registration request from node {register_data.node_id}")

                # Check if node exists
                existing_node = await get_node_by_id(register_data.node_id, db)

                if existing_node:
                    # Update existing node
                    existing_node.hostname = register_data.hostname
                    existing_node.os = register_data.os
                    existing_node.os_version = register_data.os_version
                    existing_node.kernel_version = register_data.kernel_version
                    existing_node.cpu_brand = register_data.cpu_brand
                    existing_node.cpu_cores = register_data.cpu_cores
                    existing_node.total_memory = register_data.total_memory
                    existing_node.version = register_data.version
                    existing_node.arch = register_data.arch
                    existing_node.status = NodeStatus.ONLINE
                    existing_node.last_seen = datetime.utcnow()

                    await db.commit()
                    await db.refresh(existing_node)

                    node_id = existing_node.node_id
                    assigned_id = str(existing_node.id)
                    message = "Node registered successfully (updated)"
                else:
                    # Create new node
                    node_schema = NodeRegister(
                        node_id=register_data.node_id,
                        hostname=register_data.hostname,
                        os=register_data.os,
                        os_version=register_data.os_version,
                        kernel_version=register_data.kernel_version,
                        cpu_brand=register_data.cpu_brand,
                        cpu_cores=register_data.cpu_cores,
                        total_memory=register_data.total_memory,
                        version=register_data.version,
                        arch=register_data.arch,
                    )

                    new_node = await create_node(node_schema, db)
                    await db.commit()
                    node_id = new_node.node_id
                    assigned_id = str(new_node.id)
                    message = "Node registered successfully"

                # Create response
                server_config = ProtocolServerConfig(
                    heartbeat_interval=10,
                    telemetry_interval=2,
                    model_update_url=None,
                )

                response = RegisterResponse(
                    success=True,
                    node_id=node_id,
                    assigned_id=assigned_id,
                    message=message,
                    server_time=int(datetime.utcnow().timestamp()),
                    config=server_config,
                )

                # Serialize response
                payload = response.serialize()
                return Envelope(
                    version=PROTOCOL_VERSION,
                    msg_type=MessageType.REGISTER_RESPONSE,
                    sequence=envelope.sequence,
                    timestamp=int(datetime.utcnow().timestamp()),
                    payload=payload,
                )

        except Exception as e:
            logger.error(f"Error handling registration: {e}")
            return self.create_error_response(envelope, 500, str(e))

    def create_heartbeat_ack(self, commands: List[str] = None) -> Envelope:
        """Create heartbeat acknowledgment with optional commands"""
        response = HeartbeatAck(
            node_id="server",
            server_time=int(datetime.utcnow().timestamp()),
            next_heartbeat_interval=10,
            commands=commands or [],
        )

        payload = response.serialize()
        return Envelope(
            version=PROTOCOL_VERSION,
            msg_type=MessageType.HEARTBEAT_ACK,
            sequence=0,
            timestamp=int(datetime.utcnow().timestamp()),
            payload=payload,
        )

    def create_heartbeat_ack_with_command(self, command: str, params: Dict[str, Any] = None) -> Envelope:
        """Create heartbeat acknowledgment with a server command"""
        server_command = ServerCommand(
            command=command,
            params=params or {},
        )
        command_payload = server_command.serialize()
        
        response = HeartbeatAck(
            node_id="server",
            server_time=int(datetime.utcnow().timestamp()),
            next_heartbeat_interval=10,
            commands=[command_payload.decode('utf-8') if isinstance(command_payload, bytes) else str(command_payload)],
        )

        payload = response.serialize()
        return Envelope(
            version=PROTOCOL_VERSION,
            msg_type=MessageType.HEARTBEAT_ACK,
            sequence=0,
            timestamp=int(datetime.utcnow().timestamp()),
            payload=payload,
        )

    def create_telemetry_ack(self, sequence: int) -> Envelope:
        """Create telemetry acknowledgment"""
        # For now, we use a simple acknowledgment similar to heartbeat ack
        # but with a different message type. The protocol doesn't define
        # a specific TelemetryAck message type, so we use HEARTBEAT_ACK
        # with the telemetry sequence number.
        response = HeartbeatAck(
            node_id="server",
            server_time=int(datetime.utcnow().timestamp()),
            next_heartbeat_interval=10,
            commands=[],
        )

        payload = response.serialize()
        return Envelope(
            version=PROTOCOL_VERSION,
            msg_type=MessageType.HEARTBEAT_ACK,
            sequence=sequence,
            timestamp=int(datetime.utcnow().timestamp()),
            payload=payload,
        )

    def create_error_response(self, request_envelope: Envelope, code: int, message: str) -> Envelope:
        """Create error response"""
        error = Error(
            code=code,
            message=message,
            details=None,
        )

        payload = error.serialize()
        return Envelope(
            version=PROTOCOL_VERSION,
            msg_type=MessageType.ERROR,
            sequence=request_envelope.sequence,
            timestamp=int(datetime.utcnow().timestamp()),
            payload=payload,
        )


async def start_tcp_server():
    """Start the TCP server"""
    server = SimpleTCPServer(
        host=settings.host,
        port=settings.port + 1  # Use port+1 to avoid conflict with HTTP
    )
    await server.start()


# Global reference to track connected clients for command sending
_connected_clients: Dict[str, asyncio.StreamWriter] = {}


async def send_command_to_node(node_id: str, command: str, params: Dict[str, Any] = None) -> bool:
    """
    Send a command to a connected node via TCP.
    Returns True if command was sent, False if node not connected.
    """
    writer = _connected_clients.get(node_id)
    if not writer:
        logger.warning(f"Node {node_id} not connected via TCP, cannot send command")
        return False
    
    try:
        # Create command payload
        server_command = ServerCommand(
            command=command,
            params=params or {},
        )
        command_payload = server_command.serialize()
        
        # Create envelope with command in heartbeat ACK
        envelope = Envelope(
            version=PROTOCOL_VERSION,
            msg_type=MessageType.HEARTBEAT_ACK,
            sequence=0,
            timestamp=int(datetime.utcnow().timestamp()),
            payload=command_payload,
        )
        
        data = encode_envelope(envelope)
        writer.write(data)
        await writer.drain()
        logger.info(f"Sent command '{command}' to node {node_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send command to node {node_id}: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_tcp_server())