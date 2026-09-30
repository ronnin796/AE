//! System telemetry collector (uptime, load average, processes)

use anyhow::{Context, Result};
use std::fs;

/// Collected system data
#[derive(Debug, Clone)]
pub struct SystemData {
    /// System uptime in seconds
    pub uptime: u64,

    /// Load average (1 minute)
    pub load_1: f64,

    /// Load average (5 minutes)
    pub load_5: f64,

    /// Load average (15 minutes)
    pub load_15: f64,

    /// Number of running processes
    pub processes_running: u32,

    /// Total number of processes
    pub processes_total: u32,
}

/// System collector reading from /proc/uptime, /proc/loadavg
pub struct SystemCollector;

impl SystemCollector {
    /// Create a new system collector
    pub fn new() -> Self {
        Self
    }

    /// Collect system metrics
    pub async fn collect(&self) -> Result<SystemData> {
        // Read uptime
        let uptime_content = fs::read_to_string("/proc/uptime")
            .context("Failed to read /proc/uptime")?;
        let uptime_str = uptime_content.split_whitespace().next()
            .context("Invalid /proc/uptime format")?;
        let uptime_seconds: f64 = uptime_str.parse()
            .context("Failed to parse uptime")?;
        let uptime = uptime_seconds as u64;

        // Read load average
        let loadavg_content = fs::read_to_string("/proc/loadavg")
            .context("Failed to read /proc/loadavg")?;
        let load_parts: Vec<&str> = loadavg_content.split_whitespace().collect();

        let load_1 = load_parts.get(0)
            .and_then(|s| s.parse().ok())
            .unwrap_or(0.0);
        let load_5 = load_parts.get(1)
            .and_then(|s| s.parse().ok())
            .unwrap_or(0.0);
        let load_15 = load_parts.get(2)
            .and_then(|s| s.parse().ok())
            .unwrap_or(0.0);

        // Parse processes running/total from 4th field (e.g., "2/345")
        let (processes_running, processes_total) = load_parts.get(3)
            .and_then(|s| {
                let parts: Vec<&str> = s.split('/').collect();
                if parts.len() == 2 {
                    Some((
                        parts[0].parse().unwrap_or(0),
                        parts[1].parse().unwrap_or(0),
                    ))
                } else {
                    None
                }
            })
            .unwrap_or((0, 0));

        Ok(SystemData {
            uptime,
            load_1,
            load_5,
            load_15,
            processes_running,
            processes_total,
        })
    }
}

impl Default for SystemCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_system_collector_new() {
        let collector = SystemCollector::new();
        let _ = collector;
    }
}