mod config;
mod errors;
mod vault;
mod notes;
mod frontmatter;
mod links;
mod search;
mod canvas;
mod images;
mod folders;

use std::sync::{Arc, Mutex};

use rmcp::{
    ServerHandler,
    model::{ServerCapabilities, ServerInfo},
    serve_server,
    tool,
    schemars,
};
use schemars::JsonSchema;
use serde::Deserialize;
use serde_json::{Map, Value};

use config::load_config;
use errors::ObsidianError;
use vault::{Vault, discover_vault_path, list_vaults};

/// Shared server state. Vault is protected by a Mutex because vault_switch
/// mutates the active vault.
#[derive(Clone)]
pub struct ObsidianServer {
    vault: Arc<Mutex<Vault>>,
    templates_folder: String,
}

impl ObsidianServer {
    fn new(vault: Vault, templates_folder: String) -> Self {
        Self {
            vault: Arc::new(Mutex::new(vault)),
            templates_folder,
        }
    }

    fn with_vault<F, T>(&self, f: F) -> Result<T, ObsidianError>
    where
        F: FnOnce(&Vault) -> Result<T, ObsidianError>,
    {
        let vault = self.vault.lock().expect("vault lock poisoned");
        f(&*vault)
    }

    fn with_vault_mut<F, T>(&self, f: F) -> Result<T, ObsidianError>
    where
        F: FnOnce(&mut Vault) -> Result<T, ObsidianError>,
    {
        let mut vault = self.vault.lock().expect("vault lock poisoned");
        f(&mut *vault)
    }
}

// ---------------------------------------------------------------------------
// Parameter structs — all derive Deserialize + JsonSchema for the #[tool] macro
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize, JsonSchema)]
pub struct NoteCreateParams {
    #[schemars(description = "Relative path inside the vault (with or without .md extension)")]
    pub path: String,
    #[serde(default)]
    #[schemars(description = "Initial text content")]
    pub content: String,
    #[schemars(description = "Optional template name to prepend")]
    pub template: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct NotePathParam {
    #[schemars(description = "Relative path or bare title of the note")]
    pub path: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct NoteUpdateParams {
    #[schemars(description = "Relative path or bare title of the note")]
    pub path: String,
    #[schemars(description = "New full content for the note")]
    pub content: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct FrontmatterWriteParams {
    #[schemars(description = "Relative path or bare title of the note")]
    pub path: String,
    #[schemars(description = "Key-value pairs to write into frontmatter (JSON object)")]
    pub fields: Value,
    #[serde(default)]
    #[schemars(description = "If true, replace all frontmatter; if false, merge")]
    pub replace: bool,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct InsertWikilinkParams {
    #[schemars(description = "Source note path")]
    pub source_path: String,
    #[schemars(description = "Target note title (used in the wikilink)")]
    pub target_title: String,
    #[schemars(description = "Optional display alias for the link")]
    pub alias: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct SearchParams {
    #[schemars(description = "Search query (regex or literal string)")]
    pub query: String,
    #[serde(default = "default_max_results")]
    #[schemars(description = "Maximum number of results to return (default 50)")]
    pub max_results: usize,
    #[serde(default)]
    #[schemars(description = "If true, search is case-sensitive")]
    pub case_sensitive: bool,
}

fn default_max_results() -> usize {
    50
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct CanvasCreateParams {
    #[schemars(description = "Relative path for the new canvas (with or without .canvas)")]
    pub path: String,
    #[schemars(description = "Initial nodes array (JSON array)")]
    pub nodes: Option<Value>,
    #[schemars(description = "Initial edges array (JSON array)")]
    pub edges: Option<Value>,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct CanvasPathParam {
    #[schemars(description = "Relative path of the canvas file")]
    pub path: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct CanvasUpdateParams {
    #[schemars(description = "Relative path of the canvas file")]
    pub path: String,
    #[schemars(description = "Full canvas JSON data to write")]
    pub data: Value,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct ImageEmbedParams {
    #[schemars(description = "Relative path or title of the note")]
    pub note_path: String,
    #[schemars(description = "Filename of the image in the attachments folder")]
    pub image_filename: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct ImageImportParams {
    #[schemars(description = "Relative path or title of the note")]
    pub note_path: String,
    #[schemars(description = "Absolute path of the external image to copy in")]
    pub external_image_path: String,
    #[serde(default = "default_attachments")]
    #[schemars(description = "Subfolder inside the vault to copy the image into (default: attachments)")]
    pub subfolder: String,
}

fn default_attachments() -> String {
    "attachments".to_string()
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct FolderPathParam {
    #[schemars(description = "Relative path of the folder inside the vault")]
    pub path: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct FolderRenameParams {
    #[schemars(description = "Current relative path of the folder")]
    pub old_path: String,
    #[schemars(description = "New relative path for the folder")]
    pub new_path: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct FolderDeleteParams {
    #[schemars(description = "Relative path of the folder to delete")]
    pub path: String,
    #[serde(default)]
    #[schemars(description = "If true, delete even if the folder is not empty")]
    pub force: bool,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct VaultSwitchParams {
    #[schemars(description = "Absolute path to the vault root (as returned by vault_list)")]
    pub path: String,
}

// ---------------------------------------------------------------------------
// Tool implementations using #[tool] macro
// Tools return Result<String, String> — Ok maps to success content,
// Err maps to error content (is_error = true).
// ---------------------------------------------------------------------------

#[tool(tool_box)]
impl ObsidianServer {
    // ---- Notes ----

    #[tool(description = "Create a new note in the vault. Returns the relative path of the created note.")]
    fn note_create(&self, #[tool(aggr)] params: NoteCreateParams) -> Result<String, String> {
        self.with_vault(|v| {
            notes::create_note(
                v,
                &params.path,
                &params.content,
                params.template.as_deref(),
                &self.templates_folder,
            )
        })
        .map_err(|e| e.to_string())
    }

    #[tool(description = "Read the full text content of a note.")]
    fn note_read(&self, #[tool(aggr)] params: NotePathParam) -> Result<String, String> {
        self.with_vault(|v| notes::read_note(v, &params.path))
            .map_err(|e| e.to_string())
    }

    #[tool(description = "Overwrite the content of an existing note. Returns the relative path.")]
    fn note_update(&self, #[tool(aggr)] params: NoteUpdateParams) -> Result<String, String> {
        self.with_vault(|v| notes::update_note(v, &params.path, &params.content))
            .map_err(|e| e.to_string())
    }

    #[tool(description = "Delete a note from the vault. Returns the deleted note's relative path.")]
    fn note_delete(&self, #[tool(aggr)] params: NotePathParam) -> Result<String, String> {
        self.with_vault(|v| notes::delete_note(v, &params.path))
            .map_err(|e| e.to_string())
    }

    // ---- Frontmatter ----

    #[tool(description = "Read YAML frontmatter metadata from a note. Returns a JSON object.")]
    fn frontmatter_read(&self, #[tool(aggr)] params: NotePathParam) -> Result<String, String> {
        let meta = self
            .with_vault(|v| frontmatter::read_frontmatter(v, &params.path))
            .map_err(|e| e.to_string())?;
        serde_json::to_string(&meta).map_err(|e| e.to_string())
    }

    #[tool(description = "Write frontmatter fields to a note. Use replace=true to replace all existing frontmatter.")]
    fn frontmatter_write(&self, #[tool(aggr)] params: FrontmatterWriteParams) -> Result<String, String> {
        let fields: Map<String, Value> = match params.fields {
            Value::Object(m) => m,
            _ => return Err("fields must be a JSON object".to_string()),
        };
        self.with_vault(|v| frontmatter::write_frontmatter(v, &params.path, &fields, params.replace))
            .map_err(|e| e.to_string())
    }

    // ---- Links ----

    #[tool(description = "Append a wikilink to the end of a note. Returns the note's relative path.")]
    fn link_insert_wikilink(&self, #[tool(aggr)] params: InsertWikilinkParams) -> Result<String, String> {
        self.with_vault(|v| {
            links::insert_wikilink(v, &params.source_path, &params.target_title, params.alias.as_deref())
        })
        .map_err(|e| e.to_string())
    }

    #[tool(description = "Find all notes that contain a wikilink pointing to the given note. Returns a JSON array of paths.")]
    fn link_get_backlinks(&self, #[tool(aggr)] params: NotePathParam) -> Result<String, String> {
        let backlinks = self
            .with_vault(|v| links::get_backlinks(v, &params.path))
            .map_err(|e| e.to_string())?;
        serde_json::to_string(&backlinks).map_err(|e| e.to_string())
    }

    #[tool(description = "Return all wikilinks referenced from the given note. Returns a JSON array of link targets.")]
    fn link_get_forward_links(&self, #[tool(aggr)] params: NotePathParam) -> Result<String, String> {
        let fwd = self
            .with_vault(|v| links::get_forward_links(v, &params.path))
            .map_err(|e| e.to_string())?;
        serde_json::to_string(&fwd).map_err(|e| e.to_string())
    }

    // ---- Search ----

    #[tool(description = "Search all notes for a query string. Returns a JSON array of {path, line_number, snippet} objects.")]
    fn search_notes_tool(&self, #[tool(aggr)] params: SearchParams) -> Result<String, String> {
        let results = self
            .with_vault(|v| search::search_notes(v, &params.query, params.max_results, params.case_sensitive))
            .map_err(|e| e.to_string())?;
        serde_json::to_string(&results).map_err(|e| e.to_string())
    }

    // ---- Canvas ----

    #[tool(description = "Read a .canvas file and return its JSON content.")]
    fn canvas_read(&self, #[tool(aggr)] params: CanvasPathParam) -> Result<String, String> {
        let data = self
            .with_vault(|v| canvas::read_canvas(v, &params.path))
            .map_err(|e| e.to_string())?;
        serde_json::to_string_pretty(&data).map_err(|e| e.to_string())
    }

    #[tool(description = "Create a new .canvas file with optional nodes and edges.")]
    fn canvas_create(&self, #[tool(aggr)] params: CanvasCreateParams) -> Result<String, String> {
        self.with_vault(|v| canvas::create_canvas(v, &params.path, params.nodes, params.edges))
            .map_err(|e| e.to_string())
    }

    #[tool(description = "Overwrite a .canvas file with new JSON data.")]
    fn canvas_update(&self, #[tool(aggr)] params: CanvasUpdateParams) -> Result<String, String> {
        self.with_vault(|v| canvas::update_canvas(v, &params.path, &params.data))
            .map_err(|e| e.to_string())
    }

    #[tool(description = "Delete a .canvas file. Returns the deleted file's relative path.")]
    fn canvas_delete(&self, #[tool(aggr)] params: CanvasPathParam) -> Result<String, String> {
        self.with_vault(|v| canvas::delete_canvas(v, &params.path))
            .map_err(|e| e.to_string())
    }

    // ---- Images ----

    #[tool(description = "Embed an existing attachment image in a note by appending ![[filename]].")]
    fn image_embed(&self, #[tool(aggr)] params: ImageEmbedParams) -> Result<String, String> {
        self.with_vault(|v| images::embed_image(v, &params.note_path, &params.image_filename))
            .map_err(|e| e.to_string())
    }

    #[tool(description = "Import an external image file into the vault and embed it in a note.")]
    fn image_import(&self, #[tool(aggr)] params: ImageImportParams) -> Result<String, String> {
        self.with_vault(|v| {
            images::import_image(v, &params.note_path, &params.external_image_path, &params.subfolder)
        })
        .map_err(|e| e.to_string())
    }

    // ---- Folders ----

    #[tool(description = "Create a new folder inside the vault.")]
    fn folder_create(&self, #[tool(aggr)] params: FolderPathParam) -> Result<String, String> {
        self.with_vault(|v| folders::create_folder(v, &params.path))
            .map_err(|e| e.to_string())
    }

    #[tool(description = "Rename or move a folder to a new path inside the vault.")]
    fn folder_rename(&self, #[tool(aggr)] params: FolderRenameParams) -> Result<String, String> {
        self.with_vault(|v| folders::rename_folder(v, &params.old_path, &params.new_path))
            .map_err(|e| e.to_string())
    }

    #[tool(description = "Delete a folder. Set force=true to delete non-empty folders.")]
    fn folder_delete(&self, #[tool(aggr)] params: FolderDeleteParams) -> Result<String, String> {
        self.with_vault(|v| folders::delete_folder(v, &params.path, params.force))
            .map_err(|e| e.to_string())
    }

    // ---- Vault ----

    #[tool(description = "List all Obsidian vaults registered on this machine. Returns a JSON array.")]
    fn vault_list(&self) -> Result<String, String> {
        let vault_root = {
            let vault = self.vault.lock().expect("vault lock poisoned");
            vault.root.to_string_lossy().to_string()
        };
        let mut vaults = list_vaults();
        for v in &mut vaults {
            v.active = v.path == vault_root;
        }
        serde_json::to_string(&vaults).map_err(|e| e.to_string())
    }

    #[tool(description = "Switch the active vault for this session. Returns the new vault name.")]
    fn vault_switch(&self, #[tool(aggr)] params: VaultSwitchParams) -> Result<String, String> {
        use std::path::PathBuf;
        let vault_path = PathBuf::from(&params.path);
        if !vault_path.exists() {
            return Err(format!("Vault path does not exist: {}", params.path));
        }
        if !vault_path.is_dir() {
            return Err(format!("Vault path is not a directory: {}", params.path));
        }
        let vault_name = vault_path
            .file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_else(|| params.path.clone());

        self.with_vault_mut(|v| {
            *v = Vault::new(vault_path);
            Ok(())
        })
        .map_err(|e| e.to_string())?;

        Ok(format!("Switched to vault: {}", vault_name))
    }
}

#[tool(tool_box)]
impl ServerHandler for ObsidianServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            instructions: Some(
                "Obsidian vault MCP server — exposes note, folder, canvas, and link management tools."
                    .into(),
            ),
            capabilities: ServerCapabilities::builder().enable_tools().build(),
            ..Default::default()
        }
    }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = load_config();

    let vault_root = if let Some(p) = config.vault_path {
        p
    } else {
        discover_vault_path()?
    };
    let vault = Vault::new(vault_root);

    let server = ObsidianServer::new(vault, config.templates_folder);

    let transport = rmcp::transport::io::stdio();
    let running = serve_server(server, transport).await?;
    running.waiting().await?;

    Ok(())
}
