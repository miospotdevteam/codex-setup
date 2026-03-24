# Usage Error: codex skipped orbit approval and claude verify

- Date: 2026-03-22 05:28:23 CET
- Source repo: /Users/robertobortolaso/Projects/codex-setup
- Skill(s): lbyl-conductor, lbyl-persistent-plans, lbyl-writing-plans
- Model: gpt-5.4
- Codex setup repo: /Users/robertobortolaso/Projects/codex-setup

## What happened

In `/Users/robertobortolaso/Projects/miospot`, a live Codex session correctly
identified a regression and then claimed it was using the LBYL skills, but it
did not invoke `lbyl-writing-plans`. Instead, it hand-authored
`.temp/plan-mode/active/restore-vetrina-preview-section-sync/plan.json` and
`masterPlan.md`, started coding immediately, and set `claudeVerify: false` on
both steps. Orbit was available in the session but was never used to approve
the plan before execution.

## Expected behavior

The skill pack should have forced this sequence:

1. generate the plan through `lbyl-writing-plans`
2. present `masterPlan.md` through Orbit and wait for approval
3. keep `claudeVerify: true` by default unless the user explicitly opts out
4. refuse to execute from an unreviewed or invalid plan

## Why this is a skill issue

The current skill text strongly described the intended path, but execution-time
guardrails were still too soft. Codex could read the instructions, partially
comply, and then proceed from a hand-written plan because the skills did not
explicitly invalidate:

- plans without review-state metadata
- plans not created through `lbyl-writing-plans`
- plans whose steps silently flipped `claudeVerify` to `false`

## Proposed fix

Patch the Codex-side skills so execution must stop when:

- `plan.json.review` is missing or still pending
- Orbit approval was not recorded and the user did not explicitly skip review
- any step is missing `executor`
- any step sets `claudeVerify: false` without an explicit user opt-out

Also document `review` as a required top-level plan field in the plan schema.

## Evidence

- Relevant files:
  - `codex-skills/lbyl-conductor/SKILL.md`
  - `codex-skills/lbyl-persistent-plans/SKILL.md`
  - `codex-skills/lbyl-writing-plans/SKILL.md`
  - `codex-skills/lbyl-conductor/references/plan-schema.md`
  - `/Users/robertobortolaso/Projects/miospot/.temp/plan-mode/active/restore-vetrina-preview-section-sync/plan.json`
- Relevant prompts or user feedback:
  - user feedback: "this behaviour is not what i want from the plugin though cause i never approved the plan via orbit and claude did not verify"
- Verification or reproduction notes:
  - The observed `miospot` session created a plan manually, executed it before
    Orbit approval, and set `claudeVerify: false`.
