# Architecture Brain Tests

End-to-end and unit tests for AI agent Telegram gateway and memory management system.

Covers the full pipeline: **Telegram message -> Gateway -> Claude Code -> Response -> Memory**.

## What This Tests

| Group | What | Type |
|-------|------|------|
| **T1: Config** | Gateway config loading, validation, defaults | Unit |
| **T2: Message Parsing** | Telegram update -> internal format, allowlist, group gating | Unit |
| **T3: OOB Commands** | /stop, /reset, /status routing | Unit |
| **T4: Media** | File download, audio transcription (mock Groq) | Unit |
| **T5: Session** | New session creation, resume existing | Unit |
| **T6: Claude Invoke** | Subprocess args, workspace, model, permissions | Integration |
| **T7: Response Format** | Markdown -> HTML, tables, code blocks, split >4096 chars | Unit |
| **T8: HOT Memory** | append_to_hot_memory, fcntl lock, emergency trim | Unit |
| **T9: OpenViking** | push_to_openviking, filtering (own_text yes, external skip) | Unit |
| **T10: Compression** | trim-hot.sh input/output, bash fallback, Sonnet mock | Integration |
| **T11: WARM Rotation** | rotate-warm.sh 14d cutoff, move to COLD | Integration |
| **T12: End-to-End** | Full pipeline: Telegram -> Gateway -> Claude -> Memory | E2E |
| **T13: Agent Laws** | AGENT-LAWS.md structure, 9 principles, superpowers | Unit |
| **T14: Structure** | Repo structure, templates, skills, install.sh, Vibe Kanban | Unit |
| **T15: Content API** | UUID detection, video_id extraction, tariff access | Unit |
| **T16: Skills** | 11 base skills, SKILL.md frontmatter, no secrets | Unit |
| **T17: Settings** | settings.json template, permissions, hooks format, MCP | Unit |
| **T18: Hooks** | Lifecycle events, handler types, enforcement, examples | Unit |
| **T19: Cron Pipeline** | Script safety, flock, Sonnet fallback, cron order | Integration |
| **T20: Security** | No secrets in templates, secrets paths, git safety | Unit |
| **T21: Context Budget** | Token budgets, file size limits, compression docs | Unit |
| **T22: Workspace** | Naming conventions, directory structure, symlinks | Unit |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest -v

# Run specific group
pytest tests/test_config.py -v
pytest tests/test_memory.py -v
pytest tests/test_gateway.py -v

# Lint with ruff
ruff check .
ruff format --check .
```

## Structure

```
architecture-brain-tests/
├── README.md
├── ruff.toml              # Ruff linter/formatter config
├── pytest.ini             # Pytest config
├── requirements.txt       # Test dependencies
├── tests/
│   ├── conftest.py        # Shared fixtures
│   ├── test_config.py     # T1: Config loading
│   ├── test_parsing.py    # T2: Message parsing
│   ├── test_oob.py        # T3: OOB commands
│   ├── test_media.py      # T4: Media processing
│   ├── test_session.py    # T5: Session management
│   ├── test_invoke.py     # T6: Claude invocation
│   ├── test_format.py     # T7: Response formatting
│   ├── test_memory.py     # T8: HOT memory writes
│   ├── test_openviking.py # T9: OpenViking push
│   ├── test_compression.py# T10: Memory compression
│   ├── test_rotation.py   # T11: WARM rotation
│   ├── test_e2e.py        # T12: End-to-end
│   ├── test_agent_laws.py # T13: Agent laws
│   ├── test_structure.py  # T14: Workspace structure
│   ├── test_content_api.py# T15: Content API
│   ├── test_skills.py     # T16: Skills validation
│   ├── test_settings.py   # T17: Settings template
│   ├── test_hooks.py      # T18: Hook system
│   ├── test_cron_pipeline.py # T19: Cron pipeline
│   ├── test_security.py   # T20: Security
│   ├── test_context_budget.py # T21: Token budget
│   └── test_workspace_conventions.py # T22: Workspace conventions
├── fixtures/
│   ├── config_valid.json  # Valid gateway config
│   ├── config_invalid.json# Broken config for error tests
│   ├── telegram_update.json  # Sample Telegram update
│   ├── hot_memory_sample.md  # Sample HOT memory file
│   └── warm_memory_sample.md # Sample WARM memory file
└── scripts/
    └── run_all.sh         # CI-friendly test runner
```

## How Tests Work

Each test file is self-contained and documents:
1. **What** is being tested
2. **Setup** -- fixtures and mocks needed
3. **Steps** -- exact sequence of actions
4. **Expected** -- what OK/FAIL looks like

Tests use **mocks** for external services (Telegram API, Groq, OpenViking, Claude subprocess) so they run without credentials or network access.

## Requirements

- Python 3.12+
- pytest 9.0+
- ruff 0.15+

## Related Repositories

- [public-architecture-claude-code](https://github.com/qwwiwi/public-architecture-claude-code) -- Architecture documentation
- [jarvis-telegram-gateway](https://github.com/qwwiwi/jarvis-telegram-gateway) -- Gateway documentation
- [OpenViking](https://github.com/volcengine/OpenViking) -- Semantic memory engine
- [ruff](https://github.com/astral-sh/ruff) -- Python linter/formatter
