# Recommended AGENTS.md Addition

Add this block to your project's `AGENTS.md` to reinforce the lbyl skill pack
behavior on every session.

---

```markdown
## Software Discipline

All tasks use the lbyl skill pack. This is the default operating
mode — not optional.

### Plan Discipline
- **Before editing code**: write `.temp/plan-mode/active/<plan-name>/plan.json` and `masterPlan.md`
- **After any compaction**: IMMEDIATELY read the active plan — do not wait for user prompt
- **Every 2-3 file edits**: checkpoint — update `plan.json` on disk
- **After each step**: update `plan.json` immediately and keep `masterPlan.md` frozen after Orbit approval
- **Check plan status**: `bash .temp/plan-mode/scripts/plan-status.sh`
- **Find what to resume**: `bash .temp/plan-mode/scripts/resume.sh`
- **Steps with >10 files or sweep keywords**: MUST get a sub-plan with Groups
- **Always ask**: "If compaction fired right now, could I resume from the plan file?"

### Verification
- Run type checker, linter, and tests after every task
- Check `references/verification-commands.md` for framework-specific commands

### Skill Feedback
- If the lbyl skill pack itself causes a workflow error or misleading instruction, log it back to `codex-setup` before final closeout when feasible
- Preferred helper: `bash "${LBYL_CODEX_SETUP_REPO:-$HOME/Projects/codex-setup}/scripts/log-usage-error.sh" "short title"`
- If the repo lives elsewhere, set `LBYL_CODEX_SETUP_REPO` to that checkout first
- After creating the stub, fill in what happened, expected behavior, why it is skill-related, and the smallest plausible fix
```
