//! Memory telemetry collector using /proc/meminfo

use anyhow::{Context, Result};
use std::collections::HashMap;
use std::fs;

/// Collected memory data
#[derive(Debug, Clone)]
pub struct MemoryData {
    /// Memory usage percentage (0.0 - 100.0)
    pub usage_percent: f64,

    /// Total memory in bytes
    pub total: u64,

    /// Available memory in bytes (free + buffers + cached)
    pub available: u64,

    /// Used memory in bytes
    pub used: u64,

    /// Free memory in bytes
    pub free: u64,

    /// Buffers in bytes
    pub buffers: u64,

    /// Cached memory in bytes
    pub cached: u64,
}

/// Memory collector reading from /proc/meminfo
pub struct MemoryCollector;

impl MemoryCollector {
    /// Create a new memory collector
    pub fn new() -> Self {
        Self
    }

    /// Parse /proc/meminfo into a key-value map
    fn parse_meminfo(&self) -> Result<HashMap<String, u64>> {
        let content = fs::read_to_string("/proc/meminfo")
            .context("Failed to read /proc/meminfo")?;

        let mut map = HashMap::new();

        for line in content.lines() {
            let parts: Vec<&str> = line.split(':').collect();
            if parts.len() != 2 {
                continue;
            }

            let key = parts[0].trim().to_string();
            let value_str = parts[1].trim();

            // Extract numeric value (remove "kB" suffix)
            let value = value_str.split_whitespace().next()
                .and_then(|v| v.parse::<u64>().ok())
                .unwrap_or(0);

            // Convert from kB to bytes
            map.insert(key, value * 1024);
        }

        Ok(map)
    }

    /// Collect memory metrics
    pub async fn collect(&self) -> Result<MemoryData> {
        let meminfo = self.parse_meminfo()?;

        let total = *meminfo.get("MemTotal").unwrap_or(&0);
        let free = *meminfo.get("MemFree").unwrap_or(&0);
        let buffers = *meminfo.get("Buffers").unwrap_or(&0);
        let cached = *meminfo.get("Cached").unwrap_or(&0);
        let available = *meminfo.get("MemAvailable").unwrap_or(&(free + buffers + cached));

        let used = total.saturating_sub(available);
        let usage_percent = if total > 0 {
            (used as f64 / total as f64) * 100.0
        } else {
            0.0
        };

        Ok(MemoryData {
            usage_percent,
            total,
            available,
            used,
            free,
            buffers,
            cached,
        })
    }
}

impl Default for MemoryCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_collector_new() {
        let collector = MemoryCollector::new();
        // Just verify it constructs
        let _ = collector;
    }
}