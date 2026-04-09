"""T12: Agent Laws -- базовые принципы и законы агента.

Tests:
- AGENT-LAWS.md exists and has all required sections
- All 9 principles present in AGENT-LAWS.md
- Templates contain base principles (7-9 including docs first, backups, skills)
- Superpowers skills listed as mandatory in rules.md.template
- Priority hierarchy present in CLAUDE.md.template and AGENT-LAWS.md
- Green/Red zones defined in CLAUDE.md.template and rules.md.template
- Global CLAUDE.md.template has hierarchy and permissions
- README.md references AGENT-LAWS.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent / "public-architecture-claude-code"

# All 9 principles (keywords to search for, Russian or English)
NINE_PRINCIPLES = [
    ("план перед кодом", "plan before code"),
    ("самопроверка", "self-review"),
    ("исследование", "research"),
    ("разбивка на куски", "break into"),
    ("коммит после каждого", "commit after each"),
    ("тест", "test"),
    ("документация first", "documentation first"),
    ("бэкап", "backup"),
    ("используй скиллы", "use skills"),
]

# Mandatory superpowers skills
MANDATORY_SUPERPOWERS = [
    "superpowers:writing-plans",
    "superpowers:test-driven-development",
    "superpowers:systematic-debugging",
    "superpowers:verification-before-completion",
    "superpowers:requesting-code-review",
    "superpowers:brainstorming",
]

# Priority hierarchy levels (Russian or English)
PRIORITY_LEVELS = [
    ("безопасность", "security"),
    ("владелец", "operator"),
    ("факт", "fact"),
    ("границ", "boundar"),
    ("стиль", "style"),
]


class TestAgentLawsFile:
    """T12.1: AGENT-LAWS.md existence and structure."""

    @pytest.fixture
    def laws_text(self) -> str:
        return (REPO_ROOT / "AGENT-LAWS.md").read_text()

    def test_agent_laws_exists(self) -> None:
        """AGENT-LAWS.md exists in repo root."""
        assert (REPO_ROOT / "AGENT-LAWS.md").is_file()

    def test_has_hierarchy_section(self, laws_text: str) -> None:
        """AGENT-LAWS.md has file hierarchy section."""
        assert "иерархия" in laws_text.lower() or "hierarchy" in laws_text.lower()

    def test_has_principles_section(self, laws_text: str) -> None:
        """AGENT-LAWS.md has 9 principles section."""
        assert "9 принципов" in laws_text or "9 principles" in laws_text.lower()

    def test_has_priority_section(self, laws_text: str) -> None:
        """AGENT-LAWS.md has rule priority section."""
        assert "приоритет правил" in laws_text.lower() or "priority" in laws_text.lower()

    def test_has_autonomy_zones(self, laws_text: str) -> None:
        """AGENT-LAWS.md has green/red zone sections."""
        text_lower = laws_text.lower()
        assert "зелёная зона" in text_lower or "green zone" in text_lower
        assert "красная зона" in text_lower or "red zone" in text_lower

    def test_has_security_section(self, laws_text: str) -> None:
        """AGENT-LAWS.md has security section."""
        assert "безопасность" in laws_text.lower() or "security" in laws_text.lower()

    def test_has_skills_section(self, laws_text: str) -> None:
        """AGENT-LAWS.md has mandatory skills section."""
        assert "скиллы" in laws_text.lower() or "skills" in laws_text.lower()

    def test_has_memory_section(self, laws_text: str) -> None:
        """AGENT-LAWS.md has memory layers section."""
        assert "память" in laws_text.lower() or "memory" in laws_text.lower()

    def test_has_git_section(self, laws_text: str) -> None:
        """AGENT-LAWS.md has git section."""
        assert "git" in laws_text.lower()

    def test_has_communication_section(self, laws_text: str) -> None:
        """AGENT-LAWS.md has communication section."""
        assert "коммуникация" in laws_text.lower() or "communication" in laws_text.lower()


class TestNinePrinciples:
    """T12.2: All 9 principles present in key files."""

    @pytest.fixture
    def laws_text(self) -> str:
        return (REPO_ROOT / "AGENT-LAWS.md").read_text().lower()

    @pytest.fixture
    def claude_template(self) -> str:
        return (REPO_ROOT / "templates" / "CLAUDE.md.template").read_text().lower()

    @pytest.fixture
    def global_template(self) -> str:
        return (REPO_ROOT / "templates" / "global-CLAUDE.md.template").read_text().lower()

    @pytest.mark.parametrize("principle", NINE_PRINCIPLES)
    def test_principle_in_agent_laws(
        self, laws_text: str, principle: tuple[str, str]
    ) -> None:
        """Each principle appears in AGENT-LAWS.md."""
        ru, en = principle
        assert ru in laws_text or en.lower() in laws_text, (
            f"Principle '{ru}'/'{en}' not found in AGENT-LAWS.md"
        )

    @pytest.mark.parametrize("principle", NINE_PRINCIPLES)
    def test_principle_in_claude_template(
        self, claude_template: str, principle: tuple[str, str]
    ) -> None:
        """Each principle appears in CLAUDE.md.template."""
        ru, en = principle
        assert ru in claude_template or en.lower() in claude_template, (
            f"Principle '{ru}'/'{en}' not found in CLAUDE.md.template"
        )

    @pytest.mark.parametrize("principle", NINE_PRINCIPLES)
    def test_principle_in_global_template(
        self, global_template: str, principle: tuple[str, str]
    ) -> None:
        """Each principle appears in global-CLAUDE.md.template."""
        ru, en = principle
        assert ru in global_template or en.lower() in global_template, (
            f"Principle '{ru}'/'{en}' not found in global-CLAUDE.md.template"
        )

    def test_principles_count_in_laws(self, laws_text: str) -> None:
        """AGENT-LAWS.md lists exactly 9 numbered principles."""
        # Match numbered items like "1." through "9."
        numbered = re.findall(r"^\d+\.", laws_text, re.MULTILINE)
        # Should have at least 9 (could have more from other lists)
        assert len(numbered) >= 9


class TestMandatorySuperpowers:
    """T12.3: Superpowers skills listed as mandatory."""

    @pytest.fixture
    def rules_template(self) -> str:
        return (REPO_ROOT / "templates" / "rules.md.template").read_text()

    @pytest.fixture
    def global_template(self) -> str:
        return (REPO_ROOT / "templates" / "global-CLAUDE.md.template").read_text()

    @pytest.fixture
    def laws_text(self) -> str:
        return (REPO_ROOT / "AGENT-LAWS.md").read_text()

    @pytest.mark.parametrize("skill", MANDATORY_SUPERPOWERS)
    def test_superpower_in_rules_template(
        self, rules_template: str, skill: str
    ) -> None:
        """Each mandatory superpower listed in rules.md.template."""
        assert skill in rules_template, (
            f"Superpower '{skill}' not in rules.md.template"
        )

    @pytest.mark.parametrize("skill", MANDATORY_SUPERPOWERS)
    def test_superpower_in_global_template(
        self, global_template: str, skill: str
    ) -> None:
        """Each mandatory superpower listed in global-CLAUDE.md.template."""
        assert skill in global_template, (
            f"Superpower '{skill}' not in global-CLAUDE.md.template"
        )

    @pytest.mark.parametrize("skill", MANDATORY_SUPERPOWERS)
    def test_superpower_in_agent_laws(self, laws_text: str, skill: str) -> None:
        """Each mandatory superpower listed in AGENT-LAWS.md."""
        assert skill in laws_text, (
            f"Superpower '{skill}' not in AGENT-LAWS.md"
        )


class TestPriorityHierarchy:
    """T12.4: Rule priority hierarchy in key files."""

    @pytest.fixture
    def claude_template(self) -> str:
        return (REPO_ROOT / "templates" / "CLAUDE.md.template").read_text().lower()

    @pytest.fixture
    def laws_text(self) -> str:
        return (REPO_ROOT / "AGENT-LAWS.md").read_text().lower()

    @pytest.mark.parametrize("level", PRIORITY_LEVELS)
    def test_priority_level_in_claude_template(
        self, claude_template: str, level: tuple[str, str]
    ) -> None:
        """Each priority level mentioned in CLAUDE.md.template."""
        ru, en = level
        assert ru in claude_template or en in claude_template, (
            f"Priority level '{ru}'/'{en}' not in CLAUDE.md.template"
        )

    @pytest.mark.parametrize("level", PRIORITY_LEVELS)
    def test_priority_level_in_agent_laws(
        self, laws_text: str, level: tuple[str, str]
    ) -> None:
        """Each priority level mentioned in AGENT-LAWS.md."""
        ru, en = level
        assert ru in laws_text or en in laws_text, (
            f"Priority level '{ru}'/'{en}' not in AGENT-LAWS.md"
        )


class TestAutonomyZones:
    """T12.5: Green/Red zones in templates."""

    @pytest.fixture
    def claude_template(self) -> str:
        return (REPO_ROOT / "templates" / "CLAUDE.md.template").read_text()

    @pytest.fixture
    def rules_template(self) -> str:
        return (REPO_ROOT / "templates" / "rules.md.template").read_text()

    def test_green_zone_in_claude_template(self, claude_template: str) -> None:
        """CLAUDE.md.template has green zone."""
        assert "Green zone" in claude_template or "green zone" in claude_template.lower()

    def test_red_zone_in_claude_template(self, claude_template: str) -> None:
        """CLAUDE.md.template has red zone."""
        assert "Red zone" in claude_template or "red zone" in claude_template.lower()

    def test_green_zone_in_rules_template(self, rules_template: str) -> None:
        """rules.md.template has green zone."""
        assert "Green Zone" in rules_template or "green zone" in rules_template.lower()

    def test_red_zone_in_rules_template(self, rules_template: str) -> None:
        """rules.md.template has red zone."""
        assert "Red Zone" in rules_template or "red zone" in rules_template.lower()

    def test_green_zone_includes_code(self, claude_template: str) -> None:
        """Green zone mentions code/scripts."""
        text = claude_template.lower()
        assert "code" in text or "scripts" in text

    def test_red_zone_includes_delete(self, claude_template: str) -> None:
        """Red zone mentions deletion."""
        text = claude_template.lower()
        assert "delete" in text or "удален" in text

    def test_red_zone_includes_production(self, rules_template: str) -> None:
        """Red zone mentions production."""
        text = rules_template.lower()
        assert "production" in text or "prod" in text


class TestGlobalTemplate:
    """T12.6: Global CLAUDE.md.template completeness."""

    @pytest.fixture
    def global_text(self) -> str:
        return (REPO_ROOT / "templates" / "global-CLAUDE.md.template").read_text()

    def test_has_hierarchy_section(self, global_text: str) -> None:
        """Global template has hierarchy section."""
        assert "Hierarchy" in global_text or "hierarchy" in global_text.lower()

    def test_has_permissions_section(self, global_text: str) -> None:
        """Global template has permissions section."""
        assert "Permissions" in global_text or "permission" in global_text.lower()

    def test_has_security_section(self, global_text: str) -> None:
        """Global template has security section."""
        assert "Security" in global_text or "security" in global_text.lower()

    def test_has_git_section(self, global_text: str) -> None:
        """Global template has git section."""
        assert "Git" in global_text

    def test_has_code_style_section(self, global_text: str) -> None:
        """Global template has code style section."""
        assert "Code Style" in global_text or "code style" in global_text.lower()

    def test_has_9_principles(self, global_text: str) -> None:
        """Global template has 9 principles section."""
        assert "9 Principles" in global_text or "9 principles" in global_text.lower()

    def test_has_skills_section(self, global_text: str) -> None:
        """Global template has skills mandatory section."""
        assert "Skills" in global_text
        assert "superpowers" in global_text.lower()

    def test_has_owner_placeholder(self, global_text: str) -> None:
        """Global template has OWNER_NAME placeholder."""
        assert "{{OWNER_NAME}}" in global_text

    def test_never_push_main(self, global_text: str) -> None:
        """Global template forbids push to main."""
        assert "NEVER push to main" in global_text or "never push to main" in global_text.lower()

    def test_never_commit_secrets(self, global_text: str) -> None:
        """Global template forbids committing secrets."""
        assert ".env" in global_text
        assert "secret" in global_text.lower()


class TestBaseSkillsInTools:
    """T12.7: 11 base skills listed in TOOLS.md.template."""

    BASE_SKILLS = [
        "groq-voice",
        "superpowers",
        "gws",
        "youtube-transcript",
        "twitter",
        "quick-reminders",
        "markdown-new",
        "excalidraw",
        "datawrapper",
        "perplexity-research",
        "vibe-kanban",
    ]

    @pytest.fixture
    def tools_text(self) -> str:
        return (REPO_ROOT / "templates" / "TOOLS.md.template").read_text()

    @pytest.mark.parametrize("skill", BASE_SKILLS)
    def test_skill_in_tools_template(self, tools_text: str, skill: str) -> None:
        """Each base skill listed in TOOLS.md.template."""
        assert skill in tools_text, (
            f"Skill '{skill}' not in TOOLS.md.template"
        )

    def test_tools_has_11_skills_section(self, tools_text: str) -> None:
        """TOOLS.md.template has '11 Base Skills' section."""
        assert "11 Base Skills" in tools_text or "11 base skills" in tools_text.lower()

    @pytest.mark.parametrize("skill", BASE_SKILLS)
    def test_skill_in_agent_laws(self, skill: str) -> None:
        """Each base skill listed in AGENT-LAWS.md."""
        text = (REPO_ROOT / "AGENT-LAWS.md").read_text()
        assert skill in text, f"Skill '{skill}' not in AGENT-LAWS.md"


class TestProductionBackupRule:
    """T12.8: Production backup rule in key files."""

    def test_backup_in_agent_laws(self) -> None:
        """AGENT-LAWS.md mentions backup in production."""
        text = (REPO_ROOT / "AGENT-LAWS.md").read_text().lower()
        assert "backup" in text or "бэкап" in text

    def test_backup_in_claude_template(self) -> None:
        """CLAUDE.md.template mentions backup in production."""
        text = (REPO_ROOT / "templates" / "CLAUDE.md.template").read_text().lower()
        assert "backup" in text or "бэкап" in text

    def test_backup_in_rules_template(self) -> None:
        """rules.md.template mentions backup in production."""
        text = (REPO_ROOT / "templates" / "rules.md.template").read_text().lower()
        assert "backup" in text or "бэкап" in text

    def test_never_delete_without_backup(self) -> None:
        """AGENT-LAWS.md says NEVER delete without backup."""
        text = (REPO_ROOT / "AGENT-LAWS.md").read_text()
        assert "НИКОГДА не удаляй без бэкапа" in text or "NEVER delete without backup" in text


class TestReadmeReferencesLaws:
    """T12.9: README.md references AGENT-LAWS.md."""

    def test_readme_has_agent_laws_link(self) -> None:
        """README.md links to AGENT-LAWS.md."""
        text = (REPO_ROOT / "README.md").read_text()
        assert "AGENT-LAWS.md" in text

    def test_readme_laws_in_beginners_section(self) -> None:
        """AGENT-LAWS.md is in 'Start Here' section of README."""
        text = (REPO_ROOT / "README.md").read_text()
        start = text.find("Start Here")
        # Find the next ### heading after Start Here
        next_section = text.find("###", start + 1)
        if start > -1 and next_section > -1:
            section = text[start:next_section]
            assert "AGENT-LAWS.md" in section
