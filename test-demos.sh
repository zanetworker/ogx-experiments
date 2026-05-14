#!/bin/bash
# Test runner for OGX experiments.
# Usage:
#   ./test-demos.sh                  # Run all experiments
#   ./test-demos.sh inference        # Run one category
#   ./test-demos.sh rag/rag_file     # Run scripts matching a pattern
#   ./test-demos.sh --dry-run        # List what would run
#   ./test-demos.sh --list           # List categories

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TIMEOUT=30
DRY_RUN=false
FILTER=""

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --list)
            echo "Categories:"
            for d in "$SCRIPT_DIR"/*/; do
                name=$(basename "$d")
                [[ "$name" == __pycache__ || "$name" == ogx-dev-setup || "$name" == company_app || "$name" == docker || "$name" == Guides || "$name" == redhatai_validated_models || "$name" == telemetry ]] && continue
                count=$(find "$d" -maxdepth 1 -name "*.py" ! -name "conftest.py" ! -name "__init__.py" | wc -l | tr -d ' ')
                echo "  $name ($count scripts)"
            done
            exit 0 ;;
        *) FILTER="$arg" ;;
    esac
done

echo -e "${BLUE}${BOLD}OGX Experiments Test Runner${NC}"
echo ""

OGX_PORT="${OGX_PORT:-8321}"
cd "$SCRIPT_DIR"

# Collect scripts from subdirectories
DEMOS=""
if [ -n "$FILTER" ]; then
    DEMOS=$(find inference rag tools agents multi-sdk batches -maxdepth 1 -name "*.py" ! -name "conftest.py" ! -name "__init__.py" 2>/dev/null | grep "$FILTER" | sort || true)
else
    DEMOS=$(find inference rag tools agents multi-sdk batches -maxdepth 1 -name "*.py" ! -name "conftest.py" ! -name "__init__.py" 2>/dev/null | sort || true)
fi

if [ -z "$DEMOS" ]; then
    echo -e "${RED}No scripts found matching: ${FILTER:-*}${NC}"
    exit 1
fi

TOTAL=$(echo "$DEMOS" | wc -l | tr -d ' ')
echo -e "${BLUE}Scripts (${TOTAL}):${NC}"
for demo in $DEMOS; do
    echo "  $demo"
done
echo ""

if $DRY_RUN; then
    echo -e "${YELLOW}--dry-run: nothing executed${NC}"
    exit 0
fi

# Health check
echo "Checking OGX server at localhost:${OGX_PORT} ..."
if curl -sf "http://localhost:${OGX_PORT}/v1/health" >/dev/null 2>&1; then
    echo -e "${GREEN}Server is healthy${NC}"
else
    echo -e "${RED}Server not reachable. Start it first:${NC}"
    echo "  ./experiments/ogx-dev-setup/run-ogx.sh"
    exit 1
fi
echo ""

PASSED=()
FAILED=()

for demo in $DEMOS; do
    LOG="/tmp/ogx-demo-$(basename "$demo").log"
    START=$(date +%s)

    if timeout "$TIMEOUT" python "$demo" > "$LOG" 2>&1; then
        DUR=$(( $(date +%s) - START ))
        echo -e "${GREEN}PASS${NC}  $demo  (${DUR}s)"
        PASSED+=("$demo")
    else
        RC=$?
        DUR=$(( $(date +%s) - START ))
        if [ "$RC" -eq 124 ]; then
            echo -e "${RED}TIMEOUT${NC}  $demo  (>${TIMEOUT}s)"
        else
            echo -e "${RED}FAIL${NC}  $demo  (exit ${RC}, ${DUR}s)"
        fi
        tail -5 "$LOG" | sed 's/^/    /'
        FAILED+=("$demo")
    fi
done

echo ""
echo -e "${GREEN}Passed: ${#PASSED[@]}${NC}  ${RED}Failed: ${#FAILED[@]}${NC}  Total: ${TOTAL}"

if [ ${#FAILED[@]} -gt 0 ]; then
    exit 1
fi
