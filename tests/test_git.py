"""Tests for git integration."""

import pytest
from pathlib import Path

from obsidian_mcp.git import ensure_git_repo, commit_all, run_git


class TestEnsureGitRepo:
    def test_init_new_repo(self, vault_dir):
        ensure_git_repo(vault_dir)
        assert (vault_dir / ".git").exists()

    def test_init_idempotent(self, vault_dir):
        ensure_git_repo(vault_dir)
        ensure_git_repo(vault_dir)  # Should not raise
        assert (vault_dir / ".git").exists()

    def test_creates_gitignore(self, vault_dir):
        ensure_git_repo(vault_dir)
        gitignore = vault_dir / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".obsidian/workspace" in content

    def test_does_not_overwrite_existing_gitignore(self, vault_dir):
        gitignore = vault_dir / ".gitignore"
        gitignore.write_text("my_custom_ignore\n")
        # Init git repo manually first
        run_git(vault_dir, "init")
        ensure_git_repo(vault_dir)
        assert gitignore.read_text() == "my_custom_ignore\n"

    def test_does_not_overwrite_existing_git_dir(self, vault_dir):
        run_git(vault_dir, "init")
        git_head = vault_dir / ".git" / "HEAD"
        original_content = git_head.read_text()
        ensure_git_repo(vault_dir)
        assert git_head.read_text() == original_content


class TestCommitAll:
    def test_commit_with_changes(self, vault_dir):
        ensure_git_repo(vault_dir)
        # Configure git identity for the test
        run_git(vault_dir, "config", "user.email", "test@test.com")
        run_git(vault_dir, "config", "user.name", "Test User")
        (vault_dir / "note.md").write_text("new content")
        result = commit_all(vault_dir, "test commit")
        assert result is True

    def test_commit_no_changes_returns_false(self, vault_dir):
        ensure_git_repo(vault_dir)
        run_git(vault_dir, "config", "user.email", "test@test.com")
        run_git(vault_dir, "config", "user.name", "Test User")
        # Initial commit so we have a clean state
        (vault_dir / "init.md").write_text("initial")
        run_git(vault_dir, "add", "-A")
        run_git(vault_dir, "commit", "-m", "initial")
        # Now commit again with no changes
        result = commit_all(vault_dir, "empty commit")
        assert result is False
