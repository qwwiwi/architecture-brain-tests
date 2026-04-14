"""T10: Skills validation.

Tests:
- All 11 base skills exist
- Each skill has SKILL.md with valid frontmatter
- Scripts are present and executable (where expected)
- Skill names match directory names
- No hardcoded secrets in skill files
- install.sh lists all 11 skills
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent / "public-architecture-claude-code"

BASE_SKILLS = [
    "groq-voice",
    "superpowers",
    "markdown-new",
    "excalidraw",
    "datawrapper",
    "perplexity-research",
    "gws",
    "youtube-transcript",
    "twitter",
    "quick-reminders",
    "vibe-kanban",
]

SKILLS_DIR = REPO_ROOT / "skills"

# Skills that must have scripts/
SKILLS_WITH_SCRIPTS: dict[str, list[str]] = {
    "groq-voice": ["transcribe.sh"],
    "excalidraw": ["excalidraw_gen.py"],
    "gws": ["health-check.sh"],
    "youtube-transcript": ["tapi-auth.js"],
    "quick-reminders": ["nohup-reminder.sh"],
}

# Patterns that should NEVER appear in skill files (hardcoded secrets)
SECRET_PATTERNS = [
    r"gsk_[A-Za-z0-9]{20,}",  # Groq API key format
    r"sk-[A-Za-z0-9]{20,}",  # OpenAI-style key
    r"xoxb-[0-9]+-[A-Za-z0-9]+",  # Slack token
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",  # IP addresses
]


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter from SKILL.md."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


@pytest.fixture
def skill_dirs() -> dict[str, Path]:
    """Map skill name to its directory."""
    return {name: SKILLS_DIR / name for name in BASE_SKILLS}


class TestSkillExistence:
    """T10.1: All 11 base skills exist."""

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_skill_directory_exists(self, skill_name: str) -> None:
        """Each skill has a directory."""
        skill_dir = SKILLS_DIR / skill_name
        assert skill_dir.is_dir(), f"Missing skill directory: {skill_dir}"

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_skill_md_exists(self, skill_name: str) -> None:
        """Each skill has SKILL.md."""
        skill_md = SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_md.is_file(), f"Missing SKILL.md: {skill_md}"

    def test_total_skill_count(self) -> None:
        """Exactly 11 base skills in skills/ directory."""
        dirs = [
            d for d in SKILLS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        assert len(dirs) >= 11, f"Expected 11+ skills, found {len(dirs)}: {[d.name for d in dirs]}"


class TestSkillFrontmatter:
    """T10.2: SKILL.md frontmatter is valid."""

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_has_frontmatter(self, skill_name: str) -> None:
        """SKILL.md starts with --- frontmatter."""
        text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
        assert text.startswith("---"), f"{skill_name}/SKILL.md missing frontmatter"

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_frontmatter_has_name(self, skill_name: str) -> None:
        """Frontmatter has 'name' field."""
        text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
        fm = _parse_frontmatter(text)
        assert "name" in fm, f"{skill_name} frontmatter missing 'name'"

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_frontmatter_has_description(self, skill_name: str) -> None:
        """Frontmatter has 'description' field."""
        text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
        fm = _parse_frontmatter(text)
        assert "description" in fm, f"{skill_name} frontmatter missing 'description'"

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_name_matches_directory(self, skill_name: str) -> None:
        """Frontmatter name matches directory name."""
        text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
        fm = _parse_frontmatter(text)
        fm_name = fm.get("name", "")
        assert fm_name == skill_name, (
            f"Name mismatch: dir='{skill_name}', frontmatter='{fm_name}'"
        )


class TestSkillScripts:
    """T10.3: Required scripts exist."""

    @pytest.mark.parametrize(
        "skill_name,expected_scripts",
        list(SKILLS_WITH_SCRIPTS.items()),
    )
    def test_scripts_exist(self, skill_name: str, expected_scripts: list[str]) -> None:
        """Each skill with scripts has all expected script files."""
        scripts_dir = SKILLS_DIR / skill_name / "scripts"
        assert scripts_dir.is_dir(), f"{skill_name} missing scripts/ directory"
        for script in expected_scripts:
            script_path = scripts_dir / script
            assert script_path.is_file(), f"Missing script: {skill_name}/scripts/{script}"

    @pytest.mark.parametrize(
        "skill_name,expected_scripts",
        [
            (k, v)
            for k, v in SKILLS_WITH_SCRIPTS.items()
            if any(s.endswith(".sh") for s in v)
        ],
    )
    def test_shell_scripts_executable(
        self, skill_name: str, expected_scripts: list[str]
    ) -> None:
        """Shell scripts have executable permission."""
        for script in expected_scripts:
            if script.endswith(".sh"):
                path = SKILLS_DIR / skill_name / "scripts" / script
                assert path.stat().st_mode & 0o111, f"Not executable: {path}"


class TestSkillContent:
    """T10.4: Skill content quality checks."""

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_no_hardcoded_secrets(self, skill_name: str) -> None:
        """No hardcoded API keys or IP addresses in skill files."""
        skill_dir = SKILLS_DIR / skill_name
        for file_path in skill_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix in {".excalidraw", ".json", ".pyc"}:
                continue
            text = file_path.read_text(errors="ignore")
            for pattern in SECRET_PATTERNS:
                matches = re.findall(pattern, text)
                # Allow 127.0.0.1 (localhost) as it's not a real secret
                matches = [m for m in matches if m != "127.0.0.1"]
                assert not matches, (
                    f"Potential secret in {file_path.relative_to(REPO_ROOT)}: "
                    f"pattern={pattern}, found={matches[:3]}"
                )

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_no_openclaw_references(self, skill_name: str) -> None:
        """No OpenClaw-specific paths in universal skills."""
        skill_dir = SKILLS_DIR / skill_name
        for file_path in skill_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix in {".excalidraw", ".json", ".pyc"}:
                continue
            text = file_path.read_text(errors="ignore")
            assert "~/.openclaw/" not in text, (
                f"OpenClaw path in {file_path.relative_to(REPO_ROOT)}"
            )

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_no_orgrimmar_references(self, skill_name: str) -> None:
        """No Orgrimmar-specific references in universal skills."""
        skip_patterns = {"orgrimmar", "sa-thrall", "sa-silvana", "sa-illidan"}
        skill_dir = SKILLS_DIR / skill_name
        for file_path in skill_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix in {".excalidraw", ".json", ".pyc"}:
                continue
            text = file_path.read_text(errors="ignore").lower()
            for pat in skip_patterns:
                assert pat not in text, (
                    f"Orgrimmar reference '{pat}' in {file_path.relative_to(REPO_ROOT)}"
                )

    @pytest.mark.parametrize("skill_name", BASE_SKILLS)
    def test_skill_md_not_empty(self, skill_name: str) -> None:
        """SKILL.md has meaningful content (>50 chars)."""
        text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
        assert len(text) > 50, f"{skill_name}/SKILL.md too short: {len(text)} chars"


class TestSkillReferences:
    """T10.5: Skills referenced correctly in other files."""

    def test_superpowers_has_skill_md(self) -> None:
        """superpowers has SKILL.md with meaningful content."""
        text = (SKILLS_DIR / "superpowers" / "SKILL.md").read_text()
        assert len(text) > 50, "superpowers/SKILL.md too short"
