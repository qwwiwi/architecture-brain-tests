"""
T17: Settings.json template validation.

Verifies that the settings.json.template has correct structure,
required permissions, valid hook configurations, and MCP server setup.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
ARCH_ROOT = Path("/tmp/public-architecture-claude-code")


def load_settings_template() -> dict:
    """Load and parse settings.json.template."""
    path = ARCH_ROOT / "templates" / "settings.json.template"
    if not path.exists():
        pytest.skip("settings.json.template not found")
    text = path.read_text(encoding="utf-8")
    # Remove comments (// style) that JSON doesn't support
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        # Remove inline comments after values
        lines.append(line)
    clean = "\n".join(lines)
    # Try parse; template may have placeholders, so be lenient
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return {}


def load_settings_text() -> str:
    """Load raw settings.json.template text."""
    path = ARCH_ROOT / "templates" / "settings.json.template"
    if not path.exists():
        pytest.skip("settings.json.template not found")
    return path.read_text(encoding="utf-8")


# --- Structure ---


class TestSettingsStructure:
    """T17.1 Settings template has required top-level keys."""

    def test_has_permissions_section(self) -> None:
        """Settings template must document permissions."""
        text = load_settings_text()
        assert "allow" in text.lower() or "permissions" in text.lower(), (
            "settings.json.template must have permissions section"
        )

    def test_has_hooks_section(self) -> None:
        """Settings template must document hooks."""
        text = load_settings_text()
        assert "hooks" in text.lower(), "settings.json.template must have hooks section"

    def test_has_mcp_servers_section(self) -> None:
        """Settings template must document MCP servers."""
        text = load_settings_text()
        assert "mcpServers" in text or "mcp" in text.lower(), (
            "settings.json.template must have MCP servers section"
        )


# --- Permissions ---


class TestSettingsPermissions:
    """T17.2 Permission rules are safe and correct."""

    def test_no_wildcard_allow_all(self) -> None:
        """Settings must not have a blanket allow-all rule."""
        text = load_settings_text()
        # Pattern: "allow": ["*"] or "allow": ["Bash(**)"]
        assert '"*"' not in text or "deny" in text, (
            "Settings must not have unrestricted wildcard allow"
        )

    def test_dangerous_commands_blocked(self) -> None:
        """HOOKS.md documents blocking dangerous commands."""
        hooks_path = ARCH_ROOT / "HOOKS.md"
        if not hooks_path.exists():
            pytest.skip("HOOKS.md not found")
        text = hooks_path.read_text(encoding="utf-8")
        dangerous = ["rm -rf", "DROP TABLE", "force push"]
        found = sum(1 for d in dangerous if d.lower() in text.lower())
        assert found >= 2, (
            f"HOOKS.md should document blocking dangerous commands, found {found}/3"
        )

    def test_sensitive_file_protection_documented(self) -> None:
        """HOOKS.md documents protecting sensitive files."""
        hooks_path = ARCH_ROOT / "HOOKS.md"
        if not hooks_path.exists():
            pytest.skip("HOOKS.md not found")
        text = hooks_path.read_text(encoding="utf-8")
        assert "sensitive" in text.lower() or ".env" in text or "secrets" in text.lower(), (
            "HOOKS.md should document sensitive file protection"
        )


# --- Hooks format ---


class TestSettingsHooksFormat:
    """T17.3 Hook configuration format is valid."""

    def test_hooks_documented_events(self) -> None:
        """HOOKS.md must document all standard lifecycle events."""
        hooks_path = ARCH_ROOT / "HOOKS.md"
        if not hooks_path.exists():
            pytest.skip("HOOKS.md not found")
        text = hooks_path.read_text(encoding="utf-8")
        events = ["Stop", "PreToolUse", "PostToolUse"]
        for event in events:
            assert event in text, f"HOOKS.md must document {event} event"

    def test_hooks_handler_types(self) -> None:
        """HOOKS.md must document handler types."""
        hooks_path = ARCH_ROOT / "HOOKS.md"
        if not hooks_path.exists():
            pytest.skip("HOOKS.md not found")
        text = hooks_path.read_text(encoding="utf-8")
        assert "command" in text, "HOOKS.md must document 'command' handler type"

    def test_hooks_exit_codes(self) -> None:
        """HOOKS.md must document exit code semantics."""
        hooks_path = ARCH_ROOT / "HOOKS.md"
        if not hooks_path.exists():
            pytest.skip("HOOKS.md not found")
        text = hooks_path.read_text(encoding="utf-8")
        # Exit code 0 = proceed, 2 = block
        assert "exit" in text.lower() and ("0" in text and "2" in text), (
            "HOOKS.md must document exit codes (0=proceed, 2=block)"
        )

    def test_hooks_template_has_matcher(self) -> None:
        """Settings template hooks must use matcher field."""
        text = load_settings_text()
        if "hooks" not in text.lower():
            pytest.skip("No hooks in template")
        assert "matcher" in text, "Hook entries must have 'matcher' field"


# --- MCP ---


class TestSettingsMCP:
    """T17.4 MCP server configuration."""

    def test_mcp_has_example(self) -> None:
        """Settings template must have at least one MCP example."""
        text = load_settings_text()
        assert "mcpServers" in text or "vibe-kanban" in text, (
            "Settings template must show MCP server example"
        )

    def test_mcp_documented_in_hooks(self) -> None:
        """HOOKS.md or settings template shows how hooks + MCP coexist."""
        text = load_settings_text()
        hooks_path = ARCH_ROOT / "HOOKS.md"
        hooks_text = hooks_path.read_text(encoding="utf-8") if hooks_path.exists() else ""
        combined = text + hooks_text
        assert "mcpServers" in combined, "MCP must be documented"
