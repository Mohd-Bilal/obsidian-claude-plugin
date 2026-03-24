"""Note CRUD operations for the Obsidian vault."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context

from obsidian_mcp.errors import (
    NoteAlreadyExistsError,
    NoteNotFoundError,
    TemplateNotFoundError,
)
from obsidian_mcp.vault import Vault
from obsidian_mcp.templates import get_template_content


def create_note(
    vault: Vault,
    path: str,
    content: str = "",
    template: str | None = None,
    templates_folder: str = "Templates",
) -> str:
    if not path.endswith(".md"):
        path = path + ".md"

    note_path = vault.root / path
    if note_path.exists():
        raise NoteAlreadyExistsError(f"Note already exists: {path}")

    note_path.parent.mkdir(parents=True, exist_ok=True)

    final_content = content
    if template is not None:
        template_content = get_template_content(vault, templates_folder, template)
        final_content = template_content + content

    note_path.write_text(final_content, encoding="utf-8")
    return str(note_path.relative_to(vault.root))


def read_note(vault: Vault, path: str) -> str:
    note_path = vault.resolve(path)
    return note_path.read_text(encoding="utf-8")


def update_note(vault: Vault, path: str, content: str) -> str:
    note_path = vault.resolve(path)
    note_path.write_text(content, encoding="utf-8")
    return str(note_path.relative_to(vault.root))


def delete_note(vault: Vault, path: str) -> str:
    note_path = vault.resolve(path)
    rel = str(note_path.relative_to(vault.root))
    note_path.unlink()
    return rel


def register_tools(mcp: FastMCP) -> None:
    """Register note tools with the MCP server."""
    from mcp.server.fastmcp.exceptions import ToolError

    @mcp.tool()
    async def note_create(
        path: str, content: str = "", template: str | None = None, ctx: Context = None
    ) -> str:
        """Create a new note in the vault."""
        app_ctx = ctx.request_context.lifespan_context
        vault: Vault = app_ctx.vault
        config = app_ctx.config
        try:
            return create_note(vault, path, content, template, config.templates_folder)
        except (NoteAlreadyExistsError, NoteNotFoundError, TemplateNotFoundError) as e:
            raise ToolError(str(e))
        except PermissionError as e:
            raise ToolError(f"Permission denied: {e.filename}")
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def note_read(path: str, ctx: Context = None) -> str:
        """Read the content of a note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return read_note(vault, path)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except PermissionError as e:
            raise ToolError(f"Permission denied: {e.filename}")
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def note_update(path: str, content: str, ctx: Context = None) -> str:
        """Overwrite the content of an existing note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return update_note(vault, path, content)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except PermissionError as e:
            raise ToolError(f"Permission denied: {e.filename}")
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def note_delete(path: str, ctx: Context = None) -> str:
        """Delete a note from the vault."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return delete_note(vault, path)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except PermissionError as e:
            raise ToolError(f"Permission denied: {e.filename}")
        except OSError as e:
            raise ToolError(f"I/O error: {e}")
