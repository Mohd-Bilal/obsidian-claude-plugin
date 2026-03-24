use std::fs;
use regex::RegexBuilder;
use serde_json::{json, Value};

use crate::errors::Result;
use crate::vault::Vault;

/// Search all notes for a query string (regex or literal).
/// Returns a list of {path, line_number, snippet} JSON objects.
pub fn search_notes(
    vault: &Vault,
    query: &str,
    max_results: usize,
    case_sensitive: bool,
) -> Result<Vec<Value>> {
    let pattern = RegexBuilder::new(query)
        .case_insensitive(!case_sensitive)
        .build()
        .unwrap_or_else(|_| {
            // Fall back to literal search
            RegexBuilder::new(&regex::escape(query))
                .case_insensitive(!case_sensitive)
                .build()
                .unwrap()
        });

    let mut results: Vec<Value> = Vec::new();

    'outer: for md_file in vault.all_markdown_files() {
        if results.len() >= max_results {
            break;
        }
        let content = match fs::read_to_string(&md_file) {
            Ok(c) => c,
            Err(_) => continue,
        };
        let rel_path = vault.relative(&md_file);
        for (lineno, line) in content.lines().enumerate() {
            if results.len() >= max_results {
                break 'outer;
            }
            if pattern.is_match(line) {
                results.push(json!({
                    "path": rel_path,
                    "line_number": lineno + 1,
                    "snippet": line,
                }));
            }
        }
    }

    Ok(results)
}
