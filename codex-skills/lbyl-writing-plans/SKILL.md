---
name: lbyl-writing-plans
description: "Use after discovery to write implementation plans with TDD-granularity steps. Produces plan.json (immutable plan definition), progress.json (mutable execution state created on first mutation), and masterPlan.md (user-facing proposal for Orbit review). Every step is one component/feature; TDD rhythm (test, verify fail, implement, verify pass, commit) lives in its progress items. Codex drafts and finalizes the plan locally from discovery and dep-partition context, and Orbit reviews the result. Consumes discovery.md from exploration phase. Invoke explicitly at Step 2 of the conductor. Do NOT use when: the user explicitly says 'just do it' or 'no plan', resuming an existing plan (use persistent-plans resumption protocol), executing a plan that already exists on disk, or doing pure research/exploration without code changes."
---

# Writing Plans

Turn discovery findings into bite-sized implementation plans. Assume the
implementing engineer has zero context for this codebase and questionable
taste. Document everything they need: which files to touch, precise
descriptions with file paths, exact commands, expected output. Give them
the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

**Announce at start:** "I'm using the writing-plans skill to create the
implementation plan."

**Prerequisite:** Discovery must be complete. If no `discovery.md` exists
in the plan directory, go back to Step 1 (Explore) first.

---

## The Steps

### 1. Read the discovery

Read `discovery.md` from `.temp/plan-mode/active/<plan-name>/`. This is the
raw exploration log — an append-only markdown file written during Step 1.

**Discovery flow** (each written once, never updated during execution):
1. **`discovery.md`** — raw exploration log (may have duplicates, rough notes)
2. **`plan.json.discovery`** — structured extraction: the 8 discovery fields
   distilled from the raw log into clean, self-contained summaries
3. **`masterPlan.md` Discovery Summary** — human-readable rendering of the
   same findings for Orbit review

Read discovery.md and extract what you need into plan.json's `discovery`
object. masterPlan.md's Discovery Summary is a human rendering of the same
data — both are written once during planning, then frozen.

If dep maps are configured, the discovery MUST include `deps-query.py` output
for every file in scope. If the discovery lacks deps-query output for a
TypeScript project, go back to Step 1 (Explore) and run it before planning.

**design.md**: If the brainstorming skill produced a `design.md` in the same
plan directory, read it — it contains approved design decisions that must
inform the plan. Reference specific design decisions in step descriptions
where relevant (e.g., "Per design.md: use composition over inheritance for
the validator chain").

### 2. Identify applicable disciplines

Scan the task and mark which checklists apply. Read each relevant checklist
now — they inform how you structure the steps.

| If the task involves... | Read before planning... |
|---|---|
| Writing or modifying tests | `references/testing-checklist.md` |
| Building or modifying UI | `references/frontend-design-checklist.md` + `references/ui-consistency-checklist.md` |
| Auth, input validation, secrets | `references/security-checklist.md` |
| Adding/removing packages | `references/dependency-checklist.md` |
| API route handlers or endpoints | `references/api-contracts-checklist.md` |

Also note these for the executing engineer (they apply during execution,
not planning):

- **git-checklist.md** — applies at every commit step
- **linting-checklist.md** — applies after any code changes

### 3. Build dep-partition context before drafting

If dep maps are configured, convert the target set into machine-readable
planning context before drafting the plan locally.

1. Identify the entry-point files that define the scope.
2. Run the dep-partition helper on those files:

```bash
python3 ~/.codex/skills/lbyl-conductor/scripts/dep_partition.py <project_root> <file_path> [<file_path> ...]
```

3. Save the JSON in the active plan directory as `dep-partition.json`.
4. Use that file as planning input, not just as notes. It should shape:
   - which files stay in the same step
   - where a sub-plan is mandatory
   - which groups are safe to parallelize later
   - which cross-module boundaries should be tackled earlier

If dep maps are not configured, skip this file and document that the plan is
relying on manual blast-radius judgment.

### 4. Draft the plan locally in Codex

Codex is the default plan author in this workflow. Use the current session's
discovery, dep-partition context, and applicable discipline checklists to
write the plan directly.

Write both files locally:

- `plan.json`
- `masterPlan.md`

Treat `dep-partition.json` as a planning aid, not a decorative artifact. Use
it to decide:

- which files belong in the same step
- which groups should remain serial because of shared contracts
- which groups are good candidates for later sub-agent delegation
- where a sub-plan is mandatory

### 5. Review and finalize the local draft

Produce **both** files in `.temp/plan-mode/active/<plan-name>/`:

#### plan.json — immutable plan definition

Use the schema from `references/plan-schema.md`. Codex reads this file as the
definition and merges it with `progress.json` during execution. Ensure the
local draft includes:

- All discovery findings in the `discovery` object
- A top-level `review` object initialized for Orbit gating
- Steps with TDD-granularity progress items
- Inline sub-plans for large steps (see Step 4 below)
- Exact skill identifiers in `skill` fields
- Optional `routingHint` values on steps when the default Codex bias would be wrong
- `claudeVerify: true` on every step unless the user explicitly opts out

The initial `review` object must be:

```json
{
  "status": "pending",
  "reviewedVia": "orbit",
  "approvedAt": null,
  "skipReason": null
}
```

`codex-guard validate-plan` consumes these fields directly. If review metadata
is missing or malformed, the plan is not only process-invalid; it will also
fail the Codex-side execution gate when the guard is installed.

#### masterPlan.md — user-facing proposal (write-once)

This is the document the user reviews via Orbit. It communicates **intent**,
not execution state. **It is frozen after Orbit approval** — never updated
during execution. Runtime status, results, summaries, and deviations live in
`progress.json`.

This freeze does **not** mean execution should stop for another approval
every time adjacent follow-through is discovered. After approval, keep
executing through the approved objective. If you discover non-material
follow-through that is clearly in service of the same objective, update the
plan definition in `plan.json` and continue. Reserve a new Orbit review for material scope
or tradeoff changes (see "Updating an approved plan" below).

Use the template from `references/master-plan-format.md`. No `[x]`/`[ ]`
checkboxes. No execution state. Just what, why, and what could go wrong.

After writing the draft, read both files from disk and review them
critically:

- keep changes that match repo conventions and the user request
- correct any repo-specific misses or overreach
- preserve useful dep-partition boundaries unless there is a concrete reason
  to merge or reorder them
- keep Codex as the final local reviewer before Orbit

#### Step granularity: how steps map to TDD

One plan.json step = one component or feature unit. The TDD rhythm lives
in the **progress** array within each step.

**The key insight: each step must have MULTIPLE red-green cycles.** Don't
write all tests at once — that's speculative testing, not TDD. Instead,
break the behavior into slices and iterate: simplest case first, then add
complexity one behavior at a time. Each cycle adds 1-3 tests for one
specific behavior, then implements just enough to pass.

```json
{
  "id": 1,
  "title": "Email validation utility",
  "status": "pending",
  "skill": "lbyl-test-driven-development",
  "simplify": false,
  "files": ["src/lib/validate-email.ts", "tests/lib/validate-email.test.ts"],
  "description": "Add email validation function. Rejects empty strings, missing @, missing domain.",
  "acceptanceCriteria": "npx vitest run validate-email passes, tsc --noEmit clean.",
  "progress": [
    {"task": "Cycle 1 RED: test for simplest valid email", "status": "pending", "files": ["tests/lib/validate-email.test.ts"]},
    {"task": "Cycle 1 GREEN: implement basic validation", "status": "pending", "files": ["src/lib/validate-email.ts"]},
    {"task": "Cycle 2 RED: tests for empty string and missing @", "status": "pending", "files": ["tests/lib/validate-email.test.ts"]},
    {"task": "Cycle 2 GREEN: add rejection logic", "status": "pending", "files": ["src/lib/validate-email.ts"]},
    {"task": "Cycle 3 RED: tests for missing domain and edge cases", "status": "pending", "files": ["tests/lib/validate-email.test.ts"]},
    {"task": "Cycle 3 GREEN: handle remaining cases", "status": "pending", "files": ["src/lib/validate-email.ts"]},
    {"task": "Refactor and final verification", "status": "pending"}
  ],
  "subPlan": null,
  "result": null
}
```

Each progress item is one action (2-5 minutes). Notice the pattern:
alternating RED/GREEN items, each covering a slice of behavior. The
simplest case comes first. Aim for **3-5 cycles per step** — enough to
prove incrementalism without being tedious.

**Anti-pattern to avoid:** A single "Write all tests" item followed by a
single "Implement everything" item. That's test-first waterfall, not TDD.
The whole point of TDD is that each cycle's implementation informs what
the next cycle should test.

#### When to set `simplify: true`

Set `simplify: true` on a step when any of these apply:

- Step modifies **3 or more files**
- Step creates **new abstractions** (utilities, components, modules)
- Step involves **structural changes** (refactored APIs, new patterns)
- User **explicitly requests** simplification for the step

Default to `false` for simple steps.

#### Key rules

- **Exact skill identifiers** — in each step's `skill` field, use the full
  skill name (e.g., `lbyl-frontend-design`), never vague
  hints. Post-compaction Codex has no memory — only exact names work.
  Use `"none"` for steps that don't need a specialized skill. This includes
  the Codex-native `lbyl-*` skills and any exact upstream skill names that
  are installed from the vendored tree, such as `immersive-frontend`,
  `react-native-mobile`, `svg-art`, `webapp-testing`, `mcp-builder`,
  `doc-coauthoring`, and `skill-review-standard`.
- **Separate skill from routing hint** — `skill` is the guidance Codex
  follows. `routingHint` is only an optional nudge for the conductor. The
  real `executor` is resolved later by the conductor and should not be treated
  as planner-owned source of truth.
- **Precise descriptions with file paths** — not vague "add validation" but
  specific what-to-do with exact file paths and acceptance criteria. Plans
  describe *what* to build; the executing engineer writes the code.
- **Exact file paths** — every step lists files in the `files` array
- **Include repo-mandated companion docs up front** — if AGENTS, CLAUDE.md,
  or repo-local conventions require inventory or structure docs (for example
  `.claude/project-structure/*`) to change alongside code, include those
  files in the step's `files` array and progress items instead of letting
  them appear later as surprise scope.
- **Exact commands with expected outcome** — in description or acceptance
  criteria, include the command and expected result
- **Self-contained** — the plan.json is the ONLY thing the executing
  engineer reads. If it's not in the plan, it doesn't exist for them
- **DRY / YAGNI** — cut anything not clearly needed right now
- **Frequent commits** — after every green test or logical unit of work

#### Execution-agent routing

When setting `routingHint`, use this rule set:

- Omit it or set `routingHint: "auto"` for the normal case. The conductor
  should then default to Codex.
- Set `routingHint: "visual"` or `routingHint: "claude"` only when the step
  materially changes visual presentation: layout, styling, spacing,
  typography, color, motion, responsive presentation, or theme/design-token
  work that changes rendered output.
- Set `routingHint: "codex"` only when you need to override an otherwise
  ambiguous step back toward Codex.

Do not treat touching frontend files as sufficient reason to route to Claude.
Copy-only or behavior-only changes should still resolve to Codex.

Every step should also carry `claudeVerify: true` in this repo's default
workflow. Claude verification is a hard gate before `done`.

### 6. Evaluate sub-plan needs (mandatory checkpoint)

**Before saving the plan, evaluate EVERY step against these criteria:**

For each step, count the files in its `files` array. If ANY of these are
true, the step MUST have an inline `subPlan` with groups:

1. **More than 10 files** in the `files` array
2. **Repetitive sweep** — the description contains words like "all", "every",
   "sweep", "migrate all", "across the codebase"
3. **More than 5 progress items** that are independently completable
4. **More than 8 files to read** just to understand what to change
5. **The step is a migration** that touches the same pattern in many files

If ANY criterion is met, restructure the step NOW:

```json
{
  "subPlan": {
    "groups": [
      {"name": "Dashboard pages", "files": ["a.tsx", "b.tsx", "c.tsx"], "status": "pending", "notes": null},
      {"name": "Modal components", "files": ["d.tsx", "e.tsx"], "status": "pending", "notes": null}
    ]
  }
}
```

Groups should have 3-8 files each. If a group exceeds 8, split it.

**This is a hard checkpoint.** Do not proceed to Step 7 until every step
has been evaluated. If you skip this, large steps will fail mid-execution
when context runs out.

### 7. Optional Claude attack pass for high-risk drafts

The default plan-authoring pass already came from Codex. An adversarial Claude
pass is optional and should be reserved for large, risky, or materially edited
drafts.

Use `claude-bridge` `attack_plan` only when one of these is true:

- the plan is large or high-blast-radius
- Codex materially revised the locally drafted plan
- the sequencing or verification strategy still feels fragile
- the user explicitly asks for extra pressure-testing

When you do run it:

1. Call `claude-bridge` `attack_plan` with the current cwd, the plan name,
   the `plan.json` path, the `masterPlan.md` path, and any concise summary of
   the user goal or constraints that Claude should pressure-test.
2. Read the returned findings as adversarial review, not as automatic truth.
3. Update `plan.json` and `masterPlan.md` only for findings that are actually
   relevant to the repo, user request, and discovery evidence.
4. If Claude proposes irrelevant, speculative, or already-covered changes,
   reject them and keep the draft as-is.

If you skip this pass, that is acceptable in the default Codex-led planning
flow. Do not invent a fake attack result.

### 8. Present for review via Orbit

After saving both files to disk, present masterPlan.md to the user for
interactive review using the Orbit MCP:

1. Tell the user: *"The plan is open in VS Code for review. Add inline
   comments on any section, then click Approve or Request Changes."*
2. If the Orbit MCP is available, call `orbit_await_review` with the
   masterPlan.md path. This generates
   the artifact, opens it in VS Code, and **blocks** until the user clicks
   Approve or Request Changes.

If Orbit MCP tools are unavailable or fail unexpectedly, stop and surface
the setup issue instead of silently skipping review.

#### Handle the response

`orbit_await_review` returns JSON with `status` and `threads`.

- **`approved`, no threads** → proceed to step 9.
- **`approved`, with threads** → read each thread, reply with
  `orbit_reply` acknowledging the feedback, resolve threads, then proceed
  to step 9.
- **`changes_requested`** → read all threads. Update both masterPlan.md
  and plan.json to address the feedback. Reply to each thread explaining
  what changed. Resolve threads. Call `orbit_await_review` again for
  re-review. Loop back to handle the new response.
- **`timeout`** → tell the user the review timed out and ask them to
  review when ready.

When the review is approved, update `plan.json.review` before execution:

```json
{
  "status": "approved",
  "reviewedVia": "orbit",
  "approvedAt": "<timestamp>",
  "skipReason": null
}
```

### 9. Summarize and proceed (post-approval)

After the plan is approved via Orbit:

1. Read the plan.json and masterPlan.md you just wrote from disk.
2. Summarize the approved plan to the user with the key steps, files
   involved, and acceptance criteria.
3. Proceed into execution unless the user explicitly asks for more plan
   revisions or says to stop after planning.

From this point forward, the default is **continue execution**. Do not ask
for another approval just because you found adjacent consistency work,
mirrored fixes, extra verification, or other non-material follow-through
needed to finish the approved objective correctly.

### Updating an approved plan

If execution uncovers work that was not spelled out in masterPlan.md:

- **Non-material follow-through** → update only plan.json and continue.
  This includes adjacent consistency fixes, mirrored changes in equivalent
  copies, extra verification, docs/tests/cleanup needed to make the
  approved work correct, or small step additions in the same area.
- **Material scope or tradeoff change** → stop and get fresh review before
  proceeding. Update plan.json to reflect the newly discovered work, then
  present a revised masterPlan.md through Orbit.

Treat a change as **material** when any of these are true:

- It changes the user-visible goal or acceptance criteria in a meaningful way
- It introduces a new product, UX, API, or architecture direction
- It expands into a substantially new subsystem or unrelated file area
- It requires a risky, destructive, or irreversible action not covered by
  the approved plan

Record all post-approval additions in plan.json. Use the `deviations`
array when execution meaningfully diverges from the approved baseline,
even if the change is still non-material enough to avoid a new review.

---

## Boundaries

This skill must NOT:

- **Create plans outside `.temp/plan-mode/`** — all plans live in the
  defined directory structure, nowhere else.
- **Modify discovery.md during planning** — discovery is read-only input.
  If you find gaps, go back to Step 1 (Explore) first.
- **Overwrite an existing plan without user consent** — if a plan already
  exists in the target directory, ask before replacing it.
- **Skip the Orbit review** — every plan must be presented to the user
  for review via Orbit MCP before execution unless the user explicitly says
  to skip review, in which case `plan.json.review.status` must be set to
  `skipped` with a concrete `skipReason`.
- **Allow a hand-written substitute plan** — if `lbyl-writing-plans` did not
  generate the files, the plan is invalid and must not be executed.
- **Hide delegation structure** — plans must make clear which work stays in
  the conductor, which file groups are good sub-agent candidates, and what
  artifacts those agents write back to disk.
- **Pretend Codex can self-clear context** — if a task risks overrunning the
  main session, write the state to disk and plan for fresh-session continuation
  instead of inventing an in-session `/clear` workflow.
- **Pretend `masterPlan.md` is the runtime tracker** — execution state
  belongs in `plan.json`, not in the Orbit-reviewed proposal.
- **Write implementation code** — this skill produces plans, not code files.
- **Skip the sub-plan evaluation** — Step 4 is mandatory for every plan.

**Autonomy limits**: reading discovery, reading checklists, writing plan
files, writing sub-plans, and updating plan.json for non-material
post-approval follow-through are autonomous. Overwriting an existing plan,
skipping Orbit review for a non-trivial plan, and materially changing an
approved plan require user confirmation.

**Prerequisites**: this skill is always invoked via `lbyl-conductor` at
Step 2. Discovery must be complete (`discovery.md` must exist in the plan
directory).

---

## Principles

- **Zero-context, questionable taste** — spell everything out; don't trust
  the engineer to make good test design or naming decisions
- **One component per step** — TDD rhythm in progress items, not separate steps
- **TDD by default** — test first, then implement, always
- **Precise descriptions** — never write vague "add error handling"; specify
  exactly what to do, which files, and how to verify. Plans describe intent;
  the executing engineer writes the code.
- **masterPlan.md is write-once** — frozen after Orbit approval. All runtime
  state lives in progress.json
- **Codex drafts and finalizes** — use discovery and dep-partition context to
  write the first draft locally; Claude is optional later for UI execution or
  independent verification, not for default plan authoring
- **Approved plan means proceed** — after Orbit approval, keep executing
  unless a material scope/tradeoff change requires a fresh review
- **DRY / YAGNI** — only what's needed now, nothing speculative
- **Sub-plans are mandatory** — if a step meets the criteria, it gets one
