# LBYL for Codex

Codex-native port of the `look-before-you-leap` discipline system.

## Included skills

- `lbyl-conductor`
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

If a local Orbit checkout is available, the same installer also configures the
`orbit` MCP server in Codex and refreshes the Orbit VS Code extension so Orbit
review tools are available at startup in future Codex sessions.

To install the skill pack without Orbit:

```bash
SKIP_ORBIT_INSTALL=1 bash scripts/install-codex-skills.sh
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
- The conductor assumes the companion skills are active for coding work.
- Persistent plans use `plan.json` as execution state and `masterPlan.md` as
  the frozen Orbit-reviewed proposal.
- Dep maps, when used, are configured from `.codex/lbyl-deps.json`.
- In the default Codex workflow for this repo, new plan artifacts go through
  `orbit_await_review` before execution proceeds unless the user explicitly
  skips that review.
