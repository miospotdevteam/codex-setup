#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EXT_DIR="$ROOT_DIR/claude-bridge-vscode"
MCP_DIR="$ROOT_DIR/claude-bridge"
SERVER_PATH="$MCP_DIR/server.mjs"
CLAUDE_SUPPORT_DIR="$ROOT_DIR/claude-support/look-before-you-leap"
MCP_NAME="${CLAUDE_BRIDGE_MCP_NAME:-claude-bridge}"
CONFIG_PATH="${CODEX_CONFIG_PATH:-$HOME/.codex/config.toml}"
MCP_STARTUP_TIMEOUT_SEC="${CLAUDE_BRIDGE_MCP_STARTUP_TIMEOUT_SEC:-300}"
MCP_TOOL_TIMEOUT_SEC="${CLAUDE_BRIDGE_MCP_TOOL_TIMEOUT_SEC:-10800}"
CODEX_BIN="${CODEX_BIN:-codex}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NODE_BIN="${NODE_BIN:-node}"
NPM_BIN="${NPM_BIN:-npm}"
CODE_BIN="${CODE_BIN:-code}"

resolve_cmd() {
  local cmd="$1"
  if [ -x "$cmd" ]; then
    printf '%s\n' "$cmd"
    return 0
  fi
  command -v "$cmd" 2>/dev/null || return 1
}

has_newer_inputs() {
  local target="$1"
  shift

  [ -f "$target" ] || return 0

  local path
  for path in "$@"; do
    [ -e "$path" ] || continue
    if find "$path" -type f -newer "$target" -print -quit 2>/dev/null | grep -q .; then
      return 0
    fi
  done

  return 1
}

find_latest_vsix() {
  ls -t "$EXT_DIR"/claude-bridge-vscode-*.vsix 2>/dev/null | head -1 || true
}

CODEX_CMD="$(resolve_cmd "$CODEX_BIN")" || {
  echo "Missing required command: $CODEX_BIN" >&2
  exit 1
}
CLAUDE_CMD="$(resolve_cmd "$CLAUDE_BIN")" || {
  echo "Missing required command: $CLAUDE_BIN" >&2
  echo "Install the Claude CLI and authenticate it before configuring claude-bridge." >&2
  exit 1
}
PYTHON_CMD="$(resolve_cmd "$PYTHON_BIN")" || {
  echo "Missing required command: $PYTHON_BIN" >&2
  exit 1
}
NODE_CMD="$(resolve_cmd "$NODE_BIN")" || {
  echo "Missing required command: $NODE_BIN" >&2
  exit 1
}
NPM_CMD="$(resolve_cmd "$NPM_BIN")" || {
  echo "Missing required command: $NPM_BIN" >&2
  exit 1
}
CODE_CMD="$(resolve_cmd "$CODE_BIN")" || {
  echo "Missing required command: $CODE_BIN" >&2
  echo "The claude-bridge integration requires the VS Code CLI so the live brainstorming extension can be installed." >&2
  exit 1
}

if [ ! -f "$SERVER_PATH" ]; then
  echo "Missing claude-bridge server: $SERVER_PATH" >&2
  exit 1
fi

if [ ! -f "$MCP_DIR/package.json" ]; then
  echo "Missing claude-bridge package.json in $MCP_DIR" >&2
  exit 1
fi

if [ ! -f "$EXT_DIR/package.json" ]; then
  echo "Missing claude-bridge extension package.json in $EXT_DIR" >&2
  exit 1
fi

printf 'Using claude-bridge repo: %s\n' "$ROOT_DIR"
printf 'Using Claude CLI: %s\n' "$CLAUDE_CMD"
if [ -d "$CLAUDE_SUPPORT_DIR" ]; then
  printf 'Using repo-local Claude support bundle: %s\n' "$CLAUDE_SUPPORT_DIR"
else
  printf 'Repo-local Claude support bundle not found yet: %s\n' "$CLAUDE_SUPPORT_DIR"
  printf 'claude-bridge will rely on CLAUDE_BRIDGE_PLUGIN_DIR only if you override it manually.\n'
fi

if [ ! -d "$MCP_DIR/node_modules" ]; then
  (cd "$MCP_DIR" && "$NPM_CMD" install)
else
  printf 'claude-bridge MCP dependencies are current: %s\n' "$MCP_DIR/node_modules"
fi

if [ ! -d "$EXT_DIR/node_modules" ]; then
  (cd "$EXT_DIR" && "$NPM_CMD" install)
fi

BUILD_TARGET="$EXT_DIR/out/extension.js"
BUILD_INPUTS=(
  "$EXT_DIR/src"
  "$EXT_DIR/esbuild.mjs"
  "$EXT_DIR/package.json"
  "$EXT_DIR/tsconfig.json"
)

if has_newer_inputs "$BUILD_TARGET" "${BUILD_INPUTS[@]}"; then
  (cd "$EXT_DIR" && "$NPM_CMD" run build)
else
  printf 'claude-bridge VS Code bundle is current: %s\n' "$BUILD_TARGET"
fi

if [ ! -f "$BUILD_TARGET" ]; then
  echo "claude-bridge extension build did not produce $BUILD_TARGET" >&2
  exit 1
fi

latest_vsix="$(find_latest_vsix)"
if [ -z "$latest_vsix" ] || has_newer_inputs "$latest_vsix" "${BUILD_INPUTS[@]}" "$EXT_DIR/out"; then
  (cd "$EXT_DIR" && "$NPM_CMD" run package)
  latest_vsix="$(find_latest_vsix)"
fi

if [ -z "$latest_vsix" ]; then
  echo "claude-bridge VSIX was not produced." >&2
  exit 1
fi

"$CODE_CMD" --install-extension "$latest_vsix" --force >/dev/null
printf 'Installed VS Code extension from %s\n' "$latest_vsix"

"$CODEX_CMD" mcp remove "$MCP_NAME" >/dev/null 2>&1 || true
"$CODEX_CMD" mcp add "$MCP_NAME" -- "$NODE_CMD" "$SERVER_PATH" >/dev/null
mkdir -p "$(dirname "$CONFIG_PATH")"
touch "$CONFIG_PATH"
"$PYTHON_CMD" - "$CONFIG_PATH" "$MCP_NAME" "$MCP_STARTUP_TIMEOUT_SEC" "$MCP_TOOL_TIMEOUT_SEC" <<'PYEOF'
from __future__ import annotations

import re
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
server_name = sys.argv[2]
startup_timeout = int(sys.argv[3])
tool_timeout = int(sys.argv[4])

text = config_path.read_text(encoding="utf-8")
section_re = re.compile(
    rf"(?m)^\[mcp_servers\.{re.escape(server_name)}\]\n(?P<body>(?:^(?!\[).*(?:\n|$))*)"
)
match = section_re.search(text)
if not match:
    raise SystemExit(f"MCP server section not found: [mcp_servers.{server_name}]")

body = match.group("body")

def upsert_timeout(body: str, key: str, value: int) -> str:
    line = f"{key} = {value}"
    pattern = re.compile(rf"(?m)^{re.escape(key)}\s*=.*$")
    if pattern.search(body):
        return pattern.sub(line, body, count=1)
    separator = "" if not body or body.endswith("\n") else "\n"
    return body + separator + line + "\n"

body = upsert_timeout(body, "startup_timeout_sec", startup_timeout)
body = upsert_timeout(body, "tool_timeout_sec", tool_timeout)
text = text[: match.start("body")] + body + text[match.end("body") :]
config_path.write_text(text, encoding="utf-8")
PYEOF
printf 'Configured Codex MCP server %s\n' "$MCP_NAME"
printf 'Configured claude-bridge MCP timeouts: startup=%ss tool=%ss\n' "$MCP_STARTUP_TIMEOUT_SEC" "$MCP_TOOL_TIMEOUT_SEC"
"$CODEX_CMD" mcp get "$MCP_NAME"
