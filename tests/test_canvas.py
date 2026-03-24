"""Tests for canvas file CRUD operations."""

import json
import pytest
from pathlib import Path

from obsidian_mcp.canvas import (
    read_canvas, create_canvas, update_canvas, delete_canvas
)
from obsidian_mcp.errors import CanvasParseError


class TestReadCanvas:
    def test_read_valid_canvas(self, vault, vault_dir):
        data = {"nodes": [], "edges": []}
        (vault_dir / "board.canvas").write_text(json.dumps(data))
        result = read_canvas(vault, "board")
        assert result == data

    def test_read_with_extension(self, vault, vault_dir):
        data = {"nodes": [{"id": "abc", "type": "text"}], "edges": []}
        (vault_dir / "my.canvas").write_text(json.dumps(data))
        result = read_canvas(vault, "my.canvas")
        assert result["nodes"][0]["id"] == "abc"

    def test_read_missing_raises(self, vault):
        with pytest.raises(FileNotFoundError):
            read_canvas(vault, "nonexistent")

    def test_read_malformed_json_raises(self, vault, vault_dir):
        (vault_dir / "bad.canvas").write_text("{not valid json")
        with pytest.raises(CanvasParseError):
            read_canvas(vault, "bad")


class TestCreateCanvas:
    def test_create_empty_canvas(self, vault, vault_dir):
        result = create_canvas(vault, "new_board")
        assert result == "new_board.canvas"
        assert (vault_dir / "new_board.canvas").exists()
        data = json.loads((vault_dir / "new_board.canvas").read_text())
        assert data == {"nodes": [], "edges": []}

    def test_create_with_nodes(self, vault, vault_dir):
        nodes = [{"id": "node1", "type": "text", "text": "Hello"}]
        result = create_canvas(vault, "board", nodes=nodes)
        data = json.loads((vault_dir / "board.canvas").read_text())
        assert data["nodes"] == nodes

    def test_create_duplicate_raises(self, vault, vault_dir):
        (vault_dir / "existing.canvas").write_text("{}")
        with pytest.raises(FileExistsError):
            create_canvas(vault, "existing")

    def test_create_with_extension(self, vault, vault_dir):
        result = create_canvas(vault, "board.canvas")
        assert (vault_dir / "board.canvas").exists()

    def test_create_in_subdirectory(self, vault, vault_dir):
        result = create_canvas(vault, "subdir/board")
        assert (vault_dir / "subdir" / "board.canvas").exists()


class TestUpdateCanvas:
    def test_update_canvas(self, vault, vault_dir):
        (vault_dir / "board.canvas").write_text('{"nodes":[],"edges":[]}')
        new_data = {"nodes": [{"id": "x"}], "edges": []}
        result = update_canvas(vault, "board", new_data)
        assert result == "board.canvas"
        data = json.loads((vault_dir / "board.canvas").read_text())
        assert data["nodes"] == [{"id": "x"}]

    def test_update_missing_raises(self, vault):
        with pytest.raises(FileNotFoundError):
            update_canvas(vault, "nonexistent", {"nodes": [], "edges": []})


class TestDeleteCanvas:
    def test_delete_canvas(self, vault, vault_dir):
        (vault_dir / "board.canvas").write_text("{}")
        result = delete_canvas(vault, "board")
        assert result == "board.canvas"
        assert not (vault_dir / "board.canvas").exists()

    def test_delete_missing_raises(self, vault):
        with pytest.raises(FileNotFoundError):
            delete_canvas(vault, "nonexistent")
