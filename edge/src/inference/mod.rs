//! ONNX Runtime inference engine for edge nodes

use anyhow::{Context, Result};
use std::path::Path;
use tracing::{debug, info, warn};

/// Inference engine using ONNX Runtime
pub struct InferenceEngine {
    session: Option<ort::Session>,
    input_name: String,
    output_names: Vec<String>,
}

impl InferenceEngine {
    /// Create a new inference engine from an ONNX model file
    pub fn new(model_path: &Path) -> Result<Self> {
        info!("Loading ONNX model from {}", model_path.display());

        // Initialize ONNX Runtime environment
        let environment = ort::Environment::new()
            .context("Failed to create ONNX Runtime environment")?;

        // Load model
        let session = environment
            .new_session_builder()
            .context("Failed to create session builder")?
            .with_model_from_file(model_path)
            .context("Failed to load model from file")?;

        // Get input/output metadata
        let inputs = session.inputs();
        let outputs = session.outputs();

        let input_name = inputs.first()
            .map(|i| i.name().to_string())
            .unwrap_or_else(|| "input".to_string());

        let output_names = outputs.iter()
            .map(|o| o.name().to_string())
            .collect();

        info!("Model loaded: input='{}', outputs={:?}", input_name, output_names);

        Ok(Self {
            session: Some(session),
            input_name,
            output_names,
        })
    }

    /// Run inference on input data
    pub fn infer(&mut self, input: &[f32], input_shape: &[usize]) -> Result<Vec<f32>> {
        let session = self.session.as_mut()
            .context("No session available")?;

        // Create input tensor
        let input_tensor = ort::Tensor::from_array((input_shape.to_vec(), input.to_vec()))
            .context("Failed to create input tensor")?;

        // Run inference
        let outputs = session.run(ort::inputs![
            self.input_name.as_str() => input_tensor
        ]).context("Inference failed")?;

        // Extract output
        let output_tensor = outputs.get(&self.output_names[0])
            .context("Output tensor not found")?;

        let output_data = output_tensor.try_extract_array::<f32>()
            .context("Failed to extract output array")?;

        Ok(output_data.to_vec())
    }

    /// Run inference and measure time
    pub fn infer_timed(&mut self, input: &[f32], input_shape: &[usize]) -> Result<(Vec<f32>, f64)> {
        let start = std::time::Instant::now();
        let output = self.infer(input, input_shape)?;
        let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
        Ok((output, elapsed_ms))
    }
}

/// Model metadata for inference
#[derive(Debug, Clone)]
pub struct ModelMetadata {
    pub model_id: String,
    pub input_shape: Vec<usize>,
    pub output_shape: Vec<usize>,
    pub input_type: String,
    pub output_type: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_inference_engine_creation() {
        // This would require a real model file
        // Just test the struct can be created
        let _engine = InferenceEngine {
            session: None,
            input_name: "input".to_string(),
            output_names: vec!["output".to_string()],
        };
    }
}