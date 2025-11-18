"""
Tests for LLM system prompt loading from documentation.

This ensures the load_system_prompt_from_docs() function correctly reads
the system prompt from the ai-survey-generator.md documentation file.
"""

from pathlib import Path

from django.conf import settings

from checktick_app.surveys.llm_client import (
    _FALLBACK_SYSTEM_PROMPT,
    load_system_prompt_from_docs,
)


class TestSystemPromptLoading:
    """Test suite for system prompt loading from documentation."""

    def test_load_system_prompt_from_docs_succeeds(self):
        """Test that system prompt loads successfully from documentation."""
        prompt = load_system_prompt_from_docs()

        # Should not be empty
        assert prompt, "System prompt should not be empty"

        # Should be a string
        assert isinstance(prompt, str), "System prompt should be a string"

        # Should contain key phrases that identify it as the healthcare survey prompt
        assert (
            "healthcare survey" in prompt.lower()
        ), "System prompt should mention healthcare survey"
        assert (
            "markdown" in prompt.lower()
        ), "System prompt should mention markdown format"

    def test_system_prompt_contains_expected_sections(self):
        """Test that the loaded prompt contains expected instruction sections."""
        prompt = load_system_prompt_from_docs()

        # Check for key sections that should be in a survey generation prompt
        expected_phrases = [
            "question",  # Should mention questions
            "survey",  # Should mention surveys
            "markdown",  # Should specify markdown format
        ]

        for phrase in expected_phrases:
            assert (
                phrase.lower() in prompt.lower()
            ), f"System prompt should contain '{phrase}'"

    def test_system_prompt_not_empty_lines(self):
        """Test that the loaded prompt doesn't start or end with empty lines."""
        prompt = load_system_prompt_from_docs()

        # Should not start with newline
        assert not prompt.startswith(
            "\n"
        ), "System prompt should not start with newline"

        # Should not end with excessive newlines
        assert not prompt.endswith(
            "\n\n"
        ), "System prompt should not end with multiple newlines"

    def test_fallback_prompt_exists(self):
        """Test that the fallback prompt is defined and valid."""
        assert _FALLBACK_SYSTEM_PROMPT, "Fallback system prompt should not be empty"
        assert isinstance(
            _FALLBACK_SYSTEM_PROMPT, str
        ), "Fallback system prompt should be a string"

    def test_documentation_file_exists(self):
        """Test that the ai-survey-generator.md documentation file exists."""
        docs_path = Path(settings.BASE_DIR) / "docs" / "ai-survey-generator.md"
        assert docs_path.exists(), f"Documentation file should exist at {docs_path}"

    def test_documentation_contains_markers(self):
        """Test that the documentation file contains the required markers."""
        docs_path = Path(settings.BASE_DIR) / "docs" / "ai-survey-generator.md"
        content = docs_path.read_text(encoding="utf-8")

        start_marker = "<!-- SYSTEM_PROMPT_START -->"
        end_marker = "<!-- SYSTEM_PROMPT_END -->"

        assert (
            start_marker in content
        ), f"Documentation should contain {start_marker} marker"
        assert (
            end_marker in content
        ), f"Documentation should contain {end_marker} marker"

        # Check that markers are in correct order
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        assert (
            start_idx < end_idx
        ), "SYSTEM_PROMPT_START should come before SYSTEM_PROMPT_END"

        # Check that there's content between markers
        content_between = content[start_idx + len(start_marker) : end_idx].strip()
        assert content_between, "There should be content between the markers"

    def test_loaded_prompt_matches_doc_content(self):
        """Test that the loaded prompt matches what's in the documentation."""
        docs_path = Path(settings.BASE_DIR) / "docs" / "ai-survey-generator.md"
        content = docs_path.read_text(encoding="utf-8")

        start_marker = "<!-- SYSTEM_PROMPT_START -->"
        end_marker = "<!-- SYSTEM_PROMPT_END -->"

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        # Extract expected prompt from docs
        expected_prompt = content[start_idx + len(start_marker) : end_idx].strip()

        # Clean up expected prompt (same logic as load_system_prompt_from_docs)
        lines = expected_prompt.split("\n")
        cleaned_lines = [line.rstrip() for line in lines]
        expected_prompt = "\n".join(cleaned_lines).strip()

        # Get the loaded prompt
        loaded_prompt = load_system_prompt_from_docs()

        # They should match
        assert (
            loaded_prompt == expected_prompt
        ), "Loaded prompt should match the content in documentation"

    def test_prompt_loading_is_deterministic(self):
        """Test that loading the prompt multiple times gives the same result."""
        prompt1 = load_system_prompt_from_docs()
        prompt2 = load_system_prompt_from_docs()

        assert (
            prompt1 == prompt2
        ), "Loading prompt multiple times should return identical results"

    def test_fallback_used_when_file_missing(self, tmp_path, monkeypatch):
        """Test that fallback prompt is used when documentation file doesn't exist."""
        # Create a temporary settings.BASE_DIR that points to non-existent docs
        fake_base_dir = tmp_path / "fake_checktick_app"
        fake_base_dir.mkdir()

        # Monkeypatch settings.BASE_DIR
        monkeypatch.setattr(settings, "BASE_DIR", fake_base_dir)

        # Should return fallback prompt
        prompt = load_system_prompt_from_docs()

        assert (
            prompt == _FALLBACK_SYSTEM_PROMPT
        ), "Should return fallback prompt when file doesn't exist"

    def test_fallback_used_when_markers_missing(self, tmp_path, monkeypatch):
        """Test that fallback prompt is used when markers are not in the file."""
        # Create a temporary docs directory with a file missing markers
        fake_base_dir = tmp_path / "fake_checktick_app"
        fake_docs_dir = tmp_path / "docs"
        fake_base_dir.mkdir()
        fake_docs_dir.mkdir()

        # Create a docs file without markers
        docs_file = fake_docs_dir / "ai-survey-generator.md"
        docs_file.write_text(
            "# AI Survey Generator\n\nThis is documentation without markers."
        )

        # Monkeypatch settings.BASE_DIR
        monkeypatch.setattr(settings, "BASE_DIR", fake_base_dir)

        # Should return fallback prompt
        prompt = load_system_prompt_from_docs()

        assert (
            prompt == _FALLBACK_SYSTEM_PROMPT
        ), "Should return fallback prompt when markers are missing"

    def test_system_prompt_has_reasonable_length(self):
        """Test that the system prompt is neither too short nor absurdly long."""
        prompt = load_system_prompt_from_docs()

        # Should be at least 100 characters (a meaningful prompt)
        assert len(prompt) >= 100, "System prompt should be at least 100 characters"

        # Should not be more than 10000 characters (sanity check)
        assert len(prompt) <= 10000, "System prompt should not exceed 10000 characters"

    def test_system_prompt_no_html_markers_in_output(self):
        """Test that HTML comment markers are not included in the loaded prompt."""
        prompt = load_system_prompt_from_docs()

        # Should not contain HTML comment markers
        assert (
            "<!--" not in prompt
        ), "System prompt should not contain HTML comment start marker"
        assert (
            "-->" not in prompt
        ), "System prompt should not contain HTML comment end marker"
        assert (
            "SYSTEM_PROMPT_START" not in prompt
        ), "System prompt should not contain START marker text"
        assert (
            "SYSTEM_PROMPT_END" not in prompt
        ), "System prompt should not contain END marker text"
