# AGENTS.md Templates

Use these as starting points, not copy-paste truth. Replace every placeholder
with repo-specific facts you verified locally.

---

## Simple Repo

Use when one app or package dominates the repository and the same commands
apply almost everywhere.

```markdown
## <Project Name>

### Scope
- Main application code lives in `<src-dir>`.
- Tests live in `<test-dir>`.
- Generated files live in `<generated-dir>` and must not be edited by hand.

### Commands
- Install: `<install-command>`
- Typecheck: `<typecheck-command>`
- Lint: `<lint-command>`
- Test: `<test-command>`
- Build: `<build-command>`

### Conventions
- Use `<package-manager>` for all package commands.
- Prefer patterns already used in `<reference-dir-or-file>`.
- Keep changes inside the relevant feature area; do not refactor unrelated code.

### Safety Rules
- Ask before deleting files, changing schemas, or altering production config.
- Update `.temp/plan-mode/active/<plan-name>/masterPlan.md` every 2-3 file edits.

### Workflow Notes
- Read `README.md` and this file before starting work.
- Run the relevant verify commands before declaring done.
```

---

## Monorepo

Use when commands and boundaries differ by package or app.

```markdown
## <Monorepo Name>

### Scope
- Apps: `<apps-list>`
- Packages: `<packages-list>`
- Shared code lives in `<shared-dir>`.

### Working Rules
- Run commands from the repo root unless a package-specific note says otherwise.
- When changing shared code in `<shared-dir>`, check all consuming apps/packages.
- Do not mix unrelated package changes in one task unless required.

### Commands
- Install: `<root-install-command>`
- Repo typecheck: `<root-typecheck-command>`
- Repo lint: `<root-lint-command>`
- Repo test: `<root-test-command>`

### Package Notes
- `<app-a>`:
  - Dev: `<command>`
  - Test: `<command>`
- `<package-b>`:
  - Build: `<command>`
  - Typecheck: `<command>`

### Conventions
- Prefer package-local patterns over inventing new cross-repo abstractions.
- Keep imports aligned with the existing workspace boundaries.
- If a change touches shared APIs or types, update all affected consumers.

### Safety Rules
- Ask before changing workspace config, lockfiles in bulk, or generated clients.
- Keep plan progress updated on disk during multi-package work.
```

---

## TypeScript Repo With Dep Maps

Use when the repo benefits from dependency-map-driven blast-radius analysis.

```markdown
## <Project Name>

### Scope
- TypeScript source lives in `<ts-source-dirs>`.
- Dependency maps are configured in `.codex/lbyl-deps.json`.

### Commands
- Install: `<install-command>`
- Typecheck: `<typecheck-command>`
- Lint: `<lint-command>`
- Test: `<test-command>`
- Refresh stale dep maps: `python3 ~/.codex/skills/lbyl-conductor/scripts/deps-generate.py <repo-root> --stale-only`
- Query consumers: `python3 ~/.codex/skills/lbyl-conductor/scripts/deps-query.py <repo-root> <file-path>`

### Dep-Map Rules
- Before changing shared `.ts` or `.tsx` files, run `deps-query.py` on files in scope.
- Use dep-map output for consumer checks and blast-radius analysis.
- If dep maps are stale or missing, regenerate them before broad shared-code edits.

### Conventions
- Do not use `any` or `as any` to force TypeScript through.
- Reuse existing types and validation schemas before creating new ones.
- Update all consumers when changing shared exports or contracts.

### Safety Rules
- Ask before changing tsconfig structure, package boundaries, or generated types.
- Verify with the real project commands before declaring done.

### Workflow Notes
- Record dep-map findings in `discovery.md` when planning larger tasks.
- Keep `AGENTS.md` commands aligned with the actual package scripts.
```

---

## Template Hygiene

- Remove sections that do not apply.
- Replace placeholders with verified repo facts.
- Prefer one accurate root `AGENTS.md` over multiple weak files.
- Add nested `AGENTS.md` files only when a subtree genuinely has different rules.
