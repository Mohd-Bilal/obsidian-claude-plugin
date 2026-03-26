# obsidian-mcp

An MCP server that gives AI assistants direct filesystem access to an [Obsidian](https://obsidian.md) vault. Built in Rust using [rmcp](https://github.com/modelcontextprotocol/rust-sdk).

---

## Claude Code Plugin

The easiest way to use obsidian-mcp is via the bundled **Claude Code plugin**, which adds ready-to-use skills and agents on top of the MCP server.

### What's included

| Component | What it does |
|-----------|--------------|
| **`obsidian-writer` skill** | Creates or updates structured Obsidian notes — index note with Mermaid diagram, deep-dive notes, wikilinks, and a canvas map |
| **`deep-researcher` skill** | Researches a topic from the web and produces a structured Research Brief (key concepts, subtopics, sources) |
| **`obsidian-canvas` skill** | Builds or updates an Obsidian canvas that visually maps notes as linked nodes |
| **`obsidian-writer` agent** | Autonomous agent: given a topic, writes and maintains vault notes following the obsidian-writer skill |
| **`research-and-save` agent** | Autonomous agent: researches a topic from the web, then writes structured notes + canvas to the vault |

### Plugin setup

**Step 1 — Install the MCP server** (see [Installation](#installation) below).

**Step 2 — Install the plugin into Claude Code:**

```bash
claude plugin add https://github.com/Mohd-Bilal/obsidian-mcp --subdir plugin
```

Or, if you have the repo cloned locally:

```bash
claude plugin add /path/to/obsidian-mcp/plugin
```

**Step 3 — Verify:**

```bash
claude plugin list
```

You should see `obsidian` (v1.3.0) listed.

### Using the skills

Once installed, the skills are available in any Claude Code session:

```
# Write notes about a topic you already know
"create obsidian notes about the CAP theorem"

# Research a topic from the web and save to vault
"research how transformers work and save to obsidian"

# Update existing notes with new information
"add a section on RAFT consensus to my distributed systems notes"
```

The `research-and-save` agent triggers automatically on phrases like:
- *"research X and save"*
- *"look up X and add to obsidian"*
- *"find out about X and write notes"*

### Plugin structure

```
plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── skills/
│   ├── obsidian-writer/     # Note writing conventions
│   ├── obsidian-canvas/     # Canvas layout conventions
│   └── deep-researcher/     # Web research → structured brief
└── agents/
    ├── obsidian-writer.md   # Vault writing agent
    └── research-and-save.md # Research + write agent
```

---

## MCP Server

### Features

#### Vault
- **`vault_list`** — List all Obsidian vaults registered on this machine (name, path, open status, last used)
- **`vault_switch`** — Switch the active vault for the current session

#### Notes
- **`note_create`** — Create a new note (optionally from a template)
- **`note_read`** — Read raw markdown content of a note
- **`note_update`** — Overwrite a note's content
- **`note_delete`** — Delete a note

#### Frontmatter
- **`frontmatter_read`** — Read YAML frontmatter as a JSON object
- **`frontmatter_write`** — Merge or replace frontmatter fields

#### Links
- **`link_insert_wikilink`** — Insert a `[[wikilink]]` (with optional alias) into a note
- **`link_get_backlinks`** — Find all notes that link to a given note
- **`link_get_forward_links`** — List all wikilinks inside a note

#### Search
- **`search_notes`** — Full-text search across all notes, returns path, line number, and snippet

#### Images
- **`image_embed`** — Embed an existing vault attachment into a note
- **`image_import`** — Copy an external image into the vault and embed it

#### Canvas
- **`canvas_read`** — Read a `.canvas` file (nodes + edges)
- **`canvas_create`** — Create a new canvas file
- **`canvas_update`** — Overwrite a canvas's nodes and edges
- **`canvas_delete`** — Delete a canvas file

#### Folders
- **`folder_create`** — Create a folder
- **`folder_rename`** — Rename or move a folder
- **`folder_delete`** — Delete a folder (`force=true` required if non-empty)

#### Git (background)
- Automatically initialises a git repo in your vault on startup (if one doesn't exist)
- Optional periodic auto-commit via `GIT_AUTOCOMMIT_INTERVAL`

### Installation

Requires [Rust](https://rustup.rs/) (stable toolchain).

```bash
git clone https://github.com/Mohd-Bilal/obsidian-mcp.git
cd obsidian-mcp/rust
cargo build --release
```

The compiled binary is at `rust/target/release/obsidian-mcp`.

### Configuration

The server discovers your vault automatically from `~/.config/obsidian/obsidian.json` on Linux or `~/Library/Application Support/obsidian/obsidian.json` on macOS (whichever vault was most recently open). You can override this with an environment variable.

| Environment Variable | Description | Default |
|---|---|---|
| `OBSIDIAN_VAULT_PATH` | Explicit path to vault root | Auto-discovered |
| `GIT_AUTOCOMMIT_INTERVAL` | Auto-commit interval e.g. `15m`, `1h`, `300s` | Disabled |
| `OBSIDIAN_TEMPLATES_FOLDER` | Folder name for templates inside the vault | `Templates` |

### Claude Desktop / Claude Code Setup

Add to `~/.config/claude/claude_desktop_config.json` or `.mcp.json`:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "/path/to/obsidian-mcp/rust/target/release/obsidian-mcp",
      "env": {
        "GIT_AUTOCOMMIT_INTERVAL": "15m"
      }
    }
  }
}
```

### Development

```bash
cd rust

# Build
cargo build

# Run tests
cargo test

# Run the server directly (stdio transport)
cargo run
```

## License

MIT
