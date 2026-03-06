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

## Install

```bash
bash scripts/install-codex-skills.sh
```

Or copy them manually:

```bash
cp -R codex-skills/lbyl-* ~/.codex/skills/
```

## Usage

Ask for the skills explicitly:

- `Use lbyl-conductor and lbyl-engineering-discipline for this task.`
- `Use lbyl-writing-plans, then execute with lbyl-persistent-plans.`
- `Use lbyl-test-driven-development for this feature.`
- `Use lbyl-systematic-debugging for this bug.`
- `Use lbyl-agent-setup to create a project AGENTS.md for this repo.`

## Codex-specific notes

- There are no Claude plugin hooks here. The discipline is carried by the
  skill text, local `AGENTS.md`, and on-disk plans.
- The conductor assumes the companion skills are active for coding work.
- Persistent plans live in `.temp/plan-mode/active/`.
- Dep maps, when used, are configured from `.codex/lbyl-deps.json`.
