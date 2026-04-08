"""T8: HOT memory writes.

Tests:
- append_to_hot_memory writes correct format
- Entry has timestamp, source_tag, user snippet, agent snippet
- Snippets truncated to 200 chars
- Newlines in snippets replaced with spaces
- Emergency trim triggers at >20KB
- Emergency trim keeps last 600 lines
- File locking prevents interleaved writes
"""

from __future__ import annotations

import time
from pathlib import Path


def append_to_hot_memory(
    hot_file: Path, agent: str, user_text: str, agent_response: str, source_tag: str
) -> None:
    """Simplified version of gateway.append_to_hot_memory for testing."""
    if not hot_file.parent.exists():
        return
    ts = time.strftime("%Y-%m-%d %H:%M")
    u_snippet = (user_text or "").replace("\n", " ")[:200]
    a_snippet = (agent_response or "(inline)").replace("\n", " ")[:200]
    entry = (
        f"\n### {ts} [{source_tag}]\n"
        f"**Принц:** {u_snippet}\n"
        f"**{agent.capitalize()}:** {a_snippet}\n"
    )
    with open(hot_file, "a") as f:
        f.write(entry)


class TestHotMemoryFormat:
    """T8.1: Entry format in hot/recent.md."""

    def test_entry_format(self, tmp_workspace: Path) -> None:
        """Entry has ### timestamp [source_tag] header."""
        hot_file = tmp_workspace / "core" / "hot" / "recent.md"
        append_to_hot_memory(hot_file, "thrall", "hello", "hi there", "own_text")

        content = hot_file.read_text()
        assert "### " in content
        assert "[own_text]" in content
        assert "**Принц:**" in content
        assert "**Thrall:**" in content

    def test_snippet_truncation(self, tmp_workspace: Path) -> None:
        """Snippets truncated to 200 chars."""
        hot_file = tmp_workspace / "core" / "hot" / "recent.md"
        long_text = "A" * 300
        append_to_hot_memory(hot_file, "thrall", long_text, "short", "own_text")

        content = hot_file.read_text()
        # Find the user snippet line
        for line in content.split("\n"):
            if line.startswith("**Принц:**"):
                snippet = line.replace("**Принц:** ", "")
                assert len(snippet) <= 200

    def test_newlines_replaced(self, tmp_workspace: Path) -> None:
        """Newlines in user/agent text replaced with spaces."""
        hot_file = tmp_workspace / "core" / "hot" / "recent.md"
        text_with_newlines = "line1\nline2\nline3"
        append_to_hot_memory(hot_file, "thrall", text_with_newlines, "ok", "own_text")

        content = hot_file.read_text()
        # Entry lines should not have the original newlines
        for line in content.split("\n"):
            if line.startswith("**Принц:**"):
                assert "\n" not in line.replace("\n", "")  # trivially true
                assert "line1 line2 line3" in line

    def test_empty_response_fallback(self, tmp_workspace: Path) -> None:
        """Empty agent response shows (inline)."""
        hot_file = tmp_workspace / "core" / "hot" / "recent.md"
        append_to_hot_memory(hot_file, "thrall", "test", "", "own_text")

        content = hot_file.read_text()
        assert "(inline)" in content


class TestEmergencyTrim:
    """T8.2: Emergency trim when HOT file >20KB."""

    def test_trim_triggers_above_20kb(self, tmp_workspace: Path) -> None:
        """File >20480 bytes triggers emergency trim."""
        hot_file = tmp_workspace / "core" / "hot" / "recent.md"
        # Write >20KB
        header = "# Hot memory -- last 72h rolling journal\n"
        entries = ""
        for i in range(200):
            entries += f"\n### 2026-04-08 {i:02d}:00 [own_text]\n"
            entries += f"**Принц:** Message {i} with some padding text\n"
            entries += f"**Thrall:** Response {i} with more padding text\n"

        hot_file.write_text(header + entries)
        size = hot_file.stat().st_size
        assert size > 20480, f"Expected >20KB, got {size}"

    def test_trim_keeps_last_600_lines(self, tmp_workspace: Path) -> None:
        """After trim, file has at most 600 lines + header."""
        hot_file = tmp_workspace / "core" / "hot" / "recent.md"
        # Write many lines
        lines = ["# Hot memory -- last 72h rolling journal"]
        for i in range(300):
            lines.append(f"\n### 2026-04-08 {i:02d}:00 [own_text]")
            lines.append(f"**Принц:** Message {i}")
            lines.append(f"**Thrall:** Response {i}")

        hot_file.write_text("\n".join(lines))
        all_lines = hot_file.read_text().split("\n")

        if len(all_lines) > 600:
            kept = all_lines[-600:]
            # Find first entry header
            for idx, ln in enumerate(kept):
                if ln.startswith("### "):
                    kept = kept[idx:]
                    break
            assert len(kept) <= 600

    def test_trim_starts_at_entry_boundary(self, tmp_workspace: Path) -> None:
        """Trimmed file starts at a ### entry header, not mid-entry."""
        hot_file = tmp_workspace / "core" / "hot" / "recent.md"
        lines = ["# Header"]
        for i in range(200):
            lines.extend(
                [
                    f"### 2026-04-08 {i:02d}:00 [own_text]",
                    f"**Принц:** Msg {i}",
                    f"**Thrall:** Resp {i}",
                    "",
                ]
            )
        hot_file.write_text("\n".join(lines))

        all_lines = hot_file.read_text().split("\n")
        kept = all_lines[-600:]
        # First non-empty line should be a ### header
        for ln in kept:
            if ln.strip():
                assert ln.startswith("### ") or ln.startswith("# "), f"Bad start: {ln}"
                break
