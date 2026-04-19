"""T30: EdgeLab installer (install.sh) validation.

Tests:
- Bash syntax and safety (set -euo pipefail, shebang)
- Ubuntu version support (22.04, 24.04, 25.04)
- 12-step pipeline completeness
- Groq setup (secrets, /dev/tty, key validation)
- OpenViking setup (pip install, config template, systemd gated on binary)
- Cron setup (3 scripts, crontab marker, log path)
- Security (no hardcoded secrets, chmod 600, no python3 override)
- Gateway config (groq_api_key_file field)
- Systemd service correctness
- Banner mentions all installed components
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

INSTALL_SH = Path("/tmp/edgelab-install/install.sh")


def load_installer() -> str:
    """Load the installer script."""
    if not INSTALL_SH.exists():
        pytest.skip("install.sh not found")
    return INSTALL_SH.read_text(encoding="utf-8")


# --- Basic safety ---


class TestInstallerSafety:
    """T30.1 Bash safety and structure."""

    def test_has_shebang(self) -> None:
        text = load_installer()
        assert text.startswith("#!/usr/bin/env bash"), "Must start with bash shebang"

    def test_has_set_euo_pipefail(self) -> None:
        text = load_installer()
        assert "set -euo pipefail" in text

    def test_version_is_2_0_0(self) -> None:
        text = load_installer()
        assert 'EDGELAB_VERSION="2.0.0"' in text

    def test_total_steps_is_12(self) -> None:
        text = load_installer()
        assert "TOTAL_STEPS=12" in text

    def test_cleanup_trap(self) -> None:
        text = load_installer()
        assert "trap cleanup EXIT" in text


# --- Ubuntu support ---


class TestUbuntuSupport:
    """T30.2 Ubuntu version support."""

    def test_supports_2204(self) -> None:
        text = load_installer()
        assert "22.04" in text

    def test_supports_2404(self) -> None:
        text = load_installer()
        assert "24.04" in text

    def test_supports_2504(self) -> None:
        text = load_installer()
        assert "25.04" in text

    def test_case_statement_includes_all_versions(self) -> None:
        text = load_installer()
        assert "22.04|24.04|25.04" in text


# --- 12-step pipeline ---


class TestPipelineCompleteness:
    """T30.3 All 12 steps present in main()."""

    EXPECTED_FUNCTIONS = [
        "install_system_packages",
        "install_nodejs",
        "install_python",
        "install_claude_code",
        "install_gateway",
        "setup_workspace",
        "install_caddy",
        "configure_security",
        "install_systemd_service",
        "setup_groq",
        "setup_openviking",
        "setup_cron",
    ]

    def test_all_12_functions_defined(self) -> None:
        text = load_installer()
        for func in self.EXPECTED_FUNCTIONS:
            pattern = rf"^{func}\(\)\s*\{{" if func.startswith("install_") or func.startswith("setup_") or func.startswith("configure_") else rf"{func}\(\)"
            assert re.search(rf"^{func}\(\)", text, re.MULTILINE), (
                f"Function {func}() not defined"
            )

    def test_all_12_functions_called_in_main(self) -> None:
        text = load_installer()
        main_match = re.search(r"^main\(\)\s*\{(.*?)^\}", text, re.MULTILINE | re.DOTALL)
        assert main_match, "main() function not found"
        main_body = main_match.group(1)
        for func in self.EXPECTED_FUNCTIONS:
            assert func in main_body, f"{func} not called in main()"

    def test_step_numbers_sequential(self) -> None:
        """Step numbers in step() calls should be 1-12."""
        text = load_installer()
        step_calls = re.findall(r'step\s+(\d+)\s+"', text)
        step_nums = [int(s) for s in step_calls]
        assert sorted(step_nums) == list(range(1, 13)), (
            f"Expected steps 1-12, got {sorted(step_nums)}"
        )


# --- Groq setup ---


class TestGroqSetup:
    """T30.4 Groq voice transcription setup."""

    def test_reads_from_tty(self) -> None:
        """Must use /dev/tty for curl|bash compatibility."""
        text = load_installer()
        assert "/dev/tty" in text, "Groq key read must use /dev/tty"

    def test_uses_silent_read(self) -> None:
        """API key input must be silent (read -s)."""
        text = load_installer()
        groq_section = text[text.find("setup_groq"):text.find("setup_openviking")]
        assert "read -rsp" in groq_section, "Groq key read must use -s (silent)"

    def test_key_file_chmod_600(self) -> None:
        text = load_installer()
        groq_section = text[text.find("setup_groq"):text.find("setup_openviking")]
        assert "chmod 600" in groq_section, "Groq key file must be chmod 600"

    def test_validates_key_format(self) -> None:
        text = load_installer()
        assert "gsk_" in text, "Must check for gsk_ prefix"

    def test_key_not_in_curl_argv(self) -> None:
        """API key must not be passed via curl command line args."""
        text = load_installer()
        groq_section = text[text.find("setup_groq"):text.find("setup_openviking")]
        # Should use -H @file, not -H "Authorization: Bearer ${groq_key}"
        assert "-H @" in groq_section or "--header @" in groq_section, (
            "Groq key must be passed via file, not curl argv"
        )

    def test_skip_if_no_key(self) -> None:
        text = load_installer()
        groq_section = text[text.find("setup_groq"):text.find("setup_openviking")]
        assert "return 0" in groq_section, "Must allow skipping Groq setup"

    def test_groq_api_url_constant(self) -> None:
        text = load_installer()
        assert "GROQ_API_URL" in text
        assert "api.groq.com" in text


# --- OpenViking setup ---


class TestOpenVikingSetup:
    """T30.5 OpenViking semantic memory setup."""

    def test_pip_install_openviking(self) -> None:
        text = load_installer()
        assert "openviking" in text
        assert "pip" in text

    def test_config_template_created(self) -> None:
        text = load_installer()
        ov_section = text[text.find("setup_openviking"):text.find("setup_cron")]
        assert "ov.conf" in ov_section
        assert "CHANGE_ME" in ov_section, "Config must have placeholder key"

    def test_config_chmod_600(self) -> None:
        text = load_installer()
        ov_section = text[text.find("setup_openviking"):text.find("setup_cron")]
        assert "chmod 600" in ov_section

    def test_systemd_gated_on_binary(self) -> None:
        """systemd service only created if openviking binary exists."""
        text = load_installer()
        ov_section = text[text.find("setup_openviking"):text.find("setup_cron")]
        assert "-x" in ov_section, "Must check binary exists with -x before creating service"

    def test_port_1933(self) -> None:
        text = load_installer()
        assert "1933" in text, "OpenViking default port is 1933"

    def test_openviking_dir_in_home(self) -> None:
        text = load_installer()
        assert ".openviking" in text


# --- Cron setup ---


class TestCronSetup:
    """T30.6 Memory rotation cron schedule."""

    CRON_SCRIPTS = ["rotate-warm.sh", "trim-hot.sh", "compress-warm.sh"]

    def test_three_scripts_written(self) -> None:
        text = load_installer()
        for script in self.CRON_SCRIPTS:
            assert script in text, f"Cron script {script} not found"

    def test_scripts_are_executable(self) -> None:
        text = load_installer()
        assert "chmod +x" in text

    def test_crontab_marker(self) -> None:
        """Cron uses a marker to prevent duplicate installs."""
        text = load_installer()
        assert "EdgeLab memory rotation" in text

    def test_crontab_idempotent(self) -> None:
        """Must check if cron already installed before adding."""
        text = load_installer()
        # Extract full setup_cron function body
        match = re.search(r"^setup_cron\(\)\s*\{(.*?)^\}", text, re.MULTILINE | re.DOTALL)
        assert match, "setup_cron() not found"
        cron_body = match.group(1)
        assert "grep" in cron_body, "Must grep for existing marker"

    def test_cron_log_not_in_tmp(self) -> None:
        """Cron logs must NOT go to /tmp (symlink attack risk)."""
        text = load_installer()
        match = re.search(r"^setup_cron\(\)\s*\{(.*?)^\}", text, re.MULTILINE | re.DOTALL)
        assert match, "setup_cron() not found"
        cron_body = match.group(1)
        assert "/tmp/" not in cron_body, "Cron log must not be in /tmp"
        assert ".claude/logs" in cron_body, "Cron log should be in ~/.claude/logs"

    def test_cron_times_correct(self) -> None:
        """Cron times must match canonical schedule."""
        text = load_installer()
        assert "30 4 * * *" in text, "rotate-warm must run at 04:30"
        assert "0  5 * * *" in text or "0 5 * * *" in text, "trim-hot must run at 05:00"
        assert "0  6 * * *" in text or "0 6 * * *" in text, "compress-warm must run at 06:00"


# --- Embedded cron scripts ---


class TestEmbeddedCronScripts:
    """T30.7 Embedded cron scripts have correct structure."""

    @staticmethod
    def _get_func_body(text: str, func_name: str) -> str:
        """Extract function body by finding 'func_name() {' definition."""
        pattern = rf"^{func_name}\(\)\s*\{{"
        match = re.search(pattern, text, re.MULTILINE)
        if not match:
            pytest.fail(f"Function {func_name}() not found")
        start = match.start()
        # Find the closing brace at column 0 (end of function)
        rest = text[start:]
        # Find RWEOF/THEOF/CWEOF heredoc end + closing brace
        end_match = re.search(r"^}", rest, re.MULTILINE)
        if end_match:
            return rest[:end_match.end()]
        return rest[:2000]

    def test_rotate_warm_has_set_euo(self) -> None:
        text = load_installer()
        section = self._get_func_body(text, "write_rotate_warm_script")
        assert "set -euo pipefail" in section

    def test_rotate_warm_14_day_cutoff(self) -> None:
        text = load_installer()
        section = self._get_func_body(text, "write_rotate_warm_script")
        assert "14 days" in section or "14d" in section

    def test_rotate_warm_dynamic_header(self) -> None:
        """Must NOT use head -5 magic number."""
        text = load_installer()
        section = self._get_func_body(text, "write_rotate_warm_script")
        assert "head -5" not in section, "Must use dynamic header detection, not head -5"
        assert "awk" in section, "Should use awk for dynamic header detection"

    def test_trim_hot_keeps_10_entries(self) -> None:
        text = load_installer()
        section = self._get_func_body(text, "write_trim_hot_script")
        assert "10" in section

    def test_trim_hot_has_set_euo(self) -> None:
        text = load_installer()
        section = self._get_func_body(text, "write_trim_hot_script")
        assert "set -euo pipefail" in section

    def test_compress_warm_size_guard(self) -> None:
        text = load_installer()
        section = self._get_func_body(text, "write_compress_warm_script")
        assert "10240" in section or "10KB" in section


# --- Security ---


class TestInstallerSecurity:
    """T30.8 Security checks."""

    def test_no_hardcoded_api_keys(self) -> None:
        """No real API keys in the script."""
        text = load_installer()
        assert not re.search(r'gsk_[A-Za-z0-9]{20,}', text), "Hardcoded Groq key found"
        assert not re.search(r'sk-[A-Za-z0-9]{20,}', text), "Hardcoded OpenAI key found"

    def test_no_python3_override(self) -> None:
        """Must NOT globally replace system python3."""
        text = load_installer()
        assert "update-alternatives --set python3" not in text, (
            "Must NOT override system python3"
        )

    def test_secrets_dir_chmod_700(self) -> None:
        text = load_installer()
        assert "chmod 700" in text, "Secrets dir must be chmod 700"

    def test_unattended_upgrades_not_disabled(self) -> None:
        """Must NOT permanently disable unattended-upgrades."""
        text = load_installer()
        assert "systemctl disable unattended-upgrades" not in text, (
            "Must not permanently disable security updates"
        )

    def test_unattended_upgrades_restarted(self) -> None:
        """Must restart unattended-upgrades after install."""
        text = load_installer()
        main_match = re.search(r"^main\(\)\s*\{(.*?)^\}", text, re.MULTILINE | re.DOTALL)
        assert main_match
        main_body = main_match.group(1)
        assert "unattended-upgrades" in main_body, (
            "Must re-enable unattended-upgrades in main()"
        )


# --- Gateway config ---


class TestGatewayConfig:
    """T30.9 Gateway config template."""

    def test_groq_api_key_file_in_config(self) -> None:
        text = load_installer()
        assert "groq_api_key_file" in text, "Gateway config must include groq_api_key_file"

    def test_config_has_allowlist(self) -> None:
        text = load_installer()
        assert "allowlist_user_ids" in text

    def test_config_model_opus(self) -> None:
        text = load_installer()
        assert '"model": "opus"' in text or '"model":"opus"' in text

    def test_config_uses_absolute_paths(self) -> None:
        """Config must use REAL_HOME, not tilde."""
        text = load_installer()
        config_section = text[text.find("install_gateway_config"):text.find("GWEOF")]
        assert "~/" not in config_section, "Config must use absolute paths, not ~"


# --- Final banner ---


class TestBanner:
    """T30.10 Final banner completeness."""

    def test_mentions_claude_code(self) -> None:
        text = load_installer()
        banner = text[text.find("print_banner"):]
        assert "Claude" in banner or "claude" in banner

    def test_mentions_groq(self) -> None:
        text = load_installer()
        banner = text[text.find("print_banner"):]
        assert "Groq" in banner or "groq" in banner

    def test_mentions_openviking(self) -> None:
        text = load_installer()
        banner = text[text.find("print_banner"):]
        assert "OpenViking" in banner or "openviking" in banner

    def test_mentions_cron(self) -> None:
        text = load_installer()
        banner = text[text.find("print_banner"):]
        assert "Cron" in banner or "cron" in banner

    def test_mentions_guides_url(self) -> None:
        text = load_installer()
        assert "guides.edgelab.su" in text

    def test_mentions_community_url(self) -> None:
        text = load_installer()
        assert "edgelab.su" in text


# --- Claude Code install ---


class TestClaudeCodeInstall:
    """T30.11 Claude Code CLI installation."""

    def test_uses_bash_not_sh(self) -> None:
        """Must use bash, not sh (Ubuntu sh=dash breaks arrays)."""
        text = load_installer()
        claude_section = text[text.find("install_claude_code"):text.find("install_gateway")]
        assert 'as_user "bash' in claude_section, "Must use bash for Anthropic installer"
        assert 'as_user "sh' not in claude_section, "Must NOT use sh (dash breaks arrays)"

    def test_downloads_before_executing(self) -> None:
        """curl download must come before bash execution of installer."""
        text = load_installer()
        claude_section = text[text.find("install_claude_code"):text.find("install_gateway")]
        # Find the download curl (not the update path)
        curl_pos = claude_section.find("curl -fsSL https://claude.ai")
        # Find the bash execution (not the update path)
        bash_exec_pos = claude_section.find('as_user "bash')
        assert curl_pos > 0, "Must download via curl"
        assert bash_exec_pos > 0, "Must execute via bash"
        assert curl_pos < bash_exec_pos, "Must download installer before executing"

    def test_verifies_installation(self) -> None:
        text = load_installer()
        claude_section = text[text.find("install_claude_code"):text.find("install_gateway")]
        assert "-x" in claude_section, "Must verify claude binary exists after install"
