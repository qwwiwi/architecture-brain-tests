"""
T18: Hook configuration and documentation validation.

Verifies that HOOKS.md correctly documents all hook types,
lifecycle events, examples, and that settings.json.template
has valid hook structure.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")


def load_hooks_md() -> str:
    """Load HOOKS.md content."""
    path = ARCH_ROOT / "HOOKS.md"
    if not path.exists():
        pytest.skip("HOOKS.md not found")
    return path.read_text(encoding="utf-8")


# --- Lifecycle events ---


class TestHookLifecycleEvents:
    """T18.1 All lifecycle events documented."""

    REQUIRED_EVENTS = [
        "Stop",
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "PreCompact",
    ]

    OPTIONAL_EVENTS = [
        "SessionStart",
        "SessionEnd",
        "PostCompact",
        "PostToolUseFailure",
        "SubagentStart",
        "SubagentStop",
        "FileChanged",
        "CwdChanged",
        "TaskCreated",
        "TaskCompleted",
    ]

    @pytest.mark.parametrize("event", REQUIRED_EVENTS)
    def test_required_event_documented(self, event: str) -> None:
        """Required lifecycle event must be in HOOKS.md."""
        text = load_hooks_md()
        assert event in text, f"HOOKS.md must document {event} event"

    def test_at_least_10_events_total(self) -> None:
        """HOOKS.md must document at least 10 lifecycle events."""
        text = load_hooks_md()
        all_events = self.REQUIRED_EVENTS + self.OPTIONAL_EVENTS
        found = sum(1 for e in all_events if e in text)
        assert found >= 10, f"Found only {found} events, need at least 10"

    def test_user_prompt_submit_documented(self) -> None:
        """UserPromptSubmit event must be documented with its behavior."""
        text = load_hooks_md()
        assert "UserPromptSubmit" in text, (
            "HOOKS.md must document UserPromptSubmit event"
        )
        # UserPromptSubmit should mention that stdout is added to context
        assert "context" in text.lower(), (
            "HOOKS.md must explain UserPromptSubmit stdout goes to context"
        )

    def test_pre_compact_documented(self) -> None:
        """PreCompact event must be documented."""
        text = load_hooks_md()
        assert "PreCompact" in text, "HOOKS.md must document PreCompact event"

    def test_user_prompt_submit_in_lifecycle_table(self) -> None:
        """UserPromptSubmit must appear in the lifecycle events table."""
        text = load_hooks_md()
        lines = text.split("\n")
        table_lines = [
            ln for ln in lines
            if "UserPromptSubmit" in ln and "|" in ln
        ]
        assert table_lines, (
            "UserPromptSubmit must be in the lifecycle events table"
        )

    def test_pre_compact_in_lifecycle_table(self) -> None:
        """PreCompact must appear in the lifecycle events table."""
        text = load_hooks_md()
        lines = text.split("\n")
        table_lines = [
            ln for ln in lines
            if "PreCompact" in ln and "|" in ln
        ]
        assert table_lines, "PreCompact must be in the lifecycle events table"


# --- Handler types ---


class TestHookHandlerTypes:
    """T18.2 Handler types properly documented."""

    def test_command_handler(self) -> None:
        """'command' handler type must be documented with example."""
        text = load_hooks_md()
        assert '"command"' in text or "'command'" in text or "type.*command" in text.lower(), (
            "HOOKS.md must show command handler type"
        )

    def test_handler_has_timeout(self) -> None:
        """Hook handlers should document timeout."""
        text = load_hooks_md()
        assert "timeout" in text.lower(), "Hooks must document timeout for handlers"


# --- Universal hooks ---


class TestUniversalHooks:
    """T18.3 Universal safety hooks documented."""

    def test_block_dangerous_commands(self) -> None:
        """Must have example blocking rm -rf / DROP TABLE."""
        text = load_hooks_md()
        assert "rm -rf" in text or "dangerous" in text.lower(), (
            "HOOKS.md must show how to block dangerous commands"
        )

    def test_protect_sensitive_files(self) -> None:
        """Must have example protecting sensitive files."""
        text = load_hooks_md()
        assert "sensitive" in text.lower() or ".env" in text, (
            "HOOKS.md must show how to protect sensitive files"
        )

    def test_audit_logging_example(self) -> None:
        """Must have example of command audit logging."""
        text = load_hooks_md()
        assert "log" in text.lower() and ("audit" in text.lower() or "trail" in text.lower()), (
            "HOOKS.md must document audit trail / command logging"
        )


# --- Project-specific hooks ---


class TestProjectHooks:
    """T18.4 Project-specific hook examples."""

    def test_auto_format_example(self) -> None:
        """Must have auto-format hook example (Prettier/Biome)."""
        text = load_hooks_md()
        assert "prettier" in text.lower() or "biome" in text.lower() or "format" in text.lower(), (
            "HOOKS.md must have auto-format hook example"
        )

    def test_auto_test_example(self) -> None:
        """Must have auto-test hook example."""
        text = load_hooks_md()
        assert "test" in text.lower() and "hook" in text.lower(), (
            "HOOKS.md must have auto-test hook example"
        )

    def test_stop_hook_openviking(self) -> None:
        """Must have Stop hook for OpenViking session sync."""
        text = load_hooks_md()
        assert "ov-session-sync" in text, (
            "HOOKS.md must have OpenViking Stop hook example"
        )

    def test_auto_commit_on_stop(self) -> None:
        """Must have auto-commit on Stop example."""
        text = load_hooks_md()
        assert "commit" in text.lower() and "Stop" in text, (
            "HOOKS.md must have auto-commit on Stop example"
        )


# --- Hook enforcement vs CLAUDE.md ---


class TestHookEnforcement:
    """T18.5 Hook enforcement model documented."""

    def test_enforcement_percentage(self) -> None:
        """HOOKS.md must explain hooks = 100% enforcement."""
        text = load_hooks_md()
        assert "100%" in text or "enforce" in text.lower(), (
            "HOOKS.md must explain that hooks are 100% enforcement"
        )

    def test_exit_code_block(self) -> None:
        """Exit code 2 must block tool execution."""
        text = load_hooks_md()
        # Must mention exit 2 = block
        assert "2" in text and "block" in text.lower(), (
            "HOOKS.md must document exit code 2 = block"
        )

    def test_if_filter_syntax(self) -> None:
        """Must document 'if' filter for tool-specific matching."""
        text = load_hooks_md()
        assert '"if"' in text or "'if'" in text or "if.*filter" in text.lower(), (
            "HOOKS.md must document 'if' filter syntax for tool matching"
        )


# --- Complete settings example ---


class TestCompleteSettingsExample:
    """T18.6 Complete settings.json example in HOOKS.md."""

    def test_has_complete_example(self) -> None:
        """HOOKS.md must have a complete combined settings.json example."""
        text = load_hooks_md()
        # Should have a JSON block with both hooks and permissions
        json_blocks = re.findall(r"```json\n(.*?)```", text, re.DOTALL)
        has_hooks_example = any("hooks" in block for block in json_blocks)
        assert has_hooks_example, "HOOKS.md must have a complete JSON example with hooks"

    def test_example_has_stop_hook(self) -> None:
        """Complete example must include Stop hook."""
        text = load_hooks_md()
        # Check for Stop in any JSON block
        assert '"Stop"' in text, "Complete settings example must include Stop hook"
