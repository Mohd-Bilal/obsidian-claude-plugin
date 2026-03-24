"""Tests for note CRUD operations."""

import pytest
from pathlib import Path

from obsidian_mcp.notes import create_note, read_note, update_note, delete_note
from obsidian_mcp.errors import NoteAlreadyExistsError, NoteNotFoundError, TemplateNotFoundError


class TestCreateNote:
    def test_create_basic(self, vault, vault_dir):
        result = create_note(vault, "my_note.md", "hello world")
        assert result == "my_note.md"
        assert (vault_dir / "my_note.md").read_text() == "hello world"

    def test_create_appends_md_extension(self, vault, vault_dir):
        result = create_note(vault, "my_note", "hello")
        assert result == "my_note.md"
        assert (vault_dir / "my_note.md").exists()

    def test_create_with_subdirectory(self, vault, vault_dir):
        result = create_note(vault, "subdir/note.md", "content")
        assert (vault_dir / "subdir" / "note.md").exists()

    def test_create_duplicate_raises(self, vault, vault_dir):
        (vault_dir / "existing.md").write_text("old content")
        with pytest.raises(NoteAlreadyExistsError):
            create_note(vault, "existing.md", "new content")

    def test_create_with_template(self, vault, vault_dir):
        (vault_dir / "Templates" / "daily.md").write_text("# Daily Note\n")
        result = create_note(vault, "today.md", "My content", template="daily")
        content = (vault_dir / "today.md").read_text()
        assert content.startswith("# Daily Note\n")
        assert "My content" in content

    def test_create_with_missing_template_raises(self, vault):
        with pytest.raises(TemplateNotFoundError):
            create_note(vault, "note.md", "", template="nonexistent")

    def test_create_note_with_spaces_in_name(self, vault, vault_dir):
        result = create_note(vault, "My Note With Spaces.md", "content")
        assert (vault_dir / "My Note With Spaces.md").exists()


class TestReadNote:
    def test_read_existing(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("hello")
        assert read_note(vault, "note.md") == "hello"

    def test_read_by_title(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("content")
        assert read_note(vault, "note") == "content"

    def test_read_missing_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            read_note(vault, "nonexistent.md")


class TestUpdateNote:
    def test_update_existing(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("old content")
        result = update_note(vault, "note.md", "new content")
        assert result == "note.md"
        assert (vault_dir / "note.md").read_text() == "new content"

    def test_update_missing_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            update_note(vault, "nonexistent.md", "content")


class TestDeleteNote:
    def test_delete_existing(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("content")
        result = delete_note(vault, "note.md")
        assert result == "note.md"
        assert not (vault_dir / "note.md").exists()

    def test_delete_missing_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            delete_note(vault, "nonexistent.md")

    def test_delete_by_title(self, vault, vault_dir):
        (vault_dir / "to_delete.md").write_text("bye")
        delete_note(vault, "to_delete")
        assert not (vault_dir / "to_delete.md").exists()
