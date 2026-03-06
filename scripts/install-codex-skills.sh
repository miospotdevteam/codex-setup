#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIR="$ROOT_DIR/codex-skills"
DST_DIR="$HOME/.codex/skills"

if [ ! -d "$SRC_DIR" ]; then
  echo "Missing source directory: $SRC_DIR"
  exit 1
fi

mkdir -p "$DST_DIR"

for skill in "$SRC_DIR"/lbyl-*; do
  [ -d "$skill" ] || continue
  name="$(basename "$skill")"
  rm -rf "$DST_DIR/$name"
  cp -R "$skill" "$DST_DIR/$name"
  echo "Installed $name"
done

echo "Done. Skills installed to $DST_DIR"
