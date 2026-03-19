#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/log-usage-error.sh "short title"

Environment:
  LBYL_CODEX_SETUP_REPO  Optional absolute path to the codex-setup checkout.
                         Defaults to the repo containing this script.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -lt 1 ]; then
  usage >&2
  exit 1
fi

TITLE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="${LBYL_CODEX_SETUP_REPO:-$DEFAULT_REPO_ROOT}"

if [ ! -d "$REPO_ROOT" ]; then
  echo "Repo root does not exist: $REPO_ROOT" >&2
  exit 1
fi

TARGET_DIR="$REPO_ROOT/usage-errors"
mkdir -p "$TARGET_DIR"

TIMESTAMP="$(date '+%Y-%m-%d-%H%M%S')"
DISPLAY_DATE="$(date '+%Y-%m-%d %H:%M:%S %Z')"
SOURCE_REPO="$(pwd)"
MODEL="${OPENAI_MODEL:-unknown}"

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-{2,}/-/g'
}

SLUG="$(slugify "$TITLE")"
if [ -z "$SLUG" ]; then
  SLUG="usage-error"
fi

TARGET_FILE="$TARGET_DIR/$TIMESTAMP-$SLUG.md"

cat > "$TARGET_FILE" <<EOF
# Usage Error: $TITLE

- Date: $DISPLAY_DATE
- Source repo: $SOURCE_REPO
- Skill(s):
- Model: $MODEL
- Codex setup repo: $REPO_ROOT

## What happened

Describe the concrete failure, including what the model did or suggested.

## Expected behavior

Describe what the skill pack should have encouraged instead.

## Why this is a skill issue

Connect the failure to the relevant skill text, reusable snippet, or process.

## Proposed fix

Describe the smallest documentation, process, or tooling change that would
reduce the chance of this happening again.

## Evidence

- Relevant files:
- Relevant prompts or user feedback:
- Verification or reproduction notes:
EOF

printf '%s\n' "$TARGET_FILE"
