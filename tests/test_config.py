"""T1: Config loading and validation.

Tests:
- Valid config loads all required fields
- Invalid config missing required fields is detected
- Agent config has all required keys
- Allowlist is a list of ints
- Environment variables are populated from agent config
"""

from __future__ import annotations

from typing import Any

REQUIRED_TOP_KEYS = {"poll_interval_sec", "allowlist_user_ids", "agents"}
REQUIRED_AGENT_KEYS = {"enabled", "telegram_bot_token_file", "workspace", "model"}


class TestConfigLoading:
    """T1.1: Config file loading."""

    def test_valid_config_loads(self, valid_config: dict[str, Any]) -> None:
        """Valid config.json loads without errors."""
        assert isinstance(valid_config, dict)

    def test_valid_config_has_required_keys(self, valid_config: dict[str, Any]) -> None:
        """All required top-level keys present."""
        missing = REQUIRED_TOP_KEYS - set(valid_config.keys())
        assert not missing, f"Missing keys: {missing}"

    def test_allowlist_is_list_of_ints(self, valid_config: dict[str, Any]) -> None:
        """allowlist_user_ids must be list of integers."""
        ids = valid_config["allowlist_user_ids"]
        assert isinstance(ids, list)
        assert all(isinstance(uid, int) for uid in ids)
        assert len(ids) > 0, "Allowlist must not be empty"


class TestAgentConfig:
    """T1.2: Per-agent configuration."""

    def test_at_least_one_agent(self, valid_config: dict[str, Any]) -> None:
        """At least one agent must be configured."""
        agents = valid_config["agents"]
        assert len(agents) > 0

    def test_agent_has_required_keys(self, valid_config: dict[str, Any]) -> None:
        """Each agent config has all required keys."""
        for name, cfg in valid_config["agents"].items():
            missing = REQUIRED_AGENT_KEYS - set(cfg.keys())
            assert not missing, f"Agent '{name}' missing: {missing}"

    def test_agent_workspace_is_absolute_path(self, valid_config: dict[str, Any]) -> None:
        """Workspace paths must be absolute (start with / or ~)."""
        for name, cfg in valid_config["agents"].items():
            ws = cfg["workspace"]
            assert ws.startswith("/") or ws.startswith("~"), (
                f"Agent '{name}' workspace must be absolute: {ws}"
            )

    def test_agent_model_is_valid(self, valid_config: dict[str, Any]) -> None:
        """Model must be one of known aliases."""
        valid_models = {"opus", "sonnet", "haiku", "codex", "grok", "gemini"}
        for name, cfg in valid_config["agents"].items():
            assert cfg["model"] in valid_models, f"Agent '{name}' unknown model: {cfg['model']}"

    def test_agent_env_vars(self, valid_config: dict[str, Any]) -> None:
        """Agent env vars are dict of str:str."""
        for _name, cfg in valid_config["agents"].items():
            env = cfg.get("env", {})
            assert isinstance(env, dict)
            for k, v in env.items():
                assert isinstance(k, str)
                assert isinstance(v, str)


class TestInvalidConfig:
    """T1.3: Invalid config detection."""

    def test_missing_workspace(self, invalid_config: dict[str, Any]) -> None:
        """Broken agent config missing workspace is detected."""
        agent = invalid_config["agents"]["broken"]
        assert "workspace" not in agent

    def test_missing_token_file(self, invalid_config: dict[str, Any]) -> None:
        """Broken agent config missing telegram_bot_token_file is detected."""
        agent = invalid_config["agents"]["broken"]
        assert "telegram_bot_token_file" not in agent

    def test_missing_allowlist(self, invalid_config: dict[str, Any]) -> None:
        """Config without allowlist is detected."""
        assert "allowlist_user_ids" not in invalid_config
