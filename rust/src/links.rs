use std::fs;
use regex::Regex;

use crate::errors::Result;
use crate::vault::Vault;

/// Regex that matches Obsidian wikilinks: [[target]] or [[target|alias]]
fn wikilink_re() -> Regex {
    Regex::new(r"\[\[([^\[\]]+)\]\]").unwrap()
}

/// Append a wikilink to the end of a note. Returns the note's relative path.
pub fn insert_wikilink(
    vault: &Vault,
    source_path: &str,
    target_title: &str,
    alias: Option<&str>,
) -> Result<String> {
    let note_path = vault.resolve(source_path)?;
    let link = match alias {
        Some(a) => format!("[[{}|{}]]", target_title, a),
        None => format!("[[{}]]", target_title),
    };

    let content = fs::read_to_string(&note_path)?;
    let mut new_content = content;
    if !new_content.is_empty() && !new_content.ends_with('\n') {
        new_content.push('\n');
    }
    new_content.push_str(&link);
    new_content.push('\n');

    fs::write(&note_path, new_content.as_bytes())?;
    Ok(vault.relative(&note_path))
}

/// Find all notes that contain a wikilink pointing to the given note.
/// Returns relative paths of files that link to it.
pub fn get_backlinks(vault: &Vault, path: &str) -> Result<Vec<String>> {
    let target_path = vault.resolve(path)?;
    let stem = target_path
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    let rel = vault.relative(&target_path);
    let rel_no_ext = if rel.ends_with(".md") {
        rel[..rel.len() - 3].to_string()
    } else {
        rel.clone()
    };

    let re = wikilink_re();
    let mut results: Vec<String> = Vec::new();

    for md_file in vault.all_markdown_files() {
        if md_file == target_path {
            continue;
        }
        let content = match fs::read_to_string(&md_file) {
            Ok(c) => c,
            Err(_) => continue,
        };
        let mut linked = false;
        for cap in re.captures_iter(&content) {
            let link_target = cap[1].split('|').next().unwrap_or("").trim();
            if link_target == stem || link_target == rel_no_ext {
                linked = true;
                break;
            }
        }
        if linked {
            results.push(vault.relative(&md_file));
        }
    }
    Ok(results)
}

/// Return all wikilink targets referenced from a note.
pub fn get_forward_links(vault: &Vault, path: &str) -> Result<Vec<String>> {
    let note_path = vault.resolve(path)?;
    let content = fs::read_to_string(&note_path)?;
    let re = wikilink_re();
    let links: Vec<String> = re
        .captures_iter(&content)
        .map(|cap| cap[1].split('|').next().unwrap_or("").trim().to_string())
        .collect();
    Ok(links)
}
