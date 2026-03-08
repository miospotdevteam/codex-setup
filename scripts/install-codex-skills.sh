#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC_DIRS=(
  "$ROOT_DIR/codex-skills"
  "$ROOT_DIR/look-before-you-leap/skills"
)
DST_DIR="$HOME/.codex/skills"
MAX_DESCRIPTION_LENGTH=1024
ORBIT_INSTALLER="$ROOT_DIR/scripts/install-orbit-codex-integration.sh"

find_orbit_dir() {
  if [ -n "${ORBIT_DIR:-}" ] && [ -d "$ORBIT_DIR" ]; then
    printf '%s\n' "$ORBIT_DIR"
    return 0
  fi

  local candidate
  for candidate in "$HOME/Projects/orbit" "$HOME/projects/orbit"; do
    if [ -d "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

description_override_for_skill() {
  case "$1" in
    engineering-discipline)
      printf '%s\n' "Engineering discipline for coding tasks that touch source files. Explore before edits, track blast radius, avoid type-safety shortcuts, verify with typecheck, lint, and tests, and never silently drop requested scope."
      ;;
    immersive-frontend)
      printf '%s\n' "Build immersive, motion-first web experiences with WebGL, Three.js, R3F, GSAP ScrollTrigger, shaders, and scroll-driven 3D choreography. Use for cinematic, canvas-heavy frontend work beyond standard UI layouts."
      ;;
    react-native-mobile)
      printf '%s\n' "Build premium React Native mobile apps with native-feeling motion, gestures, haptics, platform conventions, accessibility, and performance discipline. Use for Expo or React Native product work targeting iOS and Android."
      ;;
    *)
      return 1
      ;;
  esac
}

sanitize_skill_metadata() {
  local skill_dir="$1"
  local name="$2"
  local skill_file="$skill_dir/SKILL.md"
  local override=""
  local desc_length=""

  [ -f "$skill_file" ] || return 0

  if override="$(description_override_for_skill "$name")"; then
    CODEX_DESC="$override" perl -0pi -e 's/^description: ".*"$/description: "$ENV{CODEX_DESC}"/m' "$skill_file"
  fi

  desc_length="$(perl -ne 'if(/^description: /){$s=$_; $s =~ s/^description: //; chomp $s; print length($s); exit}' "$skill_file")"
  if [ -n "$desc_length" ] && [ "$desc_length" -gt "$MAX_DESCRIPTION_LENGTH" ]; then
    echo "Installed skill has an over-limit description ($desc_length chars): $skill_file" >&2
    exit 1
  fi
}

should_install_skill() {
  local src_dir="$1"
  local name="$2"

  if [ "$src_dir" = "$ROOT_DIR/look-before-you-leap/skills" ] && [ "$name" = "frontend-design" ]; then
    return 1
  fi

  return 0
}

for src_dir in "${SRC_DIRS[@]}"; do
  if [ ! -d "$src_dir" ]; then
    echo "Missing source directory: $src_dir"
    exit 1
  fi
done

mkdir -p "$DST_DIR"

for src_dir in "${SRC_DIRS[@]}"; do
  for skill in "$src_dir"/*; do
    [ -d "$skill" ] || continue
    name="$(basename "$skill")"
    if ! should_install_skill "$src_dir" "$name"; then
      rm -rf "$DST_DIR/$name"
      echo "Skipped $name"
      continue
    fi
    rm -rf "$DST_DIR/$name"
    cp -R "$skill" "$DST_DIR/$name"
    sanitize_skill_metadata "$DST_DIR/$name" "$name"
    echo "Installed $name"
  done
done

if [ "${SKIP_ORBIT_INSTALL:-0}" = "1" ]; then
  echo "Skipped Orbit integration (SKIP_ORBIT_INSTALL=1)"
else
  if orbit_dir="$(find_orbit_dir)"; then
    ORBIT_DIR="$orbit_dir" bash "$ORBIT_INSTALLER"
  else
    echo "Skipped Orbit integration (Orbit repo not found; set ORBIT_DIR=/absolute/path/to/orbit to enable it)"
  fi
fi

echo "Done. Repo skills installed to $DST_DIR"
