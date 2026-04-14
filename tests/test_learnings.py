"""T23: Learnings -- self-improvement feedback loop.

Tests:
- LEARNINGS.md exists in architecture repo with correct structure
- LEARNINGS.md.template exists in learnings repo
- Table has all 9 columns
- All 5 learning types documented with actions
- Access zones (RED, YELLOW, GREEN) with correct files
- Repeats metric described (0 = works, >0 = strengthen, 7d merge)
- Git workflow: branch per agent, commit prefix [agent]
- Minimum 5 triggers documented (incl. self-diagnosis)
- Integration sections for CLAUDE.md and AGENTS.md
- Template has structured table header
- Commit format [agent] Learning #N described
- Repo structure: agent folders + templates/
- Boot sequence: review last 10 entries at session start
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_REPO = Path(__file__).parent.parent.parent / "public-architecture-claude-code"
LEARNINGS_REPO = Path(__file__).parent.parent.parent / "learnings"

LEARNINGS_DOC = ARCH_REPO / "LEARNINGS.md"
LEARNINGS_TEMPLATE = LEARNINGS_REPO / "templates" / "LEARNINGS.template.md"

TABLE_COLUMNS = [
    "#",
    "Date",
    "Type",
    "Context",
    "Error",
    "Rule",
    "Repeats",
    "Applied to",
    "Commit",
]

LEARNING_TYPES = [
    "tool",
    "behavior",
    "workflow",
    "architecture",
    "communication",
]

REQUIRED_TRIGGERS = [
    "operator correct",
    "error pattern",
    "new tool",
    "architecture decision",
    "self-diagnosis",
]

TYPE_ACTIONS = {
    "tool": "TOOLS.md",
    "behavior": "feedback_",
    "workflow": "AGENTS.md",
    "architecture": "decisions.md",
    "communication": "rules.md",
}

EXPECTED_AGENT_DIRS = [
    "thrall",
    "arthas",
    "silvana",
    "kaelthas",
]

ACCESS_ZONES = {
    "RED": ["CLAUDE.md", "rules.md", "USER.md"],
    "YELLOW": ["AGENTS.md", "TOOLS.md"],
    "GREEN": ["LEARNINGS.md"],
}


class TestLearningsDocExists:
    """T23.1: LEARNINGS.md existence."""

    def test_learnings_doc_exists(self) -> None:
        """LEARNINGS.md exists in architecture repo."""
        assert LEARNINGS_DOC.is_file(), (
            f"Missing LEARNINGS.md at {LEARNINGS_DOC}"
        )


class TestLearningsTemplateExists:
    """T23.2: LEARNINGS.md.template existence."""

    def test_learnings_template_exists(self) -> None:
        """LEARNINGS.md.template exists in learnings repo."""
        assert LEARNINGS_TEMPLATE.is_file(), (
            f"Missing template at {LEARNINGS_TEMPLATE}"
        )


class TestLearningsTableColumns:
    """T23.3: Table contains all 9 columns."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text()

    def test_learnings_table_columns(self, doc_text: str) -> None:
        """Table header contains all 9 required columns."""
        # Find a markdown table header line containing column names
        table_lines = [
            line for line in doc_text.split("\n")
            if "|" in line and "---" not in line
        ]
        # Join all table header lines into one searchable block
        table_text = " ".join(table_lines)
        for col in TABLE_COLUMNS:
            assert col in table_text, (
                f"Column '{col}' not found in LEARNINGS.md table"
            )

    def test_table_has_exactly_9_columns(self, doc_text: str) -> None:
        """Main table header has exactly 9 columns."""
        # Find the format table (the one with #, Date, Type...)
        for line in doc_text.split("\n"):
            if "| # |" in line and "Date" in line and "Type" in line:
                # Count pipe-separated cells
                cols = [c.strip() for c in line.split("|") if c.strip()]
                assert len(cols) == 9, (
                    f"Expected 9 columns, found {len(cols)}: {cols}"
                )
                return
        pytest.fail("No table header with '| # | Date | Type |' found")


class TestLearningsTypesDocumented:
    """T23.4: All 5 learning types documented."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text().lower()

    @pytest.mark.parametrize("learning_type", LEARNING_TYPES)
    def test_learnings_types_documented(
        self, doc_text: str, learning_type: str
    ) -> None:
        """Each learning type is documented in LEARNINGS.md."""
        assert learning_type in doc_text, (
            f"Type '{learning_type}' not documented in LEARNINGS.md"
        )


class TestLearningsAccessZones:
    """T23.5: Access zones RED, YELLOW, GREEN."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text()

    @pytest.mark.parametrize("zone", ["RED", "YELLOW", "GREEN"])
    def test_zone_exists(self, doc_text: str, zone: str) -> None:
        """Each access zone is defined."""
        assert zone in doc_text, (
            f"Access zone '{zone}' not found in LEARNINGS.md"
        )

    @pytest.mark.parametrize(
        "zone,files",
        list(ACCESS_ZONES.items()),
    )
    def test_zone_files(
        self, doc_text: str, zone: str, files: list[str]
    ) -> None:
        """Each zone lists its expected files."""
        for filename in files:
            assert filename in doc_text, (
                f"File '{filename}' not listed in {zone} zone"
            )


class TestLearningsRepeatsMetric:
    """T23.6: Repeats metric described."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text().lower()

    def test_learnings_repeats_metric(self, doc_text: str) -> None:
        """Repeats metric describes 0 = works, >0 = strengthen."""
        # Check the core concepts are present
        assert "repeats" in doc_text, "Repeats metric not mentioned"
        assert "0" in doc_text, "Value 0 not mentioned for Repeats"
        assert "strengthen" in doc_text, (
            "'strengthen' action not mentioned for Repeats > 0"
        )

    def test_repeats_merge_rule(self, doc_text: str) -> None:
        """Repeats = 0 after 7 days leads to merge."""
        assert "merge" in doc_text and "main" in doc_text, (
            "Rule 'merge to main after 7 days' not described"
        )


class TestLearningsGitWorkflow:
    """T23.7: Git workflow described."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text()

    def test_branch_per_agent(self, doc_text: str) -> None:
        """Branch-per-agent strategy described."""
        text_lower = doc_text.lower()
        assert "branch" in text_lower, "Branch strategy not described"
        # Should mention agent-specific branches
        assert re.search(
            r"(agent|thrall|silvana|arthas)/learnings", doc_text.lower()
        ), "Agent-specific branch pattern not found"

    def test_commit_prefix(self, doc_text: str) -> None:
        """Commit prefix [agent] described."""
        assert re.search(
            r"\[.+\]\s+Learning\s+#\d+", doc_text
        ), "Commit format '[agent] Learning #N' not described"


class TestLearningsTriggers:
    """T23.8: Minimum 5 triggers documented."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text().lower()

    def test_learnings_triggers_count(self, doc_text: str) -> None:
        """At least 5 triggers documented in Triggers section."""
        # Find lines in the triggers table
        trigger_section = doc_text.split("## trigger")
        assert len(trigger_section) >= 2, (
            "No '## Triggers' section found"
        )
        trigger_text = trigger_section[1].split("##")[0]
        # Count table rows (lines with | that aren't headers/separators)
        rows = [
            line for line in trigger_text.split("\n")
            if "|" in line and "---" not in line and "trigger" not in line.lower().split("|")[0]
        ]
        assert len(rows) >= 5, (
            f"Expected at least 5 triggers, found {len(rows)}"
        )

    @pytest.mark.parametrize("trigger", REQUIRED_TRIGGERS)
    def test_specific_trigger_documented(
        self, doc_text: str, trigger: str
    ) -> None:
        """Each required trigger is mentioned."""
        assert trigger in doc_text, (
            f"Trigger '{trigger}' not documented in LEARNINGS.md"
        )


class TestLearningsIntegrationClaudeMd:
    """T23.9: Integration with CLAUDE.md section."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text()

    def test_learnings_integration_claude_md(self, doc_text: str) -> None:
        """Section about integration with CLAUDE.md exists."""
        assert "Integration with CLAUDE.md" in doc_text, (
            "No 'Integration with CLAUDE.md' section"
        )

    def test_claude_md_integration_has_loop(self, doc_text: str) -> None:
        """CLAUDE.md integration section describes self-improvement loop."""
        text_lower = doc_text.lower()
        assert "self-improvement" in text_lower or "loop" in text_lower, (
            "Self-improvement loop not described in CLAUDE.md integration"
        )


class TestLearningsIntegrationAgentsMd:
    """T23.10: Integration with AGENTS.md section."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text()

    def test_learnings_integration_agents_md(self, doc_text: str) -> None:
        """Section about integration with AGENTS.md exists."""
        assert "Integration with AGENTS.md" in doc_text, (
            "No 'Integration with AGENTS.md' section"
        )

    def test_agents_md_integration_has_self_learning(
        self, doc_text: str
    ) -> None:
        """AGENTS.md integration section describes self-learning."""
        # Find the AGENTS.md integration section
        idx = doc_text.find("Integration with AGENTS.md")
        assert idx > -1
        section = doc_text[idx:]
        assert "Self-Learning" in section, (
            "Self-Learning not described in AGENTS.md integration"
        )


class TestLearningsTemplateFormat:
    """T23.11: Template has structured table header."""

    @pytest.fixture
    def template_text(self) -> str:
        return LEARNINGS_TEMPLATE.read_text()

    def test_learnings_template_format(self, template_text: str) -> None:
        """Template contains structured table with all 9 columns."""
        for col in TABLE_COLUMNS:
            assert col in template_text, (
                f"Column '{col}' missing from template"
            )

    def test_template_has_agent_placeholder(
        self, template_text: str
    ) -> None:
        """Template has {Agent Name} placeholder."""
        assert "{Agent Name}" in template_text, (
            "Template missing {Agent Name} placeholder"
        )

    def test_template_has_metric_description(
        self, template_text: str
    ) -> None:
        """Template describes Repeats metric."""
        assert "Repeats" in template_text, (
            "Template missing Repeats metric description"
        )


class TestLearningsCommitFormat:
    """T23.12: Commit format [agent] Learning #N described."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text()

    def test_learnings_commit_format(self, doc_text: str) -> None:
        """Commit format [agent] Learning #N is described."""
        # Should have examples like [thrall] Learning #4: ...
        pattern = r"\[(\w+)\]\s+Learning\s+#\d+:"
        matches = re.findall(pattern, doc_text)
        assert len(matches) >= 1, (
            "No commit format examples '[agent] Learning #N:' found"
        )

    def test_commit_section_exists(self, doc_text: str) -> None:
        """Commit format section exists."""
        assert "Commit format" in doc_text or "commit format" in doc_text.lower(), (
            "No 'Commit format' section found"
        )


class TestLearningsTypeActions:
    """T23.13: Each type maps to a specific action/file."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text()

    @pytest.mark.parametrize(
        "learning_type,target_file",
        list(TYPE_ACTIONS.items()),
    )
    def test_type_maps_to_action(
        self, doc_text: str, learning_type: str, target_file: str
    ) -> None:
        """Each learning type has an associated target file/action."""
        # Find the Types and Actions section
        assert target_file in doc_text, (
            f"Type '{learning_type}' action target "
            f"'{target_file}' not found in LEARNINGS.md"
        )


class TestLearningsRepoStructure:
    """T23.14: Learnings repo has correct directory structure."""

    @pytest.mark.parametrize("agent_dir", EXPECTED_AGENT_DIRS)
    def test_agent_directory_exists(self, agent_dir: str) -> None:
        """Each agent has a dedicated directory in learnings repo."""
        path = LEARNINGS_REPO / agent_dir
        assert path.is_dir(), (
            f"Missing agent directory: {agent_dir}/"
        )

    @pytest.mark.parametrize("agent_dir", EXPECTED_AGENT_DIRS)
    def test_agent_learnings_file_exists(self, agent_dir: str) -> None:
        """Each agent directory contains LEARNINGS.md."""
        path = LEARNINGS_REPO / agent_dir / "LEARNINGS.md"
        assert path.is_file(), (
            f"Missing {agent_dir}/LEARNINGS.md"
        )

    def test_templates_directory_exists(self) -> None:
        """templates/ directory exists in learnings repo."""
        assert (LEARNINGS_REPO / "templates").is_dir(), (
            "Missing templates/ directory in learnings repo"
        )

    def test_readme_exists(self) -> None:
        """README.md exists in learnings repo."""
        assert (LEARNINGS_REPO / "README.md").is_file(), (
            "Missing README.md in learnings repo"
        )

    def test_readme_describes_format(self) -> None:
        """README.md describes the table format."""
        text = (LEARNINGS_REPO / "README.md").read_text()
        for col in ["Type", "Repeats", "Context"]:
            assert col in text, (
                f"README.md missing column description: {col}"
            )


class TestLearningsBootSequence:
    """T23.15: Boot sequence -- review last 10 entries at session start."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text()

    def test_boot_sequence_described(self, doc_text: str) -> None:
        """Boot/session start review is described."""
        text_lower = doc_text.lower()
        assert "session start" in text_lower or "boot" in text_lower, (
            "Boot/session start review not described"
        )

    def test_last_10_entries_mentioned(self, doc_text: str) -> None:
        """Review last 10 entries at session start is specified."""
        assert "10" in doc_text, (
            "Number of entries to review (10) not mentioned"
        )
        text_lower = doc_text.lower()
        assert "last" in text_lower or "review" in text_lower, (
            "'last N entries' review pattern not described"
        )


class TestLearningsSelfDiagnosis:
    """T23.16: Self-diagnosis trigger documented."""

    @pytest.fixture
    def doc_text(self) -> str:
        return LEARNINGS_DOC.read_text().lower()

    def test_self_diagnosis_trigger(self, doc_text: str) -> None:
        """Self-diagnosis (crash, timeout) is a documented trigger."""
        assert "self-diagnosis" in doc_text or (
            "crash" in doc_text and "timeout" in doc_text
        ), "Self-diagnosis trigger not documented"

    def test_at_least_5_triggers(self, doc_text: str) -> None:
        """At least 5 triggers are documented."""
        found = sum(
            1 for t in REQUIRED_TRIGGERS if t in doc_text
        )
        assert found >= 5, (
            f"Expected at least 5 triggers, found {found}"
        )
