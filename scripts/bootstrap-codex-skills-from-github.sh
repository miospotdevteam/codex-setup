#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/miospotdevteam/codex-setup.git}"
BRANCH="${BRANCH:-main}"
CHECKOUT_DIR="${CHECKOUT_DIR:-$HOME/Projects/codex-setup}"
SKIP_PULL="${SKIP_PULL:-0}"

resolve_cmd() {
  command -v "$1" 2>/dev/null || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

ensure_checkout_parent() {
  local parent
  parent="$(dirname "$CHECKOUT_DIR")"
  mkdir -p "$parent"
}

validate_existing_checkout() {
  if [ ! -d "$CHECKOUT_DIR/.git" ]; then
    echo "Target exists but is not a git checkout: $CHECKOUT_DIR" >&2
    echo "Choose a different CHECKOUT_DIR or convert this directory into a clone of $REPO_URL." >&2
    exit 1
  fi

  local existing_remote
  existing_remote="$(git -C "$CHECKOUT_DIR" remote get-url origin 2>/dev/null || true)"
  if [ -z "$existing_remote" ]; then
    echo "Existing checkout is missing an origin remote: $CHECKOUT_DIR" >&2
    exit 1
  fi

  if [ "$existing_remote" != "$REPO_URL" ]; then
    echo "Existing checkout origin does not match REPO_URL." >&2
    echo "  checkout: $CHECKOUT_DIR" >&2
    echo "  origin:   $existing_remote" >&2
    echo "  expected: $REPO_URL" >&2
    exit 1
  fi
}

clone_or_update_checkout() {
  if [ ! -e "$CHECKOUT_DIR" ]; then
    ensure_checkout_parent
    git clone --branch "$BRANCH" "$REPO_URL" "$CHECKOUT_DIR"
    return 0
  fi

  validate_existing_checkout

  if [ "$SKIP_PULL" = "1" ]; then
    echo "Skipping git pull (SKIP_PULL=1)"
    return 0
  fi

  git -C "$CHECKOUT_DIR" fetch origin "$BRANCH" --prune
  git -C "$CHECKOUT_DIR" checkout "$BRANCH"
  git -C "$CHECKOUT_DIR" pull --ff-only origin "$BRANCH"
}

main() {
  resolve_cmd git
  resolve_cmd bash

  clone_or_update_checkout

  local installer
  installer="$CHECKOUT_DIR/scripts/install-codex-skills.sh"
  if [ ! -f "$installer" ]; then
    echo "Installer not found in checkout: $installer" >&2
    exit 1
  fi

  echo "Using checkout: $CHECKOUT_DIR"
  echo "Repo URL: $REPO_URL"
  echo "Branch: $BRANCH"

  (
    cd "$CHECKOUT_DIR"
    bash "$installer"
  )
}

main "$@"
