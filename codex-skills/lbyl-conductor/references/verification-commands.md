# Verification Commands by Ecosystem

## How to Find the Right Commands

Before using generic commands below, check the project's own tooling first:

1. **package.json** `scripts` — look for `typecheck`, `lint`, `test`, `build`
2. **Makefile** — look for common targets like `check`, `test`, `lint`
3. **pyproject.toml** — check `[tool.pytest]`, `[tool.ruff]`, `[tool.mypy]`
4. **Cargo.toml** — Rust projects use `cargo` commands directly
5. **AGENTS.md / README.md** — project-specific commands and conventions
6. **Task runners** — turbo, nx, moon, just, make — use these when present

Always prefer the project's own scripts over generic commands. They're configured
for the project's specific needs (paths, configs, flags).

## Node.js / TypeScript (bun, npm, pnpm)

```bash
# Type checking
bun run typecheck          # if script exists
npx tsc --noEmit           # direct tsc
bunx tsc --noEmit          # with bun

# Linting
bun run lint               # if script exists
npx eslint .               # direct eslint
npx eslint --fix .         # auto-fix

# Tests
bun test                   # bun test runner
npx vitest run             # vitest
npx jest                   # jest

# Build
bun run build              # if script exists
npx next build             # Next.js
```

## Python

```bash
# Type checking
mypy .
pyright .

# Linting
ruff check .
ruff check --fix .
flake8 .

# Tests
pytest
python -m pytest

# Formatting
ruff format .
black .
```

## Rust

```bash
# Type checking + compile
cargo check
cargo build

# Linting
cargo clippy

# Tests
cargo test

# Formatting
cargo fmt --check
```

## Go

```bash
# Build/compile check
go build ./...
go vet ./...

# Tests
go test ./...

# Linting
golangci-lint run
```

## Monorepo Tips

In monorepos, verification often needs to target the right package:

```bash
# Turborepo
turbo run typecheck --filter=<package-name>
turbo run test --filter=<package-name>

# Nx
nx run <project>:typecheck
nx run <project>:test

# pnpm workspaces
pnpm --filter <package-name> run typecheck
pnpm --filter <package-name> run test

# From package directory
cd packages/<name> && npm run typecheck
```

If unsure which package is affected, check the file path — it usually maps
directly to a package directory under `packages/`, `apps/`, or `libs/`.

## General Tips

- Check `package.json` `scripts` section first — projects often have
  custom `typecheck`, `lint`, `test` scripts
- Check for `Makefile` with common targets
- Check `AGENTS.md` or `README.md` for project-specific commands
- In monorepos, you may need to run checks from the specific package
  directory, not the root
- If the project uses a task runner (turbo, nx, moon), use that instead
  of running tools directly
