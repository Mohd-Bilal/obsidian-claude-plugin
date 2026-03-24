use std::fs;
use std::path::PathBuf;

use crate::errors::{ObsidianError, Result};
use crate::vault::Vault;

/// Embed an existing attachment image in a note by appending ![[filename]].
/// Returns the note's relative path.
pub fn embed_image(vault: &Vault, note_path: &str, image_filename: &str) -> Result<String> {
    let resolved_note = vault.resolve(note_path)?;
    let attachments = vault.attachments_dir()?;
    let image_path = attachments.join(image_filename);
    if !image_path.exists() {
        return Err(ObsidianError::AttachmentNotFound(format!(
            "Image not found in attachments: {:?}",
            image_filename
        )));
    }

    let content = fs::read_to_string(&resolved_note)?;
    let mut new_content = content;
    if !new_content.is_empty() && !new_content.ends_with('\n') {
        new_content.push('\n');
    }
    new_content.push_str(&format!("![[{}]]\n", image_filename));

    fs::write(&resolved_note, new_content.as_bytes())?;
    Ok(vault.relative(&resolved_note))
}

/// Import an external image into the vault and embed it in a note.
/// Returns the relative path of the copied image inside the vault.
pub fn import_image(
    vault: &Vault,
    note_path: &str,
    external_image_path: &str,
    subfolder: &str,
) -> Result<String> {
    let resolved_note = vault.resolve(note_path)?;
    let src = PathBuf::from(external_image_path);
    if !src.exists() {
        return Err(ObsidianError::AttachmentNotFound(format!(
            "External image not found: {:?}",
            external_image_path
        )));
    }

    let dest_dir = vault.root.join(subfolder);
    fs::create_dir_all(&dest_dir)?;

    let filename = src
        .file_name()
        .ok_or_else(|| {
            ObsidianError::AttachmentNotFound(format!(
                "Invalid image path: {:?}",
                external_image_path
            ))
        })?
        .to_string_lossy()
        .to_string();
    let dest = dest_dir.join(&filename);

    fs::copy(&src, &dest)?;

    let content = fs::read_to_string(&resolved_note)?;
    let mut new_content = content;
    if !new_content.is_empty() && !new_content.ends_with('\n') {
        new_content.push('\n');
    }
    new_content.push_str(&format!("![[{}]]\n", filename));

    fs::write(&resolved_note, new_content.as_bytes())?;
    Ok(vault.relative(&dest))
}
