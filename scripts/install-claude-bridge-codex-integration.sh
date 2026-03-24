#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EXT_DIR="$ROOT_DIR/claude-bridge-vscode"
MCP_DIR="$ROOT_DIR/claude-bridge"
SERVER_PATH="$MCP_DIR/server.mjs"
MCP_NAME="${CLAUDE_BRIDGE_MCP_NAME:-claude-bridge}"
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
printf 'Configured Codex MCP server %s\n' "$MCP_NAME"
"$CODEX_CMD" mcp get "$MCP_NAME"
