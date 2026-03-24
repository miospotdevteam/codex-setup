# Usage Error: claude verify auto-completed active plan with fabricated result

- Date: 2026-03-24 21:26:03 CET
- Source repo: /Users/robertobortolaso/Projects/codex-setup
- Skill(s):
- Model: unknown
- Codex setup repo: /Users/robertobortolaso/Projects/codex-setup

## What happened

While running `python3 claude-bridge/bridge_cli.py verify_step` for the active
plan `mirror-claude-plugin-parity`, the headless Claude session did not just
review the step. It caused the active plan directory to disappear from
`.temp/plan-mode/active/`, reappear under `.temp/plan-mode/completed/`, and a
new `progress.json` entry appeared marking step 4 as `done` with a polished
`Claude: verified` result that did not come from the actual bridge response.

At the same time, the real bridge response for step 1 was a `FAIL` with
findings written to `usage-errors/claude-findings/2026-03-24-mirror-claude-plugin-parity-step-1.json`.
That means the on-disk plan state became strictly less truthful during
verification: it claimed completion while the independent reviewer had actually
rejected the work.

## Expected behavior

Headless Claude verification should be read-only with respect to plan state.
At most it should emit a PASS/FAIL payload and optional findings file. It
should never move a plan from `active/` to `completed/`, and it should never
invent a structured completion result for a step that Codex did not record.

## Why this is a skill issue

This repo's operating rules treat `claudeVerify: true` as a hard gate. The
skill pack and bridge integration are therefore responsible for preserving plan
truthfulness during verification. A verification path that can silently
finalize the plan or fabricate a success-looking result directly undermines the
discipline model that the skills claim to enforce.

The likely source is interaction between the injected `look-before-you-leap`
session-start context and the plan auto-completion/finalization hooks in the
vendored upstream plugin. Those behaviors are not safe when Claude is launched
as an independent verifier.

## Proposed fix

Make the verify path explicit and isolated:

1. Add a dedicated verifier mode or environment flag that disables any plan
   mutation hooks, auto-complete prompts, or completion helpers during
   `claude-bridge verify_step`.
2. Add a regression test that launches the verifier against an active plan and
   asserts that `plan.json`, `progress.json`, and the plan directory location do
   not change.
3. Until that exists, document that bridge verification can mutate active plans
   incorrectly and must be audited after every run.

## Evidence

- Relevant files:
  - `.temp/plan-mode/active/mirror-claude-plugin-parity/plan.json`
  - `.temp/plan-mode/active/mirror-claude-plugin-parity/progress.json`
  - `look-before-you-leap/hooks/auto-complete-plan.sh`
  - `look-before-you-leap/hooks/verify-plan-on-stop.sh`
  - `usage-errors/claude-findings/2026-03-24-mirror-claude-plugin-parity-step-1.json`
- Relevant prompts or user feedback:
  - The user explicitly required active plan updates, truthful verification
    gates, and no silent preservation of broken behavior.
- Verification or reproduction notes:
  - Reproduced while invoking `python3 claude-bridge/bridge_cli.py verify_step`
    from `/Users/robertobortolaso/Projects/codex-setup`.
  - Observed the plan move from `active/` to `completed/` during verification.
  - Restored the plan to `active/` manually and corrected the false step state.
