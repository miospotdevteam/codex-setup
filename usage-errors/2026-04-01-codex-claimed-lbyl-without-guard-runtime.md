# Usage Error: codex claimed LBYL without guard runtime

- Date: 2026-04-01
- Source repo: another project using this installed skill pack
- Skill(s): lbyl-conductor, lbyl-persistent-plans
- Model: gpt-5.x Codex session
- Codex setup repo: /Users/robertobortolaso/Projects/codex-setup

## What happened

A Codex session reported that it was using LBYL, but it skipped the formal
per-step verifier path and never proved that guarded runtime enforcement was
active for that repo session. The repo task still received local test/lint
verification, but the session answered as though the stricter LBYL path had
run end to end.

## Expected behavior

The installed skill pack should make two things explicit:

1. LBYL is the default operating mode for any Codex repo invocation.
2. If a repo has `codex-guard`, the session must prove guarded runtime is
   active before it can truthfully claim LBYL compliance.

That means the session should:

1. check `python3 codex-guard/guard.py status`
2. confirm `sessionSetup` is present
3. stop and repair runtime setup if `sessionSetup` is missing
4. run `validate-plan`, `begin-step`, `checkpoint`, and `complete-step`
5. satisfy the Claude verification gate before marking steps done

## Why this is a skill/runtime issue

The repo already documented `claudeVerify: true` as a hard gate, and
`complete-step` already enforced the PASS receipt. The missing piece was that
the Codex-side wording still allowed a session to speak about LBYL in broad
terms without first establishing whether the guarded runtime had actually been
activated for that repo invocation.

In other words, the process guarantee was stronger than the preflight that
proved the process was really in effect.

## Repo-side fix

This repo now:

- records `.temp/plan-mode/guard/.guard-session` during `guard.py setup`
- exposes that marker through `guard.py status`
- makes `guard.py validate-plan` fail closed when the runtime marker is missing
- updates `AGENTS.md`, the machine-global AGENTS installer, and the core Codex
  skills to say LBYL is standard for any Codex repo invocation
- explicitly tells sessions to stop, repair setup, and avoid claiming LBYL
  compliance when `sessionSetup` is absent

## Evidence

- Relevant files:
  - `codex-guard/guard.py`
  - `codex-guard/design.md`
  - `AGENTS.md`
  - `scripts/install-global-codex-agents.sh`
  - `codex-skills/lbyl-conductor/SKILL.md`
  - `codex-skills/lbyl-persistent-plans/SKILL.md`
  - `README.md`
  - `codex-skills/README.md`
  - `docs/claude-plugin-parity.md`
- Verification notes:
  - `python3 -m unittest tests.test_codex_guard`
  - formal Claude verification on the step that introduced `.guard-session`
  - formal Claude verification on the step that tightened the repo/skill rules
