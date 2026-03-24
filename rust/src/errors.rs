use thiserror::Error;

#[derive(Debug, Error)]
pub enum ObsidianError {
    #[error("Vault not found: {0}")]
    VaultNotFound(String),

    #[error("Note not found: {0}")]
    NoteNotFound(String),

    #[error("Note already exists: {0}")]
    NoteAlreadyExists(String),

    #[error("Attachment not found: {0}")]
    AttachmentNotFound(String),

    #[error("Canvas parse error: {0}")]
    CanvasParseError(String),

    #[error("Template not found: {0}")]
    TemplateNotFound(String),

    #[error("Folder not found: {0}")]
    FolderNotFound(String),

    #[error("Folder not empty: {0}")]
    FolderNotEmpty(String),

    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, ObsidianError>;
