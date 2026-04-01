# LBYL Setup

This repository tracks two related things:

- `look-before-you-leap/`: the vendored upstream Claude-oriented reference tree
- `codex-skills/`: the Codex port, adapted for Codex CLI and GPT-5.4
- `claude-support/`: the slim Claude support bundle used only for bridge-time
  exploration, UI work, and independent verification

The goal is the same in both environments: make the model behave like a
disciplined engineer instead of a fast but sloppy one. The Codex port keeps
the upstream exploration, planning, verification, and blast-radius rules, but
rewrites Claude-only concepts such as hook enforcement and plan mode into
Codex-native instructions, helper scripts, and Orbit-backed review flow.

## Why this exists

The discipline targets the recurring failure modes that show up in real coding
sessions:

- silent scope cuts
- shared-code changes without consumer checks
- type-safety shortcuts
- missing verification
- shallow exploration
- compaction without a recoverable plan

GPT-5.4 is stronger at following explicit long-horizon instructions than
earlier models, so the Codex version leans on clear contracts: exact skills,
exact plan files, exact acceptance criteria, and concise progress updates.

## Repository layout

```text
look-before-you-leap/   upstream Claude source and hooks
codex-skills/           Codex-native skill pack
claude-support/         slim Claude bundle for UI work and verification
scripts/                install helpers for Codex
```

## Slim Claude Support Bundle

`claude-support/look-before-you-leap/` is the bridge-time Claude bundle used
by this repo's default workflow. It is intentionally narrow:

- `explorer/` for read-heavy codebase discovery and plan pressure-testing
- `frontend-design/` for standard web UI direction and implementation support
- `immersive-frontend/` for canvas-heavy or motion-first visual work
- `independent-verification/` for Claude's read-only review pass

It is not a full Claude-primary plugin port. Planning, brainstorming,
orchestration, and default implementation stay in Codex.

## Install the repo skills

```bash
bash scripts/install-codex-skills.sh
```

This installs the full Codex-native pack plus the upstream skills from:

- `codex-skills/`
- `look-before-you-leap/skills/`

into `~/.codex/skills/`, except the upstream `frontend-design` skill. That
source stays in the repo for sync, but installed Codex sessions use
`lbyl-frontend-design` as the single standard frontend design skill.
`immersive-frontend` remains available for motion-heavy frontend work, and the
upstream-only skills such as `doc-coauthoring`, `mcp-builder`, `svg-art`, and
`webapp-testing` are installed directly from the vendored upstream tree. The
`lbyl-*` skills remain the Codex-native defaults for any Codex repo invocation.

The same installer also configures `codex-guard` by default:

- writes a Codex `[sandbox].setup` entry to `~/.codex/config.toml`
- runs `codex-guard/guard.py setup` at session start in future Codex sessions
- makes source files read-only by default until a validated plan step is begun
- records guard runtime activation as `.temp/plan-mode/guard/.guard-session`,
  which later `status` / `validate-plan` calls use to confirm the guarded path
  is actually active

The installer also configures a machine-global Codex instruction layer:

- writes a managed defaults block to `~/.codex/AGENTS.md`
- makes any Codex repo invocation default to `lbyl-conductor` plus
  `lbyl-engineering-discipline` in future Codex sessions
- tells Codex to treat the installed `lbyl-*` pack as its baseline workflow
  and to invoke exact `lbyl-*` skills proactively by task type
- requires Claude `attack_plan` approval before Orbit review or execution when
  a plan is large/high-blast-radius, materially revised, fragile in
  sequencing/verification, or explicitly flagged for extra pressure-testing
- preserves any unrelated user content in `~/.codex/AGENTS.md`
- defers to nearer project or nested `AGENTS.md` files when a repo provides
  stronger local guidance

If a local Orbit repo is available at `~/Projects/orbit` or `~/projects/orbit`,
the installer also:

- builds the local Orbit MCP server when needed
- packages and installs the local VS Code extension when `code` is available
- registers a global Codex MCP server named `orbit`

That makes Orbit tools available automatically in future Codex sessions at
startup via `~/.codex/config.toml`.

The installer also configures `claude-bridge` globally for Codex:

- registers a global Codex MCP server named `claude-bridge`
- persists `startup_timeout_sec` and `tool_timeout_sec` for long-running Claude calls
- builds and installs the `claude-bridge` VS Code extension
- enables authenticated Claude frontend implementation and independent
  verification flows inside Codex sessions

This path assumes:

- `claude` CLI is installed and authenticated
- `code` CLI is available
- `npm`, `node`, and `python3` are available locally
- the repo-local Claude support bundle exists at
  `claude-support/look-before-you-leap`, or `CLAUDE_BRIDGE_PLUGIN_DIR`
  points at an alternate plugin directory

By default the installer writes:

- `startup_timeout_sec = 300`
- `tool_timeout_sec = 10800`

That gives `claude-bridge` a 5 minute startup window and a 3 hour tool-call
window inside Codex, which is a much better fit for long verification or
implementation passes than the short MCP defaults. You can override these at
install time with `CLAUDE_BRIDGE_MCP_STARTUP_TIMEOUT_SEC` and
`CLAUDE_BRIDGE_MCP_TOOL_TIMEOUT_SEC`.

To skip Orbit during a skill install:

```bash
SKIP_ORBIT_INSTALL=1 bash scripts/install-codex-skills.sh
```

To skip Codex guard setup during a skill install:

```bash
SKIP_CODEX_GUARD_INSTALL=1 bash scripts/install-codex-skills.sh
```

To skip installing the machine-global Codex defaults:

```bash
SKIP_GLOBAL_AGENTS_INSTALL=1 bash scripts/install-codex-skills.sh
```

To skip the Claude bridge during a skill install:

```bash
SKIP_CLAUDE_BRIDGE_INSTALL=1 bash scripts/install-codex-skills.sh
```

To install or refresh the Codex guard separately:

```bash
bash scripts/install-codex-guard-integration.sh
```

To bootstrap Orbit separately or point at a non-default checkout:

```bash
bash scripts/install-orbit-codex-integration.sh
ORBIT_DIR=/absolute/path/to/orbit bash scripts/install-orbit-codex-integration.sh
```

To install or refresh Claude bridge separately:

```bash
bash scripts/install-claude-bridge-codex-integration.sh
CLAUDE_BRIDGE_MCP_TOOL_TIMEOUT_SEC=14400 bash scripts/install-claude-bridge-codex-integration.sh
```

## Install from GitHub

For multi-machine use, treat GitHub as the source of truth and run the
bootstrap wrapper on each machine:

```bash
curl -fsSL https://raw.githubusercontent.com/miospotdevteam/codex-setup/main/scripts/bootstrap-codex-skills-from-github.sh | bash
```

That script:

- clones `https://github.com/miospotdevteam/codex-setup.git` into
  `~/Projects/codex-setup` if it is missing
- otherwise validates the checkout and pulls the latest `main`
- runs `scripts/install-codex-skills.sh` from that checkout

You can also run it from any existing checkout:

```bash
bash scripts/bootstrap-codex-skills-from-github.sh
```

Useful overrides:

```bash
CHECKOUT_DIR=~/projects/codex-setup bash scripts/bootstrap-codex-skills-from-github.sh
REPO_URL=https://github.com/<org>/codex-setup.git bash scripts/bootstrap-codex-skills-from-github.sh
BRANCH=main bash scripts/bootstrap-codex-skills-from-github.sh
SKIP_ORBIT_INSTALL=1 bash scripts/bootstrap-codex-skills-from-github.sh
SKIP_CODEX_GUARD_INSTALL=1 bash scripts/bootstrap-codex-skills-from-github.sh
SKIP_GLOBAL_AGENTS_INSTALL=1 bash scripts/bootstrap-codex-skills-from-github.sh
SKIP_CLAUDE_BRIDGE_INSTALL=1 bash scripts/bootstrap-codex-skills-from-github.sh
SKIP_PULL=1 bash scripts/bootstrap-codex-skills-from-github.sh
```

This still installs into `~/.codex/skills/`, so future updates are not live.
After pushing changes to GitHub, rerun the bootstrap script on each machine to
pull and reinstall the latest version.

## Machine Migration

To back up the current Claude plugin state, remove the old Claude plugin
footprint, and refresh the global Codex install from this repo:

```bash
bash scripts/migrate-claude-to-codex-first.sh
```

Default behavior:

- backs up the current Claude plugin state to
  `~/.codex/backups/claude-migration-<timestamp>/`
- uninstalls all currently installed Claude plugins across user, project, and
  local scopes when possible
- removes configured Claude marketplaces after plugin uninstall
- prunes residual Claude plugin cache/data/marketplace directories
- refreshes the global Codex install by rerunning
  `scripts/install-codex-skills.sh`

If a previously recorded project path no longer exists, the migration script
warns, prunes the stale plugin entry from Claude's local state files after the
backup, and then continues the cleanup instead of leaving the machine in a
half-migrated state.

Useful overrides:

```bash
DRY_RUN=1 bash scripts/migrate-claude-to-codex-first.sh
MIGRATION_SCOPE=legacy-lbyl bash scripts/migrate-claude-to-codex-first.sh
SKIP_CODEX_REFRESH=1 bash scripts/migrate-claude-to-codex-first.sh
BACKUP_ROOT=~/Desktop/codex-backups bash scripts/migrate-claude-to-codex-first.sh
```

`MIGRATION_SCOPE=all` is the default and matches the current Codex-first
machine reset: Claude keeps no installed plugin footprint on disk, and the
repo-local `claude-support/look-before-you-leap/` bundle is used only through
`claude-bridge` for materially visual frontend work and independent
verification.

## Fresh-Session Continuation

Codex CLI does not currently provide a guaranteed Claude-style in-session
`/clear` equivalent. The supported replacement in this repo is:

1. write the current execution state back to `progress.json` and the step
   `result`
2. start a fresh Codex session
3. resume from the active plan on disk

Helper command:

```bash
bash scripts/resume-active-plan-codex.sh
```

That helper:

- finds the most recently active plan under `.temp/plan-mode/active/`
- reads the next incomplete step
- launches a fresh Codex session in the project root with a prompt that tells
  Codex to read `plan.json`, `progress.json`, and `discovery.md` before
  continuing

If you only want to inspect the exact command first:

```bash
bash scripts/resume-active-plan-codex.sh --print-command
```

## Use in Codex

Mention the skills explicitly or rely on project `AGENTS.md` defaults. After
running the installer, Codex also has a machine-global default in
`~/.codex/AGENTS.md`, so repo work should already bias toward the conductor
unless a nearer project `AGENTS.md` overrides it.
Typical prompts:

- `Use lbyl-conductor and lbyl-engineering-discipline for this task.`
- `Use lbyl-writing-plans, then execute with lbyl-persistent-plans.`
- `Use lbyl-systematic-debugging for this failure.`
- `Use immersive-frontend for this motion-heavy landing page.`

For any Codex repo invocation, the expected default is:

- explore first, in parallel
- keep the main Codex session lean by spawning sub-agents for non-trivial
  exploration, audits, and disjoint implementation lanes
- keep planning, immediate critical-path edits, and final integration in the
  main Codex session
- write `.temp/plan-mode/active/<plan-name>/plan.json` and `masterPlan.md` before source edits
- let `plan_utils.py` write mutable execution state to `progress.json` during execution
- have Codex draft and finalize the plan locally, then present it for Orbit review
- if `codex-guard` is installed, run `status` first and confirm `sessionSetup`
  is present before using `validate-plan`, `begin-step`, `checkpoint`, and
  `complete-step`
- if `codex-guard` is not installed, still follow the same LBYL loop but say
  explicitly that hard runtime enforcement is unavailable
- update the plan every 2-3 file edits
- if the session starts feeling crowded, checkpoint and resume from a fresh
  Codex session instead of trying to self-clear context in place
- run relevant verification before declaring done

By default, the Codex skill pack presents new plans through Orbit for review
with `orbit_await_review` before execution starts unless the user explicitly
skips that review.

## Codex Guard

`codex-guard` is the Codex-native runtime analogue for the Claude plugin's
hook-based enforcement. It does not try to recreate Claude hooks literally.
Instead, it uses a default-deny file-locking model plus explicit step gates:

- `python3 codex-guard/guard.py status`
- `python3 codex-guard/guard.py validate-plan`
- `python3 codex-guard/guard.py begin-step <N>`
- `python3 codex-guard/guard.py checkpoint`
- `python3 codex-guard/guard.py complete-step <N>`

`status` should report a non-null `sessionSetup` before a session claims LBYL
compliance. `validate-plan` now refuses to continue when that runtime marker is
missing, so a broken or bypassed setup path fails closed instead of quietly
degrading to best effort.

The installer writes a `[sandbox].setup` entry so future Codex sessions run:

```toml
[sandbox]
setup = "python3 /absolute/path/to/codex-setup/codex-guard/guard.py setup"
```

Current guard scope:
- runtime activation marker via `.guard-session`
- plan validation and review metadata checks
- one writable step at a time
- smart resume of in-progress steps
- completion gating on recorded Claude PASS verdicts
- audit logging for checkpoints and writable-file bypasses

Current non-goals:
- literal Claude hook parity
- hard interception of grep/deps-query choices
- receipt-signing parity with the Claude plugin
- sub-agent prompt injection as a runtime guarantee

## Asymmetric Claude Workflow

This repo now assumes an intentionally asymmetric split:

- Codex is the orchestrator, runs exploration in parallel, and is the default implementer.
- Codex is also the default planner. Plans live on disk and survive compaction,
  so a fresh Codex session can resume from them without relying on a Claude
  drafting phase.
- Codex should proactively spawn sub-agents for non-trivial exploration,
  audits, and disjoint implementation lanes so the conductor session stays
  focused on routing, integration, and final decisions.
- Those delegated lanes must write findings or progress back to disk through
  `discovery.md`, `progress.json`, or the step `result`; the conductor owns
  plan-file writes and final synthesis.
- Claude handles materially visual frontend implementation through the
  headless `frontend_implement` tool.
- Claude is a hard verification gate before steps are marked `done`.

`claude-bridge` now calls Claude in authenticated non-`--bare` mode with
`disableAllHooks: true`, `--setting-sources project,local`, and the local
`claude-support/look-before-you-leap` bundle passed via `--plugin-dir`. That
keeps Claude's UI and verification skills available while preventing the old
Claude-primary plugin model from mutating Codex plan state during bridge runs.

Plan steps should carry conductor-owned routing metadata:

- `executor: "claude"` for materially visual presentation changes
- `executor: "codex"` for copy-only UI changes, behavior-only UI changes, and
  all non-visual work
- `claudeVerify: true` by default on every step

This repo does not depend on Claude for default brainstorming or plan drafting.
If a future workflow chooses to use those bridge tools, treat them as optional
extras rather than part of the required Codex-first path.

Codex CLI does not currently expose a guaranteed Claude-style in-session
`/clear` flow. The intended replacement is persistent-plan continuation:
write state to disk, start a fresh Codex session, and resume from the active
plan instead of pretending the same session can self-clear safely. Use
`bash scripts/resume-active-plan-codex.sh` when you want the repo's default
fresh-session handoff.

Non-PASS verification rounds write JSON findings to
[`usage-errors/claude-findings`](/Users/robertobortolaso/Projects/codex-setup/usage-errors/claude-findings).
PASS does not create a findings file.

If a future session discovers that the skill pack itself caused a bad
workflow, missed requirement, or other usage error, log it back here under
`usage-errors/`. Preferred helper:

```bash
bash ~/Projects/codex-setup/scripts/log-usage-error.sh "short title"
```

If this repo lives elsewhere on that machine, set
`LBYL_CODEX_SETUP_REPO=/absolute/path/to/codex-setup` first. See
[`usage-errors/README.md`](/Users/robertobortolaso/Projects/codex-setup/usage-errors/README.md)
for the report format.

## Sync policy

When the Claude repo evolves:

1. sync the shared upstream source into `look-before-you-leap/`
2. port the relevant changes into `codex-skills/`
3. adapt for Codex instead of copying Claude-specific runtime assumptions

That adaptation layer is the important part. This repo is intentionally not a
literal mirror.

Current examples of upstream-only skills that ship directly from the vendored
tree are `doc-coauthoring`, `mcp-builder`, `svg-art`, and `webapp-testing`.
