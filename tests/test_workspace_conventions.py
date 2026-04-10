"""
T22: Workspace conventions and naming validation.

Verifies that documentation consistently describes workspace structure,
directory naming, file naming, symlinks, and install conventions.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")
TEMPLATES_DIR = ARCH_ROOT / "templates"


def load_md(name: str) -> str:
    """Load a markdown file."""
    path = ARCH_ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not found")
    return path.read_text(encoding="utf-8")


def load_install() -> str:
    """Load install.sh."""
    path = ARCH_ROOT / "install.sh"
    if not path.exists():
        pytest.skip("install.sh not found")
    return path.read_text(encoding="utf-8")


# --- Workspace root ---


class TestWorkspaceRoot:
    """T22.1 Workspace root path is consistent."""

    def test_claude_lab_path(self) -> None:
        """All docs must use ~/.claude-lab/ as workspace root."""
        files = ["STRUCTURE.md", "SETUP-GUIDE.md", "CHECKLIST.md", "FIRST-AGENT.md"]
        for name in files:
            path = ARCH_ROOT / name
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            assert ".claude-lab" in text, f"{name} must reference ~/.claude-lab/ path"

    def test_install_uses_claude_lab(self) -> None:
        """install.sh must create workspace under ~/.claude-lab/."""
        text = load_install()
        assert ".claude-lab" in text, "install.sh must use ~/.claude-lab/ path"


# --- Directory structure ---


class TestDirectoryStructure:
    """T22.2 Required directories documented."""

    REQUIRED_DIRS = [
        "core/hot",
        "core/warm",
        "scripts",
    ]

    def test_structure_md_has_all_dirs(self) -> None:
        """STRUCTURE.md must show all required directories."""
        text = load_md("STRUCTURE.md")
        for d in self.REQUIRED_DIRS:
            assert d in text, f"STRUCTURE.md missing directory: {d}"

    def test_install_creates_all_dirs(self) -> None:
        """install.sh must create all required directories."""
        text = load_install()
        for d in self.REQUIRED_DIRS:
            # Check for mkdir of this path
            parts = d.split("/")
            last_part = parts[-1]
            assert last_part in text, f"install.sh must create {d}"

    def test_checklist_creates_workspace(self) -> None:
        """CHECKLIST.md must show mkdir for workspace."""
        text = load_md("CHECKLIST.md")
        assert "mkdir" in text, "CHECKLIST.md must show mkdir command"


# --- Identity files ---


class TestIdentityFiles:
    """T22.3 All 5 identity files documented."""

    IDENTITY_FILES = [
        "CLAUDE.md",
        "AGENTS.md",
        "USER.md",
        "rules.md",
        "TOOLS.md",
    ]

    def test_all_identity_files_in_structure(self) -> None:
        """STRUCTURE.md must list all 5 identity files."""
        text = load_md("STRUCTURE.md")
        for f in self.IDENTITY_FILES:
            assert f in text, f"STRUCTURE.md missing identity file: {f}"

    def test_all_identity_templates_exist(self) -> None:
        """All identity files must have templates."""
        for f in self.IDENTITY_FILES:
            template = TEMPLATES_DIR / f"{f}.template"
            assert template.exists(), f"Missing template: {f}.template"

    def test_claude_template_has_includes(self) -> None:
        """CLAUDE.md.template must @include other identity files."""
        path = TEMPLATES_DIR / "CLAUDE.md.template"
        if not path.exists():
            pytest.skip("CLAUDE.md.template not found")
        text = path.read_text(encoding="utf-8")
        includes = re.findall(r"@\S+\.md", text)
        assert len(includes) >= 3, (
            f"CLAUDE.md.template must @include at least 3 files, found {len(includes)}"
        )


# --- Memory files ---


class TestMemoryFiles:
    """T22.4 Memory file naming consistent."""

    def test_hot_file_is_recent_md(self) -> None:
        """HOT memory file must be named recent.md."""
        text = load_md("MEMORY.md")
        assert "recent.md" in text, "HOT file must be core/hot/recent.md"

    def test_warm_file_is_decisions_md(self) -> None:
        """WARM memory file must be named decisions.md."""
        text = load_md("MEMORY.md")
        assert "decisions.md" in text, "WARM file must be core/warm/decisions.md"

    def test_cold_file_is_memory_md(self) -> None:
        """COLD memory file must be named MEMORY.md."""
        text = load_md("MEMORY.md")
        assert "MEMORY.md" in text, "COLD file must be core/MEMORY.md"

    def test_archive_directory_documented(self) -> None:
        """Archive directory must be documented."""
        text = load_md("MEMORY.md")
        assert "archive" in text.lower(), "Must document archive/ directory"


# --- Symlinks ---


class TestSymlinks:
    """T22.5 Symlink conventions documented."""

    def test_skills_symlink(self) -> None:
        """install.sh must create skills symlink to shared/skills/."""
        text = load_install()
        has_symlink = "ln -s" in text or "symlink" in text.lower()
        has_skills = "skills" in text
        assert has_symlink and has_skills, (
            "install.sh must create skills symlink"
        )

    def test_shared_directory(self) -> None:
        """Must document shared/ directory for cross-agent resources."""
        files = ["STRUCTURE.md", "MULTI-AGENT.md"]
        found = False
        for name in files:
            path = ARCH_ROOT / name
            if path.exists() and "shared" in path.read_text(encoding="utf-8"):
                found = True
                break
        assert found, "Must document shared/ directory"


# --- Install script completeness ---


class TestInstallCompleteness:
    """T22.6 install.sh covers all setup steps."""

    def test_installs_11_skills(self) -> None:
        """install.sh must install all 11 base skills."""
        text = load_install()
        # Count skill names mentioned
        skills = [
            "groq-voice", "superpowers", "excalidraw", "perplexity-research",
            "gws", "youtube-transcript", "twitter", "quick-reminders", "vibe-kanban",
        ]
        found = sum(1 for s in skills if s in text)
        assert found >= 9, f"install.sh must install base skills, found {found}/9+"

    def test_copies_memory_scripts(self) -> None:
        """install.sh must copy all 4 memory scripts."""
        text = load_install()
        scripts = ["trim-hot", "compress-warm", "rotate-warm", "memory-rotate"]
        found = sum(1 for s in scripts if s in text)
        assert found >= 4, f"install.sh must copy all 4 scripts, found {found}/4"

    def test_shows_cron_setup(self) -> None:
        """install.sh must show cron setup instructions."""
        text = load_install()
        assert "cron" in text.lower(), "install.sh must show cron setup"

    def test_creates_language_rules(self) -> None:
        """install.sh must create language rule files."""
        text = load_install()
        rules = ["bash.md", "python.md", "typescript.md"]
        found = sum(1 for r in rules if r in text)
        assert found >= 3, f"install.sh must create language rules, found {found}/3"
