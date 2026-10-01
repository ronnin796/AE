//! Dump the exact bytes the Rust client sends for a Register envelope,
//! so we can compare against what the Python server expects.

use aetheredge_edge::protocol::{encode_envelope, serialize, Envelope, MessageType};
use aetheredge_edge::protocol::messages::Register;

fn main() {
    let register = Register {
        node_id: "node-a".to_string(),
        hostname: "test-host".to_string(),
        os: "Linux".to_string(),
        os_version: "6.1".to_string(),
        kernel_version: "6.1.0".to_string(),
        cpu_brand: "Intel i7".to_string(),
        cpu_cores: 8,
        total_memory: 16_000_000_000,
        version: "0.1.0".to_string(),
        arch: "x86_64".to_string(),
        capabilities: vec!["telemetry".to_string(), "heartbeat".to_string(), "inference".to_string()],
    };

    let payload = serialize(&register).unwrap();
    println!("Register payload ({} bytes): {:02x?}", payload.len(), payload);

    let envelope = Envelope {
        version: 1,
        msg_type: MessageType::Register,
        sequence: 1,
        timestamp: 1234567890,
        payload,
    };

    let data = encode_envelope(&envelope).unwrap();
    println!("\nFull wire message ({} bytes): {:02x?}", data.len(), data);

    // Show the envelope's msg_type field specifically
    let env_payload = &data[8..];
    println!("\nEnvelope payload ({} bytes): {:02x?}", env_payload.len(), env_payload);
}