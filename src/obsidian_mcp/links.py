"""Wikilink insertion and backlink/forward-link scanning."""

from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP, Context

from obsidian_mcp.errors import NoteNotFoundError
from obsidian_mcp.vault import Vault

WIKILINK_RE = re.compile(r'\[\[([^\[\]]+)\]\]')


def insert_wikilink(
    vault: Vault, source_path: str, target_title: str, alias: str | None = None
) -> str:
    note_path = vault.resolve(source_path)
    if alias:
        link = f"[[{target_title}|{alias}]]"
    else:
        link = f"[[{target_title}]]"

    content = note_path.read_text(encoding="utf-8")
    if content and not content.endswith("\n"):
        content += "\n"
    content += link + "\n"
    note_path.write_text(content, encoding="utf-8")
    return str(note_path.relative_to(vault.root))


def get_backlinks(vault: Vault, path: str) -> list[str]:
    target_path = vault.resolve(path)
    stem = target_path.stem
    rel = str(target_path.relative_to(vault.root))
    rel_no_ext = rel[:-3] if rel.endswith(".md") else rel

    results: list[str] = []
    for md_file in vault.all_markdown_files():
        if md_file == target_path:
            continue
        content = md_file.read_text(encoding="utf-8")
        for match in WIKILINK_RE.finditer(content):
            link_target = match.group(1).split("|")[0].strip()
            if link_target == stem or link_target == rel_no_ext:
                results.append(str(md_file.relative_to(vault.root)))
                break
    return results


def get_forward_links(vault: Vault, path: str) -> list[str]:
    note_path = vault.resolve(path)
    content = note_path.read_text(encoding="utf-8")
    links = []
    for match in WIKILINK_RE.finditer(content):
        target = match.group(1).split("|")[0].strip()
        links.append(target)
    return links


def register_tools(mcp: FastMCP) -> None:
    """Register link tools with the MCP server."""
    from mcp.server.fastmcp.exceptions import ToolError

    @mcp.tool()
    async def link_insert_wikilink(
        source_path: str, target_title: str, alias: str | None = None, ctx: Context = None
    ) -> str:
        """Append a wikilink to a note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return insert_wikilink(vault, source_path, target_title, alias)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def link_get_backlinks(path: str, ctx: Context = None) -> list[str]:
        """Find all notes that link to the given note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return get_backlinks(vault, path)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def link_get_forward_links(path: str, ctx: Context = None) -> list[str]:
        """Return all wikilinks in a note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return get_forward_links(vault, path)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")
