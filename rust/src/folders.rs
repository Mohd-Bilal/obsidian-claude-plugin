use std::fs;

use crate::errors::{ObsidianError, Result};
use crate::vault::Vault;

/// Create a new folder inside the vault. Returns its relative path.
pub fn create_folder(vault: &Vault, path: &str) -> Result<String> {
    let folder_path = vault.root.join(path);
    // mkdir without exist_ok — error if already exists
    fs::create_dir_all(&folder_path)?;
    Ok(vault.relative(&folder_path))
}

/// Rename (move) a folder. Returns the new relative path.
pub fn rename_folder(vault: &Vault, old_path: &str, new_path: &str) -> Result<String> {
    let src = vault.root.join(old_path);
    if !src.exists() {
        return Err(ObsidianError::FolderNotFound(format!(
            "Folder not found: {:?}",
            old_path
        )));
    }
    let dst = vault.root.join(new_path);
    if let Some(parent) = dst.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::rename(&src, &dst)?;
    Ok(vault.relative(&dst))
}

/// Delete a folder. If `force` is false, the folder must be empty.
/// Returns the deleted folder's path.
pub fn delete_folder(vault: &Vault, path: &str, force: bool) -> Result<String> {
    let folder_path = vault.root.join(path);
    if !folder_path.exists() {
        return Err(ObsidianError::FolderNotFound(format!(
            "Folder not found: {:?}",
            path
        )));
    }

    if force {
        fs::remove_dir_all(&folder_path)?;
    } else {
        // Check if empty
        let mut entries = fs::read_dir(&folder_path)?;
        if entries.next().is_some() {
            return Err(ObsidianError::FolderNotEmpty(format!(
                "Folder is not empty: {:?}. Use force=true to delete anyway.",
                path
            )));
        }
        fs::remove_dir(&folder_path)?;
    }

    Ok(path.to_string())
}
