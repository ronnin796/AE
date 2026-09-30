//! Communication protocol definitions and serialization

pub mod messages;

use anyhow::Result;
use rmp_serde::{Deserializer, Serializer};
use serde::{Deserialize, Serialize};
use std::io::{Read, Write};

use messages::*;

/// Protocol version
pub const PROTOCOL_VERSION: u8 = 1;

/// Magic bytes for protocol identification
pub const MAGIC_BYTES: &[u8; 4] = b"AETH";

/// Maximum message size (1 MB)
pub const MAX_MESSAGE_SIZE: usize = 1_048_576;

/// Envelope wrapping all protocol messages
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Envelope {
    /// Protocol version
    pub version: u8,

    /// Message type discriminator
    pub msg_type: MessageType,

    /// Sequence number for ordering/deduplication
    pub sequence: u64,

    /// Timestamp (Unix seconds)
    pub timestamp: u64,

    /// Payload (serialized message)
    pub payload: Vec<u8>,
}

/// Message type identifiers
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[repr(u8)]
pub enum MessageType {
    Register = 1,
    RegisterResponse = 2,
    Heartbeat = 3,
    HeartbeatAck = 4,
    Telemetry = 5,
    InferenceRequest = 6,
    InferenceResult = 7,
    Error = 255,
}

impl MessageType {
    /// Convert from u8
    pub fn from_u8(value: u8) -> Option<Self> {
        match value {
            1 => Some(MessageType::Register),
            2 => Some(MessageType::RegisterResponse),
            3 => Some(MessageType::Heartbeat),
            4 => Some(MessageType::HeartbeatAck),
            5 => Some(MessageType::Telemetry),
            6 => Some(MessageType::InferenceRequest),
            7 => Some(MessageType::InferenceResult),
            255 => Some(MessageType::Error),
            _ => None,
        }
    }
}

/// Serialize a message to MessagePack bytes
pub fn serialize<T: Serialize>(msg: &T) -> Result<Vec<u8>> {
    let mut buf = Vec::new();
    msg.serialize(&mut Serializer::new(&mut buf))?;
    Ok(buf)
}

/// Deserialize MessagePack bytes to a message
pub fn deserialize<T: for<'de> Deserialize<'de>>(data: &[u8]) -> Result<T> {
    let mut deserializer = Deserializer::new(data);
    Ok(T::deserialize(&mut deserializer)?)
}

/// Encode an envelope for network transmission
pub fn encode_envelope(envelope: &Envelope) -> Result<Vec<u8>> {
    let payload = serialize(envelope)?;

    // Check size limit
    if payload.len() > MAX_MESSAGE_SIZE {
        anyhow::bail!("Message exceeds maximum size: {} > {}", payload.len(), MAX_MESSAGE_SIZE);
    }

    // Prepend magic bytes and length
    let mut buf = Vec::with_capacity(4 + 4 + payload.len());
    buf.extend_from_slice(MAGIC_BYTES);
    buf.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    buf.extend_from_slice(&payload);

    Ok(buf)
}

/// Decode an envelope from network bytes
pub fn decode_envelope(data: &[u8]) -> Result<Envelope> {
    if data.len() < 8 {
        anyhow::bail!("Message too short for header");
    }

    // Verify magic bytes
    if &data[0..4] != MAGIC_BYTES {
        anyhow::bail!("Invalid magic bytes");
    }

    // Read payload length
    let len = u32::from_be_bytes([data[4], data[5], data[6], data[7]]) as usize;

    if data.len() < 8 + len {
        anyhow::bail!("Message truncated: expected {} bytes, got {}", len, data.len() - 8);
    }

    let payload = &data[8..8 + len];
    deserialize(payload)
}

/// Read a complete message from a stream
pub fn read_message<R: Read>(reader: &mut R) -> Result<Envelope> {
    // Read header (magic + length)
    let mut header = [0u8; 8];
    reader.read_exact(&mut header)?;

    // Verify magic
    if &header[0..4] != MAGIC_BYTES {
        anyhow::bail!("Invalid magic bytes");
    }

    let len = u32::from_be_bytes([header[4], header[5], header[6], header[7]]) as usize;

    if len > MAX_MESSAGE_SIZE {
        anyhow::bail!("Message exceeds maximum size");
    }

    // Read payload
    let mut payload = vec![0u8; len];
    reader.read_exact(&mut payload)?;

    deserialize(&payload)
}

/// Write a message to a stream
pub fn write_message<W: Write>(writer: &mut W, envelope: &Envelope) -> Result<()> {
    let data = encode_envelope(envelope)?;
    writer.write_all(&data)?;
    writer.flush()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use messages::*;

    #[test]
    fn test_envelope_serialization() {
        let envelope = Envelope {
            version: PROTOCOL_VERSION,
            msg_type: MessageType::Register,
            sequence: 1,
            timestamp: 1234567890,
            payload: vec![1, 2, 3, 4],
        };

        let encoded = encode_envelope(&envelope).unwrap();
        let decoded = decode_envelope(&encoded).unwrap();

        assert_eq!(decoded.version, envelope.version);
        assert_eq!(decoded.msg_type, envelope.msg_type);
        assert_eq!(decoded.sequence, envelope.sequence);
        assert_eq!(decoded.timestamp, envelope.timestamp);
        assert_eq!(decoded.payload, envelope.payload);
    }

    #[test]
    fn test_message_type_conversion() {
        assert_eq!(MessageType::from_u8(1), Some(MessageType::Register));
        assert_eq!(MessageType::from_u8(5), Some(MessageType::Telemetry));
        assert_eq!(MessageType::from_u8(255), Some(MessageType::Error));
        assert_eq!(MessageType::from_u8(99), None);
    }

    #[test]
    fn test_register_message() {
        let register = Register {
            node_id: "test-node".to_string(),
            hostname: "test-host".to_string(),
            os: "Linux".to_string(),
            cpu_cores: 4,
            total_memory: 8_000_000_000,
            version: "0.1.0".to_string(),
            capabilities: vec!["telemetry".to_string(), "inference".to_string()],
        };

        let payload = serialize(&register).unwrap();
        let decoded: Register = deserialize(&payload).unwrap();

        assert_eq!(decoded.node_id, register.node_id);
        assert_eq!(decoded.capabilities, register.capabilities);
    }
}