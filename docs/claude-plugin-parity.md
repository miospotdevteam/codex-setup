# Claude Plugin Parity

Date: 2026-03-24

This document captures the required gap analysis for making
`codex-setup` the real inverse of the Claude `look-before-you-leap` plugin.
It is intentionally not a file-by-file changelog. The goal is to describe the
discipline model, the actual current Claude behavior, the Codex-side analogue,
and the parts that should not be mirrored literally.

## 1. Intended Model Vs. Actual Current Behavior

### What the Claude plugin is trying to do

The plugin is trying to force an LBYL discipline loop:

1. orient before editing
2. persist discovery and plan state on disk
3. require plan review before execution
4. enforce step ownership and execution routing
5. require independent verification before completion
6. preserve enough state to survive compaction or session handoff
7. log process failures instead of silently tolerating them

### What it actually does today

The current source repo at
`/Users/robertobortolaso/Projects/claude-code-setup/look-before-you-leap`
does more than the vendored tree in this repo suggested:

- hook surface:
  `session-start`, `onboarding`, `capture-user-override`,
  `guard-sensitive-state`, `enforce-step-ownership`,
  `guard-filesystem-mutation`, `track-codex-exploration`,
  `verify-step-completion`, `guard-plan-completion`, and others
- signed receipt system:
  `scripts/receipt_utils.py` plus `hooks/lib/receipt-state.sh`
- direction-locked Codex scripts:
  `run-codex-verify.sh`, `run-codex-implement.sh`,
  `write-claude-verify-receipt.sh`
- explicit Codex dispatch skill:
  `skills/codex-dispatch/SKILL.md`
- test coverage for the newer enforcement model:
  shell and Python tests under `tests/`

### What the vendored tree in this repo actually had before this parity work

Before this update, the vendored `look-before-you-leap/` tree was behind the
actual source repo in exactly the behavior-defining areas above. That meant the
Codex repo could not honestly reason about “what the plugin does today” using
its own vendored copy alone.

### What the Codex repo actually had before this parity work

Before this update, `codex-setup` had:

- strong skill text
- plan persistence guidance
- Orbit and `claude-bridge` install wiring
- an unimplemented `codex-guard/design.md`

It did not have:

- a runnable Codex guard
- install wiring for guard setup in Codex config
- a tracked parity map
- a synced current upstream snapshot

## 2. Claude-Specific Mechanisms Vs. Codex-Native Analogues

| Claude plugin capability | Current Claude mechanism | Codex-native equivalent before this work | Gap | Codex-native decision |
|---|---|---|---|---|
| Session-start enforcement | Claude `SessionStart` hook | Skill text only | High | Install `codex-guard` through Codex `[sandbox].setup` so session start locks files and resumes in-progress steps |
| Plan-before-edit gate | `PreToolUse` hook on `Edit|Write|Bash` | Process guidance only | High | `guard.py setup` locks tracked files; `begin-step` unlocks only validated step files |
| Parallel exploration discipline | Claude can fan out Codex helpers from the plugin side | Serial exploration guidance only | Medium | Codex conductor now requires foreground-parallel exploration before planning |
| Claude-led plan authoring before approval | Claude plugin leads writing-plans | Codex-side docs still centered Codex-authored drafts | High | Claude now drafts the plan via `draft_plan` from discovery + dep-partition context, Codex reviews/finalizes it, and `attack_plan` becomes an optional extra pass |
| Review / approval gate | Hook checks on plan metadata and receipts | Orbit guidance only | Medium | `guard.py validate-plan` enforces `review.status` plus `skipReason` shape; Orbit remains the preferred approval tool after the Claude attack pass |
| Step ownership | Hook-time ownership routing | None | High | One writable step at a time through `begin-step` / `complete-step`; preserves intent without per-tool interception |
| Execution routing | Claude planner / operator chooses who implements | Planner-authored `executor` field | High | Conductor-owned routing resolver now stamps `executor`, `routingReason`, and routing metadata before execution, with Codex as the default |
| Completion gate | Hook-time result / receipt checks | `claudeVerify` described in docs only | High | `guard.py complete-step` requires non-empty result and Claude PASS verdict when `claudeVerify: true` |
| Smart resume | `SessionStart` hook inspects active plan / locks | None | High | `guard.py setup` re-unlocks the active `in_progress` step |
| Filesystem mutation guard | `guard-filesystem-mutation.sh` | None | Medium | Not mirrored literally; file-lock default-deny model covers the highest-value write path on Codex |
| Signed receipts | HMAC receipts outside repo | None | Medium | Not mirrored in v1; Codex guard uses local audit + plan/result state instead |
| deps-query nudges | hook wrappers on grep | Skill text only | Low | Keep soft guidance for now; no fake hard parity |
| Sub-agent context injection | `inject-subagent-context.sh` | Skill text + native Codex delegation rules | Low | Keep as guidance, not fake hook parity |
| Usage-error logging | scripts + findings dirs | existing `usage-errors/` script | Low | Preserve and continue using the existing Codex-side logging flow |
| Install / repair flow | plugin install scripts + hooks | Orbit / `claude-bridge` installers only | Medium | Add explicit Codex guard installer and make it part of the main install flow |

## 3. Bugs / Accidental Behaviors That Should Not Be Mirrored Literally

These are real upstream behaviors or mechanisms, but they should not be copied
blindly into the Codex side:

- Claude hook mechanics themselves.
  Codex does not expose the same runtime surface, so literal hook ports would
  be fake parity.

- Receipt signing as a prerequisite for every Codex-side workflow guarantee.
  The receipt system solves hook-time trust problems in Claude. Codex-side
  enforcement gets more value from default-deny file locking first.

- Mandatory “Claude dispatches Codex for co-exploration” logic.
  That is a Claude-side orchestration rule, not a Codex-native requirement when
  Codex is the primary agent.

- Blindly accepting Claude's planning suggestions.
  Even with Claude leading the draft, Codex remains the conductor and decides
  which repo-specific edits or follow-up pressure-tests are required before the
  user sees the plan.

- Blindly preserving the old Codex-side single mutable `plan.json` divergence.
  The upstream intent is that plan definition stays stable while mutable
  execution state lives separately. Codex should mirror that behavior with its
  own helpers instead of keeping the earlier incorrect simplification.

## 4. Concrete Plan For Missing Or Incorrect Pieces

The highest-value gaps were:

1. stale vendored upstream baseline
2. no runnable Codex guard
3. install flow did not configure guard setup
4. Codex-side docs described intended parity more strongly than actual parity
5. no tracked parity map or targeted guard tests
6. Claude verification reused plugin hook behavior that could mutate plan state

## 5. Implemented In This Update

### Upstream baseline

The vendored `look-before-you-leap/` tree was refreshed from the current
upstream source repo for parity-relevant directories:

- `commands/`
- `hooks/`
- `scripts/`
- `skills/`
- `tests/`
- `PACKAGES.md`

### Codex-native enforcement

Added `codex-guard/guard.py` with:

- `setup`
- `validate-plan`
- `begin-step`
- `checkpoint`
- `complete-step`
- `status`

It now enforces the highest-value Codex-side discipline guarantees with a
default-deny file-lock model.

### Install / bootstrap wiring

Added `scripts/install-codex-guard-integration.sh` and wired it into
`scripts/install-codex-skills.sh`.

Default behavior now writes:

```toml
[sandbox]
setup = "python3 /absolute/path/to/codex-setup/codex-guard/guard.py setup"
```

to `~/.codex/config.toml` unless `SKIP_CODEX_GUARD_INSTALL=1` is set.

### Codex-side guidance alignment

Updated:

- `AGENTS.md`
- `README.md`
- `codex-skills/README.md`
- `codex-skills/lbyl-conductor/SKILL.md`
- `codex-skills/lbyl-persistent-plans/SKILL.md`
- `codex-skills/lbyl-writing-plans/SKILL.md`
- `codex-skills/lbyl-conductor/references/plan-schema.md`

so the documented Codex workflow matches the implemented runtime path.

### Workflow model alignment

Updated the Codex-side instructions so the intended asymmetric model is now:

- exploration runs in parallel by default
- Claude drafts the plan through `claude-bridge`
- dep-partition context feeds step sizing and parallelization where dep maps exist
- Codex reviews and finalizes the draft locally
- `attack_plan` is optional for high-risk or materially revised drafts
- Orbit reviews the resulting draft
- all brainstorming runs through live Claude

### Conductor-owned routing

Added `codex-skills/lbyl-conductor/scripts/resolve_executor.py` and wired
`codex-guard validate-plan` to run it before execution. The planner may provide
an optional `routingHint`, but the real `executor` is now conductor-owned
resolved output rather than manually authored source-of-truth.

### Verification

Added `tests/test_codex_guard.py` covering:

- plan validation failure on pending review
- smart resume of in-progress steps
- validation requirement before `begin-step`
- completion refusal without Claude PASS
- successful completion relocking and step status update

Added `tests/test_claude_bridge_session_manager.py` and updated
`claude-bridge/session_manager.py` so bridge calls now use authenticated
non-`--bare` Claude with `disableAllHooks: true`, `--setting-sources
project,local`, and the local `look-before-you-leap` plugin dir. That
preserves Claude skill availability while preventing the upstream plugin hook
layer from mutating Codex plan state during a review pass.

## 6. Remaining Gaps

These areas are still real but intentionally not forced into fake parity:

- hard deps-query command interception
- signed approval / bypass receipts on the Codex side
- sub-agent prompt injection guarantees
- Codex-side equivalents for every upstream hook
- richer bridge-side curation of which Claude skills are available per flow

Those remain future work if they become worth the added complexity in Codex.

## 7. Coherence Check

After this update, the Codex repo is materially closer to being the inverse of
the Claude plugin:

- the upstream reference snapshot is current
- the Codex side now has a real enforcement mechanism
- install flow activates that mechanism
- the repo guidance describes the actual inverse model rather than a loose copy

That is the correct shape for parity here: preserve the discipline model, not
the hook implementation details.
