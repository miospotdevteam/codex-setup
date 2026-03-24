# LBYL Setup

This repository tracks two related things:

- `look-before-you-leap/`: the upstream Claude-oriented source tree, kept in
  sync with `~/Projects/claude-code-setup`
- `codex-skills/`: the Codex port, adapted for Codex CLI and GPT-5.4

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
scripts/                install helpers for Codex
```

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
`lbyl-*` skills remain the Codex-native defaults for coding work.

The same installer also configures `codex-guard` by default:

- writes a Codex `[sandbox].setup` entry to `~/.codex/config.toml`
- runs `codex-guard/guard.py setup` at session start in future Codex sessions
- makes source files read-only by default until a validated plan step is begun

The installer also configures a machine-global Codex instruction layer:

- writes a managed defaults block to `~/.codex/AGENTS.md`
- makes coding work default to `lbyl-conductor` plus
  `lbyl-engineering-discipline` in future Codex sessions
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
- builds and installs the `claude-bridge` VS Code extension
- enables live Claude brainstorming in VS Code plus authenticated Claude plan-attack,
  frontend implementation, and verification flows inside Codex sessions

This path assumes:

- `claude` CLI is installed and authenticated
- `code` CLI is available
- `npm`, `node`, and `python3` are available locally
- a local Claude-control checkout is available at
  `~/Projects/claude-code-setup/look-before-you-leap` or
  `~/projects/claude-code-setup/look-before-you-leap`, or
  `CLAUDE_BRIDGE_PLUGIN_DIR` points at that plugin directory

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

## Use in Codex

Mention the skills explicitly or rely on project `AGENTS.md` defaults. After
running the installer, Codex also has a machine-global default in
`~/.codex/AGENTS.md`, so coding work should already bias toward the conductor
unless a nearer project `AGENTS.md` overrides it.
Typical prompts:

- `Use lbyl-conductor and lbyl-engineering-discipline for this task.`
- `Use lbyl-writing-plans, then execute with lbyl-persistent-plans.`
- `Use lbyl-systematic-debugging for this failure.`
- `Use immersive-frontend for this motion-heavy landing page.`

For coding work, the expected default is:

- explore first, in parallel
- write `.temp/plan-mode/active/<plan-name>/plan.json` and `masterPlan.md` before source edits
- have Codex write the draft plan, then run a Claude plan-attack pass, then let Codex accept only the relevant findings before Orbit review
- if `codex-guard` is installed, use `validate-plan`, `begin-step`, `checkpoint`, and `complete-step` during execution
- update the plan every 2-3 file edits
- run relevant verification before declaring done

By default, the Codex skill pack presents new plans through Orbit for review
with `orbit_await_review` before execution starts unless the user explicitly
skips that review.

## Codex Guard

`codex-guard` is the Codex-native runtime analogue for the Claude plugin's
hook-based enforcement. It does not try to recreate Claude hooks literally.
Instead, it uses a default-deny file-locking model plus explicit step gates:

- `python3 codex-guard/guard.py validate-plan`
- `python3 codex-guard/guard.py begin-step <N>`
- `python3 codex-guard/guard.py checkpoint`
- `python3 codex-guard/guard.py complete-step <N>`

The installer writes a `[sandbox].setup` entry so future Codex sessions run:

```toml
[sandbox]
setup = "python3 /absolute/path/to/codex-setup/codex-guard/guard.py setup"
```

Current guard scope:
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
- Claude handles all brainstorming through `claude-bridge`.
- Codex writes draft plans, Claude attacks them through the authenticated
  `attack_plan` tool, and Codex decides which findings are relevant enough to
  fold back into the plan before Orbit review.
- Claude handles materially visual frontend implementation through the
  headless `frontend_implement` tool.
- Claude is a hard verification gate before steps are marked `done`.

`claude-bridge` now calls Claude in authenticated non-`--bare` mode with
`disableAllHooks: true`, `--setting-sources project,local`, and the local
`look-before-you-leap` plugin passed via `--plugin-dir`. That keeps Claude's
skills available while preventing the plugin hook layer from mutating Codex
plan state during bridge runs.

Plan steps should carry conductor-owned routing metadata:

- `executor: "claude"` for materially visual presentation changes
- `executor: "codex"` for copy-only UI changes, behavior-only UI changes, and
  all non-visual work
- `claudeVerify: true` by default on every step

Brainstorming uses a live Claude session surfaced in VS Code and exposed back
to Codex through `brainstorm_start` and `brainstorm_status`. Plan attack uses a
headless Claude pass exposed through `attack_plan`.

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
