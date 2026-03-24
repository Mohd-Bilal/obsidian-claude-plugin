"""Tests for full-text note search."""

import pytest
from obsidian_mcp.search import search_notes


class TestSearchNotes:
    def test_finds_match(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("hello world")
        results = search_notes(vault, "hello")
        assert len(results) == 1
        assert results[0]["path"] == "note.md"
        assert results[0]["line_number"] == 1
        assert "hello world" in results[0]["snippet"]

    def test_no_match(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("hello world")
        results = search_notes(vault, "nonexistent_query")
        assert results == []

    def test_case_insensitive_default(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("Hello World")
        results = search_notes(vault, "hello world")
        assert len(results) == 1

    def test_case_sensitive_no_match(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("Hello World")
        results = search_notes(vault, "hello world", case_sensitive=True)
        assert results == []

    def test_case_sensitive_match(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("Hello World")
        results = search_notes(vault, "Hello World", case_sensitive=True)
        assert len(results) == 1

    def test_max_results_limit(self, vault, vault_dir):
        for i in range(10):
            (vault_dir / f"note_{i}.md").write_text(f"match line {i}")
        results = search_notes(vault, "match", max_results=3)
        assert len(results) <= 3

    def test_multiline_search(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("line one\nline two\nline three")
        results = search_notes(vault, "line two")
        assert len(results) == 1
        assert results[0]["line_number"] == 2

    def test_multiple_files(self, vault, vault_dir):
        (vault_dir / "a.md").write_text("keyword here")
        (vault_dir / "b.md").write_text("keyword there")
        (vault_dir / "c.md").write_text("nothing relevant")
        results = search_notes(vault, "keyword")
        paths = {r["path"] for r in results}
        assert "a.md" in paths
        assert "b.md" in paths
        assert "c.md" not in paths

    def test_regex_pattern(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("date: 2024-01-15")
        results = search_notes(vault, r"\d{4}-\d{2}-\d{2}")
        assert len(results) == 1

    def test_invalid_regex_falls_back_to_literal(self, vault, vault_dir):
        (vault_dir / "note.md").write_text("some (broken text")
        results = search_notes(vault, "(broken")
        assert len(results) == 1
