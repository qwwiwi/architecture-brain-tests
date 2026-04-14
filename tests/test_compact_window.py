"""T27: Context window compaction and COMPACT_WINDOW validation.

Tests:
- CLAUDE_CODE_AUTO_COMPACT_WINDOW is documented in TOKEN-OPTIMIZATION.md
- Value 400000 is documented and explained
- COMPACT_WINDOW appears in settings.json.template env block
- gateway.py uses env.setdefault to inject it
- setdefault allows per-agent override via config env block
- Opus context window is documented as 1M (not 200K)
- "200K for Opus" must NOT appear in docs (it's wrong for Opus 4.6)
- HOT memory window uses correct time unit (24h or 72h, consistently)

NOTE: tests test_opus_context_1m and test_no_200k_for_opus depend on
fixing "200K for Opus" typo in TOKEN-OPTIMIZATION.md (line 67).
The gateway tests depend on gateway.py having setdefault already applied
(confirmed present in jarvis-telegram-gateway/gateway.py as of 2026-04-14).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ARCH_ROOT = Path("/tmp/public-architecture-claude-code")
GATEWAY_REPO = Path(__file__).parent.parent.parent / "jarvis-telegram-gateway"


def load_md(name: str) -> str:
    """Load a markdown file from ARCH_ROOT."""
    path = ARCH_ROOT / name
    if not path.exists():
        pytest.skip(f"{name} not found at {path}")
    return path.read_text(encoding="utf-8")


def load_settings_template() -> str:
    """Load settings.json.template raw text."""
    path = ARCH_ROOT / "templates" / "settings.json.template"
    if not path.exists():
        pytest.skip("settings.json.template not found")
    return path.read_text(encoding="utf-8")


def load_gateway_py() -> str:
    """Load gateway.py from jarvis-telegram-gateway repo."""
    path = GATEWAY_REPO / "gateway.py"
    if not path.exists():
        pytest.skip(f"gateway.py not found at {path}")
    return path.read_text(encoding="utf-8")


# --- T27.1: COMPACT_WINDOW documentation ---


class TestCompactWindowDocs:
    """T27.1: COMPACT_WINDOW is documented in TOKEN-OPTIMIZATION.md."""

    def test_compact_window_documented(self) -> None:
        """CLAUDE_CODE_AUTO_COMPACT_WINDOW must be in TOKEN-OPTIMIZATION.md."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        assert "CLAUDE_CODE_AUTO_COMPACT_WINDOW" in text, (
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW not found in TOKEN-OPTIMIZATION.md. "
            "Boris Cherny (Anthropic) recommendation: set to 400000 for deeper thinking. "
            "Must be documented alongside CLAUDE_AUTOCOMPACT_PCT_OVERRIDE."
        )

    def test_compact_window_value_400k(self) -> None:
        """Value 400000 must be documented as the recommended value."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        has_value = "400000" in text or "400K" in text or "400k" in text
        assert has_value, (
            "Value 400000 not found in TOKEN-OPTIMIZATION.md. "
            "Must document: CLAUDE_CODE_AUTO_COMPACT_WINDOW=400000 "
            "(compact at 400K instead of default 800K for fresher context)."
        )

    def test_compact_window_in_settings_template(self) -> None:
        """CLAUDE_CODE_AUTO_COMPACT_WINDOW must appear in settings.json.template."""
        text = load_settings_template()
        assert "CLAUDE_CODE_AUTO_COMPACT_WINDOW" in text, (
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW missing from settings.json.template env block. "
            "Must be included as a recommended env variable."
        )

    def test_compact_window_explanation(self) -> None:
        """TOKEN-OPTIMIZATION.md must explain WHY to set COMPACT_WINDOW to 400K."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        # After mentioning COMPACT_WINDOW, there should be a rationale
        # Either "thinking", "reasoning", "fresh", "context", "earlier"
        if "CLAUDE_CODE_AUTO_COMPACT_WINDOW" not in text:
            pytest.skip("COMPACT_WINDOW not documented yet")
        idx = text.index("CLAUDE_CODE_AUTO_COMPACT_WINDOW")
        surrounding = text[max(0, idx - 200):idx + 400]
        has_rationale = re.search(
            r"(thinking|reasoning|fresh|context|earlier|deeper|quality)",
            surrounding,
            re.I,
        )
        assert has_rationale, (
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW mentioned but no rationale found nearby. "
            "Must explain: compact at 400K = fresher context = deeper reasoning."
        )


# --- T27.2: COMPACT_WINDOW in gateway ---


class TestCompactWindowGateway:
    """T27.2: Gateway correctly injects COMPACT_WINDOW into agent env."""

    def test_compact_window_in_gateway(self) -> None:
        """gateway.py must use env.setdefault for COMPACT_WINDOW."""
        text = load_gateway_py()
        assert 'env.setdefault("CLAUDE_CODE_AUTO_COMPACT_WINDOW"' in text, (
            "gateway.py missing: env.setdefault(\"CLAUDE_CODE_AUTO_COMPACT_WINDOW\", \"400000\"). "
            "Must inject default before starting Claude Code subprocess."
        )

    def test_compact_window_value_in_gateway(self) -> None:
        """gateway.py must use value '400000' for COMPACT_WINDOW."""
        text = load_gateway_py()
        # Check for the pattern: setdefault("CLAUDE_CODE_AUTO_COMPACT_WINDOW", "400000")
        has_correct_value = re.search(
            r'env\.setdefault\("CLAUDE_CODE_AUTO_COMPACT_WINDOW",\s*"400000"\)',
            text,
        )
        assert has_correct_value, (
            "gateway.py has COMPACT_WINDOW but value is not 400000. "
            "Expected: env.setdefault(\"CLAUDE_CODE_AUTO_COMPACT_WINDOW\", \"400000\")"
        )

    def test_compact_window_overridable(self) -> None:
        """setdefault must be used (not direct assignment) to allow per-agent override."""
        text = load_gateway_py()
        # setdefault means agent cfg env block can override it
        # Hard assignment would look like: env["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = "400000"
        has_setdefault = 'env.setdefault("CLAUDE_CODE_AUTO_COMPACT_WINDOW"' in text
        has_hard_assign = bool(re.search(
            r'env\["CLAUDE_CODE_AUTO_COMPACT_WINDOW"\]\s*=\s*"400000"',
            text,
        ))
        assert has_setdefault, (
            "COMPACT_WINDOW must use env.setdefault (not direct assignment) "
            "so agents can override via config 'env' block."
        )
        assert not has_hard_assign, (
            "Found hard assignment env[\"CLAUDE_CODE_AUTO_COMPACT_WINDOW\"] = \"400000\". "
            "Use setdefault instead so per-agent config can override."
        )

    def test_compact_window_before_agent_env_loop(self) -> None:
        """setdefault must be applied BEFORE the per-agent env loop."""
        text = load_gateway_py()
        compact_idx = text.find('env.setdefault("CLAUDE_CODE_AUTO_COMPACT_WINDOW"')
        env_loop_idx = text.find('for k, v in cfg')
        if compact_idx == -1:
            pytest.skip("COMPACT_WINDOW setdefault not found")
        if env_loop_idx == -1:
            pytest.skip("Agent env loop not found")
        assert compact_idx < env_loop_idx, (
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW setdefault must appear BEFORE "
            "the 'for k, v in cfg' env loop so agents can override it."
        )


# --- T27.3: Context window size accuracy ---


class TestContextWindowSize:
    """T27.3: Context window size is documented accurately for Opus 4.6."""

    def test_opus_context_1m(self) -> None:
        """TOKEN-OPTIMIZATION.md must document Opus context as 1M, not 200K.

        Opus 4.6 has a 1,000,000-token context window.
        The incorrect '200K for Opus' was documented before Opus 4.6.
        """
        text = load_md("TOKEN-OPTIMIZATION.md")
        has_1m = bool(re.search(r"1[,.]?000[,.]?000|1M\b|one.million", text, re.I))
        assert has_1m, (
            "TOKEN-OPTIMIZATION.md does not mention Opus 1M context window. "
            "Must document that Opus 4.6 has 1,000,000-token context."
        )

    def test_no_200k_for_opus(self) -> None:
        """TOKEN-OPTIMIZATION.md must NOT claim Opus context is 200K.

        Opus 4.6 context = 1M tokens. '200K for Opus' is factually wrong.
        """
        text = load_md("TOKEN-OPTIMIZATION.md")
        # Look for "200K" or "200,000" paired with "Opus"
        has_wrong_claim = bool(re.search(
            r"200[Kk]\b.{0,30}Opus|Opus.{0,30}200[Kk]\b",
            text,
            re.I,
        ))
        assert not has_wrong_claim, (
            "TOKEN-OPTIMIZATION.md still says '200K for Opus'. "
            "Opus 4.6 has 1M context -- fix this inaccuracy."
        )

    def test_hot_memory_window_consistent(self) -> None:
        """recent.md.template HOT window (24h or 72h) must match MEMORY.md docs."""
        template_path = ARCH_ROOT / "templates" / "recent.md.template"
        if not template_path.exists():
            pytest.skip("recent.md.template not found")
        template_text = template_path.read_text(encoding="utf-8")

        # Extract the time window from template header
        match = re.search(r"(\d+)h\s+rolling", template_text, re.I)
        if not match:
            pytest.skip("No 'Nh rolling' pattern found in recent.md.template")
        template_hours = int(match.group(1))

        # Now check MEMORY.md is consistent
        memory_text = load_md("MEMORY.md")
        memory_match = re.search(r"(\d+)h\b.{0,50}hot|hot.{0,50}\b(\d+)h\b", memory_text, re.I)
        if not memory_match:
            return  # MEMORY.md doesn't constrain it, template is authoritative
        memory_hours = int(memory_match.group(1) or memory_match.group(2))

        assert template_hours == memory_hours, (
            f"Time window mismatch: recent.md.template says {template_hours}h "
            f"but MEMORY.md says {memory_hours}h. Must be consistent."
        )

    def test_autocompact_pct_documented(self) -> None:
        """CLAUDE_AUTOCOMPACT_PCT_OVERRIDE must also appear in TOKEN-OPTIMIZATION.md."""
        text = load_md("TOKEN-OPTIMIZATION.md")
        assert "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE" in text, (
            "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE missing from TOKEN-OPTIMIZATION.md. "
            "Must document both COMPACT_WINDOW and AUTOCOMPACT_PCT together."
        )
