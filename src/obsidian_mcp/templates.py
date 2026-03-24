"""Template helpers for the Obsidian vault."""

from __future__ import annotations

from pathlib import Path

from obsidian_mcp.errors import TemplateNotFoundError
from obsidian_mcp.vault import Vault


def list_templates(vault: Vault, templates_folder: str) -> list[str]:
    """Return a list of template names (stems) available in the templates folder."""
    folder = vault.root / templates_folder
    if not folder.exists():
        return []
    return [f.stem for f in sorted(folder.glob("*.md"))]


def get_template_content(vault: Vault, templates_folder: str, name: str) -> str:
    """Return the content of a named template.

    Args:
        vault: The active Vault instance.
        templates_folder: Relative path of templates folder inside vault.
        name: Template name (with or without .md extension).

    Raises:
        TemplateNotFoundError: If the template does not exist.
    """
    if not name.endswith(".md"):
        name = name + ".md"
    template_path = vault.root / templates_folder / name
    if not template_path.exists():
        raise TemplateNotFoundError(
            f"Template not found: {name!r} in {templates_folder!r}"
        )
    return template_path.read_text(encoding="utf-8")
