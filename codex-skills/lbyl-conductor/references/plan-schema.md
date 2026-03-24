# plan.json Schema

The immutable plan definition for every plan. Codex reads this file and
merges it with `progress.json` to track runtime state. `masterPlan.md` is the
human-facing presentation document — it does NOT contain execution state.

## Location

```text
.temp/plan-mode/active/<plan-name>/plan.json
.temp/plan-mode/active/<plan-name>/progress.json
```

## Full Schema

```json
{
  "name": "plan-name-kebab-case",
  "title": "Descriptive Title",
  "context": "What the user asked for — enough for a fresh context window to understand the task without the original conversation.",
  "status": "active",
  "requiredSkills": ["lbyl-frontend-design"],
  "disciplines": ["testing-checklist.md", "security-checklist.md"],
  "review": {
    "status": "pending",
    "reviewedVia": "orbit",
    "approvedAt": null,
    "skipReason": null
  },
  "discovery": {
    "scope": "Files/directories in scope. Be explicit about boundaries.",
    "entryPoints": "Primary files to modify and their current state.",
    "consumers": "Who imports/uses the files you're changing. Include file paths.",
    "existingPatterns": "How similar problems are already solved in this codebase.",
    "testInfrastructure": "Test framework, where tests live, how to run them.",
    "conventions": "Project-specific conventions from AGENTS.md or observed patterns.",
    "blastRadius": "What could break if you get this wrong.",
    "confidence": "high"
  },
  "steps": [
    {
      "id": 1,
      "title": "Step title",
      "status": "pending",
      "skill": "none",
      "routingHint": "auto",
      "executor": "codex",
      "routingReason": "auto-routed to Codex because default Codex bias for non-visual engineering work",
      "routingResolvedAt": "2026-03-24T00:00:00+00:00",
      "routingResolvedBy": "lbyl-conductor",
      "claudeVerify": true,
      "simplify": false,
      "files": ["src/foo.ts", "src/bar.ts"],
      "description": "What needs to happen. Specific enough for a fresh context window.",
      "acceptanceCriteria": "Concrete, verifiable conditions (e.g., 'tsc --noEmit passes').",
      "progress": [
        {"task": "Sub-task description", "status": "pending", "files": ["src/foo.ts"]},
        {"task": "Another sub-task", "status": "pending", "files": ["src/bar.ts"]}
      ],
      "subPlan": null,
      "result": null
    },
    {
      "id": 2,
      "title": "Large sweep step",
      "status": "pending",
      "skill": "none",
      "routingHint": "visual",
      "executor": "claude",
      "routingReason": "routingHint 'visual' explicitly requested Claude ownership",
      "routingResolvedAt": "2026-03-24T00:00:00+00:00",
      "routingResolvedBy": "lbyl-conductor",
      "claudeVerify": true,
      "simplify": false,
      "files": ["a.tsx", "b.tsx", "c.tsx", "d.tsx"],
      "description": "A step large enough to warrant a sub-plan.",
      "acceptanceCriteria": "All files updated, tsc clean.",
      "progress": [
        {"task": "Group 1: Dashboard pages", "status": "pending", "files": ["a.tsx", "b.tsx"]},
        {"task": "Group 2: Modal components", "status": "pending", "files": ["c.tsx", "d.tsx"]}
      ],
      "subPlan": {
        "groups": [
          {"name": "Dashboard pages", "files": ["a.tsx", "b.tsx"], "status": "pending", "notes": null},
          {"name": "Modal components", "files": ["c.tsx", "d.tsx"], "status": "pending", "notes": null}
        ]
      },
      "result": null
    }
  ],
  "blocked": []
}
```

## progress.json Schema

```json
{
  "steps": {
    "1": {
      "status": "in_progress",
      "result": "Implemented and verified",
      "progress": [
        {"status": "done"},
        {"status": "pending"}
      ],
      "groups": {
        "0": {"status": "done", "notes": "Finished first sweep"}
      }
    }
  },
  "completedSummary": ["Step 1: implemented the API change"],
  "deviations": ["Used shared helper instead of duplicating logic"]
}
```

## Field Reference

### Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | kebab-case plan name (matches directory name) |
| `title` | string | yes | Human-readable title |
| `context` | string | yes | What the user asked for — survives compaction |
| `status` | string | yes | `"active"` or `"completed"` |
| `requiredSkills` | string[] | yes | Exact skill identifiers (empty array if none) |
| `disciplines` | string[] | yes | Checklist filenames that apply |
| `review` | object | yes | Orbit review state for execution gating |
| `discovery` | object | yes | All 8 exploration sections |
| `steps` | Step[] | yes | Ordered list of execution steps |
| `blocked` | string[] | yes | Blocked step descriptions (empty if none) |

**Note:** `completedSummary` and `deviations` are mutable fields that live in
`progress.json`.

### Review fields

| Field | Type | Required | Description |
|---|---|---|---|
| `status` | string | yes | `pending`, `approved`, or `skipped` |
| `reviewedVia` | string | yes | Usually `orbit` |
| `approvedAt` | string/null | yes | Approval timestamp, null before approval |
| `skipReason` | string/null | yes | Required when `status` is `skipped` |

### Step fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | number | yes | Sequential step number (1-based) |
| `title` | string | yes | Step title |
| `status` | string | yes | **Mutable** — initial: `pending`. Runtime value lives in `progress.json`. |
| `skill` | string | yes | Skill to invoke, or `"none"` |
| `routingHint` | string | no | Optional planner hint: `auto`, `codex`, `claude`, or `visual` |
| `executor` | string | yes | Conductor-resolved implementation owner: `codex` or `claude` |
| `routingReason` | string | yes | Why the conductor chose the executor |
| `routingResolvedAt` | string | yes | Timestamp when the conductor resolved routing |
| `routingResolvedBy` | string | yes | Always `lbyl-conductor` in the Codex workflow |
| `claudeVerify` | boolean | yes | Whether Claude verification is a hard pre-`done` gate |
| `simplify` | boolean | yes | Whether to run simplification after step |
| `files` | string[] | yes | Files involved in this step |
| `description` | string | yes | What to do — self-contained for fresh context |
| `acceptanceCriteria` | string | yes | How to know the step is done |
| `progress` | Progress[] | yes | Sub-task checklist (empty array for simple steps) |
| `subPlan` | SubPlan? | no | Inline sub-plan for large steps (null if none) |
| `result` | string? | no | **Mutable** — initial: null. Runtime value lives in `progress.json`. |

### Progress item fields

| Field | Type | Required | Description |
|---|---|---|---|
| `task` | string | yes | Sub-task description |
| `status` | string | yes | **Mutable** — runtime value lives in `progress.json`. One of: `pending`, `in_progress`, `done` |
| `files` | string[] | no | Files involved in this sub-task |

### SubPlan fields

| Field | Type | Required | Description |
|---|---|---|---|
| `groups` | Group[] | yes | Ordered list of file groups |

### Group fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Logical cluster name |
| `files` | string[] | yes | Files in this group |
| `status` | string | yes | **Mutable** — runtime value lives in `progress.json`. One of: `pending`, `in_progress`, `done` |
| `notes` | string? | no | **Mutable** — runtime value lives in `progress.json`. Execution notes (null before, filled during) |

## Status Values

Steps, progress items, and groups all use the same status values:

| Value | Meaning |
|---|---|
| `pending` | Not yet started |
| `in_progress` | Currently being worked on |
| `done` | Complete and verified |
| `blocked` | Cannot proceed (steps only) |

## Claude Routing Rules

`skill` and `executor` are separate on purpose:

- `skill` says which guidance Codex should follow.
- `routingHint` optionally nudges the conductor.
- `executor` is the conductor's resolved output, not planner-authored source of truth.

The routing rules are:

- default to Codex for non-visual engineering work
- route to Claude when the step materially changes rendered
  presentation:
- allow explicit overrides via `routingHint: "codex"`, `routingHint: "claude"`, or `routingHint: "visual"`

The planner should not hand-decide the real executor. `codex-guard
validate-plan` runs the conductor resolver and stamps `executor`,
`routingReason`, `routingResolvedAt`, and `routingResolvedBy` before
execution begins.

In this repo's workflow, `claudeVerify` defaults to `true` on every step.
Treat it as a hard gate: do not mark a step `done` until `claude-bridge`
verification returns `PASS`. If the bridge is unavailable, stop and surface
the setup failure.

## Review gating rules

`review` is not decorative metadata. It is the execution gate.

- `review.status: "pending"` means execution must not start.
- `review.status: "approved"` means Orbit review completed and execution may
  proceed.
- `review.status: "skipped"` is valid only when the user explicitly instructed
  Codex to skip Orbit review; record that instruction in `skipReason`.

If `review` is missing, treat the plan as invalid and repair it before
execution.

When `codex-guard` is installed, `guard.py validate-plan` consumes these
fields directly before any step can be unlocked.

## Guard interaction

`step.files` is also the Codex-side write scope when `codex-guard` is
installed:

- `begin-step <N>` unlocks only the listed files
- `complete-step <N>` audits writable tracked files outside that list
- `claudeVerify` determines whether a recorded Claude PASS verdict is required
  before the guard will allow completion

## Updating Runtime State

Codex updates runtime state using `plan_utils.py`. Mutation commands write to
`progress.json`; `plan.json` remains the definition unless the plan itself
needs a non-material definition update.

```bash
# Mark step 3 as in_progress
python3 /path/to/plan_utils.py update-step /path/to/plan.json 3 in_progress

# Mark progress item 1 of step 3 as done
python3 /path/to/plan_utils.py update-progress /path/to/plan.json 3 0 done

# Add to completed summary
python3 /path/to/plan_utils.py add-summary /path/to/plan.json "Step 3: Migrated all routes to typed handlers"

# Get plan status overview
python3 /path/to/plan_utils.py status /path/to/plan.json

# Get next step to work on
python3 /path/to/plan_utils.py next-step /path/to/plan.json
```

## masterPlan.md (companion file)

masterPlan.md is the human-facing proposal document. It lives alongside
plan.json in the same directory. **It is write-once** — frozen after Orbit
approval and never updated during execution.

Its purpose:

- Present the plan to the user for Orbit review
- Summarize what, why, critical decisions, warnings, risk areas
- Does NOT contain execution state (no `[x]`/`[ ]` checkboxes)
- Serves as a stable record of what was agreed upon

All runtime state (progress, results, completed summaries, deviations)
lives exclusively in `progress.json`.

After approval, `plan.json` may still absorb **non-material definition follow-through**
that is clearly in service of the same approved objective. Examples:
mirrored fixes, adjacent consistency updates, extra verification, and
small cleanup/docs/tests needed to finish the approved work correctly.
If the scope, risk, or tradeoff changes materially, do not silently keep
stretching the plan definition — revise the plan and get a fresh Orbit review.

See `references/master-plan-format.md` for the template.
