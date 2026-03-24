"""Full-text search across vault notes."""

from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP, Context

from obsidian_mcp.vault import Vault


def search_notes(
    vault: Vault,
    query: str,
    max_results: int = 50,
    case_sensitive: bool = False,
) -> list[dict]:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error:
        pattern = re.compile(re.escape(query), flags)

    results: list[dict] = []

    for md_file in vault.all_markdown_files():
        if len(results) >= max_results:
            break
        try:
            lines = md_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        rel_path = str(md_file.relative_to(vault.root))
        for lineno, line in enumerate(lines, start=1):
            if len(results) >= max_results:
                break
            if pattern.search(line):
                results.append({
                    "path": rel_path,
                    "line_number": lineno,
                    "snippet": line,
                })

    return results


def register_tools(mcp: FastMCP) -> None:
    """Register search tools with the MCP server."""
    from mcp.server.fastmcp.exceptions import ToolError

    @mcp.tool()
    async def search_notes_tool(
        query: str, max_results: int = 50, case_sensitive: bool = False, ctx: Context = None
    ) -> list[dict]:
        """Search all notes for a query string.

        Returns a list of {path, line_number, snippet} dicts.
        """
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return search_notes(vault, query, max_results, case_sensitive)
        except OSError as e:
            raise ToolError(f"I/O error: {e}")
