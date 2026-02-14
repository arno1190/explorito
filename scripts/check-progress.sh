#!/bin/bash
# Check progress and determine if Ralph loop should continue
# Exit codes:
#   0 - Continue loop
#   1 - Stop loop (blocked or completed)

set -e

if [[ ! -f "progress.txt" ]]; then
  echo "No progress.txt found - creating initial state"
  exit 0
fi

# Extract current state
STATE=$(grep -E "^## Current State:" progress.txt 2>/dev/null | head -1 | cut -d: -f2 | tr -d ' ')

case "$STATE" in
  COMPLETED)
    echo "✓ Goal completed!"
    echo ""
    echo "Final progress:"
    tail -20 progress.txt
    exit 1
    ;;
  BLOCKED)
    echo "⚠ Blocked - manual intervention needed"
    echo ""
    echo "Current blockers:"
    grep -A5 "### Blockers" progress.txt 2>/dev/null | tail -5
    exit 1
    ;;
  *)
    echo "=== Current Progress ==="
    echo "State: ${STATE:-UNKNOWN}"
    echo ""
    # Show last iteration
    grep -A20 "^## Iteration" progress.txt 2>/dev/null | tail -20
    echo "========================"
    exit 0
    ;;
esac
