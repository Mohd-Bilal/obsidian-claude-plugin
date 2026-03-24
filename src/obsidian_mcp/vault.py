"""Vault discovery and access helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

from obsidian_mcp.errors import VaultNotFoundError, NoteNotFoundError

OBSIDIAN_CONFIG_PATH = Path.home() / ".config" / "obsidian" / "obsidian.json"


def list_vaults() -> list[dict]:
    """Return all vaults registered in obsidian.json as a list of dicts.

    Each entry has: name, path, open (bool), ts (int).
    Returns an empty list if obsidian.json is missing or has no vaults.
    """
    if not OBSIDIAN_CONFIG_PATH.exists():
        return []

    try:
        config_data = json.loads(OBSIDIAN_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    vaults = config_data.get("vaults", {})
    result = []
    for vault_info in vaults.values():
        path_str = vault_info.get("path", "")
        result.append({
            "name": Path(path_str).name,
            "path": path_str,
            "open": vault_info.get("open", False),
            "ts": vault_info.get("ts", 0),
        })

    # Sort by most recently used first
    result.sort(key=lambda v: v["ts"], reverse=True)
    return result


def discover_vault_path() -> Path:
    """Discover the active Obsidian vault path.

    Order of precedence:
    1. OBSIDIAN_VAULT_PATH environment variable
    2. obsidian.json — prefer vault with "open": true; fall back to highest "ts"
    """
    env_path = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env_path:
        p = Path(env_path)
        if not p.exists():
            raise VaultNotFoundError(
                f"OBSIDIAN_VAULT_PATH points to non-existent path: {p}"
            )
        return p

    if not OBSIDIAN_CONFIG_PATH.exists():
        raise VaultNotFoundError(
            f"Obsidian config not found at {OBSIDIAN_CONFIG_PATH} "
            "and OBSIDIAN_VAULT_PATH is not set."
        )

    try:
        config_data = json.loads(OBSIDIAN_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VaultNotFoundError(
            f"Failed to parse {OBSIDIAN_CONFIG_PATH}: {exc}"
        ) from exc

    vaults = config_data.get("vaults", {})
    if not vaults:
        raise VaultNotFoundError("No vaults found in obsidian.json")

    # Prefer open=true vault; fall back to highest ts
    best_path: str | None = None
    best_ts: int = -1
    open_path: str | None = None

    for vault_info in vaults.values():
        path_str = vault_info.get("path", "")
        ts = vault_info.get("ts", 0)
        is_open = vault_info.get("open", False)

        if is_open:
            open_path = path_str

        if ts > best_ts:
            best_ts = ts
            best_path = path_str

    chosen = open_path or best_path
    if not chosen:
        raise VaultNotFoundError("Could not determine vault path from obsidian.json")

    result = Path(chosen)
    if not result.exists():
        raise VaultNotFoundError(
            f"Vault path from obsidian.json does not exist on disk: {result}"
        )
    return result


class Vault:
    def __init__(self, root: Path) -> None:
        self.root = root

    def resolve(self, note_ref: str) -> Path:
        """Resolve a note reference to an absolute path.

        Accepts:
        - A relative path (with .md extension or without)
        - A bare title (no path separators) — searches all .md files by stem
        """
        note_ref = note_ref.strip()
        if not note_ref.endswith(".md"):
            note_ref = note_ref + ".md"

        candidate = self.root / note_ref
        if candidate.exists():
            return candidate

        # Bare title search (no path separators in original ref)
        ref_without_ext = note_ref[:-3]  # strip .md
        if "/" not in ref_without_ext and "\\" not in ref_without_ext:
            matches = [
                f for f in self.all_markdown_files()
                if f.stem.lower() == ref_without_ext.lower()
            ]
            if len(matches) == 1:
                return matches[0]
            if len(matches) == 0:
                raise NoteNotFoundError(
                    f"Note not found: {ref_without_ext!r}"
                )
            # Multiple matches
            rel_matches = [str(m.relative_to(self.root)) for m in matches]
            raise NoteNotFoundError(
                f"Ambiguous note title {ref_without_ext!r}; "
                f"matches: {rel_matches}"
            )

        raise NoteNotFoundError(f"Note not found: {note_ref}")

    def exists(self, path: Path) -> bool:
        return path.exists()

    def all_markdown_files(self) -> Iterator[Path]:
        """Yield all .md files under the vault root."""
        for p in self.root.rglob("*.md"):
            yield p

    def attachments_dir(self) -> Path:
        """Return the attachments directory, creating it if absent."""
        d = self.root / "attachments"
        d.mkdir(exist_ok=True)
        return d
