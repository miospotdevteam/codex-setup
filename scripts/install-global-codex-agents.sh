#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
AGENTS_PATH="${CODEX_AGENTS_PATH:-$CODEX_HOME_DIR/AGENTS.md}"

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

mkdir -p "$(dirname "$AGENTS_PATH")"

"$PYTHON_CMD" - "$AGENTS_PATH" <<'PYEOF'
from __future__ import annotations

import re
import sys
from pathlib import Path

agents_path = Path(sys.argv[1])
begin = "<!-- BEGIN CODEX-SETUP GLOBAL DEFAULTS -->"
end = "<!-- END CODEX-SETUP GLOBAL DEFAULTS -->"
block = f"""{begin}
# Global Codex Defaults

These defaults apply machine-wide. Follow the nearer project or nested
`AGENTS.md` file when one exists.

## Default Codex Workflow

- For any Codex repo invocation, default to `lbyl-conductor` and `lbyl-engineering-discipline`.
- Explore first and do that exploration in parallel when possible.
- Before non-trivial source edits, write `.temp/plan-mode/active/<plan-name>/plan.json`
  and `masterPlan.md`.
- If the repo has `codex-guard`, check `python3 codex-guard/guard.py status` before execution.
  If `sessionSetup` is missing, stop and repair the runtime setup before claiming LBYL compliance.
- Keep the main Codex session lean: use it as the conductor and spawn
  sub-agents for non-trivial exploration, audits, and disjoint implementation
  lanes when that reduces context pressure.
- If context gets crowded, checkpoint the active plan to disk and continue from
  a fresh Codex session instead of relying on an in-session `/clear`.
- Use Claude only for materially visual frontend implementation and independent
  verification through `claude-bridge` when that workflow is available.
- Verify with the project's real lint, typecheck, and relevant tests before
  declaring the task done.
{end}
"""

text = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
pattern = re.compile(
    rf"(?ms)^[ \t]*{re.escape(begin)}\n.*?^[ \t]*{re.escape(end)}\n?"
)

if pattern.search(text):
    updated = pattern.sub(block + "\n", text, count=1)
else:
    updated = text
    if updated and not updated.endswith("\n"):
        updated += "\n"
    if updated:
        updated += "\n"
    updated += block + "\n"

agents_path.write_text(updated, encoding="utf-8")
print(agents_path)
PYEOF

printf 'Configured global Codex defaults in %s\n' "$AGENTS_PATH"
