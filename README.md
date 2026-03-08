# LBYL Setup

This repository tracks two related things:

- `look-before-you-leap/`: the upstream Claude-oriented source tree, kept in
  sync with `~/Projects/claude-code-setup`
- `codex-skills/`: the Codex port, adapted for Codex CLI and GPT-5.4

The goal is the same in both environments: make the model behave like a
disciplined engineer instead of a fast but sloppy one. The Codex port keeps
the upstream exploration, planning, verification, and blast-radius rules, but
rewrites Claude-only concepts such as hooks and plan mode into Codex-native
instructions.

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
`immersive-frontend` remains available for motion-heavy frontend work. The
`lbyl-*` skills remain the Codex-native defaults for coding work.

If a local Orbit repo is available at `~/Projects/orbit` or `~/projects/orbit`,
the installer also:

- builds the local Orbit MCP server when needed
- packages and installs the local VS Code extension when `code` is available
- registers a global Codex MCP server named `orbit`

That makes Orbit tools available automatically in future Codex sessions at
startup via `~/.codex/config.toml`.

To skip Orbit during a skill install:

```bash
SKIP_ORBIT_INSTALL=1 bash scripts/install-codex-skills.sh
```

To bootstrap Orbit separately or point at a non-default checkout:

```bash
bash scripts/install-orbit-codex-integration.sh
ORBIT_DIR=/absolute/path/to/orbit bash scripts/install-orbit-codex-integration.sh
```

## Use in Codex

Mention the skills explicitly or rely on project `AGENTS.md` defaults.
Typical prompts:

- `Use lbyl-conductor and lbyl-engineering-discipline for this task.`
- `Use lbyl-writing-plans, then execute with lbyl-persistent-plans.`
- `Use lbyl-systematic-debugging for this failure.`
- `Use immersive-frontend for this motion-heavy landing page.`

For coding work, the expected default is:

- explore first
- write `.temp/plan-mode/active/<plan-name>/masterPlan.md` before source edits
- update the plan every 2-3 file edits
- run relevant verification before declaring done

By default, the Codex skill pack presents new plans through Orbit for review
in VS Code before execution starts unless the user explicitly skips that
review.

## Sync policy

When the Claude repo evolves:

1. sync the shared upstream source into `look-before-you-leap/`
2. port the relevant changes into `codex-skills/`
3. adapt for Codex instead of copying Claude-specific runtime assumptions

That adaptation layer is the important part. This repo is intentionally not a
literal mirror.
