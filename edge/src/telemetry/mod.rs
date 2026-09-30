//! Telemetry collection from Linux /proc and /sys

pub mod cpu;
pub mod memory;
pub mod temperature;
pub mod system;

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::node::NodeIdentity;
use cpu::CpuCollector;
use memory::MemoryCollector;
use temperature::TemperatureCollector;
use system::SystemCollector;

/// Complete telemetry snapshot from an edge node
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Telemetry {
    /// Node ID this telemetry belongs to
    pub node_id: String,

    /// Unix timestamp (seconds since epoch)
    pub timestamp: u64,

    /// CPU usage percentage (0.0 - 100.0 * core_count)
    pub cpu_usage: Option<f64>,

    /// Per-core CPU usage percentages
    pub cpu_per_core: Option<Vec<f64>>,

    /// Memory usage percentage (0.0 - 100.0)
    pub memory_usage: Option<f64>,

    /// Total memory in bytes
    pub memory_total: Option<u64>,

    /// Available memory in bytes
    pub memory_available: Option<u64>,

    /// Used memory in bytes
    pub memory_used: Option<u64>,

    /// Temperature in Celsius (first available sensor)
    pub temperature: Option<f64>,

    /// All temperature sensors
    pub temperatures: Option<Vec<f64>>,

    /// System uptime in seconds
    pub uptime: Option<u64>,

    /// Load averages (1, 5, 15 min)
    pub load_1: Option<f64>,
    pub load_5: Option<f64>,
    pub load_15: Option<f64>,

    /// Number of running processes
    pub processes_running: Option<u32>,

    /// Total number of processes
    pub processes_total: Option<u32>,
}

impl Telemetry {
    /// Create a new empty telemetry with node_id and timestamp
    pub fn new(node_id: String) -> Self {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        Self {
            node_id,
            timestamp,
            cpu_usage: None,
            cpu_per_core: None,
            memory_usage: None,
            memory_total: None,
            memory_available: None,
            memory_used: None,
            temperature: None,
            temperatures: None,
            uptime: None,
            load_1: None,
            load_5: None,
            load_15: None,
            processes_running: None,
            processes_total: None,
        }
    }
}

/// Configuration for telemetry collection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryConfig {
    pub collect_cpu: bool,
    pub collect_memory: bool,
    pub collect_temperature: bool,
    pub collect_uptime: bool,
    pub collect_load: bool,
}

impl Default for TelemetryConfig {
    fn default() -> Self {
        Self {
            collect_cpu: true,
            collect_memory: true,
            collect_temperature: true,
            collect_uptime: true,
            collect_load: true,
        }
    }
}

/// Main telemetry collector coordinating all sub-collectors
pub struct TelemetryCollector {
    config: TelemetryConfig,
    cpu_collector: CpuCollector,
    memory_collector: MemoryCollector,
    temperature_collector: TemperatureCollector,
    system_collector: SystemCollector,
}

impl TelemetryCollector {
    /// Create a new telemetry collector with the given configuration
    pub fn new(config: TelemetryConfig) -> Self {
        Self {
            config,
            cpu_collector: CpuCollector::new(),
            memory_collector: MemoryCollector::new(),
            temperature_collector: TemperatureCollector::new(),
            system_collector: SystemCollector::new(),
        }
    }

    /// Collect all enabled telemetry metrics
    pub async fn collect(&mut self, identity: &NodeIdentity) -> Result<Telemetry> {
        let mut telemetry = Telemetry::new(identity.node_id.clone());

        // Collect CPU metrics
        if self.config.collect_cpu {
            if let Ok(cpu_data) = self.cpu_collector.collect().await {
                telemetry.cpu_usage = Some(cpu_data.total_usage);
                telemetry.cpu_per_core = Some(cpu_data.per_core);
            }
        }

        // Collect memory metrics
        if self.config.collect_memory {
            if let Ok(mem_data) = self.memory_collector.collect().await {
                telemetry.memory_usage = Some(mem_data.usage_percent);
                telemetry.memory_total = Some(mem_data.total);
                telemetry.memory_available = Some(mem_data.available);
                telemetry.memory_used = Some(mem_data.used);
            }
        }

        // Collect temperature metrics
        if self.config.collect_temperature {
            if let Ok(temp_data) = self.temperature_collector.collect().await {
                telemetry.temperature = temp_data.first().copied();
                telemetry.temperatures = Some(temp_data);
            }
        }

        // Collect system metrics (uptime, load)
        if self.config.collect_uptime || self.config.collect_load {
            if let Ok(sys_data) = self.system_collector.collect().await {
                if self.config.collect_uptime {
                    telemetry.uptime = Some(sys_data.uptime);
                }
                if self.config.collect_load {
                    telemetry.load_1 = Some(sys_data.load_1);
                    telemetry.load_5 = Some(sys_data.load_5);
                    telemetry.load_15 = Some(sys_data.load_15);
                }
            }
        }

        Ok(telemetry)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_telemetry_new() {
        let tel = Telemetry::new("test-node".to_string());
        assert_eq!(tel.node_id, "test-node");
        assert!(tel.timestamp > 0);
    }

    #[test]
    fn test_telemetry_config_default() {
        let config = TelemetryConfig::default();
        assert!(config.collect_cpu);
        assert!(config.collect_memory);
    }
}