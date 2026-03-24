"""Folder management tools for the Obsidian vault."""

from __future__ import annotations

import os
import shutil

from mcp.server.fastmcp import FastMCP, Context

from obsidian_mcp.errors import FolderNotFoundError, FolderNotEmptyError
from obsidian_mcp.vault import Vault


def create_folder(vault: Vault, path: str) -> str:
    folder_path = vault.root / path
    folder_path.mkdir(parents=True, exist_ok=False)
    return str(folder_path.relative_to(vault.root))


def rename_folder(vault: Vault, old_path: str, new_path: str) -> str:
    src = vault.root / old_path
    if not src.exists():
        raise FolderNotFoundError(f"Folder not found: {old_path!r}")
    dst = vault.root / new_path
    shutil.move(str(src), str(dst))
    return str(dst.relative_to(vault.root))


def delete_folder(vault: Vault, path: str, force: bool = False) -> str:
    folder_path = vault.root / path
    if not folder_path.exists():
        raise FolderNotFoundError(f"Folder not found: {path!r}")

    if not force:
        contents = list(folder_path.iterdir())
        if contents:
            raise FolderNotEmptyError(
                f"Folder is not empty: {path!r}. Use force=True to delete anyway."
            )
        os.rmdir(folder_path)
    else:
        shutil.rmtree(folder_path)

    return path


def register_tools(mcp: FastMCP) -> None:
    """Register folder tools with the MCP server."""
    from mcp.server.fastmcp.exceptions import ToolError

    @mcp.tool()
    async def folder_create(path: str, ctx: Context = None) -> str:
        """Create a new folder in the vault."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return create_folder(vault, path)
        except FileExistsError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def folder_rename(old_path: str, new_path: str, ctx: Context = None) -> str:
        """Rename or move a folder."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return rename_folder(vault, old_path, new_path)
        except FolderNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def folder_delete(path: str, force: bool = False, ctx: Context = None) -> str:
        """Delete a folder. Use force=True for non-empty folders."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return delete_folder(vault, path, force)
        except (FolderNotFoundError, FolderNotEmptyError) as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")
