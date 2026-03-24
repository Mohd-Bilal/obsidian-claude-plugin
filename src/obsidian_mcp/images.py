"""Image embedding and importing for Obsidian notes."""

from __future__ import annotations

import shutil
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context

from obsidian_mcp.errors import AttachmentNotFoundError, NoteNotFoundError
from obsidian_mcp.vault import Vault


def embed_image(vault: Vault, note_path: str, image_filename: str) -> str:
    resolved_note = vault.resolve(note_path)
    attachments = vault.attachments_dir()
    image_path = attachments / image_filename
    if not image_path.exists():
        raise AttachmentNotFoundError(
            f"Image not found in attachments: {image_filename!r}"
        )

    content = resolved_note.read_text(encoding="utf-8")
    if content and not content.endswith("\n"):
        content += "\n"
    content += f"![[{image_filename}]]\n"
    resolved_note.write_text(content, encoding="utf-8")
    return str(resolved_note.relative_to(vault.root))


def import_image(
    vault: Vault,
    note_path: str,
    external_image_path: str,
    subfolder: str = "attachments",
) -> str:
    resolved_note = vault.resolve(note_path)
    src = Path(external_image_path)
    if not src.exists():
        raise FileNotFoundError(f"External image not found: {external_image_path!r}")

    dest_dir = vault.root / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(str(src), str(dest))

    content = resolved_note.read_text(encoding="utf-8")
    if content and not content.endswith("\n"):
        content += "\n"
    content += f"![[{src.name}]]\n"
    resolved_note.write_text(content, encoding="utf-8")

    return str(dest.relative_to(vault.root))


def register_tools(mcp: FastMCP) -> None:
    """Register image tools with the MCP server."""
    from mcp.server.fastmcp.exceptions import ToolError

    @mcp.tool()
    async def image_embed(note_path: str, image_filename: str, ctx: Context = None) -> str:
        """Embed an existing attachment image in a note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return embed_image(vault, note_path, image_filename)
        except (NoteNotFoundError, AttachmentNotFoundError) as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")

    @mcp.tool()
    async def image_import(
        note_path: str, external_image_path: str, subfolder: str = "attachments", ctx: Context = None
    ) -> str:
        """Import an external image into the vault and embed it in a note."""
        vault: Vault = ctx.request_context.lifespan_context.vault
        try:
            return import_image(vault, note_path, external_image_path, subfolder)
        except NoteNotFoundError as e:
            raise ToolError(str(e))
        except FileNotFoundError as e:
            raise ToolError(str(e))
        except OSError as e:
            raise ToolError(f"I/O error: {e}")
