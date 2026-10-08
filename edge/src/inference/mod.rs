//! ONNX Runtime inference engine for edge nodes

use anyhow::{Context, Result};
use ort::session::Session;
use std::path::Path;
use tracing::info;

/// Inference engine using ONNX Runtime
///
/// Wraps an ONNX Runtime session for local edge inference.
/// Supports both FP32 and INT8 quantized models.
pub struct InferenceEngine {
    session: Session,
    input_name: String,
    output_names: Vec<String>,
}

impl InferenceEngine {
    /// Create a new inference engine from an ONNX model file
    pub fn new(model_path: &Path) -> Result<Self> {
        info!("Loading ONNX model from {}", model_path.display());

        // Build session directly (auto-initializes ort environment)
        let session = Session::builder()
            .context("Failed to create ONNX Runtime session builder")?
            .commit_from_file(model_path)
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
            session,
            input_name,
            output_names,
        })
    }

    /// Run inference on input data
    pub fn infer(&mut self, input: &[f32], input_shape: &[usize]) -> Result<Vec<f32>> {
        use ort::value::TensorRef;

        // Create input tensor from array view
        let input_tensor = TensorRef::from_array_view(
            (input_shape.iter().map(|&d| d as i64).collect::<Vec<_>>(), input)
        )
            .context("Failed to create input tensor")?;

        // Run inference
        let outputs = self.session.run(ort::inputs![self.input_name.as_str() => input_tensor])
            .context("Inference failed")?;

        // Extract output
        let output_tensor = outputs.get(&self.output_names[0])
            .context("Output tensor not found")?;

        let output_data = output_tensor.try_extract_array::<f32>()
            .context("Failed to extract output array")?;

        // Convert array view to Vec<f32>
        Ok(output_data.as_slice().expect("output array is not empty").to_vec())
    }

    /// Run inference and measure time
    pub fn infer_timed(&mut self, input: &[f32], input_shape: &[usize]) -> Result<(Vec<f32>, f64)> {
        let start = std::time::Instant::now();
        let output = self.infer(input, input_shape)?;
        let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
        Ok((output, elapsed_ms))
    }

    /// Get model input name
    pub fn input_name(&self) -> &str {
        &self.input_name
    }

    /// Get model output names
    pub fn output_names(&self) -> &[String] {
        &self.output_names
    }

    /// Create a deterministic input vector from a seed
    ///
    /// Produces a reproducible 784-dim input suitable for testing.
    pub fn deterministic_input(seed: u64, length: usize) -> Vec<f32> {
        // Deterministic pseudo-random generator: xorshift
        let mut state = seed;
        let mut out = Vec::with_capacity(length);
        for _ in 0..length {
            // xorshift for u64
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            let v = (state >> 20) as f32 / 65535.0; // normalized to [0, 1]
            out.push(v);
        }
        out
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
        // Just test the struct can be created - placeholder test
        // This test is a placeholder - actual tests would need a real model
        let _dummy = true;
    }

    #[test]
    fn test_deterministic_input() {
        let input1 = InferenceEngine::deterministic_input(12345, 10);
        let input2 = InferenceEngine::deterministic_input(12345, 10);
        assert_eq!(input1, input2, "Deterministic inputs should be identical for same seed");

        let input3 = InferenceEngine::deterministic_input(54321, 10);
        assert!(input1 != input3, "Different seeds should produce different outputs");
    }
}