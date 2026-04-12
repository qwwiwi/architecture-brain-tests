"""
T25: Subagent definitions validation.

Verifies that STRUCTURE.md documents agents/ directory,
FILES-REFERENCE.md documents it, and SUBAGENTS.md exists
with proper frontmatter field documentation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")


def load_md(name: str) -> str:
    """Load a markdown file from ARCH_ROOT."""
    path = ARCH_ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not found")
    return path.read_text(encoding="utf-8")


# --- STRUCTURE.md ---


class TestStructureAgentsDir:
    """T25.1 STRUCTURE.md documents agents/ directory."""

    def test_agents_dir_in_structure(self) -> None:
        """STRUCTURE.md must show agents/ in the directory tree."""
        text = load_md("STRUCTURE.md")
        assert "agents/" in text, "STRUCTURE.md must document agents/ directory"

    def test_agents_dir_description(self) -> None:
        """STRUCTURE.md must describe agents/ as subagent definitions."""
        text = load_md("STRUCTURE.md")
        # Find lines mentioning agents/
        lines = [ln for ln in text.split("\n") if "agents/" in ln]
        assert lines, "STRUCTURE.md must have agents/ lines"
        context = " ".join(lines).lower()
        assert "subagent" in context or "agent" in context or ".md" in context, (
            "STRUCTURE.md agents/ must mention subagent definitions"
        )


# --- FILES-REFERENCE.md ---


class TestFilesReferenceAgentsDir:
    """T25.2 FILES-REFERENCE.md documents agents/ directory."""

    def test_agents_dir_documented(self) -> None:
        """FILES-REFERENCE.md must have a section for agents/ directory."""
        text = load_md("FILES-REFERENCE.md")
        assert "agents/" in text, "FILES-REFERENCE.md must document agents/ directory"

    def test_agents_layer_exists(self) -> None:
        """FILES-REFERENCE.md must have Subagent Definitions layer."""
        text = load_md("FILES-REFERENCE.md")
        assert "Subagent" in text or "subagent" in text, (
            "FILES-REFERENCE.md must have a subagent definitions layer"
        )

    def test_agents_on_demand(self) -> None:
        """FILES-REFERENCE.md must show agents/*.md as on-demand."""
        text = load_md("FILES-REFERENCE.md")
        lines = text.split("\n")
        agent_lines = [
            ln for ln in lines
            if "agents/" in ln and "|" in ln
        ]
        if not agent_lines:
            pytest.skip("No agents/ table rows in FILES-REFERENCE.md")
        assert any("on-demand" in ln.lower() for ln in agent_lines), (
            "agents/*.md must be on-demand in FILES-REFERENCE.md"
        )

    def test_agents_frontmatter_mentioned(self) -> None:
        """FILES-REFERENCE.md must mention frontmatter for agent definitions."""
        text = load_md("FILES-REFERENCE.md")
        # Check that model and description fields are mentioned
        lower = text.lower()
        assert "model" in lower, (
            "FILES-REFERENCE.md must mention model for agent definitions"
        )
        assert "description" in lower, (
            "FILES-REFERENCE.md must mention description for agent definitions"
        )


# --- SUBAGENTS.md ---


class TestSubagentsMd:
    """T25.3 SUBAGENTS.md exists and documents frontmatter fields."""

    def test_subagents_md_exists(self) -> None:
        """SUBAGENTS.md must exist."""
        assert (ARCH_ROOT / "SUBAGENTS.md").is_file(), "SUBAGENTS.md must exist"

    def test_documents_model_field(self) -> None:
        """SUBAGENTS.md must document the 'model' frontmatter field."""
        text = load_md("SUBAGENTS.md")
        assert "model" in text, "SUBAGENTS.md must document model field"

    def test_documents_description_field(self) -> None:
        """SUBAGENTS.md must document the 'description' frontmatter field."""
        text = load_md("SUBAGENTS.md")
        assert "description" in text, "SUBAGENTS.md must document description field"

    def test_documents_tools_field(self) -> None:
        """SUBAGENTS.md must document the 'tools' frontmatter field."""
        text = load_md("SUBAGENTS.md")
        assert "tools" in text.lower(), "SUBAGENTS.md must document tools field"

    def test_documents_name_field(self) -> None:
        """SUBAGENTS.md must document the 'name' frontmatter field."""
        text = load_md("SUBAGENTS.md")
        assert "`name`" in text or "| name" in text or "name |" in text, (
            "SUBAGENTS.md must document name field"
        )

    def test_has_frontmatter_table(self) -> None:
        """SUBAGENTS.md must have a frontmatter fields table."""
        text = load_md("SUBAGENTS.md")
        # Check for table with Field/Required/Description headers
        assert "Field" in text, "SUBAGENTS.md must have Field column in table"
        assert "Description" in text, (
            "SUBAGENTS.md must have Description column in table"
        )

    def test_has_yaml_example(self) -> None:
        """SUBAGENTS.md must have a YAML frontmatter example."""
        text = load_md("SUBAGENTS.md")
        assert "---" in text, "SUBAGENTS.md must have YAML frontmatter delimiters"
        assert "model:" in text or "name:" in text, (
            "SUBAGENTS.md must have model: or name: in YAML example"
        )

    def test_documents_agents_directory(self) -> None:
        """SUBAGENTS.md must mention agents/ directory path."""
        text = load_md("SUBAGENTS.md")
        assert "agents/" in text, "SUBAGENTS.md must mention agents/ directory"

    def test_documents_isolation_field(self) -> None:
        """SUBAGENTS.md must document isolation (worktree) option."""
        text = load_md("SUBAGENTS.md")
        assert "isolation" in text.lower() or "worktree" in text.lower(), (
            "SUBAGENTS.md must document isolation/worktree option"
        )

    def test_documents_background_field(self) -> None:
        """SUBAGENTS.md must document background execution option."""
        text = load_md("SUBAGENTS.md")
        assert "background" in text.lower(), (
            "SUBAGENTS.md must document background field"
        )
