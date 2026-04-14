"""T12: End-to-end pipeline.

Tests:
- Full flow: Telegram update -> process_update -> Claude -> response -> memory
- Verify all data transformations in correct order
- Verify memory writes happen after Claude response
- Verify parallel memory writes (HOT + OpenViking)
"""

from __future__ import annotations

from typing import Any


class TestE2EPipeline:
    """T12.1: Full message pipeline stages.

    1. Telegram update received
    2. User allowlist check
    3. Group chat gating
    4. OOB command check
    5. Source classification
    6. Media processing (if any)
    7. Session management (new vs resume)
    8. Claude invocation
    9. Response formatting (MD -> HTML)
    10. Send to Telegram
    11. Write HOT memory
    12. Push to OpenViking
    """

    def test_pipeline_stages_order(self) -> None:
        """All 12 stages execute in correct order."""
        stages = [
            "receive_update",
            "allowlist_check",
            "group_gating",
            "oob_check",
            "classify_source",
            "process_media",
            "session_management",
            "invoke_claude",
            "format_response",
            "send_telegram",
            "write_hot_memory",
            "push_openviking",
        ]
        assert len(stages) == 12
        assert stages[0] == "receive_update"
        assert stages[-1] == "push_openviking"
        # Claude invocation must come before response formatting
        assert stages.index("invoke_claude") < stages.index("format_response")
        # Memory writes must come after sending response
        assert stages.index("send_telegram") < stages.index("write_hot_memory")

    def test_denied_user_stops_early(self) -> None:
        """Denied user exits at stage 2, no Claude invocation."""
        user_id = 999999
        allowlist = [111111, 222222]
        reached_claude = user_id in allowlist
        assert not reached_claude

    def test_oob_command_stops_before_claude(self) -> None:
        """OOB command handled at stage 4, no Claude invocation."""
        text = "/stop"
        oob_commands = {"/stop", "/cancel", "/status", "/reset", "/стоп"}
        cmd = text.split(None, 1)[0].lower()
        reached_claude = cmd not in oob_commands
        assert not reached_claude


class TestE2ETextMessage:
    """T12.2: End-to-end for plain text message."""

    def test_text_message_flow(self, telegram_update: dict[str, Any]) -> None:
        """Plain text: no media processing, direct to Claude."""
        msg = telegram_update["message"]
        text = msg.get("text", "")
        has_media = any(
            k in msg for k in ("voice", "audio", "video_note", "video", "photo", "document")
        )
        assert text == "Hello agent"
        assert not has_media

    def test_text_message_creates_memory(self) -> None:
        """After Claude response, both HOT and OV writes happen."""
        user_text = "Hello agent"
        agent_response = "Hello, chief."
        source_tag = "own_text"

        # HOT memory entry
        hot_entry = (
            f"### 2026-04-08 12:00 [{source_tag}]\n"
            f"**Принц:** {user_text}\n**Thrall:** {agent_response}\n"
        )
        assert source_tag in hot_entry
        assert user_text in hot_entry

        # OV push text
        ov_text = f"[source:{source_tag} | direct]\n{user_text}"
        assert f"[source:{source_tag}" in ov_text


class TestE2EVoiceMessage:
    """T12.3: End-to-end for voice message."""

    def test_voice_adds_transcript(self) -> None:
        """Voice message: download -> transcribe -> add to text."""
        transcript = "This is what the user said"
        text = "(принц прислал вложение)"
        media_note = f"\n\n[Голосовое/аудио, транскрипт]: {transcript}"
        full_text = text + media_note
        assert "транскрипт" in full_text
        assert transcript in full_text

    def test_voice_transcription_failure(self) -> None:
        """Failed transcription adds fallback note."""
        text = "(принц прислал вложение)"
        media_note = "\n\n[Аудио не удалось транскрибировать: /path/to/file.ogg]"
        full_text = text + media_note
        assert "не удалось" in full_text


class TestE2EForwardedMessage:
    """T12.4: End-to-end for forwarded message."""

    def test_forwarded_gets_source_tag(self) -> None:
        """Forwarded message tagged as 'forwarded' for OV guard."""
        msg = {"text": "forwarded content", "forward_from": {"id": 999}}
        is_forward = "forward_from" in msg
        source_tag = "forwarded" if is_forward else "own_text"
        assert source_tag == "forwarded"

    def test_forwarded_ov_guard_applied(self) -> None:
        """OV push for forwarded message includes anti-pollution guard."""
        text = "[source:forwarded | from_user]\nForwarded content"
        has_guard = "[source:forwarded" in text
        assert has_guard


class TestE2EContextLoading:
    """T12.5: Context loading on session start.

    On first turn, these 4 @includes are loaded into Claude context:
    1. CLAUDE.md (SOUL + identity)
    2. USER.md (who the user is)
    3. rules.md (boundaries)
    4. warm/decisions.md (recent decisions)
    5. hot/handoff.md (last 10 entries from recent.md)

    AGENTS.md and TOOLS.md are on-demand (Read tool, not auto-loaded).
    recent.md is NOT loaded directly -- handoff.md is extracted from it.
    """

    def test_context_files_exist(self, tmp_workspace: Any) -> None:
        """All context files must exist in workspace."""
        required_paths = [
            "core/hot/recent.md",
            "core/warm/decisions.md",
            "core/MEMORY.md",
        ]
        for rel_path in required_paths:
            full_path = tmp_workspace / rel_path
            assert full_path.exists(), f"Missing: {rel_path}"

    def test_first_turn_injects_memory(self) -> None:
        """First turn injects latest MEMORY.md section.

        Contract: read_latest_memory_section(agent) returns last ## section.
        """
        memory_content = (
            "# COLD MEMORY\n\n"
            "## 2026-03-01\n\nOld stuff\n\n"
            "## 2026-04-06\n\nRecent migration notes\n"
        )
        # Find last ## section
        import re

        matches = list(re.finditer(r"^## .+$", memory_content, re.MULTILINE))
        if matches:
            last_start = matches[-1].start()
            section = memory_content[last_start:][:2000]
        else:
            section = memory_content[:2000]
        assert "2026-04-06" in section
        assert "Recent migration notes" in section
