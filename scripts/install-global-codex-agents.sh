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
- The full LBYL flow is MANDATORY, REQUIRED, and NON-NEGOTIABLE for execution.
  No part of it may be skipped, weakened, deferred, or treated as advisory.
- Treat the installed LBYL skill pack as the baseline operating mode. Do not wait
  for the user to mention `lbyl-*` skills before following them.
- Exploration MUST happen before planning, execution, or source edits.
- Exploration MUST be parallelized. For non-trivial work, parallel exploration
  with Claude as well as Codex is REQUIRED whenever `claude-bridge` is available.
  Do not proceed with solo or serial exploration in that case.
- Proactively invoke the exact `lbyl-*` skill that matches the task shape:
  `lbyl-writing-plans` for non-trivial planning, `lbyl-systematic-debugging`
  for failures, `lbyl-refactoring` for cross-file restructuring, and
  `lbyl-agent-setup` for repo guidance updates.
- Before non-trivial source edits, write `.temp/plan-mode/active/<plan-name>/plan.json`
  and `masterPlan.md`.
- When a plan is large or high-blast-radius, materially revised, fragile in
  sequencing or verification, or the user asks for extra pressure-testing, run
  Claude `attack_plan` approval before Orbit review or execution.
- If the repo has `codex-guard`, check `python3 codex-guard/guard.py status` before execution.
  If `sessionSetup` is missing, stop and repair the runtime setup before claiming LBYL compliance.
- Keep the main Codex session lean: use it as the conductor and spawn
  sub-agents for non-trivial exploration, audits, and disjoint implementation
  lanes when that reduces context pressure.
- If context gets crowded, checkpoint the active plan to disk and continue from
  a fresh Codex session instead of relying on an in-session `/clear`.
- Use Claude only for materially visual frontend implementation and independent
  verification through `claude-bridge` when that workflow is available.
- When executing a plan, every step MUST be verified with Claude and MUST have
  an explicit Claude PASS verdict before it is marked done.
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
