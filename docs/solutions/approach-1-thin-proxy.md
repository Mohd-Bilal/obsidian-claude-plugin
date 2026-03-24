# Approach 1 — Thin Proxy over Local REST API

## Summary

A minimal MCP server that acts as a thin, stateless proxy. Every MCP tool call
maps 1:1 to a Local REST API endpoint. No local state, no caching, no
abstraction layer beyond translating MCP tool calls into HTTP requests.

---

## How It Works

- Single Python package with one module per feature area (notes, canvas, search, git)
- Each MCP tool directly calls the corresponding Local REST API endpoint
- Vault path resolution (title vs relative path) handled per-request with a
  small helper
- Git operations run via `subprocess` calls to the `git` binary
- Auto-commit runs in a background `asyncio` task started at server startup
- Canvas files read/written as raw JSON via the REST API's file endpoint
- No local index, no caching, no state between requests

## Key Technical Decisions

- **MCP SDK:** `mcp` Python SDK (`pip install mcp`)
- **HTTP client:** `httpx` (async, fits asyncio MCP server loop)
- **Git:** subprocess calls to system `git`
- **Config:** `python-dotenv` for env vars; optional `config.toml` via `tomllib`
- **Canvas:** parsed with stdlib `json`; no third-party canvas library
- **Frontmatter:** `python-frontmatter` library for YAML parsing/writing

## Architecture

```
Claude (MCP client)
      │ stdio
      ▼
MCP Server (main.py)
      │
      ├── notes.py      → GET/POST/PUT/DELETE /vault/{path}
      ├── search.py     → GET /search/simple
      ├── links.py      → GET /vault/{path}/links (backlinks via search)
      ├── canvas.py     → GET/POST/PUT/DELETE /vault/{path}.canvas
      ├── images.py     → POST /vault/{attachments}/{file}
      ├── folders.py    → POST/PATCH/DELETE /vault/{folder}/
      ├── frontmatter.py → reads note, parses YAML, writes back
      ├── templates.py  → reads template, inserts content on create
      └── git.py        → subprocess git, asyncio auto-commit loop
            │
            ▼
      Local REST API (Obsidian plugin)
            │
            ▼
      Obsidian Vault (filesystem)
```

## Pros

- Simple to understand, debug, and extend
- Each tool maps directly to a REST call — easy to test individually
- No hidden state to reason about
- Minimal dependencies
- Failures are transparent — if the REST API returns an error, MCP surfaces it
- Easy to add new tools later without touching existing ones

## Cons

- Full-text search quality depends entirely on Local REST API's search
  (no control over ranking or context window)
- Backlinks require scanning all notes via search (REST API does not expose
  a dedicated backlinks endpoint) — O(n) over vault size
- No resilience if Local REST API is briefly unavailable (no retry logic)
- Git subprocess calls are synchronous by default — could block event loop
  on large commits (mitigated by running in executor)

## Complexity

Low

## Risk

Low — well-understood pattern; all components are stable libraries

## Key Unknowns

- Local REST API backlinks endpoint availability (may need to implement via
  search + parse)
- Template resolution: does Local REST API expose template content, or must
  we read the templates folder directly?
- Exact REST API endpoint for folder rename (may require move operation)
