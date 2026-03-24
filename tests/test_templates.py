"""Tests for template listing and retrieval."""

import pytest
from obsidian_mcp.templates import list_templates, get_template_content
from obsidian_mcp.errors import TemplateNotFoundError


class TestListTemplates:
    def test_list_templates_empty(self, vault):
        result = list_templates(vault, "Templates")
        assert result == []

    def test_list_templates_with_files(self, vault, vault_dir):
        (vault_dir / "Templates" / "daily.md").write_text("# Daily")
        (vault_dir / "Templates" / "weekly.md").write_text("# Weekly")
        result = list_templates(vault, "Templates")
        assert "daily" in result
        assert "weekly" in result

    def test_list_templates_missing_folder(self, vault):
        result = list_templates(vault, "NonexistentFolder")
        assert result == []

    def test_list_templates_sorted(self, vault, vault_dir):
        (vault_dir / "Templates" / "z_template.md").write_text("")
        (vault_dir / "Templates" / "a_template.md").write_text("")
        result = list_templates(vault, "Templates")
        assert result == sorted(result)


class TestGetTemplateContent:
    def test_get_template_with_extension(self, vault, vault_dir):
        (vault_dir / "Templates" / "daily.md").write_text("# Daily Note\n")
        result = get_template_content(vault, "Templates", "daily.md")
        assert result == "# Daily Note\n"

    def test_get_template_without_extension(self, vault, vault_dir):
        (vault_dir / "Templates" / "weekly.md").write_text("# Weekly Note\n")
        result = get_template_content(vault, "Templates", "weekly")
        assert result == "# Weekly Note\n"

    def test_get_missing_template_raises(self, vault):
        with pytest.raises(TemplateNotFoundError):
            get_template_content(vault, "Templates", "nonexistent")

    def test_get_template_content_preserved(self, vault, vault_dir):
        content = "---\ntitle: Template\n---\n# Template\n\n{{date}}\n"
        (vault_dir / "Templates" / "complex.md").write_text(content)
        result = get_template_content(vault, "Templates", "complex")
        assert result == content
