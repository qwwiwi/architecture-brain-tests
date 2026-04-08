#!/usr/bin/env bash
set -euo pipefail

# CI-friendly test runner for architecture-brain-tests
# Usage: bash scripts/run_all.sh

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "=== Ruff lint ==="
ruff check . || { echo "FAIL: ruff lint"; exit 1; }

echo ""
echo "=== Ruff format check ==="
ruff format --check . || { echo "FAIL: ruff format"; exit 1; }

echo ""
echo "=== Pytest ==="
pytest -v --tb=short || { echo "FAIL: pytest"; exit 1; }

echo ""
echo "=== All checks passed ==="
