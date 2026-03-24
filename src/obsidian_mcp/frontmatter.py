"""Frontmatter read/write for Obsidian notes."""

from __future__ import annotations

import frontmatter as fm

from mcp.server.fastmcp import FastMCP, Context

from obsidian_mcp.errors import NoteNotFoundError
from obsidian_mcp.vault import Vault


def read_frontmatter(vault: Vault, path: str) -> dict:
    note_path = vault.resolve(path)
    post = fm.load(str(note_path))
    return dict(post.metadata)


def write_frontmatter(
    vault: Vault, path: str, fields: dict, replace: bool = False
) -> str:
    note_path = vault.resolve(path)
    post = fm.load(str(note_path))

    if replace:
        post.metadata = fields
    else:
        post.metadata.update(fields)

    note_path.write_text(fm.dumps(post), encoding="utf-8")
    return str(note_path.relative_to(vault.root))


def register_tools(mcp: FastMCP) -> None:
    """Register frontmatter tools with the MCP server."""
    from mcp.server.fastmcp.exceptions import ToolError

    @mcp.tool()
    async def frontmatter_read(path: str, ctx: Context = None) -> dict:
        """Read frontmatter metadata from a note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return read_frontmatter(vault, path)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def frontmatter_write(
        path: str, fields: dict, replace: bool = False, ctx: Context = None
    ) -> str:
        """Write frontmatter fields to a note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return write_frontmatter(vault, path, fields, replace)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")
