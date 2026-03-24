# Approach 2 — Direct Filesystem Access (No Obsidian Plugin Required)

## Summary

Bypass the Local REST API plugin entirely. The MCP server reads and writes
vault files directly on the filesystem using Python's standard file I/O.
Obsidian does not need to be running. The server discovers the vault path
from Obsidian's `obsidian.json` config file.

---

## How It Works

- Vault discovered by reading `~/.config/obsidian/obsidian.json` (Linux) or
  equivalent on macOS/Windows
- Notes are `.md` files; canvas files are `.json` files — read/written directly
- WikiLink parsing done with regex; backlinks found by scanning all `.md` files
- Full-text search implemented with Python's `os.walk` + string matching
  (or optionally `whoosh` for indexed search)
- Frontmatter parsed with `python-frontmatter`
- Git operations via `gitpython` library (no subprocess)
- Auto-commit on a background `asyncio` task using `gitpython`'s repo API

## Key Technical Decisions

- **MCP SDK:** `mcp` Python SDK
- **File I/O:** stdlib `pathlib` + `shutil`
- **Frontmatter:** `python-frontmatter`
- **Search:** `whoosh` (indexed) or stdlib walk (unindexed, simpler)
- **Git:** `gitpython`
- **Canvas:** stdlib `json`
- **Vault discovery:** parse `obsidian.json` from Obsidian's config dir

## Architecture

```
Claude (MCP client)
      │ stdio
      ▼
MCP Server (main.py)
      │
      ├── vault.py      → discovers vault path from obsidian.json
      ├── notes.py      → pathlib read/write .md files
      ├── search.py     → walks vault, string/regex match
      ├── links.py      → regex scan all notes for [[links]]
      ├── canvas.py     → pathlib read/write .canvas JSON files
      ├── images.py     → shutil.copy + pathlib
      ├── folders.py    → pathlib mkdir/rename/rmdir
      ├── frontmatter.py → python-frontmatter
      ├── templates.py  → reads templates folder, inserts on create
      └── git.py        → gitpython Repo API + asyncio auto-commit
            │
            ▼
      Vault filesystem (direct)
```

## Pros

- Obsidian does not need to be running — works even when Obsidian is closed
- No dependency on a community plugin (Local REST API)
- Full control over file operations — no API limitations
- Backlink scanning is straightforward (regex walk)
- Git via `gitpython` is cleaner than subprocess and async-friendly
- Template resolution is trivial (read from templates folder directly)

## Cons

- **Bypasses Obsidian's internal state** — writes may not be reflected in
  Obsidian's cache until it re-indexes (can cause temporary inconsistency)
- **No real-time sync with Obsidian UI** — if Obsidian has unsaved changes
  in memory, direct file writes could conflict
- Backlink scan is O(n) over all files on every query (no index unless
  `whoosh` is added, which adds complexity)
- `whoosh` adds a persistent index that can go stale
- `gitpython` is a heavier dependency; has known issues with some edge cases
- Vault path discovery logic must handle Linux/macOS/Windows config paths

## Complexity

Medium — direct file I/O is simple, but cache/sync risk with Obsidian
requires careful documentation and edge case handling

## Risk

Medium — direct filesystem writes while Obsidian is open risk
cache inconsistency; requires user to be aware of this limitation

## Key Unknowns

- How quickly does Obsidian re-index after external file changes?
- Does `gitpython` handle large vaults (thousands of files) efficiently?
- Obsidian config file location on all target platforms (Linux confirmed;
  macOS/Windows paths differ)
