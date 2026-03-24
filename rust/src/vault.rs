use std::fs;
use std::path::{Path, PathBuf};
use serde::Deserialize;
use walkdir::WalkDir;

use crate::errors::{ObsidianError, Result};

/// Return the path to obsidian.json based on OS.
fn obsidian_config_path() -> PathBuf {
    #[cfg(target_os = "macos")]
    {
        dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("/"))
            .join("Library")
            .join("Application Support")
            .join("obsidian")
            .join("obsidian.json")
    }
    #[cfg(not(target_os = "macos"))]
    {
        dirs::config_dir()
            .unwrap_or_else(|| dirs::home_dir().unwrap_or_else(|| PathBuf::from("/")).join(".config"))
            .join("obsidian")
            .join("obsidian.json")
    }
}

#[derive(Debug, Deserialize)]
struct ObsidianVaultEntry {
    path: String,
    #[serde(default)]
    open: bool,
    #[serde(default)]
    ts: i64,
}

#[derive(Debug, Deserialize)]
struct ObsidianConfig {
    #[serde(default)]
    vaults: std::collections::HashMap<String, ObsidianVaultEntry>,
}

/// Info about a registered Obsidian vault.
#[derive(Debug, Clone, serde::Serialize)]
pub struct VaultInfo {
    pub name: String,
    pub path: String,
    pub open: bool,
    pub ts: i64,
    pub active: bool,
}

/// Return all vaults registered in obsidian.json, sorted by most recently used.
pub fn list_vaults() -> Vec<VaultInfo> {
    let config_path = obsidian_config_path();
    if !config_path.exists() {
        return vec![];
    }
    let text = match fs::read_to_string(&config_path) {
        Ok(t) => t,
        Err(_) => return vec![],
    };
    let config: ObsidianConfig = match serde_json::from_str(&text) {
        Ok(c) => c,
        Err(_) => return vec![],
    };
    let mut result: Vec<VaultInfo> = config
        .vaults
        .values()
        .map(|v| VaultInfo {
            name: PathBuf::from(&v.path)
                .file_name()
                .map(|n| n.to_string_lossy().to_string())
                .unwrap_or_default(),
            path: v.path.clone(),
            open: v.open,
            ts: v.ts,
            active: false,
        })
        .collect();
    result.sort_by(|a, b| b.ts.cmp(&a.ts));
    result
}

/// Discover the active vault path from env var or obsidian.json.
pub fn discover_vault_path() -> Result<PathBuf> {
    if let Ok(env_path) = std::env::var("OBSIDIAN_VAULT_PATH") {
        if !env_path.is_empty() {
            let p = PathBuf::from(&env_path);
            if !p.exists() {
                return Err(ObsidianError::VaultNotFound(format!(
                    "OBSIDIAN_VAULT_PATH points to non-existent path: {}",
                    p.display()
                )));
            }
            return Ok(p);
        }
    }

    let config_path = obsidian_config_path();
    if !config_path.exists() {
        return Err(ObsidianError::VaultNotFound(format!(
            "Obsidian config not found at {} and OBSIDIAN_VAULT_PATH is not set.",
            config_path.display()
        )));
    }

    let text = fs::read_to_string(&config_path).map_err(|e| {
        ObsidianError::VaultNotFound(format!(
            "Failed to read {}: {}",
            config_path.display(),
            e
        ))
    })?;

    let config: ObsidianConfig = serde_json::from_str(&text).map_err(|e| {
        ObsidianError::VaultNotFound(format!(
            "Failed to parse {}: {}",
            config_path.display(),
            e
        ))
    })?;

    if config.vaults.is_empty() {
        return Err(ObsidianError::VaultNotFound(
            "No vaults found in obsidian.json".to_string(),
        ));
    }

    let mut best_path: Option<String> = None;
    let mut best_ts: i64 = -1;
    let mut open_path: Option<String> = None;

    for v in config.vaults.values() {
        if v.open {
            open_path = Some(v.path.clone());
        }
        if v.ts > best_ts {
            best_ts = v.ts;
            best_path = Some(v.path.clone());
        }
    }

    let chosen = open_path.or(best_path).ok_or_else(|| {
        ObsidianError::VaultNotFound(
            "Could not determine vault path from obsidian.json".to_string(),
        )
    })?;

    let result = PathBuf::from(&chosen);
    if !result.exists() {
        return Err(ObsidianError::VaultNotFound(format!(
            "Vault path from obsidian.json does not exist on disk: {}",
            result.display()
        )));
    }
    Ok(result)
}

/// The Vault struct wraps a root path and provides helpers.
#[derive(Debug, Clone)]
pub struct Vault {
    pub root: PathBuf,
}

impl Vault {
    pub fn new(root: PathBuf) -> Self {
        Vault { root }
    }

    /// Resolve a note reference to an absolute path.
    ///
    /// Accepts:
    /// - A relative path (with .md extension or without)
    /// - A bare title (no path separators) — searches all .md files by stem
    pub fn resolve(&self, note_ref: &str) -> Result<PathBuf> {
        let note_ref = note_ref.trim();
        let with_ext = if note_ref.ends_with(".md") {
            note_ref.to_string()
        } else {
            format!("{}.md", note_ref)
        };

        let candidate = self.root.join(&with_ext);
        if candidate.exists() {
            return Ok(candidate);
        }

        // Bare title search (no path separators in original ref)
        let ref_without_ext = &with_ext[..with_ext.len() - 3];
        let has_separator = ref_without_ext.contains('/') || ref_without_ext.contains('\\');

        if !has_separator {
            let lower = ref_without_ext.to_lowercase();
            let matches: Vec<PathBuf> = self
                .all_markdown_files()
                .filter(|f| {
                    f.file_stem()
                        .map(|s| s.to_string_lossy().to_lowercase())
                        .as_deref()
                        == Some(lower.as_str())
                })
                .collect();

            match matches.len() {
                0 => {
                    return Err(ObsidianError::NoteNotFound(format!(
                        "Note not found: {:?}",
                        ref_without_ext
                    )))
                }
                1 => return Ok(matches.into_iter().next().unwrap()),
                _ => {
                    let rel_matches: Vec<String> = matches
                        .iter()
                        .map(|m| {
                            m.strip_prefix(&self.root)
                                .map(|p| p.to_string_lossy().to_string())
                                .unwrap_or_else(|_| m.to_string_lossy().to_string())
                        })
                        .collect();
                    return Err(ObsidianError::NoteNotFound(format!(
                        "Ambiguous note title {:?}; matches: {:?}",
                        ref_without_ext, rel_matches
                    )));
                }
            }
        }

        Err(ObsidianError::NoteNotFound(format!(
            "Note not found: {}",
            with_ext
        )))
    }

    /// Iterate all .md files under the vault root.
    pub fn all_markdown_files(&self) -> impl Iterator<Item = PathBuf> + '_ {
        WalkDir::new(&self.root)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| {
                e.file_type().is_file()
                    && e.path()
                        .extension()
                        .map(|x| x == "md")
                        .unwrap_or(false)
            })
            .map(|e| e.into_path())
    }

    /// Return relative path from vault root.
    pub fn relative(&self, abs: &Path) -> String {
        abs.strip_prefix(&self.root)
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|_| abs.to_string_lossy().to_string())
    }

    /// Return the attachments directory, creating it if absent.
    pub fn attachments_dir(&self) -> Result<PathBuf> {
        let d = self.root.join("attachments");
        fs::create_dir_all(&d)?;
        Ok(d)
    }
}
