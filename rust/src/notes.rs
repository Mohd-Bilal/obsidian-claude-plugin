use std::fs;
use std::path::PathBuf;

use crate::errors::{ObsidianError, Result};
use crate::vault::Vault;

/// Get the content of a template by name from the templates folder.
fn get_template_content(vault: &Vault, templates_folder: &str, name: &str) -> Result<String> {
    let name_with_ext = if name.ends_with(".md") {
        name.to_string()
    } else {
        format!("{}.md", name)
    };
    let template_path = vault.root.join(templates_folder).join(&name_with_ext);
    if !template_path.exists() {
        return Err(ObsidianError::TemplateNotFound(format!(
            "Template not found: {:?} in {:?}",
            name_with_ext, templates_folder
        )));
    }
    Ok(fs::read_to_string(&template_path)?)
}

/// Create a new note. Returns its relative path.
pub fn create_note(
    vault: &Vault,
    path: &str,
    content: &str,
    template: Option<&str>,
    templates_folder: &str,
) -> Result<String> {
    let path_with_ext = if path.ends_with(".md") {
        path.to_string()
    } else {
        format!("{}.md", path)
    };

    let note_path: PathBuf = vault.root.join(&path_with_ext);
    if note_path.exists() {
        return Err(ObsidianError::NoteAlreadyExists(format!(
            "Note already exists: {}",
            path
        )));
    }

    if let Some(parent) = note_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let final_content = if let Some(tmpl_name) = template {
        let tmpl_content = get_template_content(vault, templates_folder, tmpl_name)?;
        format!("{}{}", tmpl_content, content)
    } else {
        content.to_string()
    };

    fs::write(&note_path, final_content.as_bytes())?;
    Ok(vault.relative(&note_path))
}

/// Read a note's content. Returns the UTF-8 text.
pub fn read_note(vault: &Vault, path: &str) -> Result<String> {
    let note_path = vault.resolve(path)?;
    Ok(fs::read_to_string(&note_path)?)
}

/// Overwrite an existing note's content. Returns its relative path.
pub fn update_note(vault: &Vault, path: &str, content: &str) -> Result<String> {
    let note_path = vault.resolve(path)?;
    fs::write(&note_path, content.as_bytes())?;
    Ok(vault.relative(&note_path))
}

/// Delete a note. Returns its former relative path.
pub fn delete_note(vault: &Vault, path: &str) -> Result<String> {
    let note_path = vault.resolve(path)?;
    let rel = vault.relative(&note_path);
    fs::remove_file(&note_path)?;
    Ok(rel)
}
