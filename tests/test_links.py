"""Tests for wikilink insertion and scanning."""

import pytest
from obsidian_mcp.links import insert_wikilink, get_backlinks, get_forward_links
from obsidian_mcp.errors import NoteNotFoundError


class TestInsertWikilink:
    def test_insert_basic_link(self, vault, vault_dir):
        (vault_dir / "source.md").write_text("Source note content.")
        insert_wikilink(vault, "source.md", "target")
        content = (vault_dir / "source.md").read_text()
        assert "[[target]]" in content

    def test_insert_with_alias(self, vault, vault_dir):
        (vault_dir / "source.md").write_text("Content.")
        insert_wikilink(vault, "source.md", "target", alias="Display Name")
        content = (vault_dir / "source.md").read_text()
        assert "[[target|Display Name]]" in content

    def test_insert_appends_to_content(self, vault, vault_dir):
        (vault_dir / "source.md").write_text("Original content.")
        insert_wikilink(vault, "source.md", "other_note")
        content = (vault_dir / "source.md").read_text()
        assert content.startswith("Original content.")
        assert "[[other_note]]" in content

    def test_insert_missing_source_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            insert_wikilink(vault, "nonexistent.md", "target")

    def test_insert_ensures_newline(self, vault, vault_dir):
        # No trailing newline
        (vault_dir / "source.md").write_text("content")
        insert_wikilink(vault, "source.md", "target")
        content = (vault_dir / "source.md").read_text()
        assert "\n[[target]]" in content


class TestGetBacklinks:
    def test_find_backlink(self, vault, vault_dir):
        (vault_dir / "note_a.md").write_text("see [[note_b]] for details")
        (vault_dir / "note_b.md").write_text("I am note_b")
        backlinks = get_backlinks(vault, "note_b.md")
        assert "note_a.md" in backlinks

    def test_no_backlinks(self, vault, vault_dir):
        (vault_dir / "lonely.md").write_text("no links here")
        assert get_backlinks(vault, "lonely.md") == []

    def test_backlink_not_self_referential(self, vault, vault_dir):
        (vault_dir / "self.md").write_text("[[self]] is a link to itself")
        backlinks = get_backlinks(vault, "self.md")
        assert "self.md" not in backlinks

    def test_missing_target_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            get_backlinks(vault, "nonexistent.md")

    def test_backlink_with_path_style(self, vault, vault_dir):
        (vault_dir / "sub").mkdir()
        (vault_dir / "sub" / "note.md").write_text("content")
        (vault_dir / "linker.md").write_text("[[sub/note]] is good")
        backlinks = get_backlinks(vault, "sub/note.md")
        assert "linker.md" in backlinks


class TestGetForwardLinks:
    def test_parse_wikilinks(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("see [[alpha]] and [[beta|Beta Note]]")
        links = get_forward_links(vault, "note.md")
        assert "alpha" in links
        assert "beta" in links

    def test_no_links(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("plain text")
        assert get_forward_links(vault, "note.md") == []

    def test_missing_note_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            get_forward_links(vault, "nonexistent.md")

    def test_alias_stripped(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("[[target|Display]]")
        links = get_forward_links(vault, "note.md")
        assert links == ["target"]
