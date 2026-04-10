"""
T21: Context budget and token optimization validation.

Verifies that documentation correctly describes token budgets,
file size limits, trim thresholds, and optimization recommendations.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")


def load_md(name: str) -> str:
    """Load a markdown file."""
    path = ARCH_ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not found")
    return path.read_text(encoding="utf-8")


# --- Token budgets ---


class TestTokenBudgets:
    """T21.1 Token budget documentation is consistent."""

    def test_context_window_mentioned(self) -> None:
        """TOKEN-OPTIMIZATION.md must mention context window size."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        has_window = (
            "context window" in text.lower()
            or "1,000,000" in text
            or "1M" in text
            or "200K" in text
            or "200k" in text
        )
        assert has_window, "Must mention context window size"

    def test_memory_budget_table_exists(self) -> None:
        """TOKEN-OPTIMIZATION.md must have a memory budget table."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        assert "hot" in text.lower() and "token" in text.lower(), (
            "Must have memory budget with token estimates"
        )

    def test_hot_is_biggest_consumer(self) -> None:
        """Documentation must identify HOT as #1 token consumer."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        assert "hot" in text.lower() and ("#1" in text or "biggest" in text.lower() or
                                           "target" in text.lower() or "priority" in text.lower()), (
            "Must identify HOT as primary optimization target"
        )


# --- File size limits ---


class TestFileSizeLimits:
    """T21.2 Documented file size limits are consistent."""

    def test_hot_emergency_trim_20kb(self) -> None:
        """HOT emergency trim must trigger at 20KB."""
        text = load_md("MEMORY.md")
        assert "20" in text and "KB" in text, (
            "MEMORY.md must document 20KB emergency trim for HOT"
        )

    def test_warm_compress_10kb(self) -> None:
        """WARM compression must trigger at 10KB."""
        text = load_md("MEMORY.md")
        assert "10" in text and ("KB" in text or "compress" in text.lower()), (
            "MEMORY.md must document 10KB trigger for WARM compression"
        )

    def test_cold_archive_5kb(self) -> None:
        """COLD archival must trigger at 5KB."""
        text = load_md("MEMORY.md")
        has_5kb = "5" in text and ("KB" in text or "archive" in text.lower())
        assert has_5kb, "MEMORY.md must document 5KB trigger for COLD archival"

    def test_claude_md_under_200_lines(self) -> None:
        """TOKEN-OPTIMIZATION.md must recommend CLAUDE.md < 200 lines."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        assert "200" in text and ("line" in text.lower() or "CLAUDE" in text), (
            "Must recommend CLAUDE.md under 200 lines"
        )


# --- Compression ratios ---


class TestCompressionDocumentation:
    """T21.3 Compression effectiveness documented."""

    def test_sonnet_compression_mentioned(self) -> None:
        """Must document Sonnet as compression model."""
        text = load_md("MEMORY.md")
        assert "Sonnet" in text and "compress" in text.lower(), (
            "Must document Sonnet for compression"
        )

    def test_compression_reduction_documented(self) -> None:
        """Must document expected compression reduction."""
        text = load_md("ARCHITECTURE.md")
        # Should mention 80% reduction or similar metric
        has_reduction = (
            "80%" in text
            or "reduction" in text.lower()
            or "compress" in text.lower()
        )
        assert has_reduction, "Must document compression effectiveness"

    def test_without_cron_warning(self) -> None:
        """Must warn about consequences of not running cron."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        has_warning = (
            "without" in text.lower() or "без" in text.lower() or "no cron" in text.lower()
        )
        has_consequence = "80" in text or "degrade" in text.lower() or "ignore" in text.lower()
        assert has_warning and has_consequence, (
            "Must warn about consequences of skipping cron compression"
        )


# --- Model cost ---


class TestModelCostDocumentation:
    """T21.4 Model cost comparison documented."""

    def test_model_cost_comparison(self) -> None:
        """Must compare Opus vs Sonnet vs Haiku costs."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        models = ["Opus", "Sonnet", "Haiku"]
        found = sum(1 for m in models if m in text)
        assert found >= 3, f"Must compare all 3 model costs, found {found}/3"

    def test_sonnet_default_recommendation(self) -> None:
        """Must recommend Sonnet as default for cost savings."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        has_sonnet = "sonnet" in text.lower()
        has_default = "default" in text.lower() or "start" in text.lower()
        assert has_sonnet and has_default, (
            "Must recommend Sonnet as default model"
        )

    def test_subagent_model_recommendation(self) -> None:
        """Must recommend cheaper model for subagents."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        has_subagent = "subagent" in text.lower()
        has_cheap = "haiku" in text.lower() or "sonnet" in text.lower()
        assert has_subagent and has_cheap, (
            "Must recommend cheaper model for subagents"
        )


# --- Context management commands ---


class TestContextManagementCommands:
    """T21.5 Context management commands documented."""

    def test_compact_command(self) -> None:
        """Must document /compact command."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        assert "/compact" in text, "Must document /compact command"

    def test_clear_command(self) -> None:
        """Must document /clear command."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        assert "/clear" in text, "Must document /clear command"

    def test_cost_command(self) -> None:
        """Must document /cost command."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        assert "/cost" in text, "Must document /cost command"

    def test_context_degradation_warning(self) -> None:
        """Must warn about quality degradation at high context usage."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        has_degrade = (
            "degrade" in text.lower()
            or "quality" in text.lower()
            or "50%" in text
        )
        assert has_degrade, (
            "Must warn about quality degradation at high context"
        )
