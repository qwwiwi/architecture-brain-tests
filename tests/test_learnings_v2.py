"""T28: Learnings v2 Engine -- self-improvement pipeline validation.

Tests:
- learnings-engine.mjs is documented in LEARNINGS.md
- All engine commands (capture, score, promote, lint) are present
- episodes.jsonl format is described
- Promotion score threshold (>0.8) and frequency (3+) are documented
- Reliability pyramid with 5 levels is documented
- correction-detector.sh triggers automatic learnings capture
- Weekly lint schedule is documented

T28 complements T23 (test_learnings.py) which tests the v1 Learnings system
(git-as-database, table format, access zones). T28 specifically tests the
v2 engine additions: scoring, promotion pipeline, automatic hooks.

NOTE: T28.1 and T28.2 tests depend on LEARNINGS.md being updated to document
the v2 engine (learnings-engine.mjs, episodes.jsonl, score/promote commands).
These were implemented in Orgrimmar 2026-04-11 but may not yet be in the
public architecture docs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")
HOOKS_MD = ARCH_ROOT / "HOOKS.md"
LEARNINGS_MD = ARCH_ROOT / "LEARNINGS.md"


def load_md(name: str) -> str:
    """Load a markdown file from ARCH_ROOT."""
    path = ARCH_ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not found at {path}")
    return path.read_text(encoding="utf-8")


def all_md_texts() -> str:
    """Return concatenated text of all .md files in repo."""
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in ARCH_ROOT.glob("**/*.md")
    )


# --- T28.1: learnings-engine.mjs documentation ---


class TestLearningsEngine:
    """T28.1: learnings-engine.mjs is documented with commands and format."""

    def test_engine_documented(self) -> None:
        """learnings-engine.mjs must be mentioned somewhere in architecture docs."""
        text = all_md_texts()
        assert "learnings-engine" in text or "learnings-engine.mjs" in text, (
            "learnings-engine.mjs not documented in architecture docs. "
            "Must appear in LEARNINGS.md (v2 engine section) or HOOKS.md."
        )

    def test_engine_capture_command(self) -> None:
        """'capture' command must be documented for learnings-engine."""
        text = load_md("LEARNINGS.md")
        # Looking for: capture command (v2 engine CLI)
        has_capture = bool(re.search(r"\bcapture\b", text, re.I))
        assert has_capture, (
            "'capture' command not found in LEARNINGS.md. "
            "learnings-engine.mjs capture: record a new learning from correction."
        )

    def test_engine_score_command(self) -> None:
        """'score' command or scoring concept must be documented."""
        text = load_md("LEARNINGS.md")
        has_score = bool(re.search(r"\bscore\b|\bscoring\b", text, re.I))
        assert has_score, (
            "'score' command not found in LEARNINGS.md. "
            "learnings-engine.mjs score: calculate effectiveness of a learning."
        )

    def test_engine_promote_command(self) -> None:
        """'promote' command must be documented."""
        text = load_md("LEARNINGS.md")
        has_promote = bool(re.search(r"\bpromote\b|\bpromotion\b", text, re.I))
        assert has_promote, (
            "'promote' command not found in LEARNINGS.md. "
            "learnings-engine.mjs promote: move learning up the reliability pyramid."
        )

    def test_engine_lint_command(self) -> None:
        """'lint' command or lint schedule must be documented."""
        text = load_md("LEARNINGS.md")
        has_lint = bool(re.search(r"\blint\b", text, re.I))
        assert has_lint, (
            "'lint' command not found in LEARNINGS.md. "
            "learnings-engine.mjs lint: weekly check that rules are still working."
        )

    def test_episodes_jsonl_documented(self) -> None:
        """episodes.jsonl format must be described in LEARNINGS.md."""
        text = load_md("LEARNINGS.md")
        has_episodes = "episodes.jsonl" in text or "episodes" in text.lower()
        assert has_episodes, (
            "episodes.jsonl not documented in LEARNINGS.md. "
            "Must describe: episodes.jsonl stores scored top-5 learnings, "
            "injected at session start by SessionStart hook."
        )


# --- T28.2: Promotion pipeline ---


class TestPromotionPyramid:
    """T28.2: Reliability pyramid and promotion rules are documented."""

    def test_promotion_score_threshold(self) -> None:
        """Score > 0.8 triggers promotion must be documented."""
        text = load_md("LEARNINGS.md")
        has_threshold = bool(re.search(
            r"0\.8\b|score.{0,40}0\.8|0\.8.{0,40}score|score.{0,40}(thresh|trigger|promot)",
            text,
            re.I,
        ))
        assert has_threshold, (
            "Promotion score threshold (0.8) not found in LEARNINGS.md. "
            "Must document: score > 0.8 triggers promotion to next pyramid level."
        )

    def test_promotion_frequency(self) -> None:
        """Frequency 3+ triggers promotion must be documented."""
        text = load_md("LEARNINGS.md")
        has_freq = bool(re.search(
            r"freq.{0,40}3|3.{0,40}freq|freq.{0,40}(trigger|promot)|repeat.{0,10}3",
            text,
            re.I,
        ))
        assert has_freq, (
            "Promotion frequency threshold (3+) not found in LEARNINGS.md. "
            "Must document: frequency 3+ triggers promotion (same as Repeats > 3)."
        )

    def test_pyramid_exists(self) -> None:
        """Reliability pyramid must be documented somewhere."""
        text = load_md("LEARNINGS.md")
        has_pyramid = bool(re.search(r"pyramid|reliability.{0,20}level|tier", text, re.I))
        assert has_pyramid, (
            "Reliability pyramid not found in LEARNINGS.md. "
            "Must document the 5-level pyramid from weak (session memory) "
            "to strong (scripts/hooks)."
        )

    def test_pyramid_session_memory_level(self) -> None:
        """Session memory (level 1 = weakest) must appear in pyramid."""
        text = load_md("LEARNINGS.md")
        has_session = bool(re.search(r"session.memory|memory.session", text, re.I))
        assert has_session, (
            "Session memory (weakest pyramid level) not in LEARNINGS.md. "
            "Pyramid: session memory → episodes → TOOLS → CLAUDE → hooks/scripts."
        )

    def test_pyramid_hooks_scripts_level(self) -> None:
        """Scripts/hooks (strongest level) must appear in pyramid."""
        text = load_md("LEARNINGS.md")
        pattern = r"(hook|script).{0,30}(strong|level|pyramid|top)"
        has_hooks_scripts = (
            bool(re.search(pattern, text, re.I))
            or ("hook" in text.lower() and "strongest" in text.lower())
        )
        # Looser fallback: both "hook" and "script" appear in a pyramid context
        if not has_hooks_scripts:
            fallback = r"hook.{0,100}script|script.{0,100}hook"
            has_hooks_scripts = bool(re.search(fallback, text, re.I))
        assert has_hooks_scripts, (
            "Hooks/scripts (strongest pyramid level) not found in LEARNINGS.md. "
            "Must document that critical mistakes → promoted to hook/script level."
        )

    def test_pyramid_five_levels(self) -> None:
        """Pyramid must document at least 5 distinct levels."""
        text = load_md("LEARNINGS.md")
        # Count recognized pyramid levels in the doc
        levels = [
            r"session.memory",
            r"episodes\.jsonl|episodes\b",
            r"TOOLS\.md|SKILL\.md",
            r"CLAUDE\.md",
            r"(hook|script).{0,30}(auto|run|enforce)",
        ]
        found = sum(
            1 for lvl in levels if re.search(lvl, text, re.I)
        )
        assert found >= 5, (
            f"Only {found}/5 pyramid levels found in LEARNINGS.md. "
            "Must document all 5: session memory, episodes.jsonl, "
            "TOOLS/SKILL.md, CLAUDE.md, hooks/scripts."
        )


# --- T28.3: Automatic triggers ---


class TestLearningsTriggers:
    """T28.3: Automatic trigger hooks are documented and functional."""

    def test_correction_detector_hook(self) -> None:
        """correction-detector.sh must be documented as a learnings trigger."""
        # Check HOOKS.md or LEARNINGS.md
        hooks_text = ""
        if HOOKS_MD.exists():
            hooks_text = HOOKS_MD.read_text(encoding="utf-8")
        learnings_text = load_md("LEARNINGS.md")
        combined = hooks_text + learnings_text

        has_detector = "correction-detector" in combined
        assert has_detector, (
            "correction-detector.sh not documented in HOOKS.md or LEARNINGS.md. "
            "Must document: UserPromptSubmit hook that detects corrections "
            "and triggers learnings-engine capture."
        )

    def test_weekly_lint(self) -> None:
        """Weekly lint schedule must be documented."""
        text = load_md("LEARNINGS.md")
        has_weekly = bool(re.search(r"weekly|week.{0,20}lint|lint.{0,20}week", text, re.I))
        assert has_weekly, (
            "Weekly lint not documented in LEARNINGS.md. "
            "Must document: weekly lint (launchd/cron) alerts if rules are not working."
        )

    def test_session_start_hook_for_learnings(self) -> None:
        """SessionStart hook that injects top-5 learnings must be documented."""
        hooks_text = ""
        if HOOKS_MD.exists():
            hooks_text = HOOKS_MD.read_text(encoding="utf-8")
        learnings_text = load_md("LEARNINGS.md")
        combined = hooks_text + learnings_text

        has_session_start = bool(re.search(
            r"SessionStart.{0,100}(learn|episode)|"
            r"(learn|episode).{0,100}SessionStart",
            combined,
            re.I,
        ))
        assert has_session_start, (
            "No SessionStart hook for learnings injection found. "
            "Must document: SessionStart injects top-5 scored episodes into context."
        )

    def test_auto_sync_to_repo(self) -> None:
        """Automatic sync of learnings to git repo must be documented."""
        text = load_md("LEARNINGS.md")
        has_sync = bool(re.search(
            r"auto.{0,10}sync|sync.{0,10}auto|auto.{0,10}push|push.{0,20}(learn|repo)",
            text,
            re.I,
        ))
        assert has_sync, (
            "Automatic sync to learnings repo not documented in LEARNINGS.md. "
            "Must document: capture auto-syncs to git repo (qwwiwi/learnings)."
        )

    def test_review_reminder_threshold(self) -> None:
        """review-reminder.sh threshold must be documented."""
        hooks_text = ""
        if HOOKS_MD.exists():
            hooks_text = HOOKS_MD.read_text(encoding="utf-8")
        learnings_text = load_md("LEARNINGS.md")
        combined = hooks_text + learnings_text

        has_reminder = "review-reminder" in combined
        assert has_reminder, (
            "review-reminder.sh not documented in HOOKS.md or LEARNINGS.md. "
            "PostToolUse hook: after N edits, reminds agent to run code-reviewer."
        )
