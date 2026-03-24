use std::fs;
use std::path::PathBuf;
use serde_json::{json, Value};

use crate::errors::{ObsidianError, Result};
use crate::vault::Vault;

fn resolve_canvas(vault: &Vault, path: &str) -> PathBuf {
    let path_with_ext = if path.ends_with(".canvas") {
        path.to_string()
    } else {
        format!("{}.canvas", path)
    };
    vault.root.join(path_with_ext)
}

/// Read and return a .canvas file as a JSON Value.
pub fn read_canvas(vault: &Vault, path: &str) -> Result<Value> {
    let canvas_path = resolve_canvas(vault, path);
    if !canvas_path.exists() {
        return Err(ObsidianError::NoteNotFound(format!(
            "Canvas not found: {}",
            path
        )));
    }
    let text = fs::read_to_string(&canvas_path)?;
    let val: Value = serde_json::from_str(&text).map_err(|e| {
        ObsidianError::CanvasParseError(format!("Malformed canvas JSON in {}: {}", path, e))
    })?;
    Ok(val)
}

/// Create a new .canvas file. Returns its relative path.
pub fn create_canvas(
    vault: &Vault,
    path: &str,
    nodes: Option<Value>,
    edges: Option<Value>,
) -> Result<String> {
    let canvas_path = resolve_canvas(vault, path);
    if canvas_path.exists() {
        return Err(ObsidianError::NoteAlreadyExists(format!(
            "Canvas already exists: {}",
            path
        )));
    }
    if let Some(parent) = canvas_path.parent() {
        fs::create_dir_all(parent)?;
    }
    let data = json!({
        "nodes": nodes.unwrap_or_else(|| json!([])),
        "edges": edges.unwrap_or_else(|| json!([])),
    });
    fs::write(&canvas_path, serde_json::to_string_pretty(&data)?.as_bytes())?;
    Ok(vault.relative(&canvas_path))
}

/// Overwrite a .canvas file with new JSON data. Returns its relative path.
pub fn update_canvas(vault: &Vault, path: &str, data: &Value) -> Result<String> {
    let canvas_path = resolve_canvas(vault, path);
    if !canvas_path.exists() {
        return Err(ObsidianError::NoteNotFound(format!(
            "Canvas not found: {}",
            path
        )));
    }
    fs::write(&canvas_path, serde_json::to_string_pretty(data)?.as_bytes())?;
    Ok(vault.relative(&canvas_path))
}

/// Delete a .canvas file. Returns its former relative path.
pub fn delete_canvas(vault: &Vault, path: &str) -> Result<String> {
    let canvas_path = resolve_canvas(vault, path);
    if !canvas_path.exists() {
        return Err(ObsidianError::NoteNotFound(format!(
            "Canvas not found: {}",
            path
        )));
    }
    let rel = vault.relative(&canvas_path);
    fs::remove_file(&canvas_path)?;
    Ok(rel)
}
