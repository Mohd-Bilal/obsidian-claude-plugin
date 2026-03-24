use std::fs;
use gray_matter::{Matter, engine::YAML};
use serde_json::{Map, Value};

use crate::errors::{ObsidianError, Result};
use crate::vault::Vault;

/// Read YAML frontmatter from a note, returning it as a JSON object.
pub fn read_frontmatter(vault: &Vault, path: &str) -> Result<Map<String, Value>> {
    let note_path = vault.resolve(path)?;
    let text = fs::read_to_string(&note_path)?;
    let matter = Matter::<YAML>::new();
    let parsed = matter.parse(&text);
    match parsed.data {
        Some(pod) => {
            // gray_matter returns a Pod which we serialize to JSON then deserialize to Map
            let json_val: Value = pod
                .deserialize()
                .map_err(|e| ObsidianError::CanvasParseError(format!("Frontmatter parse error: {}", e)))?;
            match json_val {
                Value::Object(map) => Ok(map),
                _ => Ok(Map::new()),
            }
        }
        None => Ok(Map::new()),
    }
}

/// Write (merge or replace) YAML frontmatter fields in a note.
///
/// If `replace` is true, the entire frontmatter is replaced with `fields`.
/// Otherwise, `fields` are merged into the existing frontmatter.
pub fn write_frontmatter(
    vault: &Vault,
    path: &str,
    fields: &Map<String, Value>,
    replace: bool,
) -> Result<String> {
    let note_path = vault.resolve(path)?;
    let text = fs::read_to_string(&note_path)?;
    let matter = Matter::<YAML>::new();
    let parsed = matter.parse(&text);

    // Build the new frontmatter map
    let mut new_meta: Map<String, Value> = if replace {
        Map::new()
    } else {
        match &parsed.data {
            Some(pod) => {
                let json_val: Value = pod
                    .deserialize()
                    .map_err(|e| ObsidianError::CanvasParseError(format!("Frontmatter parse error: {}", e)))?;
                match json_val {
                    Value::Object(m) => m,
                    _ => Map::new(),
                }
            }
            None => Map::new(),
        }
    };

    // Merge (or replace) fields
    for (k, v) in fields {
        new_meta.insert(k.clone(), v.clone());
    }

    // Serialize new frontmatter to YAML
    let yaml_str = serialize_yaml(&new_meta);

    // Reconstruct the file: frontmatter + body
    // parsed.content is the body after the frontmatter
    let body = parsed.content.trim_start_matches('\n');

    let new_text = if new_meta.is_empty() {
        body.to_string()
    } else {
        format!("---\n{}---\n{}", yaml_str, body)
    };

    fs::write(&note_path, new_text.as_bytes())?;
    Ok(vault.relative(&note_path))
}

/// Very simple YAML serializer for a flat or nested JSON object.
/// Handles string, number, boolean, null, array, and nested object values.
fn serialize_yaml(map: &Map<String, Value>) -> String {
    let mut out = String::new();
    for (k, v) in map {
        out.push_str(&format!("{}: {}\n", k, yaml_value(v, 0)));
    }
    out
}

fn yaml_value(v: &Value, indent: usize) -> String {
    let pad = "  ".repeat(indent);
    match v {
        Value::Null => "null".to_string(),
        Value::Bool(b) => b.to_string(),
        Value::Number(n) => n.to_string(),
        Value::String(s) => {
            // Quote strings that need it
            if s.contains('\n') || s.contains(':') || s.starts_with('"') || s.is_empty() {
                format!("{:?}", s)
            } else {
                s.clone()
            }
        }
        Value::Array(arr) => {
            if arr.is_empty() {
                return "[]".to_string();
            }
            let mut out = String::new();
            for item in arr {
                out.push_str(&format!("\n{}- {}", pad, yaml_value(item, indent + 1)));
            }
            out
        }
        Value::Object(obj) => {
            if obj.is_empty() {
                return "{}".to_string();
            }
            let mut out = String::new();
            for (k, val) in obj {
                out.push_str(&format!("\n{}{}  {}: {}", pad, pad, k, yaml_value(val, indent + 1)));
            }
            out
        }
    }
}
