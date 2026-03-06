---
name: lbyl-agent-setup
description: "Use when the user wants to create or improve project-local agent guidance for Codex / GPT-5.4, such as `AGENTS.md`, nested `AGENTS.md` files, or optional `.codex/` config files. Helps choose the right surface, gather repo-specific conventions, write concise high-signal instructions, and validate that the guidance matches the actual project. Do NOT use for general documentation, implementation planning, or global Codex setup outside a specific repository."
---

# Agent Setup

Set up the project-local files that make Codex / GPT-5.4 work better in a
specific repository.

The default target is `AGENTS.md`. Add other files only when the project
genuinely needs them.

**Announce at start:** "I'm using the agent-setup skill to create or refine
the project-local guidance for this repo."

---

## Primary Goal

Write the minimum durable instructions that materially improve work in this
repo:

- where work happens
- which commands verify changes
- which constraints are project-specific
- which files or directories are special
- which actions are risky or forbidden

GPT-5.4 does best with explicit, local, verifiable rules. Prefer exact file
paths and exact commands over general advice.

---

## Choose the Right Surface

Use this order by default:

1. **Root `AGENTS.md`**
   Use for repo-wide defaults, commands, architecture notes, and behavior
   rules that apply almost everywhere.
2. **Nested `AGENTS.md`**
   Use only when a subtree has meaningfully different rules, such as a
   monorepo app with different commands or a generated-code area with extra
   constraints.
3. **`.codex/lbyl-deps.json`**
   Use only when dependency maps would materially improve consumer analysis
   in a TypeScript repo.
4. **Other `.codex/` files**
   Add only when there is a clear recurring workflow that benefits from
   structured local config.

Do not create extra files just because you can. One good `AGENTS.md` beats
three speculative config files.

---

## Workflow

### 1. Explore before writing

Read the repo first. At minimum:

- `README.md`
- existing `AGENTS.md` files, if any
- package manager / build files (`package.json`, `pyproject.toml`, `go.mod`, etc.)
- test and lint entry points
- 2-3 representative source files

Capture:

- real verification commands
- directory boundaries
- naming or architecture conventions
- dangerous operations the agent should avoid
- repo-specific workflows that are easy to get wrong

If you cannot ground an instruction in the repo, do not write it.

### 2. Decide what belongs in the file

Good project-local guidance usually includes:

- the default working directories
- the canonical test / lint / typecheck / build commands
- monorepo package boundaries
- approval requirements for destructive actions
- project conventions not obvious from the code
- references to important local files

Usually exclude:

- generic advice like "write clean code"
- language basics
- model-flattering prose
- rules already guaranteed by Codex system behavior

### 3. Write for GPT-5.4

Prefer:

- short sections
- imperative instructions
- exact commands
- explicit constraints
- concrete file paths

Avoid:

- long essays
- repeated warnings
- vague policies without an action

Good:

```markdown
- Run `pnpm --filter web test` for UI changes.
- Never edit `src/generated/` by hand.
- For DB changes, update `schema.sql` and run `pnpm db:generate`.
```

Bad:

```markdown
- Be thoughtful about testing.
- Follow best practices.
- Respect the codebase.
```

If the user wants a starting point instead of writing from scratch, load
`references/agents-templates.md` and adapt the closest template to the repo.

### 4. Validate the guidance

Before finishing:

- verify every command exists
- verify every referenced path exists
- verify the rules match the actual repo shape
- remove anything speculative or redundant

If a command or convention is uncertain, mark it as an assumption or leave it
out.

---

## Recommended `AGENTS.md` Shape

Use only the sections that help:

```markdown
## Project Name

### Scope
- What this repo or subtree contains

### Commands
- Exact verify/build/dev commands

### Conventions
- Naming, structure, special directories, generated code

### Safety Rules
- Destructive actions that require approval

### Workflow Notes
- Any recurring repo-specific steps the agent must not miss
```

Keep it lean. A smaller accurate file is better than a comprehensive stale one.

For ready-made starting points, see `references/agents-templates.md`:

- simple repo
- monorepo
- TypeScript repo with dep maps

---

## Red Flags

- Writing instructions before reading the repo
- Copying another repo's `AGENTS.md` verbatim
- Adding commands that do not exist
- Creating nested `AGENTS.md` files without a real scope boundary
- Encoding temporary project state as a permanent rule
- Restating generic model behavior instead of project specifics

---

## Completion Criteria

- The chosen file surface is justified by the repo layout
- Instructions are project-specific and concise
- Every command/path mentioned was verified
- No generic boilerplate survived
- The guidance would still be useful after the current task ends
