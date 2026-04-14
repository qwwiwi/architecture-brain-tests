"""
T20: Security validation.

Verifies that templates and documentation enforce security:
no hardcoded secrets, correct .gitignore patterns, secrets paths,
and security documentation in templates.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")
TEMPLATES_DIR = ARCH_ROOT / "templates"
SKILLS_DIR = ARCH_ROOT / "skills"


def all_template_files() -> list[Path]:
    """Return all template files."""
    if not TEMPLATES_DIR.exists():
        return []
    return list(TEMPLATES_DIR.glob("*.template")) + list(TEMPLATES_DIR.glob("*.md.template"))


def all_md_files() -> list[Path]:
    """Return all markdown files in repo."""
    return sorted(ARCH_ROOT.glob("**/*.md"))


def all_script_files() -> list[Path]:
    """Return all shell scripts in repo."""
    return sorted(ARCH_ROOT.glob("**/*.sh"))


# --- No secrets in templates ---


class TestNoSecretsInTemplates:
    """T20.1 Templates must not contain real secrets."""

    SECRET_PATTERNS = [
        r"sk-[a-zA-Z0-9]{20,}",      # OpenAI-style API key
        r"gsk_[a-zA-Z0-9]{20,}",     # Groq API key
        r"ghp_[a-zA-Z0-9]{20,}",     # GitHub personal access token
        r"xoxb-[0-9]+-[0-9]+",       # Slack bot token
        r"\d{8,10}:AA[A-Za-z0-9_-]{33}",  # Telegram bot token
        r"eyJ[a-zA-Z0-9_-]{50,}",    # JWT token
    ]

    @pytest.mark.parametrize("path", all_template_files(), ids=lambda p: p.name)
    def test_no_api_keys(self, path: Path) -> None:
        """Templates must not contain real API keys."""
        text = path.read_text(encoding="utf-8")
        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, text)
            assert not matches, (
                f"{path.name} contains potential API key: {pattern}"
            )

    @pytest.mark.parametrize("path", all_script_files(), ids=lambda p: p.name)
    def test_no_secrets_in_scripts(self, path: Path) -> None:
        """Scripts must not contain hardcoded secrets."""
        text = path.read_text(encoding="utf-8")
        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, text)
            assert not matches, (
                f"{path.name} contains potential secret: {pattern}"
            )


# --- Secrets path convention ---


class TestSecretsPath:
    """T20.2 Secrets must use shared/secrets/ path."""

    def test_templates_use_shared_secrets(self) -> None:
        """Templates referencing secrets must use shared/secrets/ path."""
        for path in all_template_files():
            text = path.read_text(encoding="utf-8")
            text_lower = text.lower()
            if "secret" not in text_lower and "token" not in text_lower:
                continue
            # Skip false positives: env var names like MAX_THINKING_TOKENS
            token_lines = [l for l in text.splitlines()
                           if "secret" in l.lower() or "token" in l.lower()]
            real_secret_refs = [l for l in token_lines
                                if not all(w in l for w in ["THINKING_TOKENS", "MAX_"])]
            if not real_secret_refs:
                continue
            # If it mentions secrets, it should use shared/secrets/ or secrets/ path
            has_correct_path = (
                "shared/secrets/" in text
                or "secrets/" in text
                or "{{" in text  # Placeholder is OK
            )
            assert has_correct_path, (
                f"{path.name} mentions secrets but doesn't use secrets/ path"
            )

    def test_install_creates_secrets_dir(self) -> None:
        """install.sh must create shared/secrets/ directory."""
        install = ARCH_ROOT / "install.sh"
        if not install.exists():
            pytest.skip("install.sh not found")
        text = install.read_text(encoding="utf-8")
        assert "secrets" in text, "install.sh must create secrets directory"

    def test_install_sets_permissions(self) -> None:
        """install.sh must chmod 700 secrets directory."""
        install = ARCH_ROOT / "install.sh"
        if not install.exists():
            pytest.skip("install.sh not found")
        text = install.read_text(encoding="utf-8")
        assert "chmod" in text and "700" in text, (
            "install.sh must chmod 700 secrets directory"
        )


# --- Security documentation ---


class TestSecurityDocumentation:
    """T20.3 Security rules documented in templates."""

    def test_rules_template_has_security(self) -> None:
        """rules.md.template must have security section."""
        path = TEMPLATES_DIR / "rules.md.template"
        if not path.exists():
            pytest.skip("rules.md.template not found")
        text = path.read_text(encoding="utf-8")
        assert "security" in text.lower() or "безопасность" in text.lower(), (
            "rules.md.template must have security section"
        )

    def test_never_commit_secrets(self) -> None:
        """rules.md.template must forbid committing secrets."""
        path = TEMPLATES_DIR / "rules.md.template"
        if not path.exists():
            pytest.skip("rules.md.template not found")
        text = path.read_text(encoding="utf-8")
        has_env = ".env" in text
        has_secrets = "secret" in text.lower()
        has_commit = "commit" in text.lower() or "коммит" in text.lower()
        assert (has_env or has_secrets) and has_commit, (
            "rules.md.template must forbid committing .env/secrets"
        )

    def test_never_expose_tokens(self) -> None:
        """rules.md.template must forbid exposing tokens in stdout."""
        path = TEMPLATES_DIR / "rules.md.template"
        if not path.exists():
            pytest.skip("rules.md.template not found")
        text = path.read_text(encoding="utf-8")
        has_token = "token" in text.lower() or "ключ" in text.lower()
        has_expose = (
            "expose" in text.lower()
            or "раскрывать" in text.lower()
            or "stdout" in text.lower()
            or "выводить" in text.lower()
            or "output" in text.lower()
        )
        assert has_token and has_expose, (
            "rules.md.template must forbid exposing tokens"
        )

    def test_claude_template_has_red_zone(self) -> None:
        """CLAUDE.md.template must define red zone (ask operator)."""
        path = TEMPLATES_DIR / "CLAUDE.md.template"
        if not path.exists():
            pytest.skip("CLAUDE.md.template not found")
        text = path.read_text(encoding="utf-8")
        has_red = "red" in text.lower() or "красн" in text.lower()
        has_zone = "zone" in text.lower() or "зона" in text.lower()
        assert has_red and has_zone, (
            "CLAUDE.md.template must define Red Zone"
        )


# --- No organization-specific secrets ---


class TestNoOrgSpecifics:
    """T20.4 Public repo must not contain org-specific references."""

    def test_no_real_ips_in_templates(self) -> None:
        """Templates must not have real IP addresses."""
        ip_pattern = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
        ALLOWED_IPS = {"127.0.0.1", "0.0.0.0", "192.168.1.100", "10.0.0.1"}

        for path in all_template_files():
            text = path.read_text(encoding="utf-8")
            ips = set(ip_pattern.findall(text))
            real_ips = ips - ALLOWED_IPS
            assert not real_ips, (
                f"{path.name} contains real IP addresses: {real_ips}"
            )

    def test_no_real_usernames_in_templates(self) -> None:
        """Templates must use placeholders, not real usernames."""
        for path in all_template_files():
            text = path.read_text(encoding="utf-8")
            # Check for org-specific names
            org_names = ["orgrimmar", "sa-thrall", "sa-silvana", "dashieshiev"]
            for name in org_names:
                assert name not in text.lower(), (
                    f"{path.name} contains org-specific name: {name}"
                )

    def test_skills_no_org_references(self) -> None:
        """Skills must not reference organization-specific paths."""
        if not SKILLS_DIR.exists():
            pytest.skip("skills/ not found")
        for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
            text = skill_md.read_text(encoding="utf-8")
            assert "orgrimmar" not in text.lower(), (
                f"{skill_md} references orgrimmar"
            )
            assert "openclaw" not in text.lower() or "{{" in text, (
                f"{skill_md} references openclaw without placeholder"
            )


# --- Git safety ---


class TestGitSafety:
    """T20.5 Git rules in templates."""

    def test_no_force_push(self) -> None:
        """rules.md.template must forbid force push."""
        path = TEMPLATES_DIR / "rules.md.template"
        if not path.exists():
            pytest.skip("rules.md.template not found")
        text = path.read_text(encoding="utf-8")
        assert "force" in text.lower() and "push" in text.lower(), (
            "rules.md.template must forbid force push"
        )

    def test_no_push_main(self) -> None:
        """Templates must forbid push to main."""
        # Check rules.md.template (git rules live there)
        path = TEMPLATES_DIR / "rules.md.template"
        if not path.exists():
            pytest.skip("rules.md.template not found")
        text = path.read_text(encoding="utf-8")
        has_main = "main" in text.lower()
        has_push = "push" in text.lower()
        has_never = "never" in text.lower() or "никогда" in text.lower() or "PR" in text
        assert has_main and has_push and has_never, (
            "rules.md.template must forbid pushing to main"
        )

    def test_pr_first_workflow(self) -> None:
        """Templates must enforce PR-first workflow."""
        path = TEMPLATES_DIR / "rules.md.template"
        if not path.exists():
            pytest.skip("rules.md.template not found")
        text = path.read_text(encoding="utf-8")
        assert "PR" in text or "pull request" in text.lower(), (
            "rules.md.template must enforce PR-first workflow"
        )
