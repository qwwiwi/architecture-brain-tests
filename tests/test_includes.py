"""
T24: @include directive tests.

Verifies that CLAUDE.md.template has exactly 4 @include directives,
that AGENTS.md and TOOLS.md are on-demand (not included at startup),
and that documentation consistently reflects this.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")
TEMPLATES_DIR = ARCH_ROOT / "templates"

EXPECTED_INCLUDES = [
    "core/USER.md",
    "core/rules.md",
    "core/warm/decisions.md",
    "core/hot/handoff.md",
]

ON_DEMAND_FILES = [
    "AGENTS.md",
    "TOOLS.md",
]


def load_md(name: str) -> str:
    """Load a markdown file from ARCH_ROOT."""
    path = ARCH_ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not found")
    return path.read_text(encoding="utf-8")


def load_template(name: str) -> str:
    """Load a template file."""
    path = TEMPLATES_DIR / name
    if not path.exists():
        pytest.skip(f"templates/{name} not found")
    return path.read_text(encoding="utf-8")


def extract_includes(text: str) -> list[str]:
    """Extract @include directives (lines starting with @)."""
    return re.findall(r"^@(\S+)$", text, re.MULTILINE)


# --- CLAUDE.md.template includes ---


class TestCLAUDETemplateIncludes:
    """T24.1 CLAUDE.md.template has exactly 4 @include directives."""

    def test_exactly_4_includes(self) -> None:
        """CLAUDE.md.template must have exactly 4 @include lines."""
        text = load_template("CLAUDE.md.template")
        includes = extract_includes(text)
        assert len(includes) == 4, (
            f"Expected 4 @include directives, found {len(includes)}: {includes}"
        )

    @pytest.mark.parametrize("include_path", EXPECTED_INCLUDES)
    def test_expected_include_present(self, include_path: str) -> None:
        """Each of the 4 expected includes must be present."""
        text = load_template("CLAUDE.md.template")
        includes = extract_includes(text)
        assert include_path in includes, (
            f"@{include_path} not found in CLAUDE.md.template includes: {includes}"
        )

    def test_agents_md_not_included(self) -> None:
        """AGENTS.md must NOT be in @include directives (on-demand only)."""
        text = load_template("CLAUDE.md.template")
        includes = extract_includes(text)
        agents_includes = [i for i in includes if "AGENTS" in i.upper()]
        assert not agents_includes, (
            f"AGENTS.md must be on-demand, not @included: {agents_includes}"
        )

    def test_tools_md_not_included(self) -> None:
        """TOOLS.md must NOT be in @include directives (on-demand only)."""
        text = load_template("CLAUDE.md.template")
        includes = extract_includes(text)
        tools_includes = [i for i in includes if "TOOLS" in i.upper()]
        assert not tools_includes, (
            f"TOOLS.md must be on-demand, not @included: {tools_includes}"
        )

    def test_recent_md_not_included(self) -> None:
        """recent.md must NOT be in @include (handoff.md replaces it)."""
        text = load_template("CLAUDE.md.template")
        includes = extract_includes(text)
        recent_includes = [i for i in includes if "recent" in i.lower()]
        assert not recent_includes, (
            f"recent.md must not be @included (use handoff.md instead): {recent_includes}"
        )

    def test_handoff_md_is_included(self) -> None:
        """handoff.md must be in @include (replaces recent.md)."""
        text = load_template("CLAUDE.md.template")
        includes = extract_includes(text)
        handoff = [i for i in includes if "handoff" in i.lower()]
        assert handoff, "handoff.md must be @included instead of recent.md"


# --- STRUCTURE.md consistency ---


class TestStructureIncludes:
    """T24.2 STRUCTURE.md reflects 4 includes in directory tree."""

    def test_structure_shows_4_includes(self) -> None:
        """STRUCTURE.md directory tree must show exactly 4 @include paths."""
        text = load_md("STRUCTURE.md")
        # Find @include lines in the directory tree block
        tree_includes = re.findall(r"@(core/\S+\.md)", text)
        assert len(tree_includes) == 4, (
            f"STRUCTURE.md must show 4 @includes, found {len(tree_includes)}: {tree_includes}"
        )

    def test_structure_shows_handoff(self) -> None:
        """STRUCTURE.md must show handoff.md in the directory tree."""
        text = load_md("STRUCTURE.md")
        assert "handoff.md" in text, "STRUCTURE.md must reference handoff.md"

    def test_structure_agents_not_in_includes(self) -> None:
        """STRUCTURE.md @include block must not contain AGENTS.md."""
        text = load_md("STRUCTURE.md")
        # Find lines with @ that reference AGENTS
        at_agents = re.findall(r"@\S*AGENTS\S*", text)
        assert not at_agents, (
            f"STRUCTURE.md must not @include AGENTS.md: {at_agents}"
        )

    def test_structure_tools_not_in_includes(self) -> None:
        """STRUCTURE.md @include block must not contain TOOLS.md."""
        text = load_md("STRUCTURE.md")
        at_tools = re.findall(r"@\S*TOOLS\S*", text)
        assert not at_tools, (
            f"STRUCTURE.md must not @include TOOLS.md: {at_tools}"
        )


# --- ARCHITECTURE.md consistency ---


class TestArchitectureIncludes:
    """T24.3 ARCHITECTURE.md context loading shows 4 includes."""

    def test_architecture_shows_4_includes(self) -> None:
        """ARCHITECTURE.md context loading must list exactly 4 @include paths."""
        text = load_md("ARCHITECTURE.md")
        # Find @include-style references in the context loading section
        at_includes = re.findall(r"@(core/\S+\.md|tools/\S+\.md)", text)
        assert len(at_includes) == 4, (
            f"ARCHITECTURE.md must show 4 @includes, found {len(at_includes)}: {at_includes}"
        )

    def test_architecture_agents_on_demand(self) -> None:
        """ARCHITECTURE.md must show AGENTS.md as on-demand, not at startup."""
        text = load_md("ARCHITECTURE.md")
        # AGENTS.md should appear in on-demand section, not context loading
        on_demand_section = text.split("On-Demand")[-1] if "On-Demand" in text else ""
        context_section = text.split("Context Loading")[1].split("##")[0]
        in_on_demand = "AGENTS.md" in on_demand_section
        not_in_context = "AGENTS.md" not in context_section
        assert in_on_demand or not_in_context, (
            "ARCHITECTURE.md must show AGENTS.md as on-demand"
        )

    def test_architecture_tools_on_demand(self) -> None:
        """ARCHITECTURE.md must show TOOLS.md as on-demand, not at startup."""
        text = load_md("ARCHITECTURE.md")
        on_demand_section = text.split("On-Demand")[-1] if "On-Demand" in text else ""
        context_section = text.split("Context Loading")[1].split("##")[0]
        in_on_demand = "TOOLS.md" in on_demand_section
        not_in_context = "TOOLS.md" not in context_section
        assert in_on_demand or not_in_context, (
            "ARCHITECTURE.md must show TOOLS.md as on-demand"
        )


# --- FILES-REFERENCE.md consistency ---


class TestFilesReferenceIncludes:
    """T24.4 FILES-REFERENCE.md marks AGENTS.md and TOOLS.md as on-demand."""

    def test_agents_md_on_demand(self) -> None:
        """FILES-REFERENCE.md must mark AGENTS.md as on-demand, not always."""
        text = load_md("FILES-REFERENCE.md")
        lines = text.split("\n")
        agents_lines = [
            ln for ln in lines if "AGENTS.md" in ln and "|" in ln
        ]
        assert agents_lines, "FILES-REFERENCE.md must have AGENTS.md in a table"
        # At least one table row must say on-demand (Layer 2 or Context Budget)
        assert any("on-demand" in ln.lower() for ln in agents_lines), (
            "AGENTS.md must be 'on-demand' in at least one FILES-REFERENCE.md table"
        )
        # Must NOT be marked as 'always (@include)' anywhere
        assert not any("always (@include)" in ln for ln in agents_lines), (
            "AGENTS.md must not be marked as 'always (@include)'"
        )

    def test_tools_md_on_demand(self) -> None:
        """FILES-REFERENCE.md must mark TOOLS.md as on-demand, not always."""
        text = load_md("FILES-REFERENCE.md")
        lines = text.split("\n")
        tools_lines = [
            ln for ln in lines if "TOOLS.md" in ln and "|" in ln
        ]
        assert tools_lines, "FILES-REFERENCE.md must have TOOLS.md in a table"
        assert any("on-demand" in ln.lower() for ln in tools_lines), (
            "TOOLS.md must be 'on-demand' in at least one FILES-REFERENCE.md table"
        )
        assert not any("always (@include)" in ln for ln in tools_lines), (
            "TOOLS.md must not be marked as 'always (@include)'"
        )

    def test_user_md_always_loaded(self) -> None:
        """FILES-REFERENCE.md must mark USER.md as always loaded."""
        text = load_md("FILES-REFERENCE.md")
        lines = text.split("\n")
        user_lines = [
            ln for ln in lines if "USER.md" in ln and "|" in ln and "CLAUDE" not in ln
        ]
        assert user_lines, "FILES-REFERENCE.md must have USER.md in a table"
        assert any("always" in ln.lower() for ln in user_lines), (
            "USER.md must be 'always' loaded in FILES-REFERENCE.md"
        )

    def test_decisions_md_always_loaded(self) -> None:
        """FILES-REFERENCE.md must mark decisions.md as always loaded."""
        text = load_md("FILES-REFERENCE.md")
        lines = text.split("\n")
        decisions_lines = [
            ln for ln in lines if "decisions.md" in ln and "|" in ln
        ]
        assert decisions_lines, "FILES-REFERENCE.md must have decisions.md in a table"
        assert any("always" in ln.lower() for ln in decisions_lines), (
            "decisions.md must be 'always' loaded in FILES-REFERENCE.md"
        )
