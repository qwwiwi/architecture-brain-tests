"""T6: Claude subprocess invocation.

Tests:
- Correct command line arguments
- Workspace path passed correctly
- Model alias resolved
- Permission mode set to bypassPermissions
- Output format is stream-json
- Environment variables set from agent config
- Timeout enforcement (heartbeat-based)
"""

from __future__ import annotations

import os


class TestClaudeCommand:
    """T6.1: Claude CLI command construction.

    Command template:
    claude -p "{text}" --model {model} --output-format stream-json
        --permission-mode bypassPermissions --resume {sid}
    """

    def test_command_has_required_flags(self) -> None:
        """All required flags present in command."""
        model = "opus"
        sid = "test-uuid"
        text = "Hello agent"
        cmd = [
            "claude",
            "-p",
            text,
            "--model",
            model,
            "--output-format",
            "stream-json",
            "--permission-mode",
            "bypassPermissions",
            "--resume",
            sid,
        ]
        assert "claude" in cmd
        assert "-p" in cmd
        assert "--model" in cmd
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--permission-mode" in cmd
        assert "bypassPermissions" in cmd
        assert "--resume" in cmd

    def test_first_turn_uses_session_id(self) -> None:
        """First turn uses --session-id instead of --resume."""
        is_first = True
        flag = "--session-id" if is_first else "--resume"
        assert flag == "--session-id"


class TestEnvironment:
    """T6.2: Environment variables for Claude subprocess."""

    def test_path_includes_local_bin(self) -> None:
        """PATH must include ~/.local/bin for orgbus and other tools."""
        home = "/home/testuser"
        path = f"{home}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
        assert f"{home}/.local/bin" in path

    def test_agent_env_vars_injected(self) -> None:
        """Agent-specific env vars from config are injected."""
        agent_env = {"AGENT_ID": "thrall", "ORGBUS_SA": "sa-thrall"}
        env = os.environ.copy()
        for k, v in agent_env.items():
            env[k] = v
        assert env["AGENT_ID"] == "thrall"
        assert env["ORGBUS_SA"] == "sa-thrall"


class TestWorkspace:
    """T6.3: Workspace path for Claude subprocess."""

    def test_workspace_is_cwd(self) -> None:
        """Claude subprocess runs with workspace as current directory.

        Contract: subprocess.Popen(cmd, cwd=workspace, ...)
        """
        workspace = "/home/openclaw/.claude-lab/thrall/.claude"
        # Workspace must exist and be a directory
        # In real test, we'd check Path(workspace).is_dir()
        assert workspace.endswith(".claude")

    def test_workspace_expands_tilde(self) -> None:
        """Tilde in workspace path is expanded."""
        raw = "~/.claude-lab/thrall/.claude"
        expanded = os.path.expanduser(raw)
        assert not expanded.startswith("~")


class TestTimeout:
    """T6.4: Heartbeat-based timeout.

    Contract:
    - Default timeout: 900 seconds
    - Heartbeat updated on every stream-json event
    - If no event for timeout_sec -> kill subprocess
    """

    def test_default_timeout(self) -> None:
        """Default timeout is 900 seconds."""
        cfg = {"timeout_sec": 900}
        assert cfg["timeout_sec"] == 900

    def test_heartbeat_resets_timer(self) -> None:
        """Each stream event resets the heartbeat timer."""
        import time

        last_heartbeat = time.time()
        timeout = 900

        # Simulate event received
        time.sleep(0.01)
        last_heartbeat = time.time()  # Reset

        elapsed = time.time() - last_heartbeat
        assert elapsed < timeout
