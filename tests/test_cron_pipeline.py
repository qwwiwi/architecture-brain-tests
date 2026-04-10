"""
T19: Cron pipeline validation.

Verifies that memory management scripts follow safety standards
(set -euo pipefail, flock), cron order is correct, and pipeline
documentation is consistent across all files.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")
SCRIPTS_DIR = ARCH_ROOT / "scripts"

MEMORY_SCRIPTS = [
    "trim-hot.sh",
    "compress-warm.sh",
    "rotate-warm.sh",
    "memory-rotate.sh",
]

# Canonical cron order
CRON_ORDER = [
    "rotate-warm",     # 04:30 UTC
    "trim-hot",        # 05:00 UTC
    "compress-warm",   # 06:00 UTC
    "ov-session-sync", # 06:30 UTC
    "memory-rotate",   # 21:00 UTC
]


def load_script(name: str) -> str:
    """Load a script from scripts/ directory."""
    path = SCRIPTS_DIR / name
    if not path.exists():
        pytest.skip(f"{name} not found")
    return path.read_text(encoding="utf-8")


def load_md(name: str) -> str:
    """Load a markdown file from repo root."""
    path = ARCH_ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not found")
    return path.read_text(encoding="utf-8")


# --- Script safety ---


class TestScriptSafety:
    """T19.1 All bash scripts follow safety standards."""

    @pytest.mark.parametrize("script", MEMORY_SCRIPTS)
    def test_has_set_euo_pipefail(self, script: str) -> None:
        """Each script must use set -euo pipefail."""
        text = load_script(script)
        assert "set -euo pipefail" in text, f"{script} must have set -euo pipefail"

    @pytest.mark.parametrize("script", MEMORY_SCRIPTS)
    def test_has_shebang(self, script: str) -> None:
        """Each script must start with shebang."""
        text = load_script(script)
        assert text.startswith("#!/"), f"{script} must start with shebang"

    @pytest.mark.parametrize("script", MEMORY_SCRIPTS)
    def test_uses_quotes_for_variables(self, script: str) -> None:
        """Scripts should quote variable references."""
        text = load_script(script)
        # Count unquoted variable uses (basic heuristic)
        # Look for $VAR not inside quotes (simplified check)
        unquoted = re.findall(r'[^"]\$[A-Z_]+[^"}\s]', text)
        # Allow some false positives but flag if too many
        assert len(unquoted) < 20, (
            f"{script} has too many potentially unquoted variables: {len(unquoted)}"
        )


class TestScriptLocking:
    """T19.2 Scripts that modify shared files use flock."""

    def test_trim_hot_uses_flock(self) -> None:
        """trim-hot.sh must use flock (prevents gateway conflicts)."""
        text = load_script("trim-hot.sh")
        assert "flock" in text, "trim-hot.sh must use flock for concurrent safety"

    def test_compress_warm_has_guard(self) -> None:
        """compress-warm.sh must have size guard (>10KB)."""
        text = load_script("compress-warm.sh")
        assert "10" in text and ("KB" in text or "000" in text or "size" in text.lower()), (
            "compress-warm.sh must check WARM size before compression"
        )

    def test_memory_rotate_has_size_guard(self) -> None:
        """memory-rotate.sh must check MEMORY.md size before archival."""
        text = load_script("memory-rotate.sh")
        assert "5000" in text or "5KB" in text or "size" in text.lower(), (
            "memory-rotate.sh must have size guard for archival"
        )


# --- Sonnet fallback ---


class TestSonnetFallback:
    """T19.3 Scripts with Sonnet calls have bash fallback."""

    def test_trim_hot_has_fallback(self) -> None:
        """trim-hot.sh must have bash fallback if Sonnet unavailable."""
        text = load_script("trim-hot.sh")
        has_sonnet = "sonnet" in text.lower() or "claude" in text.lower()
        has_fallback = "fallback" in text.lower() or "120" in text
        if has_sonnet:
            assert has_fallback, (
                "trim-hot.sh uses Sonnet but has no bash fallback"
            )

    def test_compress_warm_skip_on_failure(self) -> None:
        """compress-warm.sh must skip if Sonnet unavailable."""
        text = load_script("compress-warm.sh")
        has_sonnet = "sonnet" in text.lower() or "claude" in text.lower()
        has_skip = "skip" in text.lower() or "exit" in text
        if has_sonnet:
            assert has_skip, (
                "compress-warm.sh uses Sonnet but doesn't skip on failure"
            )


# --- Cron order ---


class TestCronOrder:
    """T19.4 Cron pipeline order is correct across documentation."""

    def _extract_cron_positions(self, text: str) -> dict[str, int]:
        """Find position of each cron script in text."""
        positions = {}
        for script in CRON_ORDER:
            pos = text.find(script)
            if pos >= 0:
                positions[script] = pos
        return positions

    def test_memory_md_cron_order(self) -> None:
        """MEMORY.md must have correct cron order."""
        text = load_md("MEMORY.md")
        # Find crontab blocks
        crontab_blocks = re.findall(r"```crontab\n(.*?)```", text, re.DOTALL)
        if not crontab_blocks:
            # Check inline cron
            crontab_blocks = [text]

        for block in crontab_blocks:
            positions = self._extract_cron_positions(block)
            if len(positions) < 3:
                continue

            ordered = sorted(positions.items(), key=lambda x: x[1])
            ordered_names = [name for name, _ in ordered]

            for i in range(len(ordered_names) - 1):
                a, b = ordered_names[i], ordered_names[i + 1]
                if a in CRON_ORDER and b in CRON_ORDER:
                    a_idx = CRON_ORDER.index(a)
                    b_idx = CRON_ORDER.index(b)
                    assert a_idx < b_idx, (
                        f"MEMORY.md: {a} must come before {b}"
                    )

    def test_architecture_md_cron_order(self) -> None:
        """ARCHITECTURE.md must have correct cron order."""
        text = load_md("ARCHITECTURE.md")
        crontab_blocks = re.findall(r"```crontab\n(.*?)```", text, re.DOTALL)
        if not crontab_blocks:
            crontab_blocks = [text]

        for block in crontab_blocks:
            positions = self._extract_cron_positions(block)
            if len(positions) < 3:
                continue

            ordered = sorted(positions.items(), key=lambda x: x[1])
            ordered_names = [name for name, _ in ordered]

            for i in range(len(ordered_names) - 1):
                a, b = ordered_names[i], ordered_names[i + 1]
                if a in CRON_ORDER and b in CRON_ORDER:
                    assert CRON_ORDER.index(a) < CRON_ORDER.index(b), (
                        f"ARCHITECTURE.md: {a} must come before {b}"
                    )

    def test_checklist_cron_order(self) -> None:
        """CHECKLIST.md must have correct cron order."""
        text = load_md("CHECKLIST.md")
        positions = self._extract_cron_positions(text)
        if len(positions) < 3:
            pytest.skip("CHECKLIST.md has fewer than 3 cron scripts mentioned")

        ordered = sorted(positions.items(), key=lambda x: x[1])
        ordered_names = [name for name, _ in ordered]

        for i in range(len(ordered_names) - 1):
            a, b = ordered_names[i], ordered_names[i + 1]
            if a in CRON_ORDER and b in CRON_ORDER:
                assert CRON_ORDER.index(a) < CRON_ORDER.index(b), (
                    f"CHECKLIST.md: {a} must come before {b}"
                )


# --- Pipeline completeness ---


class TestPipelineCompleteness:
    """T19.5 All 5 cron jobs documented everywhere."""

    def test_five_scripts_in_memory_md(self) -> None:
        """MEMORY.md must reference all 5 cron scripts."""
        text = load_md("MEMORY.md")
        for script in CRON_ORDER:
            assert script in text, f"MEMORY.md missing {script}"

    def test_five_scripts_in_architecture_md(self) -> None:
        """ARCHITECTURE.md must reference all 5 cron scripts."""
        text = load_md("ARCHITECTURE.md")
        for script in CRON_ORDER:
            assert script in text, f"ARCHITECTURE.md missing {script}"

    def test_four_bash_scripts_exist(self) -> None:
        """All 4 bash scripts must exist in scripts/ directory."""
        for script in MEMORY_SCRIPTS:
            path = SCRIPTS_DIR / script
            assert path.exists(), f"scripts/{script} not found"


# --- Idempotency ---


class TestIdempotency:
    """T19.6 Scripts are safe to run multiple times."""

    def test_trim_hot_idempotent(self) -> None:
        """trim-hot.sh must be safe to run on already-trimmed files."""
        text = load_script("trim-hot.sh")
        # Should check file size or entry count before processing
        has_size_check = "KB" in text or "bytes" in text or "wc" in text or "stat" in text
        has_skip = "skip" in text.lower() or "exit 0" in text or "nothing" in text.lower()
        assert has_size_check or has_skip, (
            "trim-hot.sh must check if work is needed (idempotency)"
        )

    def test_rotate_warm_idempotent(self) -> None:
        """rotate-warm.sh must be safe to run when nothing to rotate."""
        text = load_script("rotate-warm.sh")
        has_check = "14" in text and ("day" in text.lower() or "cutoff" in text.lower())
        assert has_check, "rotate-warm.sh must check 14-day cutoff"
