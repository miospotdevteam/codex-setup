# Usage Error: parallel plan_utils writes corrupt plan.json

- Date: 2026-03-22 04:31:01 CET
- Source repo: /Users/robertobortolaso/Projects/codex-setup
- Skill(s): lbyl-persistent-plans, lbyl-conductor
- Model: Codex / GPT-5.4
- Codex setup repo: /Users/robertobortolaso/Projects/codex-setup

## What happened

I used `multi_tool_use.parallel` to run multiple `plan_utils.py` updates
against the same `.temp/plan-mode/active/.../plan.json` at once. One of the
processes read the file while another process had truncated it for rewrite,
which produced a transient empty file and a `JSONDecodeError`. The plan file
recovered on the next successful write, but the workflow briefly corrupted the
source-of-truth artifact.

## Expected behavior

The skill pack should have made it explicit that `plan.json` writes are
single-writer operations. The model should have updated the plan sequentially,
even when other reads or unrelated commands were safe to parallelize.

## Why this is a skill issue

The repo guidance strongly encourages parallel tool use for speed, and the
older persistent-plan instructions did not explicitly forbid parallel
`plan_utils.py` writes. That made it too easy to treat plan updates like
ordinary independent shell commands even though they mutate the same file.

## Proposed fix

Add an explicit rule to `lbyl-persistent-plans` and repo `AGENTS.md`:
"Never run multiple `plan_utils.py` writes against the same `plan.json` in
parallel." This session implemented that documentation fix. A future tooling
hardening option would be atomic locking inside `plan_utils.py`.

## Evidence

- Relevant files:
  - `codex-skills/lbyl-persistent-plans/SKILL.md`
  - `AGENTS.md`
  - `codex-skills/lbyl-conductor/scripts/plan_utils.py`
- Relevant prompts or user feedback:
  - none; this was discovered during plan execution
- Verification or reproduction notes:
  - the failing command raised `json.decoder.JSONDecodeError: Expecting value:
    line 1 column 1 (char 0)` while a parallel `plan_utils.py` write was in
    flight
  - subsequent sequential plan updates succeeded consistently

## Resolution

Resolved in this repo by adding explicit "serialize `plan_utils.py` writes"
guidance to `codex-skills/lbyl-persistent-plans/SKILL.md` and `AGENTS.md`.
