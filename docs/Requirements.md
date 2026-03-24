# Requirements: MANUAL-obsidian-mcp — Obsidian MCP Server

**Status:** Finalised
**Date:** 2026-03-24
**Ticket:** MANUAL-obsidian-mcp

---

## Summary

An MCP server written in Python (using `uv`) that gives AI assistants full programmatic access to an Obsidian vault via stdio transport. It connects to Obsidian through the Local REST API community plugin and exposes tools for managing notes, links, images, canvas files, folders, templates, search, frontmatter, and git version control.

---

## Acceptance Criteria

Each criterion is testable and unambiguous.

| ID | Criterion | Notes |
|----|-----------|-------|
| AC-1 | Server runs as a stdio MCP process launchable by Claude Desktop/Code | Transport: stdio only |
| AC-2 | Server connects to Obsidian via the Local REST API plugin | Obsidian must be running with the plugin active |
| AC-3 | Notes can be created, read, updated, and deleted | Full CRUD |
| AC-4 | WikiLinks can be created programmatically in note content | Inserts `[[WikiLink]]` syntax |
| AC-5 | Backlinks and forward links for a given note can be queried | Returns list of linking/linked notes |
| AC-6 | Images already in the vault can be embedded in notes | Inserts `![[image.png]]` syntax |
| AC-7 | External image files can be copied into the vault and embedded | Copies file then inserts embed syntax |
| AC-8 | Canvas files can be read (nodes and edges returned) | Returns structured canvas data |
| AC-9 | Canvas files can be created and modified (add/move nodes, create connections) | Full CRUD on `.canvas` files |
| AC-10 | Canvas files can be deleted | |
| AC-11 | Full-text search works across all notes in the vault | Returns matching notes with context |
| AC-12 | YAML frontmatter can be read from any note | Returns key-value pairs |
| AC-13 | YAML frontmatter can be written to any note (tags, date, aliases, custom fields) | Merges or replaces fields |
| AC-14 | Attempting to create a note that already exists returns an error | No silent overwrite |
| AC-15 | Note paths are accepted as Obsidian note title OR relative vault path | e.g. `"My Note"` or `"folder/My Note.md"` |
| AC-16 | Referencing a missing attachment returns a clear error message | Not silently ignored |
| AC-17 | Folders can be created, renamed, and deleted | |
| AC-18 | Obsidian templates can be inserted when creating a note | Uses core Templates plugin |
| AC-19 | The vault is git-initialised automatically on first use | Runs `git init` if no repo present |
| AC-20 | Auto-commit interval is configurable via env variable or config file at startup | e.g. `GIT_AUTOCOMMIT_INTERVAL=15m` |
| AC-21 | No authentication is required to use the MCP server | Trusted local environment |

---

## Edge Cases

| ID | Edge Case | Expected Behaviour |
|----|-----------|-------------------|
| EC-1 | Note already exists when create is called | Return error; do not overwrite |
| EC-2 | Note references an attachment that does not exist in vault | Return error with clear message identifying the missing file |
| EC-3 | Obsidian is not running or Local REST API plugin is inactive | Return clear connection error on tool call |
| EC-4 | Note path supplied as title contains spaces or special characters | Handled correctly; resolved to correct vault path |
| EC-5 | Note path supplied as relative path with subdirectories | Resolved correctly from vault root |
| EC-6 | Auto-commit fires when there are no changes | No-op; no empty commit created |
| EC-7 | Git is not installed on the host machine | Return clear error on git-related tool calls |
| EC-8 | Canvas file is malformed JSON | Return parse error with file path |

---

## Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Language | Python, managed with `uv` |
| Transport | stdio (MCP standard) |
| Compatibility | Works with Claude Desktop and Claude Code as MCP client |
| Obsidian dependency | Requires Obsidian running with Local REST API plugin active |
| Git dependency | Requires `git` installed on host machine for version control features |
| Security | No auth required; designed for trusted local use only |
| Configuration | Auto-commit interval and any connection settings via env variables or config file |

---

## Scope

### In Scope
- stdio MCP transport
- Note CRUD (create, read, update, delete)
- WikiLink creation and link graph queries (backlinks, forward links)
- Image embedding (vault-local and external upload)
- Canvas file CRUD (`.canvas` format)
- Full-text search across vault
- YAML frontmatter read/write
- Folder management (create, rename, delete)
- Template insertion on note creation (core Obsidian Templates plugin)
- Git initialisation on first use
- Configurable auto-commit

### Out of Scope
- HTTP/SSE transport
- Multiple vault support
- Plugin-dependent features (Dataview, Tasks, Templater, etc.)
- Real-time vault watching / change notifications
- Git operations beyond init and auto-commit (no push, pull, branch, diff, merge via MCP)
- Authentication / access control
- Obsidian UI automation

---

## Assumptions

1. Obsidian must be running with the Local REST API community plugin active for all vault operations to function. *(agreed: Q17)*
2. Auto-commit interval is provided via an environment variable or config file at server startup; there is no default interval — it must be explicitly set. *(agreed: Q20)*
3. `git` must be installed and available on `PATH` on the host machine for git features to work. *(agreed: Q19)*
4. Only core Obsidian features are targeted; community plugin integrations (beyond Local REST API as the transport layer) are out of scope. *(agreed: Q12)*
5. Single vault only; vault location is auto-discovered from Obsidian's own configuration. *(agreed: Q3)*

---

## Clarification Log

- Q1 → stdio transport chosen; HTTP/SSE explicitly out of scope for this version
- Q2 → full CRUD selected including delete
- Q3 → vault auto-discovered from Obsidian config; multiple vault support out of scope
- Q4 → both WikiLink creation AND link graph queries (backlinks/forward links) in scope
- Q5 → both embed existing vault images AND copy-in external images in scope
- Q6 → full CRUD on canvas files selected
- Q7 → full-text search only (tag and frontmatter search out of scope for now)
- Q8 → frontmatter read and write both in scope
- Q9 → create conflict returns error (no silent overwrite)
- Q10 → both title and relative path accepted as input
- Q11 → missing attachment returns clear error (not a warning, not silent)
- Q12 → core Obsidian features only; no plugin-dependent features
- Q13 → folder management (create, rename, delete) in scope
- Q14 → template insertion on note creation in scope
- Q15 → no real-time watching; purely request-response
- Q16 → Python with uv as package manager
- Q17 → Local REST API plugin as Obsidian interface (requires Obsidian running)
- Q18 → no authentication; trusted local environment
- Q19 → git init on first use + configurable auto-commit; no other git operations via MCP
- Q20 → auto-commit interval is configurable via env/config
