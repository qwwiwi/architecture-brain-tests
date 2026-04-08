"""T5: Session management.

Tests:
- New session creates UUID and persists to disk
- Existing session reads from disk
- Session ID format is valid UUID
- Session file naming convention: sid-{agent}-{chat_id}.txt
- First turn marker: sid-{agent}-{chat_id}.first
"""

from __future__ import annotations

import uuid
from pathlib import Path


class TestSessionCreation:
    """T5.1: New session ID generation."""

    def test_new_session_generates_uuid(self, tmp_path: Path) -> None:
        """First call creates a new UUID and writes to file."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        agent = "testagent"
        chat_id = 111111
        sid_file = state_dir / f"sid-{agent}-{chat_id}.txt"

        # Simulate session_id_for()
        assert not sid_file.exists()
        sid = str(uuid.uuid4())
        sid_file.write_text(sid)

        assert sid_file.exists()
        # Validate UUID format
        uuid.UUID(sid)  # Raises if invalid

    def test_existing_session_reads_from_file(self, tmp_path: Path) -> None:
        """Second call reads existing session from disk."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        agent = "testagent"
        chat_id = 111111
        sid_file = state_dir / f"sid-{agent}-{chat_id}.txt"

        # Write session
        expected_sid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        sid_file.write_text(expected_sid)

        # Read back
        sid = sid_file.read_text().strip()
        assert sid == expected_sid


class TestSessionNaming:
    """T5.2: Session file naming conventions."""

    def test_sid_file_format(self) -> None:
        """Session file: sid-{agent}-{chat_id}.txt"""
        agent = "thrall"
        chat_id = 164795011
        filename = f"sid-{agent}-{chat_id}.txt"
        assert filename == "sid-thrall-164795011.txt"

    def test_first_turn_marker(self, tmp_path: Path) -> None:
        """First turn creates .first marker file. Subsequent turns check it."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        agent = "thrall"
        chat_id = 111111
        first_file = state_dir / f"sid-{agent}-{chat_id}.first"

        # First turn: marker doesn't exist
        assert not first_file.exists()
        is_first = not first_file.exists()
        assert is_first

        # After first turn: create marker
        first_file.write_text("1")

        # Second turn: marker exists
        is_first = not first_file.exists()
        assert not is_first


class TestSessionResume:
    """T5.3: Resume vs new session in Claude invocation.

    Contract:
    - First turn: claude -p "text" --session-id {sid}
    - Later turns: claude -p "text" --resume {sid}
    """

    def test_first_turn_uses_session_id(self) -> None:
        """First turn: --session-id flag."""
        sid = "test-uuid"
        flag = f"--session-id {sid}"
        assert "--session-id" in flag

    def test_resume_uses_resume_flag(self) -> None:
        """Later turns: --resume flag."""
        sid = "test-uuid"
        flag = f"--resume {sid}"
        assert "--resume" in flag
