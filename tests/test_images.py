"""Tests for image embedding and importing."""

import pytest
from pathlib import Path

from obsidian_mcp.images import embed_image, import_image
from obsidian_mcp.errors import AttachmentNotFoundError, NoteNotFoundError


class TestEmbedImage:
    def test_embed_existing_image(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("My note.")
        (vault_dir / "attachments" / "photo.png").write_bytes(b"fake image")
        result = embed_image(vault, "note.md", "photo.png")
        assert result == "note.md"
        content = (vault_dir / "note.md").read_text()
        assert "![[photo.png]]" in content

    def test_embed_missing_image_raises(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("My note.")
        with pytest.raises(AttachmentNotFoundError):
            embed_image(vault, "note.md", "nonexistent.png")

    def test_embed_missing_note_raises(self, vault, vault_dir):
        (vault_dir / "attachments" / "photo.png").write_bytes(b"img")
        with pytest.raises(NoteNotFoundError):
            embed_image(vault, "nonexistent.md", "photo.png")

    def test_embed_appends_to_existing_content(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("Original content")
        (vault_dir / "attachments" / "img.jpg").write_bytes(b"data")
        embed_image(vault, "note.md", "img.jpg")
        content = (vault_dir / "note.md").read_text()
        assert content.startswith("Original content")


class TestImportImage:
    def test_import_external_image(self, vault, vault_dir, tmp_path):
        (vault_dir / "note.md").write_text("My note.")
        ext_image = tmp_path / "photo.jpg"
        ext_image.write_bytes(b"fake jpeg data")

        result = import_image(vault, "note.md", str(ext_image))
        assert result == "attachments/photo.jpg"
        assert (vault_dir / "attachments" / "photo.jpg").exists()
        content = (vault_dir / "note.md").read_text()
        assert "![[photo.jpg]]" in content

    def test_import_to_custom_subfolder(self, vault, vault_dir, tmp_path):
        (vault_dir / "note.md").write_text("My note.")
        ext_image = tmp_path / "diagram.png"
        ext_image.write_bytes(b"png data")

        result = import_image(vault, "note.md", str(ext_image), subfolder="images")
        assert result == "images/diagram.png"
        assert (vault_dir / "images" / "diagram.png").exists()

    def test_import_missing_external_raises(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("note")
        with pytest.raises(FileNotFoundError):
            import_image(vault, "note.md", "/nonexistent/image.png")

    def test_import_missing_note_raises(self, vault, vault_dir, tmp_path):
        ext_image = tmp_path / "photo.jpg"
        ext_image.write_bytes(b"data")
        with pytest.raises(NoteNotFoundError):
            import_image(vault, "nonexistent.md", str(ext_image))
