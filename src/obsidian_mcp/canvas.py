"""Canvas file CRUD for Obsidian .canvas files."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context

from obsidian_mcp.errors import CanvasParseError
from obsidian_mcp.vault import Vault


def _resolve_canvas(vault: Vault, path: str) -> Path:
    if not path.endswith(".canvas"):
        path = path + ".canvas"
    return vault.root / path


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def read_canvas(vault: Vault, path: str) -> dict:
    canvas_path = _resolve_canvas(vault, path)
    if not canvas_path.exists():
        raise FileNotFoundError(f"Canvas not found: {path}")
    try:
        return json.loads(canvas_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CanvasParseError(f"Malformed canvas JSON in {path}: {exc}") from exc


def create_canvas(
    vault: Vault,
    path: str,
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
) -> str:
    canvas_path = _resolve_canvas(vault, path)
    if canvas_path.exists():
        raise FileExistsError(f"Canvas already exists: {path}")

    canvas_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "nodes": nodes or [],
        "edges": edges or [],
    }
    canvas_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(canvas_path.relative_to(vault.root))


def update_canvas(vault: Vault, path: str, data: dict) -> str:
    canvas_path = _resolve_canvas(vault, path)
    if not canvas_path.exists():
        raise FileNotFoundError(f"Canvas not found: {path}")
    canvas_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(canvas_path.relative_to(vault.root))


def delete_canvas(vault: Vault, path: str) -> str:
    canvas_path = _resolve_canvas(vault, path)
    if not canvas_path.exists():
        raise FileNotFoundError(f"Canvas not found: {path}")
    rel = str(canvas_path.relative_to(vault.root))
    canvas_path.unlink()
    return rel


def register_tools(mcp: FastMCP) -> None:
    """Register canvas tools with the MCP server."""
    from mcp.server.fastmcp.exceptions import ToolError

    @mcp.tool()
    async def canvas_read(path: str, ctx: Context = None) -> dict:
        """Read and return a .canvas file as JSON."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return read_canvas(vault, path)
        except FileNotFoundError as e:
            raise ToolError(str(e))
        except CanvasParseError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def canvas_create(
        path: str,
        nodes: list[dict] | None = None,
        edges: list[dict] | None = None,
        ctx: Context = None,
    ) -> str:
        """Create a new .canvas file."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return create_canvas(vault, path, nodes, edges)
        except FileExistsError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def canvas_update(path: str, data: dict, ctx: Context = None) -> str:
        """Overwrite a .canvas file with new data."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return update_canvas(vault, path, data)
        except FileNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def canvas_delete(path: str, ctx: Context = None) -> str:
        """Delete a .canvas file."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return delete_canvas(vault, path)
        except FileNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")
