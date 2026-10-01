//! Node identity and metadata

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use sysinfo::System;
use uuid::Uuid;

/// Unique node identity
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct NodeIdentity {
    /// Unique node identifier (UUID v4)
    pub node_id: String,

    /// Human-readable hostname
    pub hostname: String,

    /// Operating system name
    pub os: String,

    /// OS version
    pub os_version: String,

    /// Kernel version
    pub kernel_version: String,

    /// CPU brand/model
    pub cpu_brand: String,

    /// Number of CPU cores
    pub cpu_cores: usize,

    /// Total system memory in bytes
    pub total_memory: u64,

    /// AetherEdge software version
    pub version: String,

    /// Architecture
    pub arch: String,
}

/// Extended node metadata for registration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeMetadata {
    /// Base identity
    pub identity: NodeIdentity,

    /// Additional system information
    pub cpu_info: HashMap<String, String>,
    pub memory_info: HashMap<String, String>,
    pub disk_info: HashMap<String, String>,
    pub network_info: HashMap<String, String>,

    /// Capabilities
    pub capabilities: Vec<String>,

    /// Tags for grouping/filtering
    pub tags: HashMap<String, String>,
}

impl NodeIdentity {
    /// Build node identity from system information
    pub fn build(node_id_override: Option<String>, hostname_override: Option<String>) -> Result<Self> {
        let mut sys = System::new_all();

        // Refresh CPU and memory info
        sys.refresh_all();
        sys.refresh_memory();

        // Generate or use provided node ID
        let node_id = node_id_override.unwrap_or_else(|| Uuid::new_v4().to_string());

        // Get hostname
        let hostname = hostname_override.unwrap_or_else(|| {
            System::host_name().unwrap_or_else(|| "unknown".to_string())
        });

        // OS information
        let os = System::name().unwrap_or_else(|| "Linux".to_string());
        let os_version = System::os_version().unwrap_or_else(|| "unknown".to_string());
        let kernel_version = System::kernel_version().unwrap_or_else(|| "unknown".to_string());

        // CPU information
        let cpu_brand = sys.cpus().first()
            .map(|c| c.brand().to_string())
            .unwrap_or_else(|| "Unknown CPU".to_string());
        let cpu_cores = sys.cpus().len();

        // Memory
        let total_memory = sys.total_memory();

        // Version
        let version = env!("CARGO_PKG_VERSION").to_string();

        // Architecture
        let arch = std::env::consts::ARCH.to_string();

        Ok(Self {
            node_id,
            hostname,
            os,
            os_version,
            kernel_version,
            cpu_brand,
            cpu_cores,
            total_memory,
            version,
            arch,
        })
    }

    /// Create a minimal identity for testing
    pub fn new_test(node_id: &str) -> Self {
        Self {
            node_id: node_id.to_string(),
            hostname: "test-host".to_string(),
            os: "Linux".to_string(),
            os_version: "test".to_string(),
            kernel_version: "test".to_string(),
            cpu_brand: "Test CPU".to_string(),
            cpu_cores: 4,
            total_memory: 8_000_000_000,
            version: "test".to_string(),
            arch: "x86_64".to_string(),
        }
    }
}

impl NodeMetadata {
    /// Create metadata from identity with extended system info
    /// Note: Disk and network info collected via /proc to avoid sysinfo version issues
    pub fn from_identity(identity: NodeIdentity) -> Result<Self> {
        let mut sys = System::new_all();
        sys.refresh_all();
        sys.refresh_memory();

        // CPU info
        let mut cpu_info = HashMap::new();
        cpu_info.insert("vendor_id".to_string(), sys.cpus().first().map(|c| c.vendor_id().to_string()).unwrap_or_default());
        cpu_info.insert("frequency".to_string(), sys.cpus().first().map(|c| c.frequency().to_string()).unwrap_or_default());
        cpu_info.insert("cores".to_string(), identity.cpu_cores.to_string());

        // Memory info
        let mut memory_info = HashMap::new();
        memory_info.insert("total".to_string(), identity.total_memory.to_string());
        memory_info.insert("available".to_string(), sys.available_memory().to_string());

        // Disk info (read from /proc/mounts or leave empty for Part I)
        let disk_info = Self::collect_disk_info()?;

        // Network info (read from /proc/net/dev)
        let network_info = Self::collect_network_info()?;

        // Capabilities
        let capabilities = vec![
            "telemetry".to_string(),
            "heartbeat".to_string(),
            "inference".to_string(),
        ];

        Ok(Self {
            identity,
            cpu_info,
            memory_info,
            disk_info,
            network_info,
            capabilities,
            tags: HashMap::new(),
        })
    }

    /// Collect disk info from /proc/mounts
    fn collect_disk_info() -> Result<HashMap<String, String>> {
        let mut disk_info = HashMap::new();

        // Read /proc/mounts as fallback
        if let Ok(content) = std::fs::read_to_string("/proc/mounts") {
            for line in content.lines() {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.len() >= 2 {
                    let mount_point = parts[1];
                    if mount_point.starts_with("/dev/") {
                        if let Ok(stat) = std::fs::metadata(mount_point) {
                            _ = stat;
                            // Use statvfs for actual disk info
                            if let Ok(_statvfs) = std::fs::read_to_string("/proc/mounts") {
                                // We just record mount points for Part I
                                disk_info.insert(mount_point.to_string(), "mounted".to_string());
                            }
                        }
                    }
                }
            }
        }

        Ok(disk_info)
    }

    /// Collect network interface info from /proc/net/dev
    fn collect_network_info() -> Result<HashMap<String, String>> {
        let mut network_info = HashMap::new();

        if let Ok(content) = std::fs::read_to_string("/proc/net/dev") {
            for line in content.lines().skip(2) {
                if let Some(idx) = line.find(':') {
                    let interface = line[..idx].trim();
                    let stats = line[idx + 1..].split_whitespace().collect::<Vec<_>>();
                    if interface.is_empty() || stats.len() < 2 {
                        continue;
                    }
                    // Skip loopback
                    if interface == "lo" {
                        continue;
                    }
                    network_info.insert(
                        interface.to_string(),
                        format!("rx_bytes: {} tx_bytes: {}", stats[0], stats[8]),
                    );
                }
            }
        }

        Ok(network_info)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_node_identity_build() {
        let identity = NodeIdentity::build(None, None).expect("Failed to build node identity");
        assert!(!identity.node_id.is_empty());
        assert!(!identity.hostname.is_empty());
        assert_eq!(identity.version, env!("CARGO_PKG_VERSION"));
    }

    #[test]
    fn test_node_identity_with_override() {
        let identity = NodeIdentity::build(Some("custom-id".to_string()), Some("custom-host".to_string()))
            .expect("Failed to build node identity");
        assert_eq!(identity.node_id, "custom-id");
        assert_eq!(identity.hostname, "custom-host");
    }

    #[test]
    fn test_node_metadata_from_identity() {
        let identity = NodeIdentity::new_test("test-node");
        let metadata = NodeMetadata::from_identity(identity).expect("Failed to create metadata");
        assert!(!metadata.capabilities.is_empty());
        assert!(metadata.capabilities.contains(&"telemetry".to_string()));
    }
}