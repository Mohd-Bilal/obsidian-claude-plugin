# Approach 3 — Hybrid (REST API Primary, Filesystem Fallback)

## Summary

Use the Local REST API as the primary interface when Obsidian is running, but
fall back to direct filesystem access for operations the REST API doesn't
support well (backlink scanning, template resolution, canvas CRUD, git).
A connection check at startup determines which mode is active.

---

## How It Works

- At startup, server attempts to connect to Local REST API
- If available: REST API used for note CRUD, search, frontmatter
- Regardless of REST API: filesystem used for canvas, git, backlinks, templates
  (these are either unsupported or poorly supported by the REST API)
- Vault path resolved from Obsidian config (`obsidian.json`) for filesystem ops
- Git always via subprocess (avoids `gitpython` dependency)
- Auto-commit via asyncio background task

## Key Technical Decisions

- **MCP SDK:** `mcp` Python SDK
- **HTTP client:** `httpx` (for REST API calls)
- **File I/O:** `pathlib` (for filesystem fallback + canvas + git + templates)
- **Frontmatter:** `python-frontmatter`
- **Git:** subprocess (simpler than `gitpython`, no extra dependency)
- **Canvas:** stdlib `json` via filesystem
- **Connection check:** `httpx` HEAD request to REST API on startup

## Architecture

```
Claude (MCP client)
      │ stdio
      ▼
MCP Server (main.py)
      │
      ├── connection.py  → startup check: REST API available?
      │
      ├── notes.py       → REST API (CRUD, search, frontmatter)
      │                     fallback: pathlib if REST unavailable
      ├── links.py       → filesystem scan always (REST has no backlinks endpoint)
      ├── canvas.py      → filesystem always (REST API has no canvas support)
      ├── images.py      → REST API for upload; pathlib for embed
      ├── folders.py     → REST API if available; pathlib fallback
      ├── templates.py   → filesystem always (read templates folder)
      └── git.py         → subprocess always
            │
      ┌─────┴──────┐
      ▼            ▼
  REST API     Filesystem
  (Obsidian)   (pathlib)
```

## Pros

- Best of both worlds: uses Obsidian's indexed search when available
- Canvas and backlinks handled correctly via filesystem (REST API gaps covered)
- Degrades gracefully if Obsidian is not running (filesystem fallback)
- Git stays simple (subprocess, no extra lib)
- Template resolution always reliable (read from disk)

## Cons

- **Two code paths** for some operations — doubles the testing surface
- Logic for "when to use REST vs filesystem" must be clearly documented
  and consistently applied — easy to get wrong
- Potential for subtle bugs where REST API and filesystem disagree
  (e.g. Obsidian has unsaved state)
- Higher complexity than either pure approach
- Connection check adds startup latency (small, but present)
- More dependencies than Approach 1 (both `httpx` and `pathlib` heavy use)

## Complexity

High — two interfaces to maintain, test, and keep consistent

## Risk

Medium-High — the two-path logic is the main risk; bugs could manifest
only when one path is active, making them harder to reproduce

## Key Unknowns

- Which REST API endpoints are reliable enough to trust as primary?
  (needs testing against actual Local REST API plugin version)
- Does filesystem fallback need to handle Obsidian's `.obsidian` cache
  to avoid stale index issues?
- How to handle the case where REST API goes offline mid-session
  (after startup check passed)?
