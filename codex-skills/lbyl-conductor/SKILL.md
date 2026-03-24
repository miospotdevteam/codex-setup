---
name: lbyl-conductor
description: "Unified engineering discipline for ALL coding tasks. Three layers: this file (the conductor), quick-reference checklists, and deep guides. Enforces structured exploration before planning, persistent plans that survive compaction, TDD red-green-refactor cycles that prevent implementation-first coding, disciplined execution with blast radius tracking and type safety, and multi-discipline coverage (testing, UI consistency, security, git, linting, dependencies). Use for every task that touches source files — no exceptions, no shortcuts. Do NOT use when: answering questions about code without changing it, pure research or documentation queries, conversations with no file edits, or running commands that don't modify the codebase."
---

# Software Discipline

This skill is the conductor. It controls the process and routes to deeper
guidance. The actual rules live in two companion skills that are always
injected alongside this one:

- **engineering-discipline** — The behavioral layer: explore before editing,
  track blast radius, no type shortcuts, verify work, no silent scope cuts.
- **persistent-plans** — The structural layer: plan files on disk, the
  execution loop, checkpoints, sub-plans, compaction survival.

**You must follow both companion skills for every coding task.**

---

## Step 0: Discover Available Skills

At the start of every session, note which skills are available (the
current session context provides a skill inventory). When a step calls for
specialized knowledge (testing, frontend design, security review), check
if an installed skill covers it before relying on general knowledge.

### External skill routing

Look for installed skills that match these needs:

| When you need... | Look for skills about... |
|---|---|
| Consequential design ambiguity with multiple plausible approaches | **Always** use `lbyl-brainstorming` — never another plugin's brainstorming skill |
| Writing implementation plans | **Always** use `lbyl-writing-plans` — never another plugin's writing-plans skill |
| Test strategy, TDD | **Always** use `lbyl-test-driven-development` — never another plugin's TDD skill |
| Frontend UI design, standard web interfaces | **Always** use `lbyl-frontend-design` — never another plugin's frontend-design skill |
| SVG art, illustrations, patterns, textures, generative art | **Always** use `svg-art` — installed from the vendored upstream skill pack |
| Immersive web, WebGL, 3D, scroll-driven creative dev | **Always** use `immersive-frontend` — never another skill pack's immersive-frontend skill |
| React Native, mobile apps, Expo, native feel | **Always** use `react-native-mobile` — never another skill pack's mobile skill |
| Security review | "security", "authentication", "auth" |
| Code review | "code review", "review" |
| Debugging | **Always** use `lbyl-systematic-debugging` — never another plugin's debugging skill |
| Refactoring, restructuring, extracting, moving files | **Always** use `lbyl-refactoring` (full mode) — never another plugin's refactoring skill |
| Post-execution simplification | **Always** use `lbyl-refactoring` (quick mode) — never another plugin's code-simplifier skill |
| Skill quality review after creation | **Always** use `skill-review-standard` — post-creation quality gate |
| Webapp, E2E, or browser automation testing | **Always** use `webapp-testing` — installed from the vendored upstream skill pack |
| MCP server development | **Always** use `mcp-builder` — installed from the vendored upstream skill pack |
| Writing docs, specs, RFCs, or proposals | **Always** use `doc-coauthoring` — installed from the vendored upstream skill pack |
| Creating or improving a skill | **Always** use `lbyl-skill-creator` — Codex-native skill authoring and eval workflow |
| PR/commit workflow | "commit", "PR", "git" |

If no specialized skill exists, use the checklists and guides in `references/`.

### Brainstorming gate

Before invoking `lbyl-brainstorming`, check all 3 conditions:

1. There are at least 2 plausible approaches
2. The choice materially affects UX, API shape, data model, architecture,
   or long-term maintenance
3. The correct choice is not already implied by user direction or
   established repo patterns

If all 3 are true, use `lbyl-brainstorming`.

If any condition is false, skip brainstorming and continue with discovery,
planning, or execution as appropriate.

Do not route to brainstorming for bug fixes, audits, refactors, migrations,
template sweeps, visual polish with a known target, or execution of an
already-written plan.

### First-run onboarding

Codex has no Claude-style plugin lifecycle hooks, but this repo can install a
Codex-native guard through `codex-guard/guard.py` and a `[sandbox].setup`
entry in `~/.codex/config.toml`. If project-specific defaults are useful,
create a local `AGENTS.md`, initialize `.temp/plan-mode/`, document any
dep-map config explicitly, and make sure the installed guard path matches the
actual checkout. GPT-5.4 responds well to direct operating rules, exact
commands, and explicit acceptance criteria over long motivational framing.

### Skill feedback logging

When you are working in some other repo and discover that the LBYL skill pack
itself caused a bad workflow, misleading instruction, missed requirement, or
other usage error, log it back to the `codex-setup` repo.

Count it as a usage error when the problem is about the skill guidance rather
than the target repo's own code. Finish or stabilize the user's main task
first when possible, then log the incident before final closeout.

Resolve the repo path in this order:

1. `LBYL_CODEX_SETUP_REPO`
2. `~/Projects/codex-setup`
3. `~/projects/codex-setup`

Preferred flow:

1. Run `bash <repo>/scripts/log-usage-error.sh "short title"` to create the
   markdown stub in `<repo>/usage-errors/`.
2. Fill in the report with concrete evidence: what happened, what should have
   happened, why it is skill-related, and the smallest plausible fix.
3. Mention in your final response that you logged the usage error, or explain
   clearly if the repo was unavailable and you could not log it.

---

## Step 1: Explore (mandatory before any task)

Shallow exploration is the #1 cause of failed plans — every minute exploring
saves five minutes fixing.

Follow **engineering-discipline Phase 1** (Orient Before You Touch Anything).

Additionally, read `references/exploration-protocol.md` and answer all 8
questions. Exit criterion: confidence is Medium or higher. If Low, keep
exploring.

### Minimum exploration actions

<!-- deps-exploration-start -->
**If dep maps are configured** (check the project profile for the resolved
command): run `deps-query.py` on every file in scope BEFORE the steps below.
The output reveals consumers, cross-module dependencies, and blast radius
upfront — it shapes the entire exploration. For audits/reviews, run on key
entry points per module. If dep maps are NOT configured, skip this preamble.
<!-- deps-exploration-end -->

If dep maps are NOT configured and this is a TypeScript project, suggest
setting them up before large shared-code changes. Dep maps make consumer
finding and blast-radius analysis instant and complete.

1. Read the files in scope AND their imports
2. Find consumers of files in scope — use deps-query output if available,
   otherwise `Grep` for import statements
3. Read 2-3 sibling files to learn patterns
4. Check AGENTS.md/README for project conventions
5. Search for existing solutions before implementing from scratch

For complex or unfamiliar codebases, also read
`references/exploration-guide.md`.

### Refactoring tasks

If the task is a refactoring (rename across files, move files, extract
modules, restructure directories, split files, change naming conventions),
invoke `lbyl-refactoring` to structure the exploration.
Its Phase 1 (Inventory) replaces generic exploration with a **refactoring
contract** that catalogs every target, export, consumer, and test. This
contract becomes the verification checklist for the plan.

If dep maps are configured, the refactoring skill uses `deps-query.py` to
find consumers instantly. After the refactoring, it regenerates stale dep
maps so future queries reflect the new structure.

### Persist your findings

If the task requires exploration (anything beyond a trivial single-file
fix), create the plan directory and write findings to disk **before**
moving to Step 2:

```bash
bash ~/.codex/skills/lbyl-conductor/scripts/init-plan-dir.sh
mkdir -p .temp/plan-mode/active/<plan-name>
```

Write a `discovery.md` in that directory with what you found: file paths,
patterns, conventions, dependencies, blast radius, open questions. Use
the 8 questions from `references/exploration-protocol.md` as structure.

This file survives compaction and feeds directly into the plan's
discovery section. If you skip this, your future compacted self starts
from zero.

---

## Step 2: Plan (write to disk before editing code)

**You MUST invoke `lbyl-writing-plans` to produce the plan. Do NOT hand-write
`plan.json` or `masterPlan.md` as a substitute.**

A plan is invalid for execution if any of these are true:

- `plan.json` and `masterPlan.md` were hand-written instead of produced through
  `lbyl-writing-plans`
- the plan lacks the required `review` metadata
- `review.status` is not `approved` and the user did not explicitly skip Orbit
  review
- any step sets `claudeVerify: false` without an explicit user opt-out

If the plan is invalid, stop, repair the plan path first, and only then
continue to execution.

The skill consumes your discovery.md, identifies applicable discipline
checklists, structures TDD-granularity steps, and writes both:
- `plan.json` — execution source of truth (Codex reads and updates this during execution)
- `masterPlan.md` — user-facing proposal for Orbit review (write-once, frozen after approval)

Follow **persistent-plans Phase 1** (Create the Plan) for the structural
rules — the writing-plans skill handles the content.

Initialize the plan directory if needed:
```bash
bash ~/.codex/skills/lbyl-conductor/scripts/init-plan-dir.sh
```

### Plan review via Orbit

After writing the plan, present masterPlan.md to the user for review
using the Orbit MCP. The `writing-plans` skill handles the details, but
the flow is:

1. If the Orbit MCP is available, call `orbit_await_review` on the
   masterPlan.md — it opens in VS Code and
   blocks until the user approves or requests changes
2. Handle the response (approved → proceed, changes_requested → iterate)
3. Once approved, summarize the plan for the user and proceed unless they
   explicitly ask for more changes or to stop after planning

Record the Orbit result back into `plan.json.review` before execution:

- `status: "approved"`
- `reviewedVia: "orbit"`
- `approvedAt: <timestamp>`
- `skipReason: null`

After approval, the default is to **continue through implementation**. Do
not stop for another approval just because execution uncovers adjacent
in-scope follow-through. Update plan.json and keep going unless the newly
discovered work is a material scope or tradeoff change.

If Orbit MCP tools are unavailable or fail unexpectedly, treat that as a
setup problem to surface explicitly to the user. Do not silently fall back
to a weaker manual review flow.

Exception: the user explicitly says "just do it" or "no plan" for a trivially
obvious single-line change. In that case, record `review.status: "skipped"`
with a concrete `skipReason` tied to the user's instruction.

---

## Step 3: Execute (the loop)

Follow **persistent-plans Phase 2** (Execute the Plan) for the execution
loop, checkpointing, and result tracking. Follow **engineering-discipline
Phase 2** (Make Changes Carefully) for the rules applied during execution.

Use this post-approval rule during execution:

- **Non-material follow-through** — update only plan.json and continue.
  Examples: mirrored fixes in equivalent copies, adjacent consistency
  updates, extra verification, or cleanup/tests/docs needed to make the
  approved work correct.
- **Material scope or tradeoff change** — stop and get user confirmation,
  then present a revised plan for review if needed.

For refactoring tasks, also follow the execution order from
`lbyl-refactoring` Phase 3 — it minimizes broken
intermediate states (e.g., create at new location first, then update
consumers, then delete old location). After all changes, its Phase 4
verifies against the contract and regenerates stale dep maps.

The sections below cover behavior that is unique to the conductor and not
covered in the companion skills.

### Invalid plan gate

Before marking any step `in_progress`, validate the active `plan.json`.
Execution must stop if any of these are true:

- `review.status` is missing
- `review.status` is `pending`
- `review.status` is `skipped` but there is no explicit user instruction to
  skip Orbit review
- any step has `claudeVerify` missing
- any step has `claudeVerify: false` without an explicit user opt-out

If the plan fails validation, do not keep coding and do not "fix it later."
Repair the plan first, then resume execution.

### Execution routing

`skill` and `executor` are still separate in this repo's execution format, but
`executor` is conductor-owned output rather than planner-authored input:

- `skill` = which guidance Codex should follow
- `routingHint` = optional planner hint (`auto`, `codex`, `claude`, `visual`)
- `executor` = who the conductor resolved to perform the implementation work

Execution rules:

- If `executor: "codex"`, implement the step locally as usual.
- If `executor: "claude"`, call the `claude-bridge` `frontend_implement`
  tool with discovery/design context, exact step scope, and any Codex
  follow-up prompt. Claude edits the same working tree directly.
- Brainstorming uses the live Claude path via `claude-bridge`
  `brainstorm_start` and `brainstorm_status`, not the headless worker path.

The planner may provide `routingHint`, but the conductor resolves the final
executor before execution. The default bias is Codex. Route to Claude only
for materially visual work such as layout, styling, spacing, typography,
color, motion, responsive presentation, or theme/token changes that alter
rendered output.

### Guarded execution

If `codex-guard` is installed for the repo, execution should use it as the
hard-default gate:

1. `python3 codex-guard/guard.py validate-plan`
2. `python3 codex-guard/guard.py begin-step <N>`
3. edit only the unlocked step files
4. `python3 codex-guard/guard.py checkpoint` every 2-3 file edits
5. after local verification and Claude PASS, `python3 codex-guard/guard.py complete-step <N>`

This is the Codex-native analogue for the Claude plugin's hook-time write
gates. It is not identical to hooks, but it preserves the same intent:
validated plans, explicit step ownership, and a completion gate that depends
on real verification.

`validate-plan` is also the routing checkpoint: it runs the conductor's
executor resolver and stamps each step with conductor-owned routing metadata
before execution can proceed.

### Dispatching sub-agents

When a step benefits from parallel work (audits, multi-area exploration,
independent file groups), choose the right dispatch mode:

**Foreground parallel** (default):
Use when results inform your next steps or have cross-cutting concerns.
All agents run in parallel, you see all results before proceeding. Use
for: audits, exploration, reviews, any task where one finding might
affect another agent's scope.

**Background** (fire-and-forget only):
Use only when you have genuinely independent work to continue in the
main thread. You must poll the child agent later — no automatic
cross-pollination. Use for: running builds/tests while continuing edits.

**Rule of thumb**: if you'd want to read Agent A's results before acting
on Agent B's results, use foreground. Background agents are isolated by
default.

### Shared discovery (cross-agent communication)

For parallel tasks where agents benefit from seeing each other's findings
(audits, multi-area exploration, large codebase research), agents share a
single discovery file:

**Location**: `.temp/plan-mode/active/<plan-name>/discovery.md`

This file is created during Step 1 (Explore) when the plan directory is
set up. When dispatching sub-agents, pass the active plan path and this
discovery path explicitly.

**Writing** — use Bash append (`>>`), never `Edit`. Multiple agents write
concurrently, and append is atomic at the OS level:
```bash
printf '\n## [your-focus-area]\n- **[severity]** `file:line` — finding (evidence: ...)\n' >> discovery.md
```

**Reading** — read the file periodically to see other agents' findings,
but treat them as **informational context only**:
- Other findings may be wrong, incomplete, or irrelevant to your scope
- Do NOT change your investigation direction based on them
- Only note a cross-reference if you independently confirm a connection

After all agents complete, read the consolidated `discovery.md` to
synthesize results.

### Post-step simplification

When a completed step has `simplify: true` in plan.json, dispatch a
refactoring sub-agent (quick mode) after marking the step `done`:

1. **Run tests first** — establish a passing baseline before dispatch
2. **Dispatch** the `refactoring` sub-agent in quick mode (foreground) with:
   - The step number and its `files` list from plan.json
   - The active plan path
3. **After the agent returns**, record its simplification summary in the
   step's `result` field
4. If the agent reverted changes due to test failures, note that too

The simplifier is opt-in per step. The `writing-plans` skill decides which
steps warrant it based on complexity (3+ files modified, new abstractions,
structural changes, or user request). Do not dispatch it for steps without
`simplify: true`.

---

## Step 4: Verify (every time, no exceptions)

Follow **engineering-discipline Phase 3** (Verify Before Declaring Done).

See `references/verification-commands.md` for framework-specific commands.
Always check the project's own scripts first (package.json, Makefile).

After local verification, check the step's `claudeVerify` field in
`plan.json`:

- If `false`, you may mark the step `done` after normal verification.
- If `true`, Claude verification is a hard gate. Call `claude-bridge`
  `verify_step` before marking the step `done`.
- If `verify_step` returns non-PASS, fix the issues, then call `verify_step`
  again on the same `bridgeSessionId`.
- If `claude-bridge` is unavailable, stop and surface the setup failure.

Non-PASS rounds should produce JSON findings under the configured
`usage-errors/claude-findings` path. PASS should not write a findings file.

Before declaring done, re-read the user's original request word by word.
Confirm every requirement is implemented and working. If anything is
unaddressed, finish it or explicitly flag it.

If the active plan's steps are all `done`, finalize the plan before the
final user closeout:

```bash
python3 .temp/plan-mode/scripts/plan_utils.py complete-plan .temp/plan-mode/active/<plan-name>/plan.json
```

Do not leave a fully executed plan sitting in `active/`. The work is not
closed out until the plan has been finalized and moved to `completed/`.

---

## Compaction Survival Protocol

Follow **persistent-plans Phase 3** (Resumption After Compaction).

Helper scripts:
```bash
bash .temp/plan-mode/scripts/plan-status.sh    # see all plan states
bash .temp/plan-mode/scripts/resume.sh         # find what to pick up
```

---

## Codex-Specific Operating Notes

Codex does not have Claude plugin hooks or plan mode. That means the process
here is enforced by explicit skill text, local `AGENTS.md`, on-disk plans,
helper scripts, and Orbit-backed review tooling.

- Treat plan creation, Orbit review, plan checkpoints, and verification as
  hard requirements even when nothing blocks you automatically.
- `plan.json` is the execution source of truth. `masterPlan.md` is the
  frozen user-facing proposal reviewed through Orbit.
- When dispatching sub-agents, include the active plan path and any shared
  discovery path in the prompt explicitly.
- Orbit review should use `orbit_await_review` when available; do not fall
  back to a weaker manual flow unless the user explicitly asks to skip Orbit
  or Orbit is unavailable and you surface that setup issue.
- Skill-pack usage errors discovered in other repos should be written back to
  the `codex-setup` checkout under `usage-errors/` before final closeout when
  feasible.

---

## Reference Files

All paths relative to `~/.codex/skills/lbyl-conductor/`:

### Process & Templates
- `references/exploration-protocol.md` — 8-question exploration checklist
- `references/exploration-guide.md` — deep exploration techniques
- `references/plan-schema.md` — plan.json schema (execution source of truth)
- `references/master-plan-format.md` — masterPlan.md template (user-facing proposal)
- `references/agents-md-snippet.md` — recommended AGENTS.md addition
- `usage-errors/README.md` in the resolved `codex-setup` checkout — usage-error report format and logging rules

### Discipline Checklists (Layer 2)
- `references/testing-checklist.md` — before/during/after testing
- `references/ui-consistency-checklist.md` — design tokens, components, visual consistency
- `references/frontend-design-checklist.md` — accessibility, responsive, performance, coherence for frontend design
- `references/security-checklist.md` — auth, input validation, secrets
- `references/git-checklist.md` — commits, branches, messages
- `references/linting-checklist.md` — linter and formatter discipline
- `references/dependency-checklist.md` — package management and verification
- `references/api-contracts-checklist.md` — API boundary discipline

### Deep Guides (Layer 3)
- `references/testing-strategy.md` — TDD-lite, test pyramid, edge cases, test theater
- `references/ui-consistency-guide.md` — design tokens, component discipline, drift detection
- `references/frontend-design-guide.md` — aesthetic axes, font sourcing, animation, color, anti-slop blacklist
- `references/anti-slop.md` — shared cross-skill anti-AI-slop banlist for typography, color, layout, animation, illustration, and copy
- `references/color-palettes.md` — curated light/dark semantic palettes for frontend design work
- `references/security-guide.md` — OWASP Top 10, S.E.C.U.R.E. framework, slopsquatting
- `references/api-contracts-guide.md` — API boundary discipline, shared schema enforcement
- `references/debugging-root-cause-tracing.md` — trace bugs backward through call stack to source
- `references/debugging-defense-in-depth.md` — multi-layer validation after fixing root cause
- `references/debugging-condition-based-waiting.md` — replace arbitrary timeouts with condition polling
- `references/dependency-mapping.md` — dep map configuration, module setup, query usage

### Operational
- `references/verification-commands.md` — type checker/linter/test commands by ecosystem
- `references/recommended-plugins.md` — suggested companion tooling for onboarding
- `scripts/init-plan-dir.sh` — initialize `.temp/plan-mode/` directory
- `scripts/plan-status.sh` — show status of all active plans
- `scripts/resume.sh` — find what to resume after compaction
- `scripts/plan_utils.py` — read/update plan.json and finalize completed plans from Codex sessions and helper scripts
- `scripts/deps-query.py` — query dependency maps for consumers and dependencies
- `scripts/deps-generate.py` — generate or regenerate dependency maps
