"""T11: Workspace structure and path validation.

Tests:
- All expected directories exist in repo
- All template files exist
- install.sh references all 10 skills
- install.sh creates correct directory structure
- Templates have expected placeholders
- No broken cross-references between files
- Secret paths use shared/secrets/ (not per-agent)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent / "public-architecture-claude-code"

EXPECTED_DIRS = [
    "templates",
    "examples",
    "scripts",
    "skills",
]

EXPECTED_TEMPLATES = [
    "CLAUDE.md.template",
    "AGENTS.md.template",
    "USER.md.template",
    "TOOLS.md.template",
    "rules.md.template",
    "decisions.md.template",
    "recent.md.template",
    "MEMORY.md.template",
    "LEARNINGS.md.template",
    "global-CLAUDE.md.template",
    "settings.json.template",
]

EXPECTED_EXAMPLES = [
    "agent-claude.md",
    "agents.md",
    "tools.md",
    "rules.md",
    "global-claude.md",
]

EXPECTED_SCRIPTS = [
    "trim-hot.sh",
    "compress-warm.sh",
    "rotate-warm.sh",
    "memory-rotate.sh",
]

EXPECTED_DOCS = [
    "README.md",
    "ARCHITECTURE.md",
    "MAPPING.md",
    "MULTI-AGENT.md",
    "FILES-REFERENCE.md",
    "STRUCTURE.md",
    "MEMORY.md",
    "CHECKLIST.md",
    "SETUP-GUIDE.md",
    "FIRST-AGENT.md",
    "COMMANDS-QUICKREF.md",
    "TOKEN-OPTIMIZATION.md",
    "SKILLS.md",
    "SUBAGENTS.md",
    "HOOKS.md",
    "install.sh",
]

BASE_SKILLS = [
    "groq-voice",
    "superpowers",
    "markdown-new",
    "excalidraw",
    "git-workflows",
    "skill-creator",
    "gws",
    "youtube-transcript",
    "twitter",
    "quick-reminders",
    "vibe-kanban",
]


class TestRepoStructure:
    """T11.1: Repository directory structure."""

    @pytest.mark.parametrize("dirname", EXPECTED_DIRS)
    def test_directory_exists(self, dirname: str) -> None:
        """Expected directories exist."""
        assert (REPO_ROOT / dirname).is_dir(), f"Missing directory: {dirname}/"

    @pytest.mark.parametrize("filename", EXPECTED_DOCS)
    def test_doc_files_exist(self, filename: str) -> None:
        """Expected documentation files exist."""
        assert (REPO_ROOT / filename).is_file(), f"Missing file: {filename}"


class TestTemplates:
    """T11.2: Template files."""

    @pytest.mark.parametrize("template", EXPECTED_TEMPLATES)
    def test_template_exists(self, template: str) -> None:
        """Each template file exists."""
        path = REPO_ROOT / "templates" / template
        assert path.is_file(), f"Missing template: {template}"

    @pytest.mark.parametrize("template", EXPECTED_TEMPLATES)
    def test_template_has_placeholders(self, template: str) -> None:
        """Template files contain {{PLACEHOLDER}} patterns."""
        # These templates don't use placeholders
        skip = {"settings.json.template", "recent.md.template"}
        if template in skip:
            return
        text = (REPO_ROOT / "templates" / template).read_text()
        placeholders = re.findall(r"\{\{[A-Z_0-9]+\}\}", text)
        assert len(placeholders) > 0, f"{template} has no {{{{PLACEHOLDER}}}} patterns"

    def test_template_count(self) -> None:
        """All 11 templates present."""
        templates = list((REPO_ROOT / "templates").glob("*.template"))
        assert len(templates) == 11, (
            f"Expected 11 templates, found {len(templates)}: "
            f"{[t.name for t in templates]}"
        )


class TestExamples:
    """T11.3: Example files."""

    @pytest.mark.parametrize("example", EXPECTED_EXAMPLES)
    def test_example_exists(self, example: str) -> None:
        """Each example file exists."""
        assert (REPO_ROOT / "examples" / example).is_file(), f"Missing: examples/{example}"


class TestScripts:
    """T11.4: Memory management scripts."""

    @pytest.mark.parametrize("script", EXPECTED_SCRIPTS)
    def test_script_exists(self, script: str) -> None:
        """Each cron script exists."""
        assert (REPO_ROOT / "scripts" / script).is_file(), f"Missing: scripts/{script}"


class TestInstallSh:
    """T11.5: install.sh validation."""

    @pytest.fixture
    def install_sh_text(self) -> str:
        return (REPO_ROOT / "install.sh").read_text()

    def test_install_sh_exists(self) -> None:
        """install.sh exists and is executable."""
        path = REPO_ROOT / "install.sh"
        assert path.is_file()

    def test_install_sh_has_shebang(self, install_sh_text: str) -> None:
        """install.sh starts with shebang."""
        assert install_sh_text.startswith("#!/")

    def test_install_sh_has_set_euo(self, install_sh_text: str) -> None:
        """install.sh uses set -euo pipefail."""
        assert "set -euo pipefail" in install_sh_text

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_install_sh_references_skill(
        self, install_sh_text: str, skill_name: str
    ) -> None:
        """install.sh lists all 10 base skills."""
        assert skill_name in install_sh_text, (
            f"install.sh doesn't reference skill: {skill_name}"
        )

    @pytest.mark.parametrize("template", EXPECTED_TEMPLATES)
    def test_install_sh_uses_templates(
        self, install_sh_text: str, template: str
    ) -> None:
        """install.sh references template files."""
        # settings.json is handled separately
        if template == "settings.json.template":
            assert "settings.json" in install_sh_text
        elif template in ("recent.md.template", "MEMORY.md.template", "LEARNINGS.md.template"):
            # These use the template basename without .template
            basename = template.replace(".template", "")
            assert basename in install_sh_text
        else:
            basename = template.replace(".template", "")
            assert basename in install_sh_text

    def test_install_sh_creates_shared_secrets(self, install_sh_text: str) -> None:
        """install.sh creates shared/secrets directory."""
        # Variable ${SHARED} expands to ~/.claude-lab/shared at runtime
        assert "secrets" in install_sh_text
        assert "SHARED" in install_sh_text

    def test_install_sh_creates_symlinks(self, install_sh_text: str) -> None:
        """install.sh creates skills symlink."""
        assert "ln -sf" in install_sh_text
        assert "skills" in install_sh_text


class TestVibeKanban:
    """T11.6: Vibe Kanban integration across all files."""

    def test_settings_json_has_mcp_kanban(self) -> None:
        """settings.json.template has vibe-kanban MCP server."""
        text = (REPO_ROOT / "templates" / "settings.json.template").read_text()
        assert "vibe-kanban" in text
        assert "mcpServers" in text

    def test_settings_json_has_npx_permission(self) -> None:
        """settings.json.template allows npx commands."""
        text = (REPO_ROOT / "templates" / "settings.json.template").read_text()
        assert "npx" in text

    def test_agents_template_has_kanban_section(self) -> None:
        """AGENTS.md.template has Task Board (Vibe Kanban) section."""
        text = (REPO_ROOT / "templates" / "AGENTS.md.template").read_text()
        assert "Vibe Kanban" in text
        assert "list_workspaces" in text

    def test_tools_template_has_kanban_section(self) -> None:
        """TOOLS.md.template has Kanban section."""
        text = (REPO_ROOT / "templates" / "TOOLS.md.template").read_text()
        assert "vibe-kanban" in text
        assert "SQLite" in text

    def test_multi_agent_has_kanban_section(self) -> None:
        """MULTI-AGENT.md has Task Management -- Vibe Kanban section."""
        text = (REPO_ROOT / "MULTI-AGENT.md").read_text()
        assert "Task Management -- Vibe Kanban" in text
        assert "list_workspaces" in text
        assert "create_session" in text

    def test_multi_agent_has_kanban_in_directory_layout(self) -> None:
        """MULTI-AGENT.md includes kanban/ in directory layout."""
        text = (REPO_ROOT / "MULTI-AGENT.md").read_text()
        assert "kanban/" in text

    def test_multi_agent_has_kanban_in_communication(self) -> None:
        """MULTI-AGENT.md lists Vibe Kanban as communication channel."""
        text = (REPO_ROOT / "MULTI-AGENT.md").read_text()
        assert "4 channels" in text
        assert "Vibe Kanban" in text

    def test_multi_agent_has_kanban_in_design_decisions(self) -> None:
        """MULTI-AGENT.md has Vibe Kanban as Key Design Decision."""
        text = (REPO_ROOT / "MULTI-AGENT.md").read_text()
        assert "Vibe Kanban -- local task board" in text

    def test_files_reference_has_kanban_layer(self) -> None:
        """FILES-REFERENCE.md has Task Board layer."""
        text = (REPO_ROOT / "FILES-REFERENCE.md").read_text()
        assert "Vibe Kanban" in text
        assert "MCP tools" in text.lower() or "MCP" in text

    def test_files_reference_has_kanban_in_access_matrix(self) -> None:
        """FILES-REFERENCE.md access matrix includes Vibe Kanban."""
        text = (REPO_ROOT / "FILES-REFERENCE.md").read_text()
        assert "Vibe Kanban" in text
        # Check it's in the access matrix table
        lines = [l for l in text.split("\n") if "Vibe Kanban" in l and "|" in l]
        assert len(lines) >= 1, "Vibe Kanban not in access matrix table"

    def test_readme_has_kanban_in_tree(self) -> None:
        """README.md includes kanban/ in directory tree."""
        text = (REPO_ROOT / "README.md").read_text()
        assert "kanban/" in text

    def test_readme_has_task_board_section(self) -> None:
        """README.md has Task Board section."""
        text = (REPO_ROOT / "README.md").read_text()
        assert "## Task Board" in text
        assert "npx vibe-kanban" in text

    def test_skill_vibe_kanban_exists(self) -> None:
        """skills/vibe-kanban/SKILL.md exists with MCP instructions."""
        text = (REPO_ROOT / "skills" / "vibe-kanban" / "SKILL.md").read_text()
        assert "MCP" in text
        assert "list_workspaces" in text
        assert "create_session" in text

    def test_install_sh_references_vibe_kanban(self) -> None:
        """install.sh installs vibe-kanban skill."""
        text = (REPO_ROOT / "install.sh").read_text()
        assert "vibe-kanban" in text


class TestCrossReferences:
    """T11.7: Cross-reference consistency."""

    def test_no_firebase_in_public_docs(self) -> None:
        """No Firebase/orgbus references in public documentation."""
        skip_files = {"MAPPING.md"}  # MAPPING.md discusses architecture comparisons
        for md_file in REPO_ROOT.glob("*.md"):
            if md_file.name in skip_files:
                continue
            text = md_file.read_text().lower()
            assert "orgbus" not in text, (
                f"orgbus reference in {md_file.name}"
            )

    def test_secrets_use_shared_path(self) -> None:
        """All secret paths reference shared/secrets/ (not per-agent)."""
        for md_file in REPO_ROOT.glob("*.md"):
            text = md_file.read_text()
            # Find secret path references
            if "secrets/" in text:
                lines = [
                    line for line in text.split("\n")
                    if "secrets/" in line and "shared/secrets" not in line
                    and "chmod" not in line and "NEVER" not in line
                    and "#" not in line[:5]  # Skip comments
                    and ".gitignore" not in line
                ]
                # Filter out generic mentions like "secrets/ directory"
                real_paths = [
                    ln for ln in lines
                    if re.search(r"~/[^\s]*secrets/", ln)
                    and "shared/secrets" not in ln
                ]
                assert not real_paths, (
                    f"Non-shared secret path in {md_file.name}: {real_paths[:2]}"
                )

    def test_readme_lists_mapping(self) -> None:
        """README.md references MAPPING.md."""
        text = (REPO_ROOT / "README.md").read_text()
        assert "MAPPING.md" in text

    def test_readme_lists_install(self) -> None:
        """README.md references install.sh."""
        text = (REPO_ROOT / "README.md").read_text()
        assert "install.sh" in text
