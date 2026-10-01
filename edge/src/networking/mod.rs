//! Networking layer for edge-to-server communication

use anyhow::{Context, Result};
use std::net::SocketAddr;
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::sync::Mutex;
use tokio::time::timeout;
use tracing::{debug, info};

use crate::node::NodeIdentity;
use crate::protocol::{encode_envelope, Envelope, MessageType};
use crate::protocol::messages::{Heartbeat, HeartbeatAck, Register, RegisterResponse};

/// Network client for communicating with the server
pub struct NetworkClient {
    server_addr: SocketAddr,
    node_identity: NodeIdentity,
    stream: Arc<Mutex<Option<TcpStream>>>,
    sequence: Arc<Mutex<u64>>,
    connect_timeout: Duration,
    request_timeout: Duration,
}

impl NetworkClient {
    /// Create a new network client
    pub fn new(server_addr: SocketAddr, node_identity: NodeIdentity) -> Self {
        Self {
            server_addr,
            node_identity,
            stream: Arc::new(Mutex::new(None)),
            sequence: Arc::new(Mutex::new(0)),
            connect_timeout: Duration::from_secs(10),
            request_timeout: Duration::from_secs(30),
        }
    }

    /// Set connection timeout
    pub fn with_connect_timeout(mut self, timeout: Duration) -> Self {
        self.connect_timeout = timeout;
        self
    }

    /// Set request timeout
    pub fn with_request_timeout(mut self, timeout: Duration) -> Self {
        self.request_timeout = timeout;
        self
    }

    /// Get next sequence number
    async fn next_sequence(&self) -> u64 {
        let mut seq = self.sequence.lock().await;
        *seq += 1;
        *seq
    }

    /// Connect to the server
    pub async fn connect(&self) -> Result<()> {
        let mut stream_guard = self.stream.lock().await;

        if stream_guard.is_some() {
            return Ok(()); // Already connected
        }

        info!("Connecting to server at {}", self.server_addr);

        let stream = timeout(self.connect_timeout, TcpStream::connect(self.server_addr))
            .await
            .context("Connection timeout")?
            .context("Failed to connect to server")?;

        stream.set_nodelay(true).context("Failed to set TCP_NODELAY")?;

        *stream_guard = Some(stream);
        info!("Connected to server");

        Ok(())
    }

    /// Ensure connection is active, reconnect if needed
    async fn ensure_connected(&self) -> Result<()> {
        let stream_guard = self.stream.lock().await;

        if stream_guard.is_none() {
            drop(stream_guard);
            self.connect().await?;
        }

        Ok(())
    }

    /// Send an envelope and wait for response
    async fn send_request(&self, envelope: Envelope) -> Result<Envelope> {
        self.ensure_connected().await?;

        let mut stream_guard = self.stream.lock().await;
        let stream = stream_guard.as_mut()
            .context("Stream not available after connect")?;

        // Send request
        let data = encode_envelope(&envelope)?;
        debug!("Sending message type {:?}, {} bytes", envelope.msg_type, data.len());
        debug!("First 10 bytes: {:?}", &data[..std::cmp::min(10, data.len())]);

        timeout(self.request_timeout, stream.write_all(&data))
            .await
            .context("Write timeout")?
            .context("Failed to write to stream")?;

        // Read response
        let mut header = [0u8; 8];
        timeout(self.request_timeout, stream.read_exact(&mut header))
            .await
            .context("Read header timeout")?
            .context("Failed to read header")?;

        // Verify magic bytes
        if &header[0..4] != crate::protocol::MAGIC_BYTES {
            debug!("Received header magic bytes: {:?}, expected: {:?}",
                   &header[0..4], crate::protocol::MAGIC_BYTES);
            anyhow::bail!("Invalid magic bytes in response");
        }

        let len = u32::from_be_bytes([header[4], header[5], header[6], header[7]]) as usize;

        if len > crate::protocol::MAX_MESSAGE_SIZE {
            anyhow::bail!("Response exceeds maximum size");
        }

        let mut payload = vec![0u8; len];
        timeout(self.request_timeout, stream.read_exact(&mut payload))
            .await
            .context("Read payload timeout")?
            .context("Failed to read payload")?;

        let response: Envelope = crate::protocol::deserialize(&payload)?;
        debug!("Received response type {:?}", response.msg_type);

        Ok(response)
    }

    /// Register node with server
    pub async fn register(&mut self, identity: &NodeIdentity) -> Result<RegisterResponse> {
        let sequence = self.next_sequence().await;
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let register = Register {
            node_id: identity.node_id.clone(),
            hostname: identity.hostname.clone(),
            os: identity.os.clone(),
            os_version: identity.os_version.clone(),
            kernel_version: identity.kernel_version.clone(),
            cpu_brand: identity.cpu_brand.clone(),
            cpu_cores: identity.cpu_cores,
            total_memory: identity.total_memory,
            version: identity.version.clone(),
            arch: identity.arch.clone(),
            capabilities: vec![
                "telemetry".to_string(),
                "heartbeat".to_string(),
                "inference".to_string(),
            ],
        };

        let payload = crate::protocol::serialize(&register)?;
        let envelope = Envelope {
            version: crate::protocol::PROTOCOL_VERSION,
            msg_type: MessageType::Register,
            sequence,
            timestamp,
            payload,
        };

        let response = self.send_request(envelope).await?;

        if response.msg_type != MessageType::RegisterResponse {
            anyhow::bail!("Expected RegisterResponse, got {:?}", response.msg_type);
        }

        let register_response: RegisterResponse = crate::protocol::deserialize(&response.payload)?;

        if !register_response.success {
            anyhow::bail!("Registration failed: {}", register_response.message);
        }

        info!("Registration successful: {}", register_response.message);
        Ok(register_response)
    }

    /// Send heartbeat
    pub async fn heartbeat(&self, identity: &NodeIdentity) -> Result<HeartbeatAck> {
        let sequence = self.next_sequence().await;
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let heartbeat = Heartbeat {
            node_id: identity.node_id.clone(),
            timestamp,
            status: crate::protocol::messages::NodeStatus::Online,
            uptime: timestamp, // Simplified
        };

        let payload = crate::protocol::serialize(&heartbeat)?;
        let envelope = Envelope {
            version: crate::protocol::PROTOCOL_VERSION,
            msg_type: MessageType::Heartbeat,
            sequence,
            timestamp,
            payload,
        };

        let response = self.send_request(envelope).await?;

        if response.msg_type != MessageType::HeartbeatAck {
            anyhow::bail!("Expected HeartbeatAck, got {:?}", response.msg_type);
        }

        let ack: HeartbeatAck = crate::protocol::deserialize(&response.payload)?;
        Ok(ack)
    }

    /// Send telemetry data
    pub async fn send_telemetry(&self, telemetry: &crate::telemetry::Telemetry) -> Result<()> {
        let sequence = self.next_sequence().await;
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let proto_telemetry: crate::protocol::messages::Telemetry = telemetry.clone().into();
        let payload = crate::protocol::serialize(&proto_telemetry)?;
        let envelope = Envelope {
            version: crate::protocol::PROTOCOL_VERSION,
            msg_type: MessageType::Telemetry,
            sequence,
            timestamp,
            payload,
        };

        let response = self.send_request(envelope).await?;

        if response.msg_type == MessageType::Error {
            let err: crate::protocol::messages::Error = crate::protocol::deserialize(&response.payload)?;
            anyhow::bail!("Server error: {}", err.message);
        }

        Ok(())
    }

    /// Disconnect from server
    pub async fn disconnect(&self) {
        let mut stream_guard = self.stream.lock().await;
        if let Some(mut stream) = stream_guard.take() {
            let _ = stream.shutdown().await;
            info!("Disconnected from server");
        }
    }
}

impl Clone for NetworkClient {
    fn clone(&self) -> Self {
        Self {
            server_addr: self.server_addr,
            node_identity: self.node_identity.clone(),
            stream: self.stream.clone(),
            sequence: self.sequence.clone(),
            connect_timeout: self.connect_timeout,
            request_timeout: self.request_timeout,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_network_client_creation() {
        let addr: SocketAddr = "127.0.0.1:8080".parse().unwrap();
        let identity = crate::node::NodeIdentity::new_test("test-node");
        let client = NetworkClient::new(addr, identity);
        assert_eq!(client.server_addr, addr);
    }
}