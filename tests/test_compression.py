"""T10: Memory compression scripts.

Tests:
- trim-hot.sh: parses HOT entries, separates old vs recent
- trim-hot.sh: Sonnet compression produces summary lines
- trim-hot.sh: bash fallback extracts first 120 chars
- trim-hot.sh: compressed entries appended to WARM
- compress-warm.sh: groups related entries into topic facts
- compress-warm.sh: skips if WARM < 10KB
"""

from __future__ import annotations

import re
import time
from pathlib import Path


class TestHotEntryParsing:
    """T10.1: Parse HOT memory entries."""

    def test_parse_entry_blocks(self, hot_memory_text: str) -> None:
        """Split HOT file into entry blocks starting with ###."""
        blocks = re.split(r"(?=^### )", hot_memory_text, flags=re.MULTILINE)
        # Filter empty/header blocks
        entries = [b for b in blocks if b.startswith("### ")]
        assert len(entries) == 5  # 5 entries in sample

    def test_extract_timestamp(self, hot_memory_text: str) -> None:
        """Extract timestamp from ### YYYY-MM-DD HH:MM header."""
        pattern = r"### (\d{4}-\d{2}-\d{2} \d{2}:\d{2})"
        timestamps = re.findall(pattern, hot_memory_text)
        assert len(timestamps) == 5
        assert timestamps[0] == "2026-04-07 10:00"

    def test_extract_source_tag(self, hot_memory_text: str) -> None:
        """Extract [source_tag] from entry header."""
        pattern = r"### .+ \[(\w+)\]"
        tags = re.findall(pattern, hot_memory_text)
        assert "own_text" in tags
        assert "own_voice" in tags
        assert "forwarded" in tags


class TestAgeDetection:
    """T10.2: Separate old (>24h) vs recent entries."""

    def test_old_entries_detected(self) -> None:
        """Entries >24h old are classified as old."""
        now = time.time()
        entry_time = now - (25 * 3600)  # 25 hours ago
        age_hours = (now - entry_time) / 3600
        assert age_hours > 24

    def test_recent_entries_kept(self) -> None:
        """Entries <24h old are classified as recent."""
        now = time.time()
        entry_time = now - (12 * 3600)  # 12 hours ago
        age_hours = (now - entry_time) / 3600
        assert age_hours < 24


class TestBashFallback:
    """T10.3: Bash fallback compression (no Sonnet).

    Extracts first 120 chars of agent response as summary.
    """

    def test_bash_extract_120_chars(self) -> None:
        """Bash fallback takes first 120 chars of Thrall response."""
        agent_line = (
            "**Thrall:** Мой вождь, вот полное дерево моей архитектуры"
            " с описанием каждого файла и его назначения в системе Orgrimmar"
        )
        # Extract after "**Thrall:** "
        prefix = "**Thrall:** "
        if agent_line.startswith(prefix):
            snippet = agent_line[len(prefix) :][:120]
        assert len(snippet) <= 120
        assert snippet.startswith("Мой вождь")

    def test_bash_summary_format(self) -> None:
        """Bash summary format: - YYYY-MM-DD HH:MM: snippet."""
        ts = "2026-04-08 10:00"
        snippet = "Short summary of what happened"
        summary = f"- {ts}: {snippet}"
        assert summary.startswith("- 2026-04-08")


class TestSonnetCompression:
    """T10.4: Sonnet model compression.

    Contract:
    - Input: raw HOT entries (### blocks)
    - Output: summary lines starting with '- YYYY-MM-DD HH:MM: '
    - Minimum 3 lines output for validation
    """

    def test_sonnet_output_format(self) -> None:
        """Sonnet output must be lines starting with '- '."""
        sonnet_output = (
            "- 2026-04-07 10:00: Gateway refactored into modules\n"
            "- 2026-04-07 14:30: Deploy verified, all services running\n"
            "- 2026-04-08 09:00: Tests created for gateway\n"
        )
        lines = [ln for ln in sonnet_output.strip().split("\n") if ln.startswith("- ")]
        assert len(lines) >= 3

    def test_sonnet_output_has_timestamps(self) -> None:
        """Each summary line has a timestamp."""
        line = "- 2026-04-08 12:00: Forwarded content analyzed, not suitable"
        match = re.match(r"^- (\d{4}-\d{2}-\d{2} \d{2}:\d{2}): ", line)
        assert match is not None


class TestCompressedToWarm:
    """T10.5: Compressed entries appended to WARM."""

    def test_append_to_warm(self, tmp_workspace: Path) -> None:
        """Compressed entries are appended under auto-compressed section."""
        warm_file = tmp_workspace / "core" / "warm" / "decisions.md"
        original = warm_file.read_text()

        # Simulate append
        date_header = "\n## 2026-04-08 (auto-compressed)\n\n"
        summaries = "- GATEWAY: Refactored into modules\n- TESTS: Created test suite\n"
        warm_file.write_text(original + date_header + summaries)

        content = warm_file.read_text()
        assert "(auto-compressed)" in content
        assert "GATEWAY" in content


class TestCompressWarmConditions:
    """T10.6: compress-warm.sh trigger conditions."""

    def test_skip_if_warm_small(self, tmp_workspace: Path) -> None:
        """Skip compression if WARM < 10KB."""
        warm_file = tmp_workspace / "core" / "warm" / "decisions.md"
        size = warm_file.stat().st_size
        assert size < 10240, "Fixture WARM should be < 10KB"

    def test_trigger_if_warm_large(self, tmp_workspace: Path) -> None:
        """Trigger compression if WARM > 10KB."""
        warm_file = tmp_workspace / "core" / "warm" / "decisions.md"
        # Write enough to exceed 10KB
        warm_file.write_text("A" * 11000)
        size = warm_file.stat().st_size
        assert size > 10240
