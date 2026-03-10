## LBYL Codex Setup

This repository contains a Codex port of the `look-before-you-leap` discipline plugin.

### Skills in this repo

Codex-native skills:
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
- `codex-skills/lbyl-skill-creator`

Upstream skills also shipped from this repo:
- `look-before-you-leap/skills/look-before-you-leap`
- `look-before-you-leap/skills/engineering-discipline`
- `look-before-you-leap/skills/persistent-plans`
- `look-before-you-leap/skills/writing-plans`
- `look-before-you-leap/skills/test-driven-development`
- `look-before-you-leap/skills/systematic-debugging`
- `look-before-you-leap/skills/refactoring`
- `look-before-you-leap/skills/immersive-frontend`
- `look-before-you-leap/skills/brainstorming`
- `look-before-you-leap/skills/react-native-mobile`
- `look-before-you-leap/skills/skill-review-standard`

### Operating rules
- Default to `lbyl-conductor` + `lbyl-engineering-discipline` for coding work.
- Before editing source, create `.temp/plan-mode/active/<plan-name>/plan.json` and `.temp/plan-mode/active/<plan-name>/masterPlan.md`.
- Present non-trivial plans through Orbit review before source edits unless the user explicitly skips that review.
- Update plan progress every 2-3 file edits.
- Verify with project typecheck, lint, and relevant tests before declaring done.
- Never silently drop requested scope.

### Install

```bash
bash scripts/install-codex-skills.sh
```

This installs the Codex-native `lbyl-*` skills plus the upstream skill set from
`look-before-you-leap/skills/`, except `frontend-design`, into
`~/.codex/skills`. The upstream `frontend-design` source stays in the repo for
sync purposes, but Codex sessions use `lbyl-frontend-design` as the single
standard frontend design skill. `immersive-frontend` remains installed as the
separate motion-heavy frontend skill.
