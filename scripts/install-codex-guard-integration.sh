#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_PATH="${CODEX_CONFIG_PATH:-$HOME/.codex/config.toml}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
GUARD_PATH="$ROOT_DIR/codex-guard/guard.py"

resolve_cmd() {
  local cmd="$1"
  if [ -x "$cmd" ]; then
    printf '%s\n' "$cmd"
    return 0
  fi
  command -v "$cmd" 2>/dev/null || return 1
}

PYTHON_CMD="$(resolve_cmd "$PYTHON_BIN")" || {
  echo "Missing required command: $PYTHON_BIN" >&2
  exit 1
}

if [ ! -f "$GUARD_PATH" ]; then
  echo "Missing codex guard: $GUARD_PATH" >&2
  exit 1
fi

mkdir -p "$(dirname "$CONFIG_PATH")"
touch "$CONFIG_PATH"

"$PYTHON_CMD" - "$CONFIG_PATH" "$PYTHON_CMD" "$GUARD_PATH" <<'PYEOF'
from __future__ import annotations

import re
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
python_cmd = sys.argv[2]
guard_path = sys.argv[3]


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


desired = f'{python_cmd} {guard_path} setup'
escaped = toml_escape(desired)
line = f'setup = "{escaped}"'
text = config_path.read_text(encoding="utf-8")

section_re = re.compile(r"(?ms)^\[sandbox\]\n(?P<body>(?:(?!^\[).*\n?)*)")
match = section_re.search(text)

if match:
    body = match.group("body")
    if re.search(r"(?m)^setup\s*=", body):
        new_body = re.sub(r"(?m)^setup\s*=.*$", line, body, count=1)
    else:
        separator = "" if not body or body.endswith("\n") else "\n"
        new_body = body + separator + line + "\n"
    text = text[: match.start("body")] + new_body + text[match.end("body") :]
else:
    if text and not text.endswith("\n"):
        text += "\n"
    if text:
        text += "\n"
    text += "[sandbox]\n" + line + "\n"

config_path.write_text(text, encoding="utf-8")
print(config_path)
PYEOF

printf 'Configured Codex sandbox setup for codex-guard in %s\n' "$CONFIG_PATH"
