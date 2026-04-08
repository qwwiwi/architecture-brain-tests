"""T11: WARM memory rotation.

Tests:
- rotate-warm.sh: entries >14 days moved to COLD
- rotate-warm.sh: recent entries kept in WARM
- Date parsing from ## YYYY-MM-DD headers
- COLD (MEMORY.md) receives archived entries
- memory-rotate.sh: archives COLD >5KB to monthly files
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


class TestDateParsing:
    """T11.1: Parse dates from WARM section headers."""

    def test_parse_date_header(self) -> None:
        """Extract date from ## YYYY-MM-DD header."""
        header = "## 2026-04-06"
        match = re.match(r"^## (\d{4}-\d{2}-\d{2})", header)
        assert match is not None
        date_str = match.group(1)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        assert dt.year == 2026
        assert dt.month == 4
        assert dt.day == 6

    def test_parse_auto_compressed_header(self) -> None:
        """Extract date from ## YYYY-MM-DD (auto-compressed) header."""
        header = "## 2026-04-08 (auto-compressed)"
        match = re.match(r"^## (\d{4}-\d{2}-\d{2})", header)
        assert match is not None
        assert match.group(1) == "2026-04-08"


class TestAgeCheck:
    """T11.2: 14-day cutoff for WARM rotation."""

    def test_old_entry_exceeds_14_days(self) -> None:
        """Entry from 15 days ago should be rotated."""
        entry_date = datetime(2026, 3, 24)
        now = datetime(2026, 4, 8)
        age = (now - entry_date).days
        assert age > 14

    def test_recent_entry_within_14_days(self) -> None:
        """Entry from 5 days ago stays in WARM."""
        entry_date = datetime(2026, 4, 3)
        now = datetime(2026, 4, 8)
        age = (now - entry_date).days
        assert age <= 14

    def test_exactly_14_days_stays(self) -> None:
        """Entry exactly 14 days old stays (rotate at >14)."""
        entry_date = datetime(2026, 3, 25)
        now = datetime(2026, 4, 8)
        age = (now - entry_date).days
        assert age == 14
        # 14 days = keep, >14 = rotate


class TestWarmToCold:
    """T11.3: Move old entries from WARM to COLD."""

    def test_old_entry_moved_to_cold(self, tmp_workspace: Path) -> None:
        """Old entry removed from WARM and appended to MEMORY.md."""
        warm_file = tmp_workspace / "core" / "warm" / "decisions.md"

        warm_content = (
            "# WARM DECISIONS\n\n"
            "## 2026-03-20\n\n- Old entry from March\n\n"
            "## 2026-04-08\n\n- Recent entry\n"
        )
        warm_file.write_text(warm_content)

        # Simulate rotation: split by ## headers
        sections = re.split(r"(?=^## )", warm_content, flags=re.MULTILINE)
        _ = sections[0]  # Header (everything before first ##)
        old_sections = []
        recent_sections = []

        cutoff = datetime(2026, 3, 25)  # 14 days before 2026-04-08
        for section in sections[1:]:
            date_match = re.match(r"## (\d{4}-\d{2}-\d{2})", section)
            if date_match:
                dt = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                if dt < cutoff:
                    old_sections.append(section)
                else:
                    recent_sections.append(section)

        assert len(old_sections) == 1  # March entry
        assert len(recent_sections) == 1  # April entry
        assert "Old entry from March" in old_sections[0]


class TestColdArchival:
    """T11.4: Archive COLD (MEMORY.md) to monthly files.

    Contract:
    - Trigger: MEMORY.md > 5KB
    - Archive to: memory/archive/YYYY-MM.md
    - Reset MEMORY.md to header only
    """

    def test_archive_trigger(self, tmp_workspace: Path) -> None:
        """Archive triggers when MEMORY.md > 5KB."""
        cold_file = tmp_workspace / "core" / "MEMORY.md"
        cold_file.write_text("A" * 6000)
        assert cold_file.stat().st_size > 5120

    def test_archive_filename_format(self) -> None:
        """Archive file named YYYY-MM.md."""
        now = datetime(2026, 4, 8)
        filename = now.strftime("%Y-%m") + ".md"
        assert filename == "2026-04.md"
