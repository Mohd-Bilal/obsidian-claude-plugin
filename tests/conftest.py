import pytest
from pathlib import Path
from obsidian_mcp.vault import Vault


@pytest.fixture
def vault_dir(tmp_path) -> Path:
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / "Templates").mkdir()
    (tmp_path / "attachments").mkdir()
    return tmp_path


@pytest.fixture
def vault(vault_dir) -> Vault:
    return Vault(vault_dir)


@pytest.fixture(autouse=True)
def set_vault_env(vault_dir, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault_dir))
