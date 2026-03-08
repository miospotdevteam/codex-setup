#!/usr/bin/env bash
set -euo pipefail

DEFAULT_ORBIT_DIR="$HOME/Projects/orbit"
ALT_ORBIT_DIR="$HOME/projects/orbit"
ORBIT_DIR="${ORBIT_DIR:-$DEFAULT_ORBIT_DIR}"
ORBIT_MCP_NAME="${ORBIT_MCP_NAME:-orbit}"
CODEX_BIN="${CODEX_BIN:-codex}"
NODE_BIN="${NODE_BIN:-node}"
NPM_BIN="${NPM_BIN:-npm}"
CODE_BIN="${CODE_BIN:-code}"

if [ ! -d "$ORBIT_DIR" ] && [ -d "$ALT_ORBIT_DIR" ]; then
  ORBIT_DIR="$ALT_ORBIT_DIR"
fi

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
  ls -t "$ORBIT_DIR"/orbit-artifact-review-*.vsix 2>/dev/null | head -1 || true
}

if [ ! -d "$ORBIT_DIR" ]; then
  echo "Orbit repo not found at $ORBIT_DIR" >&2
  echo "Set ORBIT_DIR=/absolute/path/to/orbit to point this installer at your local Orbit repo." >&2
  exit 1
fi

if [ ! -f "$ORBIT_DIR/package.json" ]; then
  echo "Orbit repo at $ORBIT_DIR is missing package.json" >&2
  exit 1
fi

CODEX_CMD="$(resolve_cmd "$CODEX_BIN")" || {
  echo "Missing required command: $CODEX_BIN" >&2
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
CODE_CMD="$(resolve_cmd "$CODE_BIN" || true)"

MCP_SERVER="$ORBIT_DIR/out/mcp-server.js"
BUILD_INPUTS=(
  "$ORBIT_DIR/src"
  "$ORBIT_DIR/esbuild.mjs"
  "$ORBIT_DIR/package.json"
  "$ORBIT_DIR/package-lock.json"
  "$ORBIT_DIR/tsconfig.json"
)

printf 'Using Orbit repo: %s\n' "$ORBIT_DIR"

if has_newer_inputs "$MCP_SERVER" "${BUILD_INPUTS[@]}"; then
  (cd "$ORBIT_DIR" && "$NPM_CMD" run build)
else
  printf 'Orbit MCP bundle is current: %s\n' "$MCP_SERVER"
fi

if [ ! -f "$MCP_SERVER" ]; then
  echo "Orbit MCP server bundle was not produced at $MCP_SERVER" >&2
  exit 1
fi

if [ -n "$CODE_CMD" ]; then
  latest_vsix="$(find_latest_vsix)"
  if [ -z "$latest_vsix" ] || has_newer_inputs "$latest_vsix" "${BUILD_INPUTS[@]}" "$ORBIT_DIR/out"; then
    (cd "$ORBIT_DIR" && "$NPM_CMD" run package)
    latest_vsix="$(find_latest_vsix)"
  else
    printf 'Orbit VSIX is current: %s\n' "$latest_vsix"
  fi

  if [ -n "$latest_vsix" ]; then
    "$CODE_CMD" --install-extension "$latest_vsix" --force >/dev/null
    printf 'Installed VS Code extension from %s\n' "$latest_vsix"
  else
    printf 'Skipping VS Code extension install: no VSIX was produced.\n'
  fi
else
  printf 'Skipping VS Code extension install: code CLI not found.\n'
fi

"$CODEX_CMD" mcp remove "$ORBIT_MCP_NAME" >/dev/null 2>&1 || true
"$CODEX_CMD" mcp add "$ORBIT_MCP_NAME" -- "$NODE_CMD" "$MCP_SERVER" >/dev/null
printf 'Configured Codex MCP server %s\n' "$ORBIT_MCP_NAME"
"$CODEX_CMD" mcp get "$ORBIT_MCP_NAME"
