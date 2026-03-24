# Usage Error: Codex plan_utils mutated plan.json instead of progress.json

## What happened

The Codex-side workflow kept using a single mutable `plan.json` even after the
upstream Claude plugin model had returned to an immutable `plan.json` plus
mutable `progress.json` split. In real usage this caused implementation runs to
rewrite step status, progress item status, and result text directly inside the
plan definition file.

## Why this was wrong

This broke the intended separation between:

- stable plan definition
- mutable execution checkpoint state

It also made resumed sessions and guard freshness logic rely on the wrong file,
and it obscured whether extra runtime edits were true plan-definition changes or
just progress updates.

## Evidence

- Real user report from `~/Projects/miospot` showed step completion rewriting
  `.temp/plan-mode/active/.../plan.json` instead of a sibling `progress.json`.
- Codex-native `plan_utils.py` in this repo wrote status/result/progress fields
  directly into `plan.json`.
- The upstream Claude plugin `plan_utils.py` and schema already used
  `progress.json` for mutable execution state.

## Fix

Port the Codex-side helpers and docs back to the split-state model:

- `plan.json` is the immutable definition
- `progress.json` stores mutable execution state
- merged reads preserve backward compatibility for legacy plans
- guard/resume/status flows consider `progress.json` mtimes and merged state

## Files involved

- `codex-skills/lbyl-conductor/scripts/plan_utils.py`
- `.temp/plan-mode/scripts/plan_utils.py`
- `codex-guard/guard.py`
- `codex-skills/lbyl-conductor/references/plan-schema.md`
- `codex-skills/lbyl-persistent-plans/SKILL.md`
