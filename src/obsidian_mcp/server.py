"""MCP server entry point for obsidian-mcp."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from obsidian_mcp.config import Config, load_config
from obsidian_mcp.vault import Vault, discover_vault_path
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


def main() -> None:
    mcp.run(transport="stdio")
