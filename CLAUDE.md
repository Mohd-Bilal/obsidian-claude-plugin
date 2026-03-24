# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test module
uv run pytest -v tests/test_notes.py

# Run a single test
uv run pytest -v tests/test_notes.py::test_create_note

# Run the server (stdio transport)
uv run obsidian-mcp
```

## Architecture

This is an MCP server built with [FastMCP](https://github.com/jlowin/fastmcp) that exposes Obsidian vault operations as tools over stdio.

### Startup flow

`server.py` → `lifespan()` → loads `Config` → calls `discover_vault_path()` → constructs `Vault` → optionally starts `auto_commit_loop` background task → yields `AppContext(vault, config)` into every tool's `ctx.request_context.lifespan_context`.

### Tool registration pattern

Each domain module (`notes.py`, `frontmatter.py`, `links.py`, etc.) exposes two layers:
1. **Pure functions** (e.g. `create_note(vault, ...)`) — sync, no MCP dependency, directly tested.
2. **`register_tools(mcp)`** — wraps the pure functions in `@mcp.tool()` async handlers that extract `vault`/`config` from context and convert domain errors to `ToolError`.

`server.py` imports each module and calls `register_tools(mcp)` at import time. The two vault-level tools (`vault_list`, `vault_switch`) are defined directly in `server.py`.

### Vault discovery (`vault.py`)

`OBSIDIAN_CONFIG_PATH` is resolved at import time via `_obsidian_config_path()`: `~/Library/Application Support/obsidian/obsidian.json` on macOS, `~/.config/obsidian/obsidian.json` on Linux. Discovery order: `OBSIDIAN_VAULT_PATH` env var → `obsidian.json` (open vault preferred, else highest `ts`).

### Key files

| File | Role |
|------|------|
| `src/obsidian_mcp/server.py` | FastMCP app, lifespan, vault_list/vault_switch tools |
| `src/obsidian_mcp/vault.py` | `Vault` class, `discover_vault_path()`, `list_vaults()` |
| `src/obsidian_mcp/config.py` | `load_config()` from env vars |
| `src/obsidian_mcp/errors.py` | Domain exception hierarchy |
| `tests/conftest.py` | `vault` and `vault_dir` fixtures; sets `OBSIDIAN_VAULT_PATH` env var |

### Error handling convention

Domain errors (`NoteNotFoundError`, `NoteAlreadyExistsError`, etc.) are raised from pure functions and caught in `register_tools` wrappers, which re-raise as `ToolError` for the MCP client.
