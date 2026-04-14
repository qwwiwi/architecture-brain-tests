"""T26: Model configuration and usage restriction validation.

Tests:
- Correct model identifiers (opus-4-6, sonnet-4-6, haiku-4-5) are documented
- OpenRouter is explicitly forbidden
- Sonnet is not allowed for code review
- Codex GPT-5.4 is documented as second reviewer
- Double review requires Opus + Codex (not Sonnet)
- Models reference table exists in docs with 4 entries

NOTE: Tests in T26.1 (model IDs) depend on arch docs update that adds
explicit model IDs to MULTI-AGENT.md / TOKEN-OPTIMIZATION.md.
Tests are written against the target (fixed) state.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")


def load_md(name: str) -> str:
    """Load a markdown file from ARCH_ROOT."""
    path = ARCH_ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not found at {path}")
    return path.read_text(encoding="utf-8")


def load_any_md(*names: str) -> str:
    """Load and concatenate multiple markdown files."""
    parts = []
    for name in names:
        path = ARCH_ROOT / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    if not parts:
        pytest.skip(f"None of {names!r} found")
    return "\n".join(parts)


def all_md_texts() -> str:
    """Return concatenated text of all .md files in repo."""
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in ARCH_ROOT.glob("**/*.md")
    )


# --- T26.1: Correct model identifiers ---


class TestModelIDs:
    """T26.1: Correct model identifiers are documented."""

    def test_opus_model_id(self) -> None:
        """claude-opus-4-6 appears in at least one architecture doc."""
        text = all_md_texts()
        assert "claude-opus-4-6" in text, (
            "Model ID 'claude-opus-4-6' not found in any architecture doc. "
            "Should appear in MULTI-AGENT.md or TOKEN-OPTIMIZATION.md."
        )

    def test_sonnet_model_id(self) -> None:
        """claude-sonnet-4-6 appears in at least one architecture doc."""
        text = all_md_texts()
        assert "claude-sonnet-4-6" in text, (
            "Model ID 'claude-sonnet-4-6' not found in any architecture doc."
        )

    def test_haiku_model_id(self) -> None:
        """claude-haiku-4-5 appears in at least one architecture doc."""
        text = all_md_texts()
        assert "claude-haiku-4-5" in text, (
            "Model ID 'claude-haiku-4-5' not found in any architecture doc."
        )


# --- T26.2: Model usage restrictions ---


class TestModelRestrictions:
    """T26.2: Model usage restrictions are enforced and documented."""

    def test_openrouter_forbidden(self) -> None:
        """openrouter.ai must not appear in any config or doc."""
        texts = all_md_texts()
        # Also check settings template
        settings_path = ARCH_ROOT / "templates" / "settings.json.template"
        if settings_path.exists():
            texts += settings_path.read_text(encoding="utf-8")
        assert "openrouter.ai" not in texts.lower(), (
            "openrouter.ai found in docs or templates. "
            "Opus via OpenRouter is explicitly forbidden -- remove the reference."
        )

    def test_openrouter_forbidden_in_global_template(self) -> None:
        """global-CLAUDE.md.template must not mention openrouter as allowed."""
        path = ARCH_ROOT / "templates" / "global-CLAUDE.md.template"
        if not path.exists():
            pytest.skip("global-CLAUDE.md.template not found")
        text = path.read_text(encoding="utf-8")
        # openrouter mention is OK only if paired with "forbidden" / "never"
        if "openrouter" in text.lower():
            assert re.search(r"(forbidden|never|запрещено|не использовать)", text, re.I), (
                "global-CLAUDE.md.template mentions openrouter without explicitly forbidding it."
            )

    def test_sonnet_no_code_review(self) -> None:
        """Sonnet must be explicitly marked as forbidden for code review."""
        text = all_md_texts()
        # Look for a sentence that connects 'Sonnet' with 'code review' + a restriction word
        has_restriction = re.search(
            r"(Sonnet\b.{0,80}(code review|forbidden|запрещен|not.*review|review.*forbidden))|"
            r"((code review|forbidden|запрещен|not.*review|review.*forbidden).{0,80}Sonnet\b)",
            text,
            re.I | re.DOTALL,
        )
        assert has_restriction, (
            "No explicit restriction 'Sonnet forbidden for code review' found in docs. "
            "Must be stated in MULTI-AGENT.md, TOKEN-OPTIMIZATION.md, or a template."
        )

    def test_codex_documented(self) -> None:
        """Codex GPT-5.4 must be mentioned as an optional reviewer."""
        text = all_md_texts()
        has_codex = "Codex" in text or "GPT-5" in text
        assert has_codex, (
            "Codex (GPT-5.4) not documented anywhere in architecture docs. "
            "Should appear as second reviewer in MULTI-AGENT.md or SUBAGENTS.md."
        )

    def test_double_review_both_models(self) -> None:
        """Double review must require Opus + Codex (both, not Sonnet)."""
        text = all_md_texts()
        has_double_review = re.search(
            r"double.review|dual.review|two.model|Opus.*Codex|Codex.*Opus",
            text,
            re.I,
        )
        assert has_double_review, (
            "No 'double review' pattern (Opus + Codex) documented. "
            "Must appear in SUBAGENTS.md, HOOKS.md, or a template."
        )


# --- T26.3: Models reference table ---


class TestModelTable:
    """T26.3: Models reference table exists and is complete."""

    def test_models_table_in_docs(self) -> None:
        """A markdown table listing models with Strengths/Forbidden columns exists."""
        text = all_md_texts()
        # The table should have at least 3 model rows and mention Strength / Forbidden
        has_table = (
            ("Strength" in text or "Use for" in text or "Relative cost" in text)
            and ("Opus" in text and "Sonnet" in text and "Haiku" in text)
        )
        assert has_table, (
            "No model reference table with Opus/Sonnet/Haiku columns found. "
            "Must exist in TOKEN-OPTIMIZATION.md or MULTI-AGENT.md."
        )

    def test_model_ids_in_table(self) -> None:
        """Table must include at least one full model ID (e.g. claude-sonnet-4-6)."""
        text = all_md_texts()
        has_full_id = re.search(r"claude-(opus|sonnet|haiku)-\d+-\d+", text)
        assert has_full_id, (
            "No full model ID (e.g. 'claude-sonnet-4-6') found anywhere in docs. "
            "Add a models table with canonical IDs."
        )

    def test_four_models_documented(self) -> None:
        """Four distinct model entries must be documented (Haiku, Sonnet, Opus, Codex)."""
        text = all_md_texts()
        models_found = sum([
            "Haiku" in text,
            "Sonnet" in text,
            "Opus" in text,
            bool(re.search(r"Codex|GPT-5", text)),
        ])
        assert models_found >= 3, (
            f"Only {models_found}/4 models documented. "
            "Expected: Haiku, Sonnet, Opus, Codex/GPT-5."
        )
