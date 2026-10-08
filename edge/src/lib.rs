//! AetherEdge Edge Daemon - Library crate
//!
//! This crate provides the core functionality for the AetherEdge edge daemon,
//! including telemetry collection, network communication, and protocol handling.

pub mod config;
pub mod logging;
pub mod node;
pub mod networking;
pub mod protocol;
pub mod telemetry;
pub mod inference;

// Re-export key types for convenience
pub use config::Config;
pub use node::NodeIdentity;
pub use networking::NetworkClient;
pub use protocol::{Envelope, MessageType, decode_envelope, encode_envelope, read_message, write_message};
pub use telemetry::{Telemetry, TelemetryCollector, TelemetryConfig};
pub use inference::InferenceEngine;