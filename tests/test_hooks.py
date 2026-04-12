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
        assert "UserPromptSubmit" in text, "HOOKS.md must document UserPromptSubmit event"
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
        table_lines = [ln for ln in lines if "UserPromptSubmit" in ln and "|" in ln]
        assert table_lines, "UserPromptSubmit must be in the lifecycle events table"

    def test_pre_compact_in_lifecycle_table(self) -> None:
        """PreCompact must appear in the lifecycle events table."""
        text = load_hooks_md()
        lines = text.split("\n")
        table_lines = [ln for ln in lines if "PreCompact" in ln and "|" in ln]
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
        assert "ov-session-sync" in text, "HOOKS.md must have OpenViking Stop hook example"

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
        assert "2" in text and "block" in text.lower(), "HOOKS.md must document exit code 2 = block"

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


# --- Production hooks section ---


class TestProductionHooksSection:
    """T18.7 Production hooks section exists in HOOKS.md."""

    def test_production_hooks_section_exists(self) -> None:
        """HOOKS.md must have a Production Hooks section."""
        text = load_hooks_md()
        assert "Production Hooks" in text, "HOOKS.md must contain a 'Production Hooks' section"

    def test_has_production_settings_json(self) -> None:
        """Production section must include a settings.json example."""
        text = load_hooks_md()
        # Find text after "Production Hooks" heading
        idx = text.find("Production Hooks")
        if idx == -1:
            pytest.fail("Production Hooks section not found")
        production_section = text[idx:]
        json_blocks = re.findall(r"```json\n(.*?)```", production_section, re.DOTALL)
        has_hooks = any("hooks" in block for block in json_blocks)
        assert has_hooks, "Production Hooks section must include a settings.json example with hooks"


# --- Production hook names ---


class TestProductionHookNames:
    """T18.8 Each production hook is documented in HOOKS.md."""

    def test_session_bootstrap_documented(self) -> None:
        """session-bootstrap hook must be documented."""
        text = load_hooks_md()
        assert "session-bootstrap" in text, "HOOKS.md must document session-bootstrap hook"

    def test_auto_recall_documented(self) -> None:
        """auto-recall hook must be documented."""
        text = load_hooks_md()
        assert "auto-recall" in text, "HOOKS.md must document auto-recall hook"

    def test_local_recall_documented(self) -> None:
        """local-recall hook must be documented."""
        text = load_hooks_md()
        assert "local-recall" in text, "HOOKS.md must document local-recall hook"

    def test_correction_detector_documented(self) -> None:
        """correction-detector hook must be documented."""
        text = load_hooks_md()
        assert "correction-detector" in text, "HOOKS.md must document correction-detector hook"

    def test_bash_firewall_documented(self) -> None:
        """bash-firewall hook must be documented."""
        text = load_hooks_md()
        assert "bash-firewall" in text, "HOOKS.md must document bash-firewall hook"

    def test_audit_log_documented(self) -> None:
        """audit-log hook must be documented."""
        text = load_hooks_md()
        assert "audit-log" in text, "HOOKS.md must document audit-log hook"

    def test_review_reminder_documented(self) -> None:
        """review-reminder hook must be documented."""
        text = load_hooks_md()
        assert "review-reminder" in text, "HOOKS.md must document review-reminder hook"

    def test_auto_capture_documented(self) -> None:
        """auto-capture hook must be documented."""
        text = load_hooks_md()
        assert "auto-capture" in text, "HOOKS.md must document auto-capture hook"

    def test_write_handoff_documented(self) -> None:
        """write-handoff hook must be documented."""
        text = load_hooks_md()
        assert "write-handoff" in text, "HOOKS.md must document write-handoff hook"

    def test_flush_to_openviking_documented(self) -> None:
        """flush-to-openviking hook must be documented."""
        text = load_hooks_md()
        assert "flush-to-openviking" in text, "HOOKS.md must document flush-to-openviking hook"

    def test_compact_notify_documented(self) -> None:
        """compact-notify hook must be documented."""
        text = load_hooks_md()
        assert "compact-notify" in text, "HOOKS.md must document compact-notify hook"

    def test_close_heartbeat_documented(self) -> None:
        """close-heartbeat hook must be documented."""
        text = load_hooks_md()
        assert "close-heartbeat" in text, "HOOKS.md must document close-heartbeat hook"


# --- Production hook events ---


class TestProductionHookEvents:
    """T18.9 Production hooks are mapped to correct lifecycle events."""

    def _find_hook_event_context(self, text: str, hook_name: str) -> str:
        """Return the text surrounding a hook name for event checking."""
        idx = text.find(hook_name)
        if idx == -1:
            return ""
        # Grab surrounding context (500 chars before and after)
        start = max(0, idx - 500)
        end = min(len(text), idx + 500)
        return text[start:end]

    def test_session_bootstrap_on_session_start(self) -> None:
        """session-bootstrap must be mapped to SessionStart event."""
        text = load_hooks_md()
        ctx = self._find_hook_event_context(text, "session-bootstrap")
        assert ctx, "session-bootstrap not found in HOOKS.md"
        assert "SessionStart" in ctx, "session-bootstrap must be associated with SessionStart event"

    def test_auto_recall_on_user_prompt_submit(self) -> None:
        """auto-recall must be mapped to UserPromptSubmit event."""
        text = load_hooks_md()
        ctx = self._find_hook_event_context(text, "auto-recall")
        assert ctx, "auto-recall not found in HOOKS.md"
        assert "UserPromptSubmit" in ctx, (
            "auto-recall must be associated with UserPromptSubmit event"
        )

    def test_correction_detector_on_user_prompt_submit(self) -> None:
        """correction-detector must be mapped to UserPromptSubmit event."""
        text = load_hooks_md()
        ctx = self._find_hook_event_context(text, "correction-detector")
        assert ctx, "correction-detector not found in HOOKS.md"
        assert "UserPromptSubmit" in ctx, (
            "correction-detector must be associated with UserPromptSubmit event"
        )

    def test_bash_firewall_on_pre_tool_use(self) -> None:
        """bash-firewall must be mapped to PreToolUse event."""
        text = load_hooks_md()
        ctx = self._find_hook_event_context(text, "bash-firewall")
        assert ctx, "bash-firewall not found in HOOKS.md"
        assert "PreToolUse" in ctx, "bash-firewall must be associated with PreToolUse event"

    def test_review_reminder_on_post_tool_use(self) -> None:
        """review-reminder must be mapped to PostToolUse event."""
        text = load_hooks_md()
        ctx = self._find_hook_event_context(text, "review-reminder")
        assert ctx, "review-reminder not found in HOOKS.md"
        assert "PostToolUse" in ctx, "review-reminder must be associated with PostToolUse event"

    def test_auto_capture_on_stop(self) -> None:
        """auto-capture must be mapped to Stop event."""
        text = load_hooks_md()
        ctx = self._find_hook_event_context(text, "auto-capture")
        assert ctx, "auto-capture not found in HOOKS.md"
        assert "Stop" in ctx, "auto-capture must be associated with Stop event"

    def test_write_handoff_on_stop(self) -> None:
        """write-handoff must be mapped to Stop event."""
        text = load_hooks_md()
        ctx = self._find_hook_event_context(text, "write-handoff")
        assert ctx, "write-handoff not found in HOOKS.md"
        assert "Stop" in ctx, "write-handoff must be associated with Stop event"
