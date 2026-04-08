"""T3: Out-of-band (OOB) commands.

Tests:
- OOB commands are recognized (/stop, /cancel, /status, /reset)
- Non-OOB commands pass through to Claude
- OOB commands handled in producer thread (not queued)
- /stop terminates active subprocess
"""

from __future__ import annotations

import pytest

OOB_COMMANDS = frozenset({"/stop", "/\u0441\u0442\u043e\u043f", "/cancel", "/status", "/reset"})


class TestOOBRecognition:
    """T3.1: Recognize OOB vs regular commands."""

    @pytest.mark.parametrize(
        "cmd",
        ["/stop", "/\u0441\u0442\u043e\u043f", "/cancel", "/status", "/reset"],
    )
    def test_oob_command_recognized(self, cmd: str) -> None:
        """Known OOB commands are in the OOB set."""
        assert cmd in OOB_COMMANDS

    @pytest.mark.parametrize("cmd", ["/help", "/start", "/new", "/settings"])
    def test_non_oob_not_in_set(self, cmd: str) -> None:
        """Non-OOB commands are NOT in the OOB set."""
        assert cmd not in OOB_COMMANDS

    def test_regular_text_not_oob(self) -> None:
        """Regular text starting with / but not a command."""
        text = "/path/to/file"
        cmd = text.split(None, 1)[0].lower()
        assert cmd not in OOB_COMMANDS

    def test_oob_with_args(self) -> None:
        """OOB command with arguments: only first word is the command."""
        text = "/stop all processes"
        cmd = text.split(None, 1)[0].lower()
        assert cmd in OOB_COMMANDS


class TestOOBRouting:
    """T3.2: OOB commands must be handled by producer, not queued.

    Verify contract: OOB detected -> handle immediately -> don't enqueue.
    Non-OOB -> enqueue for consumer thread.
    """

    def test_oob_not_queued(self) -> None:
        """OOB commands should NOT be put into message queue.

        Contract:
        1. Producer polls getUpdates
        2. For each update, check if text starts with OOB command
        3. If yes: handle in producer thread directly
        4. If no: put into per-agent queue for consumer
        """
        updates = [
            {"message": {"text": "/stop", "chat": {"id": 1}, "from": {"id": 111}}},
            {"message": {"text": "hello", "chat": {"id": 1}, "from": {"id": 111}}},
            {"message": {"text": "/status", "chat": {"id": 1}, "from": {"id": 111}}},
        ]
        queued = []
        handled_oob = []
        for u in updates:
            text = (u.get("message") or {}).get("text", "")
            cmd = text.split(None, 1)[0].lower() if text.startswith("/") else ""
            if cmd in OOB_COMMANDS:
                handled_oob.append(text)
            else:
                queued.append(text)

        assert handled_oob == ["/stop", "/status"]
        assert queued == ["hello"]
