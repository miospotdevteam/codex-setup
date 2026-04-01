#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
CLAUDE_PLUGINS_DIR="$CLAUDE_DIR/plugins"
INSTALLER="$ROOT_DIR/scripts/install-codex-skills.sh"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/.codex/backups}"
TIMESTAMP="${TIMESTAMP:-$(date +%Y%m%d-%H%M%S)}"
BACKUP_DIR="${BACKUP_DIR:-$BACKUP_ROOT/claude-migration-$TIMESTAMP}"
MIGRATION_SCOPE="${MIGRATION_SCOPE:-all}"
DRY_RUN="${DRY_RUN:-0}"
SKIP_CODEX_REFRESH="${SKIP_CODEX_REFRESH:-0}"

resolve_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

log() {
  printf '%s\n' "$*"
}

run_cmd() {
  if [ "$DRY_RUN" = "1" ]; then
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

run_in_dir() {
  local dir="$1"
  shift
  if [ "$DRY_RUN" = "1" ]; then
    printf 'DRY-RUN: (cd %q &&' "$dir"
    printf ' %q' "$@"
    printf ')\n'
    return 0
  fi
  (
    cd "$dir"
    "$@"
  )
}

warn_cmd() {
  local message="$1"
  shift
  if ! run_cmd "$@"; then
    printf 'Warning: %s\n' "$message" >&2
  fi
}

warn_in_dir() {
  local dir="$1"
  local message="$2"
  shift 2
  if ! run_in_dir "$dir" "$@"; then
    printf 'Warning: %s\n' "$message" >&2
  fi
}

backup_path() {
  local src="$1"
  [ -e "$src" ] || return 0
  local rel="${src#$HOME/}"
  local dest="$BACKUP_DIR/$rel"
  if [ "$DRY_RUN" = "1" ]; then
    printf 'DRY-RUN: backup %q -> %q\n' "$src" "$dest"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  cp -R "$src" "$dest"
}

write_backup_metadata() {
  if [ "$DRY_RUN" = "1" ]; then
    printf 'DRY-RUN: write backup metadata to %q\n' "$BACKUP_DIR/metadata.txt"
    return 0
  fi
  mkdir -p "$BACKUP_DIR"
  cat >"$BACKUP_DIR/metadata.txt" <<EOF
timestamp=$TIMESTAMP
repo_root=$ROOT_DIR
migration_scope=$MIGRATION_SCOPE
skip_codex_refresh=$SKIP_CODEX_REFRESH
EOF
}

collect_installs() {
  local state_file="$CLAUDE_PLUGINS_DIR/installed_plugins.json"
  [ -f "$state_file" ] || return 0
  python3 - "$state_file" "$MIGRATION_SCOPE" <<'PY'
import json
import sys
from pathlib import Path

state_path = Path(sys.argv[1])
scope = sys.argv[2]
data = json.loads(state_path.read_text())

def wanted(plugin_key: str) -> bool:
    if scope == "all":
        return True
    if scope == "legacy-lbyl":
        return plugin_key.startswith("look-before-you-leap@claude-code-setup")
    raise SystemExit(f"Unsupported MIGRATION_SCOPE: {scope}")

for plugin_key, installs in data.get("plugins", {}).items():
    if not wanted(plugin_key):
        continue
    for install in installs:
        print(
            "\t".join(
                [
                    install.get("scope", "user"),
                    plugin_key,
                    install.get("projectPath", ""),
                ]
            )
        )
PY
}

collect_marketplaces() {
  local state_file="$CLAUDE_PLUGINS_DIR/known_marketplaces.json"
  [ -f "$state_file" ] || return 0
  python3 - "$state_file" "$MIGRATION_SCOPE" <<'PY'
import json
import sys
from pathlib import Path

state_path = Path(sys.argv[1])
scope = sys.argv[2]
data = json.loads(state_path.read_text())

for name in sorted(data):
    if scope == "all":
        print(name)
    elif scope == "legacy-lbyl" and name == "claude-code-setup":
        print(name)
PY
}

prune_state_files() {
  local installed="$CLAUDE_PLUGINS_DIR/installed_plugins.json"
  local marketplaces="$CLAUDE_PLUGINS_DIR/known_marketplaces.json"
  [ -d "$CLAUDE_PLUGINS_DIR" ] || return 0
  if [ "$DRY_RUN" = "1" ]; then
    printf 'DRY-RUN: prune residual plugin state in %q for scope %q\n' "$CLAUDE_PLUGINS_DIR" "$MIGRATION_SCOPE"
    return 0
  fi
  python3 - "$installed" "$marketplaces" "$MIGRATION_SCOPE" <<'PY'
import json
import sys
from pathlib import Path

installed_path = Path(sys.argv[1])
marketplaces_path = Path(sys.argv[2])
scope = sys.argv[3]

def wants_plugin(plugin_key: str) -> bool:
    if scope == "all":
        return True
    return plugin_key.startswith("look-before-you-leap@claude-code-setup")

def wants_marketplace(name: str) -> bool:
    if scope == "all":
        return True
    return name == "claude-code-setup"

if installed_path.exists():
    installed = json.loads(installed_path.read_text())
    plugins = installed.get("plugins", {})
    installed["plugins"] = {
        key: value for key, value in plugins.items() if not wants_plugin(key)
    }
    installed_path.write_text(json.dumps(installed, indent=2) + "\n")

if marketplaces_path.exists():
    marketplaces = json.loads(marketplaces_path.read_text())
    marketplaces = {
        key: value for key, value in marketplaces.items() if not wants_marketplace(key)
    }
    marketplaces_path.write_text(json.dumps(marketplaces, indent=2) + "\n")
PY
}

cleanup_paths() {
  local paths=()
  if [ "$MIGRATION_SCOPE" = "all" ]; then
    paths=(
      "$CLAUDE_DIR/look-before-you-leap"
      "$CLAUDE_DIR/look-before-you-leap.local.md"
      "$CLAUDE_PLUGINS_DIR/cache"
      "$CLAUDE_PLUGINS_DIR/data"
      "$CLAUDE_PLUGINS_DIR/marketplaces"
    )
  else
    paths=(
      "$CLAUDE_DIR/look-before-you-leap"
      "$CLAUDE_DIR/look-before-you-leap.local.md"
      "$CLAUDE_PLUGINS_DIR/cache/claude-code-setup"
      "$CLAUDE_PLUGINS_DIR/data/look-before-you-leap-claude-code-setup"
      "$CLAUDE_PLUGINS_DIR/data/look-before-you-leap-inline"
      "$CLAUDE_PLUGINS_DIR/marketplaces/claude-code-setup"
    )
  fi

  local path=""
  for path in "${paths[@]}"; do
    [ -e "$path" ] || continue
    run_cmd rm -rf "$path"
  done

  if [ "$MIGRATION_SCOPE" = "all" ] && [ "$DRY_RUN" != "1" ]; then
    mkdir -p \
      "$CLAUDE_PLUGINS_DIR/cache" \
      "$CLAUDE_PLUGINS_DIR/data" \
      "$CLAUDE_PLUGINS_DIR/marketplaces"
  fi
}

uninstall_plugins() {
  local line=""
  while IFS=$'\t' read -r scope plugin project_path; do
    [ -n "$plugin" ] || continue
    case "$scope" in
      project)
        if [ -n "$project_path" ] && [ -d "$project_path" ]; then
          warn_in_dir "$project_path" \
            "failed to uninstall $plugin from project scope at $project_path; stale entries will be pruned from state files" \
            claude plugin uninstall --scope project "$plugin"
        else
          printf 'Warning: missing project path for %s; pruning residual state instead\n' "$plugin" >&2
        fi
        ;;
      local)
        if [ -n "$project_path" ] && [ -d "$project_path" ]; then
          warn_in_dir "$project_path" \
            "failed to uninstall $plugin from local scope at $project_path; stale entries will be pruned from state files" \
            claude plugin uninstall --scope local "$plugin"
        else
          printf 'Warning: missing local path for %s; pruning residual state instead\n' "$plugin" >&2
        fi
        ;;
      *)
        warn_cmd \
          "failed to uninstall $plugin from $scope scope; stale entries will be pruned from state files" \
          claude plugin uninstall --scope "$scope" "$plugin"
        ;;
    esac
  done < <(collect_installs)
}

remove_marketplaces() {
  local marketplace=""
  while IFS= read -r marketplace; do
    [ -n "$marketplace" ] || continue
    warn_cmd \
      "failed to remove marketplace $marketplace; residual state will be pruned directly" \
      claude plugin marketplace remove "$marketplace"
  done < <(collect_marketplaces)
}

main() {
  case "$MIGRATION_SCOPE" in
    all|legacy-lbyl) ;;
    *)
      echo "Unsupported MIGRATION_SCOPE: $MIGRATION_SCOPE (expected all or legacy-lbyl)" >&2
      exit 1
      ;;
  esac

  resolve_cmd bash
  resolve_cmd python3
  if [ "$DRY_RUN" != "1" ]; then
    resolve_cmd claude
  fi

  if [ ! -f "$INSTALLER" ]; then
    echo "Missing Codex installer: $INSTALLER" >&2
    exit 1
  fi

  log "Codex-first migration"
  log "  repo: $ROOT_DIR"
  log "  scope: $MIGRATION_SCOPE"
  log "  backup: $BACKUP_DIR"
  log "  dry-run: $DRY_RUN"

  write_backup_metadata
  backup_path "$CLAUDE_DIR/settings.json"
  backup_path "$CLAUDE_DIR/CLAUDE.md"
  backup_path "$CLAUDE_DIR/look-before-you-leap"
  backup_path "$CLAUDE_DIR/look-before-you-leap.local.md"
  backup_path "$CLAUDE_PLUGINS_DIR"

  uninstall_plugins
  remove_marketplaces
  prune_state_files
  cleanup_paths

  if [ "$SKIP_CODEX_REFRESH" = "1" ]; then
    log "Skipped Codex refresh (SKIP_CODEX_REFRESH=1)"
  else
    run_in_dir "$ROOT_DIR" bash "$INSTALLER"
  fi

  log "Migration complete."
  if [ "$DRY_RUN" = "1" ]; then
    log "Dry run only: no machine state was changed."
  else
    log "Backup saved to: $BACKUP_DIR"
    log "Post-checks:"
    log "  claude plugin list"
    log "  claude plugin marketplace list"
    log "  codex mcp get claude-bridge"
  fi
}

main "$@"
