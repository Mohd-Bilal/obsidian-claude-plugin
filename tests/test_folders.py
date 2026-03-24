"""Tests for folder management operations."""

import pytest
from pathlib import Path

from obsidian_mcp.folders import create_folder, rename_folder, delete_folder
from obsidian_mcp.errors import FolderNotFoundError, FolderNotEmptyError


class TestCreateFolder:
    def test_create_folder(self, vault, vault_dir):
        result = create_folder(vault, "new_folder")
        assert result == "new_folder"
        assert (vault_dir / "new_folder").is_dir()

    def test_create_nested_folder(self, vault, vault_dir):
        result = create_folder(vault, "parent/child/grandchild")
        assert (vault_dir / "parent" / "child" / "grandchild").is_dir()

    def test_create_duplicate_raises(self, vault, vault_dir):
        (vault_dir / "existing").mkdir()
        with pytest.raises(FileExistsError):
            create_folder(vault, "existing")


class TestRenameFolder:
    def test_rename_folder(self, vault, vault_dir):
        (vault_dir / "old_name").mkdir()
        result = rename_folder(vault, "old_name", "new_name")
        assert result == "new_name"
        assert not (vault_dir / "old_name").exists()
        assert (vault_dir / "new_name").is_dir()

    def test_rename_with_contents(self, vault, vault_dir):
        (vault_dir / "folder").mkdir()
        (vault_dir / "folder" / "note.md").write_text("content")
        rename_folder(vault, "folder", "renamed_folder")
        assert (vault_dir / "renamed_folder" / "note.md").exists()

    def test_rename_missing_raises(self, vault):
        with pytest.raises(FolderNotFoundError):
            rename_folder(vault, "nonexistent", "new_name")


class TestDeleteFolder:
    def test_delete_empty_folder(self, vault, vault_dir):
        (vault_dir / "empty_folder").mkdir()
        result = delete_folder(vault, "empty_folder")
        assert result == "empty_folder"
        assert not (vault_dir / "empty_folder").exists()

    def test_delete_nonempty_raises(self, vault, vault_dir):
        folder = vault_dir / "nonempty"
        folder.mkdir()
        (folder / "file.md").write_text("content")
        with pytest.raises(FolderNotEmptyError):
            delete_folder(vault, "nonempty", force=False)

    def test_delete_nonempty_with_force(self, vault, vault_dir):
        folder = vault_dir / "nonempty"
        folder.mkdir()
        (folder / "file.md").write_text("content")
        result = delete_folder(vault, "nonempty", force=True)
        assert not (vault_dir / "nonempty").exists()

    def test_delete_missing_raises(self, vault):
        with pytest.raises(FolderNotFoundError):
            delete_folder(vault, "nonexistent")
