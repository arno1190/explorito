#!/bin/bash
# Ralph Mode - Autonomous Loop Runner
# Runs Claude Code in a loop with fresh context per iteration

set -e

# Configuration
MAX_ITERATIONS=${MAX_ITERATIONS:-15}
ITERATION_DELAY=${ITERATION_DELAY:-5}
AUTO_CONTINUE=${AUTO_CONTINUE:-true}
PROMPT_FILE=${PROMPT_FILE:-prompt.md}
PROGRESS_FILE=${PROGRESS_FILE:-progress.txt}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check requirements
check_requirements() {
    if ! command -v claude &> /dev/null; then
        log_error "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        exit 1
    fi

    # Note: claude CLI manages its own auth, no need to check ANTHROPIC_API_KEY

    if [ ! -f "$PROMPT_FILE" ]; then
        log_error "Prompt file not found: $PROMPT_FILE"
        exit 1
    fi
}

# Check if goal is complete or blocked
check_completion() {
    if [ -f "$PROGRESS_FILE" ]; then
        # Match the format used by check-progress.sh: "## Current State: COMPLETED"
        if grep -qE "^## Current State:.*COMPLETED" "$PROGRESS_FILE"; then
            return 0  # Complete
        fi
        if grep -qE "^## Current State:.*BLOCKED" "$PROGRESS_FILE"; then
            return 2  # Blocked
        fi
    fi
    return 1  # Not complete
}

# Run single iteration
run_iteration() {
    local iteration=$1

    log "Starting iteration $iteration/$MAX_ITERATIONS"

    # Prepare iteration header for progress file
    echo "" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
    echo "" >> "$PROGRESS_FILE"
    echo "## Iteration $iteration - $(date '+%Y-%m-%d %H:%M:%S')" >> "$PROGRESS_FILE"

    # Run Claude with fresh context
    local exit_code=0
    claude -p "$(cat $PROMPT_FILE)" --dangerously-skip-permissions || exit_code=$?

    if [ $exit_code -ne 0 ]; then
        log_warn "Claude exited with code $exit_code"
    fi

    # Log iteration completion
    echo "### Iteration $iteration completed at $(date '+%H:%M:%S')" >> .claude/session.log

    return $exit_code
}

# Main loop
main() {
    log "=== Explorito Ralph Mode ==="
    log "Max iterations: $MAX_ITERATIONS"
    log "Delay between iterations: ${ITERATION_DELAY}s"
    log "Auto-continue: $AUTO_CONTINUE"
    echo ""

    check_requirements

    # Initialize session log
    mkdir -p .claude
    echo "=== Ralph Session Started $(date) ===" >> .claude/session.log

    local iteration=1

    while [ $iteration -le $MAX_ITERATIONS ]; do
        # Check if already complete or blocked
        local status=0
        check_completion && status=0 || status=$?
        if [ $status -eq 0 ]; then
            log_success "Goal achieved! Stopping loop."
            break
        elif [ $status -eq 2 ]; then
            log_error "Goal is blocked! Manual intervention needed."
            break
        fi

        # Run iteration
        run_iteration $iteration

        # Check completion after iteration
        check_completion && status=0 || status=$?
        if [ $status -eq 0 ]; then
            log_success "Goal achieved after iteration $iteration!"
            break
        elif [ $status -eq 2 ]; then
            log_error "Goal blocked after iteration $iteration! Check progress.txt for details."
            break
        fi

        # Check if we should continue
        if [ "$AUTO_CONTINUE" != "true" ]; then
            read -p "Continue to next iteration? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log "Stopping loop by user request"
                break
            fi
        fi

        # Delay before next iteration
        if [ $iteration -lt $MAX_ITERATIONS ]; then
            log "Waiting ${ITERATION_DELAY}s before next iteration..."
            sleep $ITERATION_DELAY
        fi

        ((iteration++))
    done

    if [ $iteration -gt $MAX_ITERATIONS ]; then
        log_warn "Reached maximum iterations ($MAX_ITERATIONS) without completion"
    fi

    # Summary
    echo ""
    log "=== Session Summary ==="
    log "Total iterations: $((iteration - 1))"
    # Extract state from "## Current State: XXX" format
    local final_status=$(grep -E "^## Current State:" "$PROGRESS_FILE" | head -1 | sed 's/.*: //' | tr -d ' ')
    log "Final status: ${final_status:-UNKNOWN}"

    echo "=== Ralph Session Ended $(date) ===" >> .claude/session.log
}

# Handle interrupts
trap 'log_warn "Interrupted. Progress saved in $PROGRESS_FILE"; exit 130' INT TERM

# Run
main "$@"
