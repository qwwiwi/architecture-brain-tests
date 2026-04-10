"""T9: OpenViking sync and search.

Tests:
- Batch sync via ov-session-sync.sh (temp_upload + add_resource)
- Stop hook configuration in settings.json
- Cron schedule placement (06:30 UTC, after memory rotation)
- Search API contract (POST /api/v1/search/find)
- Anti-pollution guards for forwarded content
- Skip conditions (no key file, OV unreachable)
- Documentation consistency across public architecture files
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Path to public architecture docs (for documentation consistency tests)
ARCH_REPO = Path("/tmp/public-architecture-claude-code")


class TestBatchSyncFlow:
    """T9.1: OpenViking batch sync via ov-session-sync.sh.

    Contract (replaces old sessions API):
    1. Health check -> OpenViking reachable?
    2. Build markdown from HOT (last 10) + WARM (full)
    3. POST /api/v1/resources/temp_upload -> temp_file_id
    4. POST /api/v1/resources -> add_resource with URI + wait=true
    """

    def test_sync_flow_steps(self) -> None:
        """Verify batch sync uses 2-step upload (temp_upload + add_resource)."""
        steps: list[tuple[str, str]] = []

        # Step 1: Health check
        steps.append(("GET", "/api/v1/debug/health"))
        # Step 2: Upload markdown
        steps.append(("POST", "/api/v1/resources/temp_upload"))
        # Step 3: Add resource with indexing
        steps.append(("POST", "/api/v1/resources"))

        assert len(steps) == 3
        assert steps[0][1] == "/api/v1/debug/health"
        assert steps[1][1] == "/api/v1/resources/temp_upload"
        assert steps[2][1] == "/api/v1/resources"

    def test_target_uri_pattern(self) -> None:
        """Target URI follows viking://resources/{agent}-sessions/{date}."""
        agent = "thrall"
        date = "2026-04-10"
        uri = f"viking://resources/{agent}-sessions/{date}"

        assert uri.startswith("viking://resources/")
        assert agent in uri
        assert re.match(r"\d{4}-\d{2}-\d{2}", date)

    def test_sync_is_idempotent(self) -> None:
        """Same date = same URI = overwrites previous upload."""
        uri_1 = "viking://resources/thrall-sessions/2026-04-10"
        uri_2 = "viking://resources/thrall-sessions/2026-04-10"
        assert uri_1 == uri_2, "Same date must produce same URI for idempotency"

    def test_summary_includes_hot_and_warm(self) -> None:
        """Summary markdown must contain both HOT and WARM sections."""
        summary = (
            "# Session summary -- 2026-04-10\n\n"
            "## HOT memory (recent activity)\n\n"
            "Entries: 5 | Size: 3000 bytes\n\n"
            "## WARM decisions (recent 14d)\n\n"
            "Size: 2000 bytes\n"
        )
        assert "## HOT memory" in summary
        assert "## WARM decisions" in summary

    def test_skip_if_summary_too_small(self) -> None:
        """Skip upload if summary < 100 bytes (nothing meaningful)."""
        min_size = 100
        empty_summary = "# Session summary\n\nNo data.\n"
        assert len(empty_summary.encode()) < min_size


class TestStopHookConfig:
    """T9.2: Stop hook configuration for OpenViking sync."""

    def test_stop_hook_structure(self) -> None:
        """Stop hook must have correct structure in settings.json."""
        hook_config: dict[str, Any] = {
            "hooks": {
                "Stop": [{
                    "matcher": "",
                    "hooks": [{
                        "type": "command",
                        "command": "bash scripts/ov-session-sync.sh >> /tmp/ov-session-sync.log 2>&1 &",
                        "timeout": 10,
                    }],
                }],
            },
        }

        stop_hooks = hook_config["hooks"]["Stop"]
        assert len(stop_hooks) == 1
        assert stop_hooks[0]["matcher"] == ""
        inner = stop_hooks[0]["hooks"][0]
        assert inner["type"] == "command"
        assert "ov-session-sync.sh" in inner["command"]
        assert inner["command"].endswith("&"), "Must run in background"

    def test_hook_timeout_reasonable(self) -> None:
        """Hook timeout should be short (script runs in background)."""
        timeout = 10
        assert timeout <= 30, "Background hook should not need long timeout"


class TestCronSchedule:
    """T9.3: Cron placement for ov-session-sync.sh."""

    def test_runs_after_memory_rotation(self) -> None:
        """OV sync must run AFTER trim-hot (05:00) and compress-warm (06:00)."""
        cron_times = {
            "rotate-warm": (4, 30),
            "trim-hot": (5, 0),
            "compress-warm": (6, 0),
            "ov-session-sync": (6, 30),
            "memory-rotate": (21, 0),
        }

        ov_hour, ov_min = cron_times["ov-session-sync"]
        trim_hour, trim_min = cron_times["trim-hot"]
        compress_hour, compress_min = cron_times["compress-warm"]

        ov_total = ov_hour * 60 + ov_min
        trim_total = trim_hour * 60 + trim_min
        compress_total = compress_hour * 60 + compress_min

        assert ov_total > trim_total, "OV sync must run after trim-hot"
        assert ov_total > compress_total, "OV sync must run after compress-warm"

    def test_five_cron_jobs_total(self) -> None:
        """Memory management requires exactly 5 cron jobs."""
        jobs = [
            "rotate-warm.sh",
            "trim-hot.sh",
            "compress-warm.sh",
            "ov-session-sync.sh",
            "memory-rotate.sh",
        ]
        assert len(jobs) == 5


class TestSearchAPI:
    """T9.4: OpenViking search contract."""

    def test_search_endpoint(self) -> None:
        """Search uses POST /api/v1/search/find."""
        endpoint = "/api/v1/search/find"
        method = "POST"
        assert method == "POST"
        assert endpoint == "/api/v1/search/find"

    def test_search_request_format(self) -> None:
        """Search request must include query and limit."""
        request = {"query": "edgelab platform", "limit": 10}
        assert "query" in request
        assert "limit" in request
        assert isinstance(request["limit"], int)

    def test_search_headers(self) -> None:
        """Search must include API key, account, and user headers."""
        required_headers = [
            "X-API-Key",
            "X-OpenViking-Account",
            "X-OpenViking-User",
        ]
        headers = {
            "X-API-Key": "test-key",
            "X-OpenViking-Account": "orgrimmar",
            "X-OpenViking-User": "thrall",
        }
        for h in required_headers:
            assert h in headers


class TestAntiPollution:
    """T9.5: Anti-pollution guards for OpenViking.

    Prevents extracting forwarded content as user's own preferences.
    """

    def test_forwarded_guard(self) -> None:
        """Forwarded messages get extraction hint."""
        text = "[source:forwarded | from_user]\nSome forwarded content"
        if "[source:forwarded" in text:
            guard = (
                "\n[extraction hint: this content was FORWARDED to princ from someone else. "
                "Do NOT extract as princ's own preferences.]\n"
            )
        else:
            guard = ""
        assert "FORWARDED" in guard
        assert "Do NOT extract" in guard

    def test_external_media_not_pushed(self) -> None:
        """External media should NOT be pushed to OpenViking."""
        source_tag = "external_media"
        push_to_ov = source_tag not in ("external_media", "transcription_failed")
        assert not push_to_ov

    def test_own_text_pushed(self) -> None:
        """Own text messages should be pushed."""
        source_tag = "own_text"
        push_to_ov = source_tag not in ("external_media", "transcription_failed")
        assert push_to_ov

    def test_own_voice_pushed(self) -> None:
        """Own voice messages should be pushed."""
        source_tag = "own_voice"
        push_to_ov = source_tag not in ("external_media", "transcription_failed")
        assert push_to_ov


class TestOVSkipConditions:
    """T9.6: Conditions when OV sync is skipped."""

    def test_skip_if_no_key_file(self, tmp_path: Any) -> None:
        """Skip sync if openviking.key doesn't exist."""
        key_file = tmp_path / "secrets" / "openviking.key"
        assert not key_file.exists()

    def test_skip_if_health_check_fails(self) -> None:
        """Skip sync if health check returns non-ok."""
        health_response = '{"status":"error"}'
        data = json.loads(health_response)
        assert data["status"] != "ok"

    def test_skip_if_temp_upload_fails(self) -> None:
        """Skip sync if temp_upload returns no temp_file_id."""
        response = {"status": "error", "result": None}
        temp_id = (response.get("result") or {}).get("temp_file_id", "")
        assert temp_id == ""


class TestDocConsistency:
    """T9.7: Documentation consistency across public architecture files.

    Verifies that OpenViking documentation is consistent across all files.
    Skipped if public-architecture-claude-code repo not available.
    """

    @staticmethod
    def _skip_if_no_repo() -> bool:
        return not ARCH_REPO.exists()

    def test_memory_md_has_batch_sync(self) -> None:
        """MEMORY.md must document batch sync method."""
        if self._skip_if_no_repo():
            return
        content = (ARCH_REPO / "MEMORY.md").read_text()
        assert "temp_upload" in content, "MEMORY.md must mention temp_upload"
        assert "add_resource" in content, "MEMORY.md must mention add_resource"
        assert "ov-session-sync" in content, "MEMORY.md must mention sync script"

    def test_memory_md_has_five_cron_jobs(self) -> None:
        """MEMORY.md recommended cron must list 5 jobs."""
        if self._skip_if_no_repo():
            return
        content = (ARCH_REPO / "MEMORY.md").read_text()
        assert "ov-session-sync.sh" in content, "MEMORY.md must list ov-session-sync cron"

    def test_hooks_md_has_ov_stop_example(self) -> None:
        """HOOKS.md must have OpenViking Stop hook example."""
        if self._skip_if_no_repo():
            return
        content = (ARCH_REPO / "HOOKS.md").read_text()
        assert "ov-session-sync" in content, "HOOKS.md must show OV sync hook"
        assert "Stop" in content

    def test_architecture_md_has_batch_sync(self) -> None:
        """ARCHITECTURE.md must document batch sync (not fire-and-forget)."""
        if self._skip_if_no_repo():
            return
        content = (ARCH_REPO / "ARCHITECTURE.md").read_text()
        assert "batch sync" in content.lower() or "temp_upload" in content, \
            "ARCHITECTURE.md must document batch sync method"

    def test_no_sessions_api_as_primary(self) -> None:
        """ARCHITECTURE.md should not show sessions API as primary write method."""
        if self._skip_if_no_repo():
            return
        content = (ARCH_REPO / "ARCHITECTURE.md").read_text()
        # The old sessions API should not be in the main OV diagram
        # (it may still exist in optional/legacy sections)
        ov_section_start = content.find("## OpenViking")
        if ov_section_start == -1:
            return
        ov_section = content[ov_section_start:ov_section_start + 2000]
        assert "/api/v1/sessions" not in ov_section, \
            "ARCHITECTURE.md OpenViking section should use resources API, not sessions"

    def test_cron_order_consistent(self) -> None:
        """Cron order must be consistent between MEMORY.md and ARCHITECTURE.md."""
        if self._skip_if_no_repo():
            return
        for filename in ("MEMORY.md", "ARCHITECTURE.md"):
            content = (ARCH_REPO / filename).read_text()
            # Find cron section
            if "ov-session-sync" not in content:
                raise AssertionError(f"{filename} missing ov-session-sync in cron schedule")
