use std::net::SocketAddr;
use std::time::Duration;
use tokio::time::interval;

use anyhow::{Context, Result};
use clap::Parser;
use tracing::{debug, error, info};
use aetheredge_edge::{Config, NodeIdentity, NetworkClient, TelemetryCollector};

#[derive(Parser, Debug)]
#[command(name = "aetheredge-edge", version, about = "AetherEdge Edge Daemon")]
struct Args {
    /// Node ID (unique identifier)
    #[arg(long, env = "AETHEREDGE_NODE_ID")]
    node_id: Option<String>,

    /// Server address (host:port)
    #[arg(long, env = "AETHEREDGE_SERVER_ADDR", default_value = "127.0.0.1:8081")]
    server_addr: String,

    /// Config file path
    #[arg(long, env = "AETHEREDGE_CONFIG")]
    config: Option<std::path::PathBuf>,

    /// Telemetry interval in seconds
    #[arg(long, env = "AETHEREDGE_TELEMETRY_INTERVAL", default_value = "2")]
    telemetry_interval: u64,

    /// Disable telemetry
    #[arg(long, env = "AETHEREDGE_NO_TELEMETRY")]
    no_telemetry: bool,

    /// Disable heartbeat
    #[arg(long, env = "AETHEREDGE_NO_HEARTBEAT")]
    no_heartbeat: bool,

    /// Log level
    #[arg(long, env = "AETHEREDGE_LOG_LEVEL", default_value = "info")]
    log_level: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    // Initialize logging
    aetheredge_edge::logging::init(&args.log_level)?;

    info!("Starting AetherEdge Edge Daemon v{}", env!("CARGO_PKG_VERSION"));

    // Load configuration
    let config = Config::load(args.config.as_deref())?;
    info!("Configuration loaded");

    // Build node identity
    let node_identity = NodeIdentity::build(args.node_id.clone(), config.node.hostname.clone())?;
    info!("Node identity: {} ({})", node_identity.node_id, node_identity.hostname);

    // Parse server address
    let server_addr: SocketAddr = args.server_addr.parse()
        .context("Invalid server address format (expected host:port)")?;

    // Create network client
    let mut network_client = NetworkClient::new(server_addr, node_identity.clone());

    // Connect to server
    network_client.connect().await
        .context("Failed to connect to server")?;
    info!("Connected to server at {}", server_addr);

    // Register node
    let register_response = network_client.register(&node_identity).await
        .context("Node registration failed")?;
    info!("Registration successful: {}", register_response.message);

    // Convert config telemetry to the correct type
    let telemetry_config = aetheredge_edge::TelemetryConfig {
        collect_cpu: config.telemetry.collect_cpu,
        collect_memory: config.telemetry.collect_memory,
        collect_temperature: config.telemetry.collect_temperature,
        collect_uptime: config.telemetry.collect_uptime,
        collect_load: config.telemetry.collect_load,
    };

    // Start heartbeat task
    if !args.no_heartbeat {
        let hb_client = network_client.clone();
        let hb_identity = node_identity.clone();

        tokio::spawn(async move {
            let mut hb_interval = interval(Duration::from_secs(10));
            loop {
                hb_interval.tick().await;

                match hb_client.heartbeat(&hb_identity).await {
                    Ok(_) => debug!("Heartbeat sent successfully"),
                    Err(e) => error!("Heartbeat failed: {}", e),
                }
            }
        });
    }

    // Start telemetry collection task
    if !args.no_telemetry {
        let tel_client = network_client.clone();
        let tel_identity = node_identity.clone();
        let mut collector = TelemetryCollector::new(telemetry_config);

        tokio::spawn(async move {
            let mut tel_interval = interval(Duration::from_secs(args.telemetry_interval));
            loop {
                tel_interval.tick().await;

                match collector.collect(&tel_identity).await {
                    Ok(telemetry) => {
                        if let Err(e) = tel_client.send_telemetry(&telemetry).await {
                            error!("Failed to send telemetry: {}", e);
                        }
                    }
                    Err(e) => {
                        error!("Telemetry collection failed: {}", e);
                    }
                }
            }
        });
    }

    info!("Daemon running. Press Ctrl+C to stop.");

    // Wait for shutdown signal
    tokio::signal::ctrl_c().await?;
    info!("Shutting down daemon...");

    // Disconnect
    // In a real implementation, we'd track handles to cancel them

    info!("Daemon stopped");
    Ok(())
}