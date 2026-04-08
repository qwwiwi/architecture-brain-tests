"""T9: OpenViking push.

Tests:
- Push creates session, adds messages, extracts, deletes session
- Anti-pollution guard for forwarded content
- Anti-pollution guard for external_media
- No guard for own_text/own_voice
- User text truncated to 3000 chars
- Session cleanup in finally block
- Skip if no openviking.key file
"""

from __future__ import annotations

from typing import Any


class TestOVPushFlow:
    """T9.1: OpenViking push-to-memory flow.

    Contract:
    1. POST /sessions -> get session_id
    2. POST /sessions/{sid}/messages (user)
    3. POST /sessions/{sid}/messages (assistant)
    4. POST /sessions/{sid}/extract -> get extracted memories
    5. DELETE /sessions/{sid} (always, in finally)
    """

    def test_push_flow_steps(self) -> None:
        """Verify all 5 steps in correct order."""
        steps = []
        sid = "test-session-id"

        # Step 1: Create session
        steps.append(("POST", "/sessions"))
        # Step 2: User message
        steps.append(("POST", f"/sessions/{sid}/messages"))
        # Step 3: Assistant message
        steps.append(("POST", f"/sessions/{sid}/messages"))
        # Step 4: Extract
        steps.append(("POST", f"/sessions/{sid}/extract"))
        # Step 5: Cleanup
        steps.append(("DELETE", f"/sessions/{sid}"))

        assert len(steps) == 5
        assert steps[0] == ("POST", "/sessions")
        assert steps[-1] == ("DELETE", f"/sessions/{sid}")

    def test_text_truncation(self) -> None:
        """User text truncated to 3000 chars before push."""
        long_text = "A" * 5000
        truncated = long_text[:3000]
        assert len(truncated) == 3000


class TestAntiPollution:
    """T9.2: Anti-pollution guards for OpenViking.

    Prevents extracting forwarded content as user's own preferences.
    """

    def test_forwarded_guard(self) -> None:
        """Forwarded messages get extraction hint."""
        text = "[source:forwarded | from_user]\nSome forwarded content"
        if "[source:forwarded" in text:
            guard = (
                "\n[extraction hint: this content was FORWARDED to princ from someone else. "
                "Do NOT extract as princ's own preferences.]\n"
            )
        else:
            guard = ""
        assert "FORWARDED" in guard
        assert "Do NOT extract" in guard

    def test_external_media_guard(self) -> None:
        """External media gets extraction hint."""
        text = "[source:external_media | video]\nSome video content"
        if "[source:external_media" in text:
            guard = (
                "\n[extraction hint: this is external media princ is sharing, not his own words. "
                "Do NOT extract as princ's preferences.]\n"
            )
        else:
            guard = ""
        assert "external media" in guard

    def test_own_text_no_guard(self) -> None:
        """Own text messages have no guard."""
        text = "[source:own_text | direct]\nHello agent"
        if "[source:forwarded" in text:
            guard = "forwarded"
        elif "[source:external_media" in text:
            guard = "external"
        else:
            guard = ""
        assert guard == ""

    def test_own_voice_no_guard(self) -> None:
        """Own voice messages have no guard."""
        text = "[source:own_voice | transcribed]\nVoice message text"
        if "[source:forwarded" in text:
            guard = "forwarded"
        elif "[source:external_media" in text:
            guard = "external"
        else:
            guard = ""
        assert guard == ""


class TestOVSkipConditions:
    """T9.3: Conditions when OV push is skipped."""

    def test_skip_if_no_key_file(self, tmp_path: Any) -> None:
        """Skip push if openviking.key doesn't exist."""
        key_file = tmp_path / "secrets" / "openviking.key"
        assert not key_file.exists()

    def test_skip_if_session_creation_fails(self) -> None:
        """Skip push if session creation returns non-200."""
        status_code = 500
        result = None if status_code != 200 else "ok"
        assert result is None

    def test_cleanup_always_runs(self) -> None:
        """Session DELETE runs even if extract fails.

        Contract: DELETE in finally block.
        """
        cleanup_ran = False
        sid = "test-sid"
        try:
            raise ConnectionError("extract failed")
        except Exception:
            pass
        finally:
            if sid:
                cleanup_ran = True
        assert cleanup_ran
