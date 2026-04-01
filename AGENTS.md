## LBYL Codex Setup

This repository contains a Codex port of the `look-before-you-leap` discipline plugin.

### Skills in this repo

Codex-native skills:
- `codex-skills/lbyl-conductor`
- `codex-skills/lbyl-cost-optimization`
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
- `look-before-you-leap/skills/doc-coauthoring`
- `look-before-you-leap/skills/mcp-builder`
- `look-before-you-leap/skills/react-native-mobile`
- `look-before-you-leap/skills/skill-review-standard`
- `look-before-you-leap/skills/svg-art`
- `look-before-you-leap/skills/webapp-testing`

### Operating rules
- Default to `lbyl-conductor` + `lbyl-engineering-discipline` for any Codex repo invocation, not only obvious coding tasks.
- The installer also writes a managed machine-global default block to `~/.codex/AGENTS.md`, so Codex sessions from anywhere on this machine inherit that default unless a nearer project `AGENTS.md` overrides it.
- Run exploration in parallel by default; split discovery across at least two lanes when the task is non-trivial.
- Before editing source, create `.temp/plan-mode/active/<plan-name>/plan.json` and `.temp/plan-mode/active/<plan-name>/masterPlan.md`.
- During execution, treat `plan.json` as the definition and `progress.json` as the mutable runtime tracker.
- For non-trivial work, Codex owns planning locally, fans out discovery and implementation lanes through sub-agents where useful, and presents the resulting plan through Orbit review before execution.
- Keep planning, immediate critical-path edits, and final integration in the main Codex session; delegated lanes must write findings or progress back to disk for the conductor to merge.
- If `codex-guard` is installed for the session, run `python3 codex-guard/guard.py status` first and confirm `sessionSetup` is present. If the guard runtime is missing, stop and repair setup before claiming LBYL compliance. Then run `python3 codex-guard/guard.py validate-plan` before execution, `begin-step <N>` before step edits, `checkpoint` every 2-3 file edits, and `complete-step <N>` after verification.
- If `codex-guard` is not installed in the repo, still follow the full LBYL plan/review/verification process, but state explicitly that hard runtime enforcement is unavailable instead of implying it ran.
- Present non-trivial plans through Orbit review before source edits unless the user explicitly skips that review.
- Update plan progress every 2-3 file edits.
- Serialize `plan_utils.py` writes; never update the same `plan.json` in parallel.
- Verify with project typecheck, lint, and relevant tests before declaring done.
- Treat `claudeVerify: true` as a hard gate: do not mark a step `done` until `claude-bridge` returns `PASS`.
- Use Codex as the default conductor and implementer; route only materially visual frontend steps to Claude via the conductor-resolved `executor: "claude"`, and keep Claude as the independent verification gate where `claudeVerify: true`.
- If context gets crowded, checkpoint the plan state to disk and continue from a fresh Codex session; do not assume an in-session `/clear` exists. The repo helper for that handoff is `bash scripts/resume-active-plan-codex.sh`.
- If a future session uncovers a failure caused by the LBYL skill pack itself, log it here under `usage-errors/`, preferably via `bash scripts/log-usage-error.sh "short title"`.
- Never silently drop requested scope.

### Install

```bash
bash scripts/install-codex-skills.sh
bash scripts/bootstrap-codex-skills-from-github.sh
```

This installs the Codex-native `lbyl-*` skills plus the upstream skill set from
`look-before-you-leap/skills/`, except `frontend-design`, into
`~/.codex/skills`. The upstream `frontend-design` source stays in the repo for
sync purposes, but Codex sessions use `lbyl-frontend-design` as the single
standard frontend design skill. The upstream-only skills such as
`doc-coauthoring`, `mcp-builder`, `svg-art`, and `webapp-testing` are also
installed directly from `look-before-you-leap/skills/`. `immersive-frontend`
remains installed as the separate motion-heavy frontend skill. For
multi-machine use, prefer `scripts/bootstrap-codex-skills-from-github.sh` so
each machine clones or pulls the GitHub repo and then runs the local installer.
The installer also configures `codex-guard` globally for Codex unless
`SKIP_CODEX_GUARD_INSTALL=1` is set, and configures `claude-bridge` unless
`SKIP_CLAUDE_BRIDGE_INSTALL=1` is set. It also installs the machine-global
Codex default block unless `SKIP_GLOBAL_AGENTS_INSTALL=1` is set.
