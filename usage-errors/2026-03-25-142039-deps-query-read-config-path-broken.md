# Usage Error: deps-query read-config path broken

- Date: 2026-03-25 14:20:39 CET
- Source repo: /Users/robertobortolaso/Projects/paroola
- Skill(s):
- Model: unknown
- Codex setup repo: /Users/robertobortolaso/Projects/codex-setup

## What happened

While implementing step 13 in `paroola`, the `lbyl-conductor` / `lbyl-engineering-discipline`
workflow required using `deps-query.py` because `.claude/look-before-you-leap.local.md`
contains a `dep_maps` section with `modules`.

Running:

```bash
python3 /Users/robertobortolaso/Projects/antigravity-setup/look-before-you-leap/skills/look-before-you-leap/scripts/deps-query.py . api/src/routes/brand-inquiries.ts
```

returned:

```text
Error: No dep_maps.modules configured in .claude/look-before-you-leap.local.md
```

But the project config does include:

```yaml
dep_maps:
  dir: .claude/deps
  tool_cmd: "madge --json --extensions ts,tsx"
  modules:
    - .
    - portal
```

The actual root cause is that this installed `deps-query.py` resolves
`READ_CONFIG` to:

`/Users/robertobortolaso/Projects/antigravity-setup/look-before-you-leap/hooks/lib/read-config.py`

and that file does not exist in this installation layout, so config loading
silently fails and the tool reports a misleading missing-modules error.

## Expected behavior

If dep maps are configured, `deps-query.py` should successfully load the project
config and query dependents. If the helper path is broken, it should fail with a
direct path/config loading error rather than claiming the repo has no configured
modules.

## Why this is a skill issue

The skill text explicitly requires using `deps-query.py` when dep maps are
configured. In this session that instruction pushed the workflow onto a broken
tool path. Because the tool masked the real problem as a repo-config problem,
it cost extra exploration time and forced a fallback to manual consumer checks.

## Proposed fix

Smallest fix:

1. Fix `deps-query.py` to resolve `read-config.py` from the actual installed
   plugin layout instead of assuming a relative path that may not exist.
2. If `read-config.py` is missing, print a hard error naming the missing path.
3. Optionally add a quick self-check in the skill/tool bootstrap so broken
   helper paths are caught once at install time, not during execution.

## Evidence

- Relevant files:
  - `/Users/robertobortolaso/Projects/paroola/.claude/look-before-you-leap.local.md`
  - `/Users/robertobortolaso/Projects/antigravity-setup/look-before-you-leap/skills/look-before-you-leap/scripts/deps-query.py`
- Relevant prompts or user feedback:
  - User requested step-13 implementation and asked to check consumers via deps-query if configured.
- Verification or reproduction notes:
  - `deps-query.py` reported no configured modules.
  - Direct invocation of its expected helper path failed with:
    `can't open file '/Users/robertobortolaso/Projects/antigravity-setup/look-before-you-leap/hooks/lib/read-config.py': [Errno 2] No such file or directory`
