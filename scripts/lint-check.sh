#!/bin/bash
# Run linting based on detected project type
# Called after file edits

set -e

# Detect and run appropriate linter
if [[ -f "pyproject.toml" ]]; then
  # Python project
  if command -v uv &>/dev/null; then
    uv run ruff check . --fix 2>/dev/null || true
    uv run ruff format . 2>/dev/null || true
  fi
elif [[ -f "package.json" ]]; then
  # Node.js project
  if command -v npx &>/dev/null; then
    # Run eslint if configured
    if [[ -f ".eslintrc.json" || -f ".eslintrc.js" || -f "eslint.config.js" ]]; then
      npx eslint --fix . 2>/dev/null || true
    fi
    # Run prettier if configured
    if [[ -f ".prettierrc" || -f ".prettierrc.json" || -f "prettier.config.js" ]]; then
      npx prettier --write . 2>/dev/null || true
    fi
  fi
elif [[ -f "Cargo.toml" ]]; then
  # Rust project
  cargo fmt 2>/dev/null || true
  cargo clippy --fix --allow-dirty 2>/dev/null || true
elif [[ -f "go.mod" ]]; then
  # Go project
  gofmt -w . 2>/dev/null || true
  go vet ./... 2>/dev/null || true
fi

exit 0
