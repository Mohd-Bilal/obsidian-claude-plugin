"""Tests for frontmatter read/write operations."""

import pytest
from obsidian_mcp.frontmatter import read_frontmatter, write_frontmatter
from obsidian_mcp.errors import NoteNotFoundError


class TestReadFrontmatter:
    def test_read_empty_frontmatter(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("# Just content\nNo frontmatter.")
        result = read_frontmatter(vault, "note.md")
        assert result == {}

    def test_read_with_frontmatter(self, vault, vault_dir):
        (vault_dir / "note.md").write_text(
            "---\ntitle: My Note\ntags: [a, b]\n---\ncontent"
        )
        result = read_frontmatter(vault, "note.md")
        assert result["title"] == "My Note"
        assert result["tags"] == ["a", "b"]

    def test_read_missing_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            read_frontmatter(vault, "nonexistent.md")


class TestWriteFrontmatter:
    def test_write_new_fields(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("# Content")
        write_frontmatter(vault, "note.md", {"title": "Hello"})
        result = read_frontmatter(vault, "note.md")
        assert result["title"] == "Hello"

    def test_merge_fields(self, vault, vault_dir):
        (vault_dir / "note.md").write_text(
            "---\ntitle: Old Title\ntags: [x]\n---\ncontent"
        )
        write_frontmatter(vault, "note.md", {"author": "Alice"})
        result = read_frontmatter(vault, "note.md")
        assert result["title"] == "Old Title"  # preserved
        assert result["author"] == "Alice"    # added

    def test_replace_mode(self, vault, vault_dir):
        (vault_dir / "note.md").write_text(
            "---\ntitle: Old\nextra: removed\n---\ncontent"
        )
        write_frontmatter(vault, "note.md", {"title": "New"}, replace=True)
        result = read_frontmatter(vault, "note.md")
        assert result == {"title": "New"}
        assert "extra" not in result

    def test_round_trip_preserves_content(self, vault, vault_dir):
        original_body = "# My Note\n\nSome content here."
        (vault_dir / "note.md").write_text(f"---\ntitle: Test\n---\n{original_body}")
        write_frontmatter(vault, "note.md", {"status": "draft"})
        import frontmatter as fm
        post = fm.load(str(vault_dir / "note.md"))
        assert post.content.strip() == original_body.strip()
        assert post["status"] == "draft"

    def test_write_missing_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            write_frontmatter(vault, "nonexistent.md", {"key": "val"})
