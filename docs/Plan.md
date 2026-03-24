# Implementation Plan: MANUAL-obsidian-mcp — Obsidian MCP Server

**Status:** Ready for implementation
**Date:** 2026-03-24
**Ticket:** MANUAL-obsidian-mcp
**Approach:** Approach 2 — Direct Filesystem Access

---

## 1. Project Structure

```
obsidian-mcp/
├── pyproject.toml
├── README.md
├── .env.example
├── src/
│   └── obsidian_mcp/
│       ├── __init__.py
│       ├── server.py          # FastMCP app + lifespan + entry point
│       ├── vault.py           # Vault discovery from obsidian.json
│       ├── config.py          # Env var / config loading
│       ├── notes.py           # Note CRUD MCP tools
│       ├── links.py           # WikiLink insertion + backlink/forward-link query tools
│       ├── images.py          # Image embed + external import tools
│       ├── canvas.py          # Canvas file CRUD tools
│       ├── folders.py         # Folder management tools
│       ├── frontmatter.py     # Frontmatter read/write tools
│       ├── search.py          # Full-text search tool
│       ├── templates.py       # Template insertion helper
│       ├── git.py             # Git subprocess wrapper + auto-commit loop
│       └── errors.py          # Shared error types and helpers
├── tests/
│   ├── conftest.py            # Temp vault fixture
│   ├── test_vault.py
│   ├── test_notes.py
│   ├── test_links.py
│   ├── test_images.py
│   ├── test_canvas.py
│   ├── test_folders.py
│   ├── test_frontmatter.py
│   ├── test_search.py
│   ├── test_templates.py
│   └── test_git.py
└── docs/
    ├── Requirements.md
    ├── Plan.md
    ├── solutions/
    └── decisions/
```

---

## 2. Dependencies — `pyproject.toml`

```toml
[project]
name = "obsidian-mcp"
version = "0.1.0"
description = "MCP server for direct filesystem access to an Obsidian vault"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.26.0",
    "python-frontmatter>=1.1.0",
    "pyyaml>=6.0.2",
]

[project.scripts]
obsidian-mcp = "obsidian_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/obsidian_mcp"]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-mock>=3.14.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Rationale:**
- `mcp>=1.26.0` — FastMCP class with lifespan support
- `python-frontmatter>=1.1.0` — YAML frontmatter parse/write; handles round-trip without destroying content
- No `gitpython` — subprocess only (override decision)
- No `whoosh` — stdlib `os.walk` + string matching (simpler, no stale index risk)

---

## 3. Implementation Phases

### Phase 1 — Skeleton and Vault Discovery
1. Create `pyproject.toml` and `src/obsidian_mcp/__init__.py`
2. Implement `config.py` — env var loading
3. Implement `vault.py` — obsidian.json parsing, vault path resolution
4. Implement `errors.py` — shared error helpers
5. Implement `server.py` — bare FastMCP app, no tools yet
6. Verify: `uv run obsidian-mcp` launches without error

### Phase 2 — Note CRUD
1. Implement `notes.py`
2. Write `tests/test_notes.py` against temp vault
3. Verify AC-3, AC-14, AC-15, EC-1, EC-4, EC-5

### Phase 3 — Frontmatter
1. Implement `frontmatter.py`
2. Write `tests/test_frontmatter.py`
3. Verify AC-12, AC-13

### Phase 4 — Links
1. Implement `links.py`
2. Write `tests/test_links.py`
3. Verify AC-4, AC-5

### Phase 5 — Search
1. Implement `search.py`
2. Write `tests/test_search.py`
3. Verify AC-11

### Phase 6 — Images
1. Implement `images.py`
2. Write `tests/test_images.py`
3. Verify AC-6, AC-7, AC-16, EC-2

### Phase 7 — Folders
1. Implement `folders.py`
2. Write `tests/test_folders.py`
3. Verify AC-17

### Phase 8 — Templates
1. Implement `templates.py`
2. Wire into `create_note` in `notes.py`
3. Write `tests/test_templates.py`
4. Verify AC-18

### Phase 9 — Canvas
1. Implement `canvas.py`
2. Write `tests/test_canvas.py`
3. Verify AC-8, AC-9, AC-10, EC-8

### Phase 10 — Git
1. Implement `git.py`
2. Wire lifespan into `server.py`
3. Write `tests/test_git.py`
4. Verify AC-19, AC-20, EC-6, EC-7

### Phase 11 — Integration and Acceptance
1. Run full test suite
2. Test with real vault
3. Add Claude Desktop / Claude Code config entry
4. Fix any gaps found against acceptance criteria

---

## 4. Module Breakdown

### `config.py`
**Responsibilities:** Load and validate all configuration from environment variables at startup.

```python
@dataclass
class Config:
    vault_path: Path | None       # None = use discovery
    git_autocommit_interval: int | None   # seconds; None = disabled
    templates_folder: str         # default "Templates"

def load_config() -> Config: ...
```

**Env vars:**
- `OBSIDIAN_VAULT_PATH` — overrides vault discovery (required for tests)
- `GIT_AUTOCOMMIT_INTERVAL` — e.g. `"15m"`, `"300s"`, `"1h"`. If absent, auto-commit is disabled (no default).
- `OBSIDIAN_TEMPLATES_FOLDER` — folder name inside vault (default: `"Templates"`)

---

### `vault.py`
**Responsibilities:** Discover vault path from Obsidian config; expose a `Vault` class with path helpers.

```python
OBSIDIAN_CONFIG_PATH = Path.home() / ".config" / "obsidian" / "obsidian.json"

def discover_vault_path() -> Path: ...

class Vault:
    def __init__(self, root: Path): ...
    def resolve(self, note_ref: str) -> Path: ...  # See Section 7
    def exists(self, path: Path) -> bool: ...
    def all_markdown_files(self) -> Iterator[Path]: ...
    def attachments_dir(self) -> Path: ...  # vault_root/attachments, created if absent
```

---

### `errors.py`

```python
class VaultNotFoundError(Exception): ...
class NoteNotFoundError(Exception): ...
class NoteAlreadyExistsError(Exception): ...
class AttachmentNotFoundError(Exception): ...
class CanvasParseError(Exception): ...
class GitNotAvailableError(Exception): ...
class TemplateNotFoundError(Exception): ...
class FolderNotFoundError(Exception): ...
class FolderNotEmptyError(Exception): ...
```

All tool handlers catch domain exceptions and re-raise as `ToolError(str(e))`.

---

### `server.py`
**Responsibilities:** Create FastMCP app, register all tools, configure lifespan.

```python
@asynccontextmanager
async def lifespan(app: FastMCP):
    config = load_config()
    vault = Vault(discover_vault_path())
    ensure_git_repo(vault.root)       # AC-19
    app.state.vault = vault
    app.state.config = config

    task = None
    if config.git_autocommit_interval:
        task = asyncio.create_task(
            auto_commit_loop(vault.root, config.git_autocommit_interval)
        )
    try:
        yield
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

mcp = FastMCP("obsidian-mcp", lifespan=lifespan)

def main():
    mcp.run(transport="stdio")
```

Sub-modules import `mcp` from `server.py` and use `@mcp.tool()`.

---

### `notes.py`
MCP tools: `note_create`, `note_read`, `note_update`, `note_delete`

---

### `frontmatter.py`
MCP tools: `frontmatter_read`, `frontmatter_write`

Uses `python-frontmatter`. Writing merges incoming fields into existing metadata unless `replace=True`.

---

### `links.py`
MCP tools: `link_insert_wikilink`, `link_get_backlinks`, `link_get_forward_links`

Key regex: `WIKILINK_RE = re.compile(r'\[\[([^\[\]]+)\]\]')`

Backlinks: `os.walk` all `.md` files, match regex, collect filenames linking to target.

---

### `search.py`
MCP tool: `search_notes`

`os.walk` + case-insensitive substring/regex match. Returns `{path, line_number, snippet}` list. Default max 50 results.

---

### `images.py`
MCP tools: `image_embed`, `image_import`

`image_import` uses `shutil.copy2` into `vault.root/attachments` then appends `![[filename]]` to note.

---

### `canvas.py`
MCP tools: `canvas_read`, `canvas_create`, `canvas_update`, `canvas_delete`

See Section 9 for canvas format.

---

### `folders.py`
MCP tools: `folder_create`, `folder_rename`, `folder_delete`

`folder_delete` requires `force=True` if non-empty.

---

### `templates.py`
Internal helpers only (not MCP tools directly):

```python
def list_templates(vault: Vault, templates_folder: str) -> list[str]: ...
def get_template_content(vault: Vault, templates_folder: str, name: str) -> str: ...
```

Templates are `.md` files inside `vault.root / templates_folder`. No variable substitution.

---

### `git.py`
MCP tools: none (internal + lifespan only)

```python
def run_git(vault_root: Path, *args: str) -> subprocess.CompletedProcess: ...
def ensure_git_repo(vault_root: Path) -> None: ...
def commit_all(vault_root: Path, message: str) -> bool: ...
async def auto_commit_loop(vault_root: Path, interval_seconds: int) -> None: ...
```

---

## 5. MCP Tool Definitions

### Notes

| Tool | Parameters | Returns |
|------|------------|---------|
| `note_create` | `path: str`, `content: str = ""`, `template: str \| None = None` | vault-relative path |
| `note_read` | `path: str` | raw markdown content |
| `note_update` | `path: str`, `content: str` | `"updated"` |
| `note_delete` | `path: str` | `"deleted"` |

### Frontmatter

| Tool | Parameters | Returns |
|------|------------|---------|
| `frontmatter_read` | `path: str` | JSON object of key-value pairs |
| `frontmatter_write` | `path: str`, `fields: dict[str, Any]`, `replace: bool = False` | `"updated"` |

### Links

| Tool | Parameters | Returns |
|------|------------|---------|
| `link_insert_wikilink` | `source_path: str`, `target_title: str`, `alias: str \| None = None` | `"inserted"` |
| `link_get_backlinks` | `path: str` | JSON array of vault-relative paths |
| `link_get_forward_links` | `path: str` | JSON array of link targets |

### Search

| Tool | Parameters | Returns |
|------|------------|---------|
| `search_notes` | `query: str`, `max_results: int = 50`, `case_sensitive: bool = False` | JSON array of `{path, line_number, snippet}` |

### Images

| Tool | Parameters | Returns |
|------|------------|---------|
| `image_embed` | `note_path: str`, `image_filename: str` | `"embedded"` |
| `image_import` | `note_path: str`, `external_image_path: str`, `subfolder: str = "attachments"` | vault-relative image path |

### Canvas

| Tool | Parameters | Returns |
|------|------------|---------|
| `canvas_read` | `path: str` | JSON with `nodes` and `edges` arrays |
| `canvas_create` | `path: str`, `nodes: list \| None = None`, `edges: list \| None = None` | resolved path |
| `canvas_update` | `path: str`, `nodes: list`, `edges: list` | `"updated"` |
| `canvas_delete` | `path: str` | `"deleted"` |

### Folders

| Tool | Parameters | Returns |
|------|------------|---------|
| `folder_create` | `path: str` | vault-relative path |
| `folder_rename` | `old_path: str`, `new_path: str` | new vault-relative path |
| `folder_delete` | `path: str`, `force: bool = False` | `"deleted"` |

---

## 6. Vault Discovery Logic

**Config file (Linux):** `~/.config/obsidian/obsidian.json`

**Confirmed structure on this machine:**
```json
{"vaults":{"e8443d72530063f2":{"path":"/path/to/your/vault","ts":1774291514054,"open":true}}}
```

**Algorithm:**
1. If `OBSIDIAN_VAULT_PATH` env var is set → use it directly (bypasses file)
2. Parse `obsidian.json`
3. Prefer vault with `"open": true`; fall back to highest `"ts"` (most recently used)
4. Verify path exists on disk
5. Raise `VaultNotFoundError` with clear message on any failure

---

## 7. Path Resolution (AC-15)

**`Vault.resolve(note_ref: str) -> Path` algorithm:**

```
1. Strip whitespace; append ".md" if not present
2. candidate = vault.root / note_ref
3. If candidate.exists() → return it  (covers relative paths)
4. If no path separator in note_ref (bare title):
   a. Walk all .md files
   b. Match where file.stem == note_ref (case-insensitive)
   c. Exactly one match → return it
   d. Zero matches → raise NoteNotFoundError
   e. Multiple matches → raise NoteNotFoundError with list of matches
5. Path separator present but not found → raise NoteNotFoundError
```

**For `note_create`:** Does NOT call `resolve()`. Builds `vault.root / note_ref_with_extension` directly. Creates parent dirs with `mkdir(parents=True, exist_ok=True)`.

---

## 8. Git Design

### Core function

```python
def run_git(vault_root: Path, *args: str) -> subprocess.CompletedProcess:
    if shutil.which("git") is None:
        raise GitNotAvailableError("git is not installed or not on PATH.")
    result = subprocess.run(
        ["git", *args],
        cwd=vault_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result
```

### Git init (AC-19)

```python
def ensure_git_repo(vault_root: Path) -> None:
    if not (vault_root / ".git").exists():
        run_git(vault_root, "init")
        gitignore = vault_root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(".obsidian/workspace*\n.obsidian/cache\n")
```

### Auto-commit (AC-20, EC-6)

```python
def commit_all(vault_root: Path, message: str) -> bool:
    result = run_git(vault_root, "status", "--porcelain")
    if not result.stdout.strip():
        return False    # EC-6: no-op on empty
    run_git(vault_root, "add", "-A")
    run_git(vault_root, "commit", "-m", message)
    return True

async def auto_commit_loop(vault_root: Path, interval_seconds: int) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            commit_all(vault_root, "auto-commit")
        except Exception:
            pass  # log, do not crash server
```

### Interval parsing

`GIT_AUTOCOMMIT_INTERVAL` accepts `"15m"`, `"900s"`, `"1h"`, or bare seconds.

```python
def parse_interval(raw: str) -> int:
    m = re.fullmatch(r'(\d+)(s|m|h)?', raw.strip())
    if not m:
        raise ValueError(f"Cannot parse GIT_AUTOCOMMIT_INTERVAL='{raw}'.")
    value, unit = int(m.group(1)), m.group(2) or "s"
    return value * {"s": 1, "m": 60, "h": 3600}[unit]
```

---

## 9. Canvas Format

Obsidian `.canvas` files are JSON:

```json
{
  "nodes": [
    {
      "id": "abc12345",
      "type": "text",
      "x": 0, "y": 0, "width": 400, "height": 300,
      "text": "Node content"
    }
  ],
  "edges": [
    {
      "id": "def67890",
      "fromNode": "abc12345", "fromSide": "right",
      "toNode": "xyz00001", "toSide": "left",
      "label": "optional"
    }
  ]
}
```

- Node types: `"text"`, `"file"`, `"link"`, `"group"`
- ID generation: `uuid.uuid4().hex[:8]`
- Malformed JSON → `CanvasParseError` (EC-8)
- Canvas path resolution: appends `.canvas` instead of `.md`

---

## 10. Error Handling Strategy

| AC/EC | Exception | ToolError message |
|-------|-----------|-------------------|
| AC-14 / EC-1 | `NoteAlreadyExistsError` | `"Note already exists at '{path}'. Use note_update to modify it."` |
| AC-15 / EC-4,5 | `NoteNotFoundError` | `"Note '{ref}' not found in vault."` or ambiguous match list |
| AC-16 / EC-2 | `AttachmentNotFoundError` | `"Attachment '{filename}' not found in vault."` |
| EC-6 | (no error) | `commit_all` returns `False`, silent no-op |
| EC-7 | `GitNotAvailableError` | `"git is not installed or not on PATH."` |
| EC-8 | `CanvasParseError` | `"Canvas file '{path}' is malformed JSON: {detail}"` |
| Vault missing | `VaultNotFoundError` | Raised at startup; crashes server with clear message |
| Permission | `PermissionError` | `"Permission denied: {filename}"` |
| Generic I/O | `OSError` | `"I/O error: {e}"` |

All tool handlers follow this pattern:
```python
@mcp.tool()
async def some_tool(...) -> str:
    vault: Vault = mcp.state.vault
    try:
        # domain logic
    except (NoteNotFoundError, ...) as e:
        raise ToolError(str(e))
    except PermissionError as e:
        raise ToolError(f"Permission denied: {e.filename}")
    except OSError as e:
        raise ToolError(f"I/O error: {e}")
```

---

## 11. Testing Approach

All tests use a temp directory vault — no Obsidian install required.

### `tests/conftest.py`

```python
@pytest.fixture
def vault_dir(tmp_path) -> Path:
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / "Templates").mkdir()
    (tmp_path / "attachments").mkdir()
    return tmp_path

@pytest.fixture
def vault(vault_dir) -> Vault:
    return Vault(vault_dir)

@pytest.fixture(autouse=True)
def set_vault_env(vault_dir, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_dir))
```

### Per-module test coverage

| Module | Key tests |
|--------|-----------|
| `test_vault.py` | Discovery logic, `open=true` preference, `ts` fallback, missing config |
| `test_notes.py` | CRUD, duplicate create error, title vs path resolution, ambiguous title, spaces in name |
| `test_frontmatter.py` | Round-trip, merge fields, replace mode |
| `test_links.py` | WikiLink insert, alias insert, backlinks scan, forward links parse |
| `test_search.py` | Hit, miss, case-insensitive, max results |
| `test_images.py` | Embed existing, import external, missing attachment error |
| `test_canvas.py` | CRUD, malformed JSON error |
| `test_folders.py` | Create, rename, delete empty, delete non-empty with/without force |
| `test_templates.py` | List, apply, unknown template error |
| `test_git.py` | Init idempotent, commit with changes, no-op on empty, git missing error |

### Running tests
```bash
uv run pytest
uv run pytest -v tests/test_notes.py
```

---

## 12. Claude Desktop / Claude Code Integration

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

---

## 13. Key Constraints for Implementation

1. **No `gitpython`** — subprocess only.
2. **No default auto-commit interval** — if `GIT_AUTOCOMMIT_INTERVAL` is unset, the background task must not start.
3. **`mcp.state` access** — vault and config live in `app.state` (set in lifespan), not module-level globals.
4. **`ToolError` wrapping** — all domain exceptions must be caught and wrapped before leaving a tool handler.
5. **`python-frontmatter` round-trip** — always use `frontmatter.load()` / `frontmatter.dumps()`. Never manually splice YAML.
6. **Canvas uses `.canvas` extension** — not `.json`.
7. **`OBSIDIAN_VAULT_PATH` env var** — checked first in `discover_vault_path()`. Essential for tests.
8. **Ambiguous titles must error** — do not silently pick first match.
9. **`note_create` skips `resolve()`** — builds path directly; creates parent dirs automatically.
10. **`.gitignore` on init** — exclude `.obsidian/workspace*` and `.obsidian/cache`.
