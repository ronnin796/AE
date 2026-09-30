#!/usr/bin/env rust
//! AetherEdge Edge Daemon

use anyhow::{Context, Result};
use clap::{Parser, ValueEnum};
use tokio::{signal, time::{self, Duration}};
use tracing::{error, info, warn, debug};

mod config;
mod logging;
mod network;
mod node;
mod protocol;
mod telemetry;

use config::Config;
use node::NodeIdentity;
use network::NetworkClient;
use telemetry::TelemetryCollector;

#[derive(Parser, Debug)]
#[command(name = "aetheredge-edge", version, about = "Edge daemon for AetherEdge")]
struct Args {
    /// Node ID (unique identifier)
    #[arg(long, env = "AETHEREDGE_NODE_ID")]
    node_id: Option<String>,

    /// Server address
    #[arg(long, env = "AETHEREDGE_SERVER_ADDR", default_value = "127.0.0.1:8080")]
    server_addr: String,

    /// Config file path
    #[arg(long, env = "AETHEREDGE_CONFIG")]
    config: Option<String>,

    /// Log level
    #[arg(long, env = "AETHEREDGE_LOG_LEVEL", default_value = "info")]
    log_level: String,

    /// Disable telemetry
    #[arg(long, env = "AETHEREDGE_NO_TELEMETRY")]
    no_telemetry: bool,

    /// Disable heartbeat
    #[arg(long, env = "AETHEREDGE_NO_HEARTBEAT")]
    no_heartbeat: bool,

    /// Start inference with model
    #[arg(long, env = "AETHEREDGE_MODEL_PATH")]
    model_path: Option<String>,

    /// Run inference once with sample data
    #[arg(long, env = "AETHEREDGE_INFERENCE_ONCE")]
    inference_once: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    logging::init(&args.log_level)?;

    info!("Starting AetherEdge Edge Daemon v{}", env!("CARGO_PKG_VERSION"));

    let config = Config::load(args.config.as_deref())?;
    info!("Configuration loaded");

    // Build node identity
    let node_identity = NodeIdentity::build(
        args.node_id.clone(),
        config.node.hostname.clone(),
    )?;

    info!("Node: {} ({})", node_identity.node_id, node_identity.hostname);

    // Parse server address
    let server_addr: std::net::SocketAddr = args.server_addr.parse()
        .context("Invalid server address")?;

    let mut network_client = NetworkClient::new(server_addr, node_identity.clone());

    // Connect
    network_client.connect().await.context("Connect failed")?;

    // Register
    let register_response = network_client.register(&node_identity).await
        .context("Registration failed")?;

    info!("Registration successful: {}", register_response.message);

    // Start tasks
    let mut tasks = vec![];

    // Heartbeat task
    if !args.no_heartbeat {
        let mut hb_client = network_client.clone();
        let hb_identity = node_identity.clone();

        let handle = tokio::spawn(async move {
            let mut interval = time::interval(Duration::from_secs(10));
            loop {
                interval.tick().await;
                match hb_client.heartbeat(&hb_identity).await {
                    Ok(ack) => {
                        debug!("Heartbeat ACK: {}", ack.server_time);
                    }
                    Err(e) => {
                        error!("Heartbeat failed: {}", e);
                    }
                }
            }
        });
        tasks.push(handle);
    }

    // Telemetry task
    if !args.no_telemetry {
        let mut tel_client = network_client.clone();
        let tel_identity = node_identity.clone();
        let mut collector = TelemetryCollector::new(config.telemetry);

        let handle = tokio::spawn(async move {
            let mut interval = time::interval(Duration::from_secs(2));
            loop {
                interval.tick().await;

                match collector.collect(&tel_identity).await {
                    Ok(telemetry) => {
                        if let Err(e) = tel_client.send_telemetry(&telemetry).await {
                            error!("Send telemetry failed: {}", e);
                        }
                    }
                    Err(e) => {
                        error!("Collect telemetry failed: {}", e);
                    }
                }
            }
        });
        tasks.push(handle);
    }

    // Inference task
    if args.model_path.is_some() || args.inference_once {
        let mut inf_client = network_client.clone();
        let inf_identity = node_identity.clone();
        let model_path = args.model_path.clone();

        let handle = tokio::spawn(async move {
            let model_path = model_path.unwrap_or_else(|| "/tmp/test.onnx".to_string());

            // In a real implementation, you would load and run the model
            // For now, we'll just simulate
            info!("Model path: {}", model_path);

            if args.inference_once {
                // Simulate one inference
                let input = vec![1.0, 2.0, 3.0, 4.0, 5.0]; // Sample input
                let input_shape = vec![1, 5];

                info!("Running inference on: {:?}", input_shape);
                // This would use the actual inference engine
                // For now, just log
            }

            // Continuous inference loop
            let mut interval = time::interval(Duration::from_secs(30));
            loop {
                interval.tick().await;
                debug!("Periodic inference check");
                // In real implementation, run inference here
            }
        });
        tasks.push(handle);
    }

    // Wait for Ctrl+C
    info!("Daemon running. Press Ctrl+C to stop.");
    signal::ctrl_c().await?;

    info!("Shutting down...");

    // Cancel tasks
    for task in tasks {
        task.abort();
    }

    // Disconnect
    network_client.disconnect().await;
    info!("Daemon stopped.");

    Ok(())
}