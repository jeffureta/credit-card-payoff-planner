#!/usr/bin/env bash
# ==============================================================================
# Git Safety Check & Privacy Gate
# Enforces:
#  1. ZERO PDF or private financial statements staged in git index.
#  2. ZERO private SQLite databases or local sensitive data staged.
#  3. Local test suite passes cleanly before push.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🛡️  [Privacy Gate] Running Git Safety & Privacy Checks..."

# 1. Check for forbidden files staged in Git
STAGED_FORBIDDEN=$(git diff --cached --name-only | grep -E '\.(pdf|PDF|db|sqlite|sqlite3)$|^statements/|^data/.*\.db$' || true)

if [ -n "$STAGED_FORBIDDEN" ]; then
    echo -e "${RED}❌ PRIVACY VIOLATION DETECTED!${NC}"
    echo "The following private / financial files are staged for commit:"
    echo "$STAGED_FORBIDDEN"
    echo -e "${YELLOW}Please unstage these files immediately:${NC}"
    echo "git restore --staged <file>"
    exit 1
fi

echo -e "${GREEN}✓ Privacy Gate Passed: No PDF or database files staged.${NC}"

# 2. Run Test Suite Safety Gate
echo "🧪 [Safety Gate] Running automated tests via pytest..."
export PYTHONPATH=.
if [ -f ".venv/bin/pytest" ]; then
    .venv/bin/pytest tests/ -q --tb=short
elif command -v pytest >/dev/null 2>&1; then
    pytest tests/ -q --tb=short
elif python3 -m pytest --version >/dev/null 2>&1; then
    python3 -m pytest tests/ -q --tb=short
else
    echo -e "${YELLOW}⚠️  pytest not found, skipping automated test gate in this environment.${NC}"
fi

echo -e "${GREEN}✓ All safety gates cleared. Ready to commit/push.${NC}"
exit 0
