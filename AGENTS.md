## LBYL Codex Setup

This repository contains a Codex port of the `look-before-you-leap` discipline plugin.

### Skills in this repo
- `codex-skills/lbyl-conductor`
- `codex-skills/lbyl-engineering-discipline`
- `codex-skills/lbyl-persistent-plans`
- `codex-skills/lbyl-writing-plans`
- `codex-skills/lbyl-test-driven-development`
- `codex-skills/lbyl-systematic-debugging`
- `codex-skills/lbyl-refactoring`
- `codex-skills/lbyl-frontend-design`
- `codex-skills/lbyl-brainstorming`
- `codex-skills/lbyl-agent-setup`

### Operating rules
- Default to `lbyl-conductor` + `lbyl-engineering-discipline` for coding work.
- Before editing source, create `.temp/plan-mode/active/<plan-name>/masterPlan.md`.
- Update plan progress every 2-3 file edits.
- Verify with project typecheck, lint, and relevant tests before declaring done.
- Never silently drop requested scope.

### Install

```bash
bash scripts/install-codex-skills.sh
```
