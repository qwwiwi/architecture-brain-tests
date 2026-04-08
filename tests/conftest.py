"""Shared fixtures for architecture-brain-tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def valid_config() -> dict[str, Any]:
    """Load valid gateway config from fixtures."""
    return json.loads((FIXTURES_DIR / "config_valid.json").read_text())


@pytest.fixture
def invalid_config() -> dict[str, Any]:
    """Load invalid (incomplete) gateway config from fixtures."""
    return json.loads((FIXTURES_DIR / "config_invalid.json").read_text())


@pytest.fixture
def telegram_update() -> dict[str, Any]:
    """Load sample Telegram update from fixtures."""
    return json.loads((FIXTURES_DIR / "telegram_update.json").read_text())


@pytest.fixture
def hot_memory_text() -> str:
    """Load sample HOT memory content."""
    return (FIXTURES_DIR / "hot_memory_sample.md").read_text()


@pytest.fixture
def warm_memory_text() -> str:
    """Load sample WARM memory content."""
    return (FIXTURES_DIR / "warm_memory_sample.md").read_text()


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace mimicking agent structure."""
    ws = tmp_path / ".claude"
    (ws / "core" / "hot").mkdir(parents=True)
    (ws / "core" / "warm").mkdir(parents=True)
    (ws / "scripts").mkdir(parents=True)
    # Create minimal hot memory
    (ws / "core" / "hot" / "recent.md").write_text("# Hot memory -- last 72h rolling journal\n")
    (ws / "core" / "warm" / "decisions.md").write_text("# WARM DECISIONS -- Test\n")
    (ws / "core" / "MEMORY.md").write_text("# COLD MEMORY\n")
    return ws


@pytest.fixture
def mock_tg_api() -> MagicMock:
    """Mock for Telegram API calls. Returns success by default."""
    mock = MagicMock()
    mock.return_value = {"ok": True, "result": {"message_id": 1}}
    return mock


@pytest.fixture
def mock_requests() -> MagicMock:
    """Mock for requests.post/get used by gateway."""
    mock = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"ok": True, "result": {}}
    mock.post.return_value = response
    mock.get.return_value = response
    return mock
