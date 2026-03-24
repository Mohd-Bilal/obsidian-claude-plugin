"""Configuration loading for obsidian-mcp."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    vault_path: Path | None       # None = use discovery
    git_autocommit_interval: int | None   # seconds; None = disabled
    templates_folder: str         # default "Templates"


def parse_interval(raw: str) -> int:
    """Parse interval string to seconds.

    Examples:
        "15m" -> 900
        "1h"  -> 3600
        "300s" -> 300
        "300"  -> 300  (bare number treated as seconds)
    """
    raw = raw.strip()
    match = re.fullmatch(r'(\d+)([smh]?)', raw, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid interval format: {raw!r}")
    value = int(match.group(1))
    unit = (match.group(2) or 's').lower()
    multipliers = {'s': 1, 'm': 60, 'h': 3600}
    return value * multipliers[unit]


def load_config() -> Config:
    """Load configuration from environment variables."""
    vault_path_raw = os.environ.get("OBSIDIAN_VAULT_PATH")
    vault_path = Path(vault_path_raw) if vault_path_raw else None

    interval_raw = os.environ.get("GIT_AUTOCOMMIT_INTERVAL")
    git_autocommit_interval: int | None = None
    if interval_raw:
        git_autocommit_interval = parse_interval(interval_raw)

    templates_folder = os.environ.get("OBSIDIAN_TEMPLATES_FOLDER", "Templates")

    return Config(
        vault_path=vault_path,
        git_autocommit_interval=git_autocommit_interval,
        templates_folder=templates_folder,
    )
