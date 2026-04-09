"""T14: Biome linter/formatter configuration validation.

Tests:
- biome.json exists and is valid JSON
- Required linter rules are configured correctly
- Formatter settings match project conventions
- Security and correctness rules are strict
- No forbidden patterns allowed through config
- TypeScript strict mode rules enforced
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Biome config lives in platform-edgelab frontend
BIOME_CONFIG_PATH = Path(
    "/home/openclaw/.openclaw/workspace/projects/"
    "platform-edgelab/frontend/biome.json"
)


@pytest.fixture
def biome_config() -> dict:
    """Load biome.json configuration."""
    assert BIOME_CONFIG_PATH.is_file(), f"biome.json not found: {BIOME_CONFIG_PATH}"
    return json.loads(BIOME_CONFIG_PATH.read_text())


class TestBiomeFileValidity:
    """T14.1: biome.json is valid and well-formed."""

    def test_biome_json_exists(self) -> None:
        """biome.json exists at expected path."""
        assert BIOME_CONFIG_PATH.is_file()

    def test_biome_json_valid(self) -> None:
        """biome.json is valid JSON."""
        text = BIOME_CONFIG_PATH.read_text()
        config = json.loads(text)
        assert isinstance(config, dict)

    def test_has_schema(self, biome_config: dict) -> None:
        """biome.json has $schema field for IDE support."""
        assert "$schema" in biome_config
        assert "biomejs.dev" in biome_config["$schema"]

    def test_schema_version_matches(self, biome_config: dict) -> None:
        """Schema version is 2.x (current major)."""
        schema = biome_config["$schema"]
        assert "/2." in schema, f"Expected Biome 2.x schema, got: {schema}"


class TestBiomeFormatter:
    """T14.2: Formatter settings match project conventions."""

    def test_formatter_enabled(self, biome_config: dict) -> None:
        """Formatter is enabled."""
        assert biome_config.get("formatter", {}).get("enabled") is True

    def test_line_width_100(self, biome_config: dict) -> None:
        """Line width = 100 (project convention)."""
        width = biome_config.get("formatter", {}).get("lineWidth")
        assert width == 100, f"Expected lineWidth=100, got {width}"

    def test_indent_style(self, biome_config: dict) -> None:
        """Indent style is configured."""
        style = biome_config.get("formatter", {}).get("indentStyle")
        assert style in ("tab", "space"), f"Unexpected indentStyle: {style}"

    def test_indent_width(self, biome_config: dict) -> None:
        """Indent width is 2."""
        width = biome_config.get("formatter", {}).get("indentWidth")
        assert width == 2, f"Expected indentWidth=2, got {width}"


class TestBiomeLinter:
    """T14.3: Linter rules enforce project standards."""

    def test_linter_enabled(self, biome_config: dict) -> None:
        """Linter is enabled."""
        assert biome_config.get("linter", {}).get("enabled") is True

    def test_recommended_rules(self, biome_config: dict) -> None:
        """Recommended rules are enabled."""
        rules = biome_config.get("linter", {}).get("rules", {})
        assert rules.get("recommended") is True

    def test_no_explicit_any_is_error(self, biome_config: dict) -> None:
        """noExplicitAny = error (TypeScript strict, no 'any')."""
        rules = biome_config.get("linter", {}).get("rules", {})
        suspicious = rules.get("suspicious", {})
        assert suspicious.get("noExplicitAny") == "error", (
            "noExplicitAny must be 'error' -- any in TypeScript is forbidden"
        )

    def test_use_const_is_error(self, biome_config: dict) -> None:
        """useConst = error (no var/let when const works)."""
        rules = biome_config.get("linter", {}).get("rules", {})
        style = rules.get("style", {})
        assert style.get("useConst") == "error"

    def test_no_unused_imports_is_error(self, biome_config: dict) -> None:
        """noUnusedImports = error (dead code cleanup)."""
        rules = biome_config.get("linter", {}).get("rules", {})
        correctness = rules.get("correctness", {})
        assert correctness.get("noUnusedImports") == "error"

    def test_no_unused_variables_is_error(self, biome_config: dict) -> None:
        """noUnusedVariables = error (dead code cleanup)."""
        rules = biome_config.get("linter", {}).get("rules", {})
        correctness = rules.get("correctness", {})
        assert correctness.get("noUnusedVariables") == "error"

    def test_security_rules_recommended(self, biome_config: dict) -> None:
        """Security rules are enabled."""
        rules = biome_config.get("linter", {}).get("rules", {})
        security = rules.get("security", {})
        assert security.get("recommended") is True

    def test_a11y_rules_recommended(self, biome_config: dict) -> None:
        """Accessibility rules are enabled."""
        rules = biome_config.get("linter", {}).get("rules", {})
        a11y = rules.get("a11y", {})
        assert a11y.get("recommended") is True


class TestBiomeJavaScript:
    """T14.4: JavaScript/TypeScript specific settings."""

    def test_js_formatter_exists(self, biome_config: dict) -> None:
        """JavaScript formatter section exists."""
        assert "javascript" in biome_config
        assert "formatter" in biome_config["javascript"]

    def test_quote_style(self, biome_config: dict) -> None:
        """Quote style is double quotes."""
        js_fmt = biome_config.get("javascript", {}).get("formatter", {})
        assert js_fmt.get("quoteStyle") == "double"

    def test_semicolons(self, biome_config: dict) -> None:
        """Semicolons = asNeeded (not always)."""
        js_fmt = biome_config.get("javascript", {}).get("formatter", {})
        assert js_fmt.get("semicolons") == "asNeeded"


class TestBiomeVCS:
    """T14.5: VCS integration."""

    def test_vcs_enabled(self, biome_config: dict) -> None:
        """VCS integration is enabled."""
        vcs = biome_config.get("vcs", {})
        assert vcs.get("enabled") is True

    def test_vcs_uses_git(self, biome_config: dict) -> None:
        """VCS client is git."""
        vcs = biome_config.get("vcs", {})
        assert vcs.get("clientKind") == "git"

    def test_uses_ignore_file(self, biome_config: dict) -> None:
        """Respects .gitignore."""
        vcs = biome_config.get("vcs", {})
        assert vcs.get("useIgnoreFile") is True


class TestBiomeFileIncludes:
    """T14.6: File includes cover all project directories."""

    REQUIRED_INCLUDES = ["app/**", "components/**", "lib/**"]

    def test_files_section_exists(self, biome_config: dict) -> None:
        """files section with includes exists."""
        assert "files" in biome_config
        assert "includes" in biome_config["files"]

    @pytest.mark.parametrize("pattern", REQUIRED_INCLUDES)
    def test_required_include_present(
        self, biome_config: dict, pattern: str
    ) -> None:
        """Required directory pattern is in includes."""
        includes = biome_config.get("files", {}).get("includes", [])
        assert pattern in includes, f"Missing include pattern: {pattern}"

    def test_ts_files_included(self, biome_config: dict) -> None:
        """TypeScript files are included."""
        includes = biome_config.get("files", {}).get("includes", [])
        has_ts = any("*.ts" in i for i in includes)
        assert has_ts, "*.ts not in includes"

    def test_tsx_files_included(self, biome_config: dict) -> None:
        """TSX files are included."""
        includes = biome_config.get("files", {}).get("includes", [])
        has_tsx = any("*.tsx" in i for i in includes)
        assert has_tsx, "*.tsx not in includes"


class TestBiomeAssist:
    """T14.7: Assist (auto-actions) configuration."""

    def test_assist_enabled(self, biome_config: dict) -> None:
        """Assist is enabled."""
        assert biome_config.get("assist", {}).get("enabled") is True

    def test_organize_imports(self, biome_config: dict) -> None:
        """Auto organize imports is on."""
        actions = biome_config.get("assist", {}).get("actions", {})
        source = actions.get("source", {})
        assert source.get("organizeImports") == "on"
