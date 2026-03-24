# Usage Error: codex-guard design shipped without runnable implementation

- Date: 2026-03-24 21:16:08 CET
- Source repo: /Users/robertobortolaso/Projects/codex-setup
- Skill(s):
- Model: unknown
- Codex setup repo: /Users/robertobortolaso/Projects/codex-setup

## What happened

The repo documented a Codex-native enforcement story in multiple places:

- `README.md` described the Codex port as rewriting Claude-only concepts into
  Codex-native instructions, helper scripts, and review flow.
- `AGENTS.md` imposed strict plan / review / verification rules.
- `codex-guard/design.md` described a concrete `guard.py` CLI and
  `config.toml` `[sandbox].setup` integration.

But the repo shipped no runnable `codex-guard/guard.py`, no guard installer,
and no `~/.codex/config.toml` wiring. The practical effect was that the Codex
side still relied almost entirely on soft compliance even though the repo
implied stronger enforcement existed or was ready.

## Expected behavior

If the repo claims a Codex-native guard, it should ship one of these:

1. a real runnable guard plus install wiring, or
2. guidance that is explicit that the guard is only an unimplemented design.

The skill pack should not imply harder Codex enforcement than the repo can
actually install.

## Why this is a skill issue

This is a skill/setup issue because the repo-local operating model depends on
the discipline pack being truthful about its own enforcement surface.

- `AGENTS.md` told Codex sessions to behave as if the repo had a strong
  process layer.
- `README.md` framed the Codex port as already adapted into Codex-native
  mechanisms.
- `codex-guard/design.md` looked like the next enforcement layer was already
  concretely specified.

That combination creates false confidence: users and future sessions can
reasonably assume a real guard exists when it did not.

## Proposed fix

The smallest plausible fix is the combination implemented in this session:

1. add a real `codex-guard/guard.py`
2. add an installer that writes the guard into Codex `config.toml`
3. update docs so the claimed Codex-native enforcement matches the actual
   shipped behavior

If the guard is ever removed again, docs should immediately fall back to
describing it as a design-only future plan rather than current behavior.

## Evidence

- Relevant files:
  - `AGENTS.md`
  - `README.md`
  - `codex-guard/design.md`
  - `scripts/install-codex-skills.sh`
- Relevant prompts or user feedback:
  - User request to make this repo the real inverse of the Claude plugin and
    to treat intended-vs-actual analysis as mandatory.
- Verification or reproduction notes:
  - Before this fix, `codex-guard/` contained only `design.md`.
  - Before this fix, `scripts/install-codex-skills.sh` installed skills,
    Orbit, and `claude-bridge`, but did not install a guard.
