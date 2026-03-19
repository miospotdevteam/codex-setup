# Usage Error: plan-utils set-result command missing

- Date: 2026-03-19 22:59:17 CET
- Source repo: /Users/robertobortolaso/Projects/codex-setup
- Skill(s):
- Model: unknown
- Codex setup repo: /Users/robertobortolaso/Projects/codex-setup
- Resolved: yes

## Resolved note

Resolved in this repo by adding `set-result` support to
`codex-skills/lbyl-conductor/scripts/plan_utils.py` and refreshing the
generated `.temp/plan-mode/scripts/plan_utils.py` copy from source.

## What happened

While updating `.temp/plan-mode/active/add-usage-error-logging/plan.json`,
the documented command
`python3 .temp/plan-mode/scripts/plan_utils.py set-result <plan.json> <step> "..."`
failed with `Unknown command: set-result`.

The skill docs and plan schema examples currently tell sessions that
`set-result` exists, but the shipped `plan_utils.py` in this repo does not
implement it.

## Expected behavior

The helper should either support `set-result` exactly as documented or the
skill docs should stop instructing sessions to use it.

## Why this is a skill issue

This is a mismatch between the LBYL planning instructions and the actual
helper script shipped with the skill pack. A session following the docs does
the right thing and still hits a dead end, which makes this a workflow bug in
the skill/tooling layer rather than an ordinary repo bug.

## Proposed fix

Preferred fix: add `set-result` support to `.temp/plan-mode/scripts/plan_utils.py`
and any source copy it is generated from.

Fallback fix: remove or replace every documented `set-result` example in the
skills and references so sessions do not rely on a missing command.

## Evidence

- Relevant files:
  - `.temp/plan-mode/scripts/plan_utils.py`
  - `codex-skills/lbyl-persistent-plans/SKILL.md`
  - `codex-skills/lbyl-conductor/references/plan-schema.md`
- Relevant prompts or user feedback:
  - The plan update flow in this session needed to record step results after
    implementing the usage-error logging feature.
- Verification or reproduction notes:
  - Reproduction command:
    `python3 .temp/plan-mode/scripts/plan_utils.py set-result .temp/plan-mode/active/add-usage-error-logging/plan.json 1 "example"`
  - Observed output: `Unknown command: set-result`
