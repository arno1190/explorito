#!/bin/bash
# Validate bash command results
# Called after bash tool use to check for errors

set -e

# Parse command result from stdin (if available)
INPUT=$(cat 2>/dev/null) || true

# Check for common error patterns
if echo "$INPUT" | grep -qiE "error:|failed:|exception:|traceback" 2>/dev/null; then
  echo "⚠ Potential error detected in command output"
  echo "$INPUT" | grep -iE "error:|failed:|exception:|traceback" | head -5
fi

exit 0
