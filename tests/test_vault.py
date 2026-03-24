"""Tests for vault discovery and resolution logic."""

import json
import pytest
from pathlib import Path

from obsidian_mcp.vault import Vault, discover_vault_path
from obsidian_mcp.errors import VaultNotFoundError, NoteNotFoundError


class TestDiscoverVaultPath:
    def test_env_var_takes_precedence(self, vault_dir, monkeypatch):
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_dir))
        result = discover_vault_path()
        assert result == vault_dir

    def test_env_var_nonexistent_raises(self, monkeypatch):
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "/nonexistent/path/xyz")
        with pytest.raises(VaultNotFoundError):
            discover_vault_path()

    def test_missing_obsidian_json_raises(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
        # Point config path to a non-existent file
        from obsidian_mcp import vault as vault_mod
        original = vault_mod.OBSIDIAN_CONFIG_PATH
        vault_mod.OBSIDIAN_CONFIG_PATH = tmp_path / "nonexistent.json"
        try:
            with pytest.raises(VaultNotFoundError):
                discover_vault_path()
        finally:
            vault_mod.OBSIDIAN_CONFIG_PATH = original

    def test_open_true_preferred(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
        # Create two fake vaults
        vault_a = tmp_path / "vault_a"
        vault_a.mkdir()
        vault_b = tmp_path / "vault_b"
        vault_b.mkdir()

        config = {
            "vaults": {
                "id1": {"path": str(vault_a), "ts": 1000, "open": False},
                "id2": {"path": str(vault_b), "ts": 500, "open": True},
            }
        }
        config_file = tmp_path / "obsidian.json"
        config_file.write_text(json.dumps(config))

        from obsidian_mcp import vault as vault_mod
        original = vault_mod.OBSIDIAN_CONFIG_PATH
        vault_mod.OBSIDIAN_CONFIG_PATH = config_file
        try:
            result = discover_vault_path()
            assert result == vault_b
        finally:
            vault_mod.OBSIDIAN_CONFIG_PATH = original

    def test_ts_fallback_when_no_open(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
        vault_a = tmp_path / "vault_a"
        vault_a.mkdir()
        vault_b = tmp_path / "vault_b"
        vault_b.mkdir()

        config = {
            "vaults": {
                "id1": {"path": str(vault_a), "ts": 1000},
                "id2": {"path": str(vault_b), "ts": 2000},
            }
        }
        config_file = tmp_path / "obsidian.json"
        config_file.write_text(json.dumps(config))

        from obsidian_mcp import vault as vault_mod
        original = vault_mod.OBSIDIAN_CONFIG_PATH
        vault_mod.OBSIDIAN_CONFIG_PATH = config_file
        try:
            result = discover_vault_path()
            assert result == vault_b
        finally:
            vault_mod.OBSIDIAN_CONFIG_PATH = original

    def test_vault_path_missing_on_disk_raises(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
        config = {
            "vaults": {
                "id1": {"path": str(tmp_path / "nonexistent_vault"), "ts": 1000},
            }
        }
        config_file = tmp_path / "obsidian.json"
        config_file.write_text(json.dumps(config))

        from obsidian_mcp import vault as vault_mod
        original = vault_mod.OBSIDIAN_CONFIG_PATH
        vault_mod.OBSIDIAN_CONFIG_PATH = config_file
        try:
            with pytest.raises(VaultNotFoundError):
                discover_vault_path()
        finally:
            vault_mod.OBSIDIAN_CONFIG_PATH = original


class TestVaultResolve:
    def test_resolve_by_relative_path(self, vault, vault_dir):
        note = vault_dir / "test.md"
        note.write_text("hello")
        result = vault.resolve("test.md")
        assert result == note

    def test_resolve_appends_md(self, vault, vault_dir):
        note = vault_dir / "test.md"
        note.write_text("hello")
        result = vault.resolve("test")
        assert result == note

    def test_resolve_bare_title(self, vault, vault_dir):
        note = vault_dir / "subdir" / "My Note.md"
        note.parent.mkdir()
        note.write_text("content")
        result = vault.resolve("My Note")
        assert result == note

    def test_resolve_bare_title_case_insensitive(self, vault, vault_dir):
        note = vault_dir / "Hello.md"
        note.write_text("content")
        result = vault.resolve("hello")
        assert result == note

    def test_resolve_not_found_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            vault.resolve("nonexistent_note")

    def test_resolve_ambiguous_raises(self, vault, vault_dir):
        (vault_dir / "dir1").mkdir()
        (vault_dir / "dir2").mkdir()
        (vault_dir / "dir1" / "Note.md").write_text("a")
        (vault_dir / "dir2" / "Note.md").write_text("b")
        with pytest.raises(NoteNotFoundError, match="Ambiguous"):
            vault.resolve("Note")

    def test_resolve_path_not_found_raises(self, vault):
        with pytest.raises(NoteNotFoundError):
            vault.resolve("subdir/nonexistent.md")

    def test_all_markdown_files(self, vault, vault_dir):
        (vault_dir / "a.md").write_text("a")
        (vault_dir / "sub").mkdir()
        (vault_dir / "sub" / "b.md").write_text("b")
        files = list(vault.all_markdown_files())
        names = {f.name for f in files}
        assert "a.md" in names
        assert "b.md" in names
