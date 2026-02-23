#!/usr/bin/env bash
# PreToolUse(Grep) hook: Remind to use deps-query.py when grepping for
# import/consumer patterns and dep maps are configured.
#
# This hook does NOT block — it only injects a reminder via additionalContext.
# It fires when the grep pattern looks like an import/consumer search
# (import, from, require) on TypeScript files.
#
# Input: JSON on stdin with tool_name, tool_input (pattern, type, glob), cwd

set -euo pipefail

INPUT=$(cat)

# Extract grep pattern and file type/glob filters
read -r PATTERN FILE_TYPE FILE_GLOB <<< "$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
ti = data.get('tool_input', {})
print(ti.get('pattern', ''), ti.get('type', ''), ti.get('glob', ''))
" <<< "$INPUT" 2>/dev/null)" || exit 0

# Quick exit: only care about patterns that look like import/consumer searches
# Match: import, from, require — common patterns when searching for consumers
case "$PATTERN" in
  *import*|*from\ *|*from\\s*|*require*|*"from ["*|*"from '"*)
    ;;
  *)
    exit 0
    ;;
esac

# Quick exit: only care about TypeScript-related searches
case "${FILE_TYPE}${FILE_GLOB}" in
  *ts*|*tsx*|"")
    # Empty type+glob means searching all files, which includes TS — proceed
    ;;
  *)
    exit 0
    ;;
esac

# Check if dep maps are configured
source "${BASH_SOURCE[0]%/*}/lib/find-root.sh"

CWD=$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('cwd', ''))
" <<< "$INPUT" 2>/dev/null) || true

PROJECT_ROOT="$(find_project_root "${CWD:-$PWD}")"
CONFIG_FILE="$PROJECT_ROOT/.claude/look-before-you-leap.local.md"

[ -f "$CONFIG_FILE" ] || exit 0

# Check if dep_maps with modules is configured (use read-config.py via subprocess)
LIB_DIR="${BASH_SOURCE[0]%/*}/lib"
has_dep_maps=$(python3 -c "
import json, subprocess, sys
result = subprocess.run(
    [sys.executable, '$LIB_DIR/read-config.py', '$PROJECT_ROOT'],
    capture_output=True, text=True
)
config = json.loads(result.stdout) if result.stdout.strip() else {}
dm = config.get('dep_maps', {})
modules = dm.get('modules', [])
print('yes' if modules else 'no')
" 2>/dev/null) || true

# If no dep maps or parse failed, nothing to remind about
if [ "$has_dep_maps" != "yes" ]; then
  exit 0
fi

# Dep maps ARE configured and the pattern looks like an import/consumer search.
# Inject a reminder (do NOT block).
PLUGIN_ROOT="$(cd "${BASH_SOURCE[0]%/*}/.." && pwd)"
SCRIPTS_DIR="${PLUGIN_ROOT}/skills/look-before-you-leap/scripts"

python3 << PYEOF
import json, sys

output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": (
            "REMINDER: Dep maps are configured for this project. "
            "You MUST use deps-query.py instead of grepping for import/consumer patterns. "
            "Run: python3 ${SCRIPTS_DIR}/deps-query.py ${PROJECT_ROOT} <file_path>\n"
            "Grep is only for non-TypeScript files, string references (config keys, env vars), "
            "or projects without dep maps."
        )
    }
}
json.dump(output, sys.stdout)
PYEOF
