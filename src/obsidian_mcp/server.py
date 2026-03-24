"""MCP server entry point for obsidian-mcp."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP, Context

from mcp.server.fastmcp.exceptions import ToolError

from obsidian_mcp.config import Config, load_config
from obsidian_mcp.vault import Vault, discover_vault_path, list_vaults
from obsidian_mcp.git import ensure_git_repo, auto_commit_loop


@dataclass
class AppContext:
    vault: Vault
    config: Config


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[AppContext]:
    config = load_config()
    vault_root = config.vault_path or discover_vault_path()
    vault = Vault(vault_root)
    ensure_git_repo(vault.root)

    task = None
    if config.git_autocommit_interval:
        task = asyncio.create_task(
            auto_commit_loop(vault.root, config.git_autocommit_interval)
        )
    try:
        yield AppContext(vault=vault, config=config)
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


mcp = FastMCP("obsidian-mcp", lifespan=lifespan)

# Register tools from sub-modules (avoids circular imports)
import obsidian_mcp.notes as _notes
import obsidian_mcp.frontmatter as _frontmatter
import obsidian_mcp.links as _links
import obsidian_mcp.search as _search
import obsidian_mcp.images as _images
import obsidian_mcp.canvas as _canvas
import obsidian_mcp.folders as _folders

_notes.register_tools(mcp)
_frontmatter.register_tools(mcp)
_links.register_tools(mcp)
_search.register_tools(mcp)
_images.register_tools(mcp)
_canvas.register_tools(mcp)
_folders.register_tools(mcp)


@mcp.tool()
async def vault_list(ctx: Context = None) -> list[dict]:
    """List all Obsidian vaults registered on this machine.

    Returns a list of vaults with their name, path, whether they are
    currently open in Obsidian, and last-used timestamp. Use vault_switch
    to change the active vault for this session.
    """
    app_ctx = ctx.request_context.lifespan_context
    vaults = list_vaults()
    if not vaults:
        return []
    current = str(app_ctx.vault.root)
    for v in vaults:
        v["active"] = v["path"] == current
    return vaults


@mcp.tool()
async def vault_switch(path: str, ctx: Context = None) -> str:
    """Switch the active vault for this session.

    Args:
        path: Absolute path to the vault root (as returned by vault_list).

    Returns the name of the newly active vault.
    """
    vault_path = Path(path)
    if not vault_path.exists():
        raise ToolError(f"Vault path does not exist: {path}")
    if not vault_path.is_dir():
        raise ToolError(f"Vault path is not a directory: {path}")
    app_ctx = ctx.request_context.lifespan_context
    app_ctx.vault = Vault(vault_path)
    ensure_git_repo(app_ctx.vault.root)
    return f"Switched to vault: {vault_path.name}"


def main() -> None:
    mcp.run(transport="stdio")
