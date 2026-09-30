//! Protocol message definitions

use serde::{Deserialize, Serialize};

/// Node registration request (edge -> server)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Register {
    pub node_id: String,
    pub hostname: String,
    pub os: String,
    pub os_version: String,
    pub kernel_version: String,
    pub cpu_brand: String,
    pub cpu_cores: usize,
    pub total_memory: u64,
    pub version: String,
    pub arch: String,
    pub capabilities: Vec<String>,
}

/// Node registration response (server -> edge)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegisterResponse {
    pub success: bool,
    pub node_id: String,
    pub assigned_id: Option<String>, // Server-assigned ID if different
    pub message: String,
    pub server_time: u64,
    pub config: Option<ServerConfig>,
}

/// Server configuration pushed to node on registration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub heartbeat_interval: u64,
    pub telemetry_interval: u64,
    pub model_update_url: Option<String>,
}

/// Heartbeat message (edge -> server)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Heartbeat {
    pub node_id: String,
    pub timestamp: u64,
    pub status: NodeStatus,
    pub uptime: u64,
}

/// Heartbeat acknowledgment (server -> edge)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeartbeatAck {
    pub node_id: String,
    pub server_time: u64,
    pub next_heartbeat_interval: Option<u64>,
    pub commands: Vec<ServerCommand>,
}

/// Node status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[repr(u8)]
pub enum NodeStatus {
    Online = 1,
    Degraded = 2,
    Offline = 3,
    Maintenance = 4,
}

/// Server commands sent to node via heartbeat ACK
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ServerCommand {
    UpdateTelemetryInterval { interval: u64 },
    UpdateHeartbeatInterval { interval: u64 },
    FetchModel { model_id: String, url: String },
    RunInference { model_id: String, input: Vec<f32> },
    Reboot,
    Shutdown,
}

/// Telemetry message (edge -> server)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Telemetry {
    pub node_id: String,
    pub timestamp: u64,
    pub cpu_usage: Option<f64>,
    pub cpu_per_core: Option<Vec<f64>>,
    pub memory_usage: Option<f64>,
    pub memory_total: Option<u64>,
    pub memory_available: Option<u64>,
    pub memory_used: Option<u64>,
    pub temperature: Option<f64>,
    pub temperatures: Option<Vec<f64>>,
    pub uptime: Option<u64>,
    pub load_1: Option<f64>,
    pub load_5: Option<f64>,
    pub load_15: Option<f64>,
    pub processes_running: Option<u32>,
    pub processes_total: Option<u32>,
}

/// Inference request (server -> edge or edge internal)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceRequest {
    pub request_id: String,
    pub model_id: String,
    pub input: Vec<f32>,
    pub input_shape: Vec<usize>,
}

/// Inference result (edge -> server)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceResult {
    pub request_id: String,
    pub node_id: String,
    pub model_id: String,
    pub timestamp: u64,
    pub output: Vec<f32>,
    pub output_shape: Vec<usize>,
    pub inference_time_ms: f64,
    pub success: bool,
    pub error: Option<String>,
}

/// Error message
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Error {
    pub code: u32,
    pub message: String,
    pub details: Option<String>,
}

/// Convert from our telemetry crate's Telemetry to protocol Telemetry
impl From<crate::telemetry::Telemetry> for Telemetry {
    fn from(t: crate::telemetry::Telemetry) -> Self {
        Self {
            node_id: t.node_id,
            timestamp: t.timestamp,
            cpu_usage: t.cpu_usage,
            cpu_per_core: t.cpu_per_core,
            memory_usage: t.memory_usage,
            memory_total: t.memory_total,
            memory_available: t.memory_available,
            memory_used: t.memory_used,
            temperature: t.temperature,
            temperatures: t.temperatures,
            uptime: t.uptime,
            load_1: t.load_1,
            load_5: t.load_5,
            load_15: t.load_15,
            processes_running: t.processes_running,
            processes_total: t.processes_total,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_register_serialization() {
        let reg = Register {
            node_id: "test-node".to_string(),
            hostname: "test-host".to_string(),
            os: "Linux".to_string(),
            os_version: "6.1".to_string(),
            kernel_version: "6.1.0".to_string(),
            cpu_brand: "Intel i7".to_string(),
            cpu_cores: 8,
            total_memory: 16_000_000_000,
            version: "0.1.0".to_string(),
            arch: "x86_64".to_string(),
            capabilities: vec!["telemetry".to_string(), "inference".to_string()],
        };

        let encoded = rmp_serde::to_vec(&reg).unwrap();
        let decoded: Register = rmp_serde::from_slice(&encoded).unwrap();

        assert_eq!(decoded.node_id, reg.node_id);
        assert_eq!(decoded.cpu_cores, reg.cpu_cores);
    }

    #[test]
    fn test_heartbeat_serialization() {
        let hb = Heartbeat {
            node_id: "test-node".to_string(),
            timestamp: 1234567890,
            status: NodeStatus::Online,
            uptime: 3600,
        };

        let encoded = rmp_serde::to_vec(&hb).unwrap();
        let decoded: Heartbeat = rmp_serde::from_slice(&encoded).unwrap();

        assert_eq!(decoded.node_id, hb.node_id);
        assert_eq!(decoded.status, hb.status);
    }
}