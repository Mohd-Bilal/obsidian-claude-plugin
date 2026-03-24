# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
cd rust

# Build
cargo build

# Run all tests
cargo test

# Run a single test
cargo test test_create_note

# Run the server (stdio transport)
cargo run
```

## Architecture

This is an MCP server built in Rust using [rmcp](https://github.com/modelcontextprotocol/rust-sdk) that exposes Obsidian vault operations as tools over stdio.

### Startup flow

`main.rs` → `load_config()` → `discover_vault_path()` → constructs `Vault` → spawns optional `auto_commit_loop` background task → starts `serve_server` on stdio transport.

### Tool registration pattern

Each domain module (`notes.rs`, `frontmatter.rs`, `links.rs`, etc.) exposes pure functions (e.g. `create_note(vault, ...)`). Tool handlers are defined in `main.rs` via the `#[tool]` macro on `ObsidianServer`, which holds shared state behind `Arc<Mutex<Vault>>`. Handlers call `with_vault` / `with_vault_mut` to access the vault and map `ObsidianError` to a `String` error.

### Vault discovery (`vault.rs`)

`OBSIDIAN_CONFIG_PATH` is resolved via `_obsidian_config_path()`: `~/Library/Application Support/obsidian/obsidian.json` on macOS, `~/.config/obsidian/obsidian.json` on Linux. Discovery order: `OBSIDIAN_VAULT_PATH` env var → `obsidian.json` (open vault preferred, else highest `ts`).

### Key files

| File | Role |
|------|------|
| `rust/src/main.rs` | `ObsidianServer`, all `#[tool]` handlers, entry point |
| `rust/src/vault.rs` | `Vault` struct, `discover_vault_path()`, `list_vaults()` |
| `rust/src/config.rs` | `load_config()` from env vars |
| `rust/src/errors.rs` | `ObsidianError` enum |
| `rust/src/git.rs` | `ensure_git_repo()`, `auto_commit_loop()` |

### Error handling convention

Domain errors are represented by `ObsidianError` variants, returned from pure functions. Tool handlers convert them to `String` via `.map_err(|e| e.to_string())`, which rmcp surfaces as an error response to the MCP client.
