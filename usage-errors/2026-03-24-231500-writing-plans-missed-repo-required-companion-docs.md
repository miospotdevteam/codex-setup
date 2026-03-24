# Usage Error: Writing-plans missed repo-required companion docs

## What happened

In real usage on `~/Projects/miospot`, a Codex-owned implementation step changed
application code and then also updated `.claude/project-structure/mobile.md`,
even though that companion doc was not clearly declared as planned scope in the
step files.

## Why this was a workflow bug

The `miospot` repo rules explicitly require `.claude/project-structure/` docs
to stay in sync after route, API, component, i18n, env-var, or convention
changes. That means the doc update was required work, not optional scope creep.

The actual bug was that the planning guidance did not force Codex to include
repo-mandated companion docs in the step's `files` array and progress items up
front, so implementation reports made those edits look surprising.

## Fix

Update writing-plans guidance so that when AGENTS, CLAUDE.md, or repo-local
conventions require companion docs or inventories, those files must be listed
explicitly in the plan step.

## Files involved

- `codex-skills/lbyl-writing-plans/SKILL.md`
- `~/Projects/miospot/AGENTS.md`
- `~/Projects/miospot/.claude/CLAUDE.md`
