//! Temperature telemetry collector using /sys/class/thermal

use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

/// Temperature collector reading from /sys/class/thermal
pub struct TemperatureCollector;

impl TemperatureCollector {
    /// Create a new temperature collector
    pub fn new() -> Self {
        Self
    }

    /// Read temperature from a thermal zone file
    fn read_thermal_zone(path: &Path) -> Result<Option<f64>> {
        let temp_path = path.join("temp");
        let type_path = path.join("type");

        // Read sensor type for filtering
        let sensor_type = fs::read_to_string(&type_path)
            .unwrap_or_default()
            .trim()
            .to_string();

        // Read temperature (millidegrees Celsius)
        let temp_str = fs::read_to_string(&temp_path)
            .context(format!("Failed to read {}", temp_path.display()))?;

        let temp_millidegrees: i64 = temp_str.trim().parse()
            .context(format!("Failed to parse temperature from {}", temp_path.display()))?;

        // Convert to Celsius
        let temp_celsius = temp_millidegrees as f64 / 1000.0;

        // Filter out invalid readings
        if temp_celsius < -50.0 || temp_celsius > 150.0 {
            return Ok(None);
        }

        // Skip non-CPU thermal zones if we have CPU ones
        // (We'll collect all and let the caller decide)
        Ok(Some(temp_celsius))
    }

    /// Collect temperatures from all available thermal zones
    pub async fn collect(&self) -> Result<Vec<f64>> {
        let thermal_base = Path::new("/sys/class/thermal");

        if !thermal_base.exists() {
            return Ok(Vec::new());
        }

        let mut temperatures = Vec::new();

        // Read all thermal_zone* directories
        let entries = fs::read_dir(thermal_base)
            .context("Failed to read /sys/class/thermal")?;

        for entry in entries {
            let entry = entry.context("Failed to read directory entry")?;
            let path = entry.path();

            if path.is_dir() {
                if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                    if name.starts_with("thermal_zone") {
                        if let Ok(Some(temp)) = Self::read_thermal_zone(&path) {
                            temperatures.push(temp);
                        }
                    }
                }
            }
        }

        // Sort for consistent ordering
        temperatures.sort_by(|a, b| a.partial_cmp(b).unwrap());

        Ok(temperatures)
    }
}

impl Default for TemperatureCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_temperature_collector_new() {
        let collector = TemperatureCollector::new();
        let _ = collector;
    }
}