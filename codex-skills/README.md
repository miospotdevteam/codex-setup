# LBYL for Codex

Codex-native port of the `look-before-you-leap` discipline system.

## Included skills

- `lbyl-conductor`
- `lbyl-cost-optimization`
- `lbyl-engineering-discipline`
- `lbyl-persistent-plans`
- `lbyl-writing-plans`
- `lbyl-test-driven-development`
- `lbyl-systematic-debugging`
- `lbyl-refactoring`
- `lbyl-frontend-design`
- `lbyl-brainstorming`
- `lbyl-agent-setup`
- `lbyl-skill-creator`

## Install

```bash
bash scripts/install-codex-skills.sh
```

The repo installer installs this Codex-native pack and the upstream skills
under `look-before-you-leap/skills/`, except upstream `frontend-design`. The
upstream source stays in the repo for sync, but installed Codex sessions use
`lbyl-frontend-design` as the single standard frontend design skill.

The same installer also configures `codex-guard` by default by writing a
Codex `[sandbox].setup` entry that runs `codex-guard/guard.py setup` at
session start in future Codex sessions.

If a local Orbit checkout is available, the same installer also configures the
`orbit` MCP server in Codex and refreshes the Orbit VS Code extension so Orbit
review tools are available at startup in future Codex sessions.

The same installer also configures `claude-bridge` globally for Codex:

- live Claude brainstorming in VS Code
- headless Claude frontend implementation for materially visual steps
- hard Claude verification before `claudeVerify` steps are marked done

To install the skill pack without Orbit:

```bash
SKIP_ORBIT_INSTALL=1 bash scripts/install-codex-skills.sh
```

To install the skill pack without Codex guard:

```bash
SKIP_CODEX_GUARD_INSTALL=1 bash scripts/install-codex-skills.sh
```

To install the skill pack without the Claude bridge:

```bash
SKIP_CLAUDE_BRIDGE_INSTALL=1 bash scripts/install-codex-skills.sh
```

To bootstrap Orbit only:

```bash
bash scripts/install-orbit-codex-integration.sh
```

To copy the full repo inventory manually:

```bash
cp -R codex-skills/* ~/.codex/skills/
cp -R look-before-you-leap/skills/* ~/.codex/skills/
rm -rf ~/.codex/skills/frontend-design
```

## Usage

Ask for the skills explicitly:

- `Use lbyl-conductor and lbyl-engineering-discipline for this task.`
- `Use lbyl-writing-plans, then execute with lbyl-persistent-plans.`
- `Use lbyl-test-driven-development for this feature.`
- `Use lbyl-systematic-debugging for this bug.`
- `Use lbyl-agent-setup to create a project AGENTS.md for this repo.`
- `Use lbyl-skill-creator to add or improve a Codex skill.`

## Codex-specific notes

- There are no Claude plugin hooks here. The discipline is carried by the
  skill text, local `AGENTS.md`, on-disk plans, and Orbit-backed MCP review
  tooling.
- Claude is still part of the default workflow through `claude-bridge`:
  live brainstorming, Claude-routed visual frontend steps, and the hard
  verification gate.
- When installed, `codex-guard` is the hard-default write gate on the Codex
  side for validated step execution.
- The conductor assumes the companion skills are active for coding work.
- Persistent plans use `plan.json` as execution state and `masterPlan.md` as
  the frozen Orbit-reviewed proposal.
- Plan steps now separate `skill` from `executor`, and default to
  `claudeVerify: true`.
- Dep maps, when used, are configured from `.codex/lbyl-deps.json`.
- In the default Codex workflow for this repo, new plan artifacts go through
  `orbit_await_review` before execution proceeds unless the user explicitly
  skips that review.
- When the skill pack itself causes a workflow error in another session, log
  it back to this repo under `usage-errors/`, preferably via
  `bash ~/Projects/codex-setup/scripts/log-usage-error.sh "short title"`.
