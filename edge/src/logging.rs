//! Logging initialization and configuration

use anyhow::Result;
use tracing::Level;
use tracing_subscriber::{fmt, layer::SubscriberExt, util::SubscriberInitExt, EnvFilter, Layer};

/// Initialize the global tracing subscriber
pub fn init(log_level: &str) -> Result<()> {
    // Parse log level from string
    let level = log_level.parse::<Level>()
        .unwrap_or(Level::INFO);

    // Create env filter with default level
    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new(level.to_string()));

    // Console layer with pretty formatting for development
    let console_layer = fmt::layer()
        .with_target(true)
        .with_thread_ids(true)
        .with_thread_names(true)
        .with_file(true)
        .with_line_number(true)
        .with_filter(env_filter);

    // Initialize subscriber
    tracing_subscriber::registry()
        .with(console_layer)
        .init();

    Ok(())
}

/// Initialize JSON-formatted logging for production
pub fn init_json(log_level: &str) -> Result<()> {
    let level = log_level.parse::<Level>()
        .unwrap_or(Level::INFO);

    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new(level.to_string()));

    let json_layer = fmt::layer()
        .json()
        .with_current_span(true)
        .with_span_list(true)
        .with_filter(env_filter);

    tracing_subscriber::registry()
        .with(json_layer)
        .init();

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_init_logging() {
        init("debug").expect("Failed to init logging");
        tracing::info!("Test log message");
    }
}