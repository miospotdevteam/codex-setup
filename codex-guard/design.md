# Codex Guard

`codex-guard/guard.py` is the Codex-native enforcement layer for this repo.
It exists because Codex does not have the Claude plugin's lifecycle hooks, but
the discipline model still needs something stronger than skill text alone.

## What It Enforces

The implemented guard covers the highest-value parity rules:

1. Plan must exist and pass validation before execution starts.
2. Source files are read-only by default at session start.
3. Guard runtime activation is recorded on disk at session start.
4. Only one plan step is writable at a time.
5. Step completion is blocked without a recorded Claude PASS verdict when
   `claudeVerify: true`.
6. Session start can resume an in-progress step automatically.
7. Checkpoints and bypasses are audited on disk.

The guard preserves intent rather than copying Claude hook mechanics.

## Command Surface

```bash
python3 codex-guard/guard.py setup
python3 codex-guard/guard.py validate-plan
python3 codex-guard/guard.py begin-step <step-id>
python3 codex-guard/guard.py checkpoint
python3 codex-guard/guard.py complete-step <step-id>
python3 codex-guard/guard.py status
```

### `setup`

Runs from Codex `config.toml` via `[sandbox].setup`.

Behavior:
- locks all git-tracked files with write bits removed
- clears stale validation state for the new session
- writes `.temp/plan-mode/guard/.guard-session` so later commands can prove
  the guard runtime was actually established for this repo
- if the active plan has an `in_progress` step, re-unlocks that step's files
- records the resumed step in `.temp/plan-mode/guard/.guard-state`

Typical output:
- `All source files locked. Create a plan to begin.`
- `Resumed step 2: Implement guard — 4 file(s) unlocked`

### `validate-plan`

Checks the active plan before execution:
- `.guard-session` exists for the current repo, proving `setup` ran
- active `plan.json` exists
- `review.status` is `approved` or `skipped`
- skipped review has a non-empty `skipReason`
- every step has the fields the Codex workflow depends on:
  `id`, `title`, `status`, `files`, `acceptanceCriteria`, `progress`,
  `executor`, `claudeVerify`

On success it writes `.temp/plan-mode/guard/.guard-validated`.
If the runtime marker is missing, validation fails because the session cannot
truthfully claim LBYL-compliant guarded execution.

### `begin-step <step-id>`

Execution gate for a specific step:
- refuses to run if `validate-plan` has not passed for the current plan
- refuses to unlock a second step while another is active
- unlocks only the step's `files`
- records unlock state in `.temp/plan-mode/guard/.guard-state`
- marks the step `in_progress` through `plan_utils.py`

### `checkpoint`

Audit checkpoint during execution:
- requires an unlocked step
- logs a checkpoint event to `.temp/plan-mode/guard/.guard-audit.log`
- flags when unlocked files are newer than `plan.json`

This is intentionally lightweight. The discipline still depends on the
operator updating the plan every 2-3 file edits.

### `complete-step <step-id>`

Completion gate:
- requires a non-empty step `result`
- if `claudeVerify: true`, requires a Claude PASS verdict in `result`
- audits writable git-tracked files outside the step's file list
- re-locks the step files
- marks the step `done`
- clears `.temp/plan-mode/guard/.guard-state`

The current PASS detector looks for `PASS` near `Claude` or `claude-bridge`
in the result text. The recommended result shape is:

```text
### Verdict
Claude: PASS
```

### `status`

Prints JSON status for the current project:
- tracked file count
- validated plan marker
- unlocked step state
- last audit event

## State Files

The guard writes project-local state:

```text
<project-root>/
└── .temp/plan-mode/
    ├── active/<plan>/plan.json
    └── guard/
        ├── .guard-state
        ├── .guard-session
        ├── .guard-audit.log
        └── .guard-validated
```

.temp/plan-mode/guard/.guard-session example:

```json
{
  "setupAt": "2026-04-01T15:14:00+00:00",
  "projectRoot": "/abs/path/to/repo",
  "triggeredFrom": "/abs/path/to/repo"
}
```

`.temp/plan-mode/guard/.guard-state` example:

```json
{
  "plan_path": "/abs/path/.temp/plan-mode/active/demo/plan.json",
  "step_id": 2,
  "files": ["src/app.ts", "tests/app.test.ts"],
  "unlocked_at": "2026-03-24T20:04:51+00:00"
}
```

`.temp/plan-mode/guard/.guard-audit.log` is newline-delimited JSON:

```jsonl
{"event":"validate_plan","ts":"...","plan":"/abs/path/.../plan.json"}
{"event":"begin_step","ts":"...","step":2,"files":4}
{"event":"checkpoint","ts":"...","step":2,"stale_plan":false}
{"event":"bypass_detected","ts":"...","step":2,"extra_writable":["src/unexpected.ts"]}
{"event":"complete_step","ts":"...","step":2,"extras":[]}
```

## Install Integration

`scripts/install-codex-guard-integration.sh` writes this into
`~/.codex/config.toml` by default:

```toml
[sandbox]
setup = "python3 /absolute/path/to/codex-setup/codex-guard/guard.py setup"
```

The main installer calls it automatically unless
`SKIP_CODEX_GUARD_INSTALL=1` is set.

## What It Does Not Do

The guard intentionally does not try to mirror every Claude hook literally.

Not implemented as hard enforcement:
- deps-query grep wrappers
- sub-agent prompt injection
- signed approval / bypass receipts
- destructive-command interception outside the file-lock model

Those areas remain soft guidance or future work on the Codex side. The current
implementation focuses on the highest-value runtime gap: turning planning and
verification rules into a real write-access gate.

## Why This Shape

The upstream Claude plugin uses hooks, receipts, and command interception.
Codex gives us different primitives. The guard therefore uses:
- file locking as the default-deny mechanism
- explicit step unlock/lock commands
- plan metadata validation
- audit logs
- Codex config setup integration

That keeps the discipline model intact without pretending Codex has the same
runtime hook surface Claude does.
