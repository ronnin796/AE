//! Configuration management for the edge daemon

use std::path::Path;
use anyhow::{Context, Result};
use config::{Config as ConfigLib, File, FileFormat, Environment};
use serde::{Deserialize, Serialize};

/// Top-level configuration
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Config {
    pub node: NodeConfig,
    pub server: ServerConfig,
    pub network: NetworkConfig,
    pub telemetry: TelemetryConfig,
    pub inference: InferenceConfig,
}

/// Node-specific configuration
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct NodeConfig {
    /// Node ID (auto-generated if not provided)
    pub node_id: Option<String>,

    /// Hostname override (auto-detected if empty)
    pub hostname: Option<String>,
}

/// Server connection configuration
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ServerConfig {
    /// Server address (host:port)
    pub address: String,

    /// Reconnection interval in seconds
    pub reconnect_interval: u64,
}

/// Network communication configuration
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct NetworkConfig {
    /// Heartbeat interval in seconds
    pub heartbeat_interval: u64,

    /// Connection timeout in seconds
    pub connect_timeout: u64,

    /// Request timeout in seconds
    pub request_timeout: u64,
}

/// Telemetry collection configuration
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct TelemetryConfig {
    /// Collection interval in seconds
    pub interval: u64,

    /// Enable CPU collection
    pub collect_cpu: bool,

    /// Enable memory collection
    pub collect_memory: bool,

    /// Enable temperature collection
    pub collect_temperature: bool,

    /// Enable uptime collection
    pub collect_uptime: bool,

    /// Enable load average collection
    pub collect_load: bool,
}

/// Inference configuration
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct InferenceConfig {
    /// Path to ONNX model file
    pub model_path: Option<String>,

    /// Inference interval in seconds (for periodic inference)
    pub interval: u64,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            node: NodeConfig::default(),
            server: ServerConfig::default(),
            network: NetworkConfig::default(),
            telemetry: TelemetryConfig::default(),
            inference: InferenceConfig::default(),
        }
    }
}

impl Default for NodeConfig {
    fn default() -> Self {
        Self {
            node_id: None,
            hostname: None,
        }
    }
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            address: "127.0.0.1:8080".to_string(),
            reconnect_interval: 5,
        }
    }
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            heartbeat_interval: 10,
            connect_timeout: 10,
            request_timeout: 30,
        }
    }
}

impl Default for TelemetryConfig {
    fn default() -> Self {
        Self {
            interval: 2,
            collect_cpu: true,
            collect_memory: true,
            collect_temperature: true,
            collect_uptime: true,
            collect_load: true,
        }
    }
}

impl Default for InferenceConfig {
    fn default() -> Self {
        Self {
            model_path: None,
            interval: 30,
        }
    }
}

impl Config {
    /// Load configuration from file and environment
    pub fn load(config_path: Option<&Path>) -> Result<Self> {
        let mut builder = ConfigLib::builder()
            .set_default("node.node_id", "")?
            .set_default("node.hostname", None::<String>)?
            .set_default("server.address", "127.0.0.1:8080")?
            .set_default("server.reconnect_interval", 5)?
            .set_default("network.heartbeat_interval", 10)?
            .set_default("network.connect_timeout", 10)?
            .set_default("network.request_timeout", 30)?
            .set_default("telemetry.interval", 2)?
            .set_default("telemetry.collect_cpu", true)?
            .set_default("telemetry.collect_memory", true)?
            .set_default("telemetry.collect_temperature", true)?
            .set_default("telemetry.collect_uptime", true)?
            .set_default("telemetry.collect_load", true)?
            .set_default("inference.model_path", "")?
            .set_default("inference.interval", 30)?;

        // Load from file if provided
        if let Some(path) = config_path {
            if path.exists() {
                builder = builder.add_source(File::from(path).format(FileFormat::Toml));
            }
        } else {
            // Try default locations
            for path in [
                "config.toml",
                "/etc/aetheredge/edge.toml",
                &format!("{}/.config/aetheredge/edge.toml", std::env::var("HOME").unwrap_or_default()),
            ] {
                if Path::new(path).exists() {
                    let path_buf = std::path::PathBuf::from(path);
                    builder = builder.add_source(File::from(path_buf).format(FileFormat::Toml));
                    break;
                }
            }
        }

        // Load from environment (AETHEREDGE_* prefix)
        builder = builder.add_source(Environment::with_prefix("AETHEREDGE").separator("_"));

        let config = builder.build()?;
        config.try_deserialize().context("Failed to deserialize configuration")
    }
}