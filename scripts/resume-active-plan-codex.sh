#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLAN_UTIL="$ROOT_DIR/.temp/plan-mode/scripts/plan_utils.py"
CODEX_BIN="${CODEX_BIN:-codex}"
PRINT_ONLY="${PRINT_ONLY:-0}"

usage() {
  cat <<'EOF'
Usage: resume-active-plan-codex.sh [--print-command] [project_root]

Starts a fresh Codex session from the most recently active persistent plan in
the target project. This is the supported replacement for an in-session
context-clear flow.
EOF
}

resolve_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

PROJECT_ROOT="${PWD}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --print-command)
      PRINT_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      PROJECT_ROOT="$1"
      shift
      ;;
  esac
done

if [ ! -f "$PLAN_UTIL" ]; then
  echo "Missing plan utility: $PLAN_UTIL" >&2
  exit 1
fi

resolve_cmd python3
resolve_cmd "$CODEX_BIN"

PLAN_PATH="$(python3 "$PLAN_UTIL" find-active "$PROJECT_ROOT")"
if [ -z "$PLAN_PATH" ]; then
  echo "No active plan found under $PROJECT_ROOT/.temp/plan-mode/active" >&2
  exit 1
fi

NEXT_STEP_JSON="$(python3 "$PLAN_UTIL" next-step "$PLAN_PATH")"
PLAN_DIR="$(dirname "$PLAN_PATH")"

PLAN_CONTEXT="$(
  python3 - "$PLAN_PATH" "$NEXT_STEP_JSON" <<'PY'
import json
import sys
from pathlib import Path

plan_path = Path(sys.argv[1])
step = json.loads(sys.argv[2])
plan = json.loads(plan_path.read_text())

title = plan.get("title") or plan.get("name") or plan_path.parent.name
step_id = step.get("id")
step_title = step.get("title") or "unknown"

if step_id is None:
    step_summary = "No pending step remains; verify completion and close the plan if appropriate."
else:
    step_summary = f"Continue from step {step_id}: {step_title}."

prompt = (
    f"Resume work from the active persistent plan '{title}'. "
    f"First read {plan_path} plus the sibling progress.json and discovery.md if present. "
    f"{step_summary} Keep the main Codex session as the conductor, delegate bounded non-trivial work when useful, "
    "and checkpoint back to disk before context gets crowded. Do not assume an in-session /clear exists."
)
print(prompt)
PY
)"

if [ "$PRINT_ONLY" = "1" ]; then
  printf '%q ' "$CODEX_BIN" -C "$PROJECT_ROOT" "$PLAN_CONTEXT"
  printf '\n'
  exit 0
fi

exec "$CODEX_BIN" -C "$PROJECT_ROOT" "$PLAN_CONTEXT"
