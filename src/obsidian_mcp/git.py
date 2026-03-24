"""Git integration for vault auto-commit."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path


def run_git(vault_root: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a git command in the vault root directory."""
    return subprocess.run(
        ["git", *args],
        cwd=vault_root,
        capture_output=True,
        text=True,
    )


def ensure_git_repo(vault_root: Path) -> None:
    """Ensure vault_root is a git repository; init if needed."""
    if not (vault_root / ".git").exists():
        run_git(vault_root, "init")
        gitignore = vault_root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(".obsidian/workspace*\n.obsidian/cache\n")


def commit_all(vault_root: Path, message: str) -> bool:
    """Stage all changes and commit. Returns True if a commit was made."""
    run_git(vault_root, "add", "-A")
    result = run_git(vault_root, "commit", "-m", message)
    return result.returncode == 0


async def auto_commit_loop(vault_root: Path, interval_seconds: int) -> None:
    """Periodically commit all changes in the vault."""
    while True:
        await asyncio.sleep(interval_seconds)
        commit_all(vault_root, "obsidian-mcp: auto-commit")
