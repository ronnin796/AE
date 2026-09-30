//! CPU telemetry collector using /proc/stat

use anyhow::{Context, Result};
use std::fs;
use std::time::Duration;
use tokio::time::sleep;

/// CPU time samples for calculating usage
#[derive(Debug, Clone, Default)]
struct CpuTimes {
    user: u64,
    nice: u64,
    system: u64,
    idle: u64,
    iowait: u64,
    irq: u64,
    softirq: u64,
    steal: u64,
    guest: u64,
    guest_nice: u64,
}

impl CpuTimes {
    /// Total CPU time (active + idle)
    fn total(&self) -> u64 {
        self.user + self.nice + self.system + self.idle + self.iowait + self.irq + self.softirq + self.steal + self.guest + self.guest_nice
    }

    /// Active (non-idle) CPU time
    fn active(&self) -> u64 {
        self.user + self.nice + self.system + self.irq + self.softirq + self.steal
    }
}

/// Collected CPU data
#[derive(Debug, Clone)]
pub struct CpuData {
    /// Total CPU usage percentage (0.0 - 100.0 * core_count)
    pub total_usage: f64,

    /// Per-core CPU usage percentages
    pub per_core: Vec<f64>,
}

/// CPU collector reading from /proc/stat
pub struct CpuCollector {
    prev_total: Option<Vec<CpuTimes>>,
}

impl CpuCollector {
    /// Create a new CPU collector
    pub fn new() -> Self {
        Self { prev_total: None }
    }

    /// Parse /proc/stat and return CPU times for each core + total
    fn parse_proc_stat(&self) -> Result<Vec<CpuTimes>> {
        let content = fs::read_to_string("/proc/stat")
            .context("Failed to read /proc/stat")?;

        let mut cpus = Vec::new();

        for line in content.lines() {
            if !line.starts_with("cpu") {
                continue;
            }

            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 11 {
                continue;
            }

            let mut times = CpuTimes::default();
            times.user = parts[1].parse().unwrap_or(0);
            times.nice = parts[2].parse().unwrap_or(0);
            times.system = parts[3].parse().unwrap_or(0);
            times.idle = parts[4].parse().unwrap_or(0);
            times.iowait = parts[5].parse().unwrap_or(0);
            times.irq = parts[6].parse().unwrap_or(0);
            times.softirq = parts[7].parse().unwrap_or(0);
            times.steal = parts[8].parse().unwrap_or(0);
            times.guest = parts[9].parse().unwrap_or(0);
            times.guest_nice = parts[10].parse().unwrap_or(0);

            cpus.push(times);
        }

        Ok(cpus)
    }

    /// Calculate CPU usage percentage between two samples
    fn calculate_usage(prev: &CpuTimes, curr: &CpuTimes) -> f64 {
        let total_diff = curr.total().saturating_sub(prev.total());
        let active_diff = curr.active().saturating_sub(prev.active());

        if total_diff == 0 {
            0.0
        } else {
            (active_diff as f64 / total_diff as f64) * 100.0
        }
    }

    /// Collect CPU metrics
    pub async fn collect(&mut self) -> Result<CpuData> {
        // First sample
        let prev = self.parse_proc_stat()?;

        // Small delay to get a time delta
        sleep(Duration::from_millis(100)).await;

        // Second sample
        let curr = self.parse_proc_stat()?;

        if prev.is_empty() || curr.is_empty() || prev.len() != curr.len() {
            anyhow::bail!("Invalid CPU samples");
        }

        // Calculate usage for each CPU (first entry is aggregate)
        let mut per_core = Vec::new();
        let mut total_usage = 0.0;

        for (i, (p, c)) in prev.iter().zip(curr.iter()).enumerate() {
            let usage = Self::calculate_usage(p, c);
            if i == 0 {
                total_usage = usage;
            } else {
                per_core.push(usage);
            }
        }

        // Store for next call
        self.prev_total = Some(curr);

        Ok(CpuData { total_usage, per_core })
    }
}

impl Default for CpuCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cpu_times_total() {
        let times = CpuTimes {
            user: 100, nice: 10, system: 50, idle: 800,
            iowait: 20, irq: 5, softirq: 3, steal: 0, guest: 0, guest_nice: 0,
        };
        assert_eq!(times.total(), 988);
        assert_eq!(times.active(), 168);
    }

    #[test]
    fn test_calculate_usage() {
        let prev = CpuTimes { user: 100, nice: 0, system: 50, idle: 800, ..Default::default() };
        let curr = CpuTimes { user: 150, nice: 0, system: 70, idle: 820, ..Default::default() };
        let usage = CpuCollector::calculate_usage(&prev, &curr);
        assert!(usage > 0.0 && usage < 100.0);
    }
}