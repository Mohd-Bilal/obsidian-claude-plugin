# obsidian-mcp

An MCP server that gives AI assistants direct filesystem access to an [Obsidian](https://obsidian.md) vault. Built with [FastMCP](https://github.com/jlowin/fastmcp).

## Features

### Vault
- **`vault_list`** — List all Obsidian vaults registered on this machine (name, path, open status, last used)
- **`vault_switch`** — Switch the active vault for the current session

### Notes
- **`note_create`** — Create a new note (optionally from a template)
- **`note_read`** — Read raw markdown content of a note
- **`note_update`** — Overwrite a note's content
- **`note_delete`** — Delete a note

### Frontmatter
- **`frontmatter_read`** — Read YAML frontmatter as a JSON object
- **`frontmatter_write`** — Merge or replace frontmatter fields

### Links
- **`link_insert_wikilink`** — Insert a `[[wikilink]]` (with optional alias) into a note
- **`link_get_backlinks`** — Find all notes that link to a given note
- **`link_get_forward_links`** — List all wikilinks inside a note

### Search
- **`search_notes`** — Full-text search across all notes, returns path, line number, and snippet

### Images
- **`image_embed`** — Embed an existing vault attachment into a note
- **`image_import`** — Copy an external image into the vault and embed it

### Canvas
- **`canvas_read`** — Read a `.canvas` file (nodes + edges)
- **`canvas_create`** — Create a new canvas file
- **`canvas_update`** — Overwrite a canvas's nodes and edges
- **`canvas_delete`** — Delete a canvas file

### Folders
- **`folder_create`** — Create a folder
- **`folder_rename`** — Rename or move a folder
- **`folder_delete`** — Delete a folder (`force=True` required if non-empty)

### Git (background)
- Automatically initialises a git repo in your vault on startup (if one doesn't exist)
- Optional periodic auto-commit via `GIT_AUTOCOMMIT_INTERVAL`

## Installation

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Mohd-Bilal/obsidian-mcp.git
cd obsidian-mcp
uv sync
```

## Configuration

The server discovers your vault automatically from `~/.config/obsidian/obsidian.json` (the currently open vault). You can override this with an environment variable.

| Environment Variable | Description | Default |
|---|---|---|
| `OBSIDIAN_VAULT_PATH` | Explicit path to vault root | Auto-discovered |
| `GIT_AUTOCOMMIT_INTERVAL` | Auto-commit interval e.g. `15m`, `1h`, `300s` | Disabled |
| `OBSIDIAN_TEMPLATES_FOLDER` | Folder name for templates inside the vault | `Templates` |

## Claude Desktop / Claude Code Setup

Add to `~/.config/claude/claude_desktop_config.json` or `.mcp.json`:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uv",
      "args": ["--directory", "/path/to/obsidian-mcp", "run", "obsidian-mcp"],
      "env": {
        "GIT_AUTOCOMMIT_INTERVAL": "15m"
      }
    }
  }
}
```

## Development

```bash
# Run tests
uv run pytest

# Run a specific test module
uv run pytest -v tests/test_notes.py
```

## License

MIT
