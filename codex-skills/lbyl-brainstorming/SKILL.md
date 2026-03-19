---
name: lbyl-brainstorming
description: "Use when a task has unresolved design ambiguity with materially different approaches. Best for new features, components, workflows, or behavior changes where multiple plausible UX, API, data-model, or architecture choices exist and the right answer is not already implied by user direction or repo patterns. Do NOT use for implementation planning (use writing-plans), debugging, bug fixes, refactoring, migrations, audits, or executing an already-written plan."
---

# Brainstorming

Turn ambiguous ideas into designs before writing code. Understand what
you're building, explore approaches, get approval, then plan.

**Announce at start:** "I'm using the brainstorming skill to explore the
design before any code is written."

**No code until the design is approved.** No exceptions, no matter how
simple the task seems. Simple tasks are where unexamined assumptions
waste the most time.

Use this skill only when the task needs a real design choice, not just
careful execution.

## Trigger gate

Use brainstorming when all of these are true:

- There are at least 2 plausible approaches
- The choice materially affects UX, API shape, data model, architecture,
  or long-term maintenance
- The right answer is not already implied by the user's direction or
  established repo patterns

Skip brainstorming when any of these are true:

- The task is mainly implementation, cleanup, or execution of an existing plan
- The repo already has a clear pattern to follow
- The user already provided the concrete design or execution sequence
- The task is a bug fix, audit, migration, refactor, or review
- The desired outcome is known and the only question is how to implement it

---

## The Steps

### 1. Understand the context

Follow engineering-discipline Phase 1 (Orient Before You Touch Anything)
to build a picture of the relevant codebase:

- Read AGENTS.md / README for project conventions
- Read files in the feature area and their imports
- Check recent commits touching relevant modules
- Find sibling files to learn existing patterns

If this is a **greenfield project** with no existing codebase, skip the
reads and note the greenfield context — proceed directly to questions.

### 2. Ask questions — one at a time

Explore the idea through conversation. One question per message. Prefer
multiple choice when the options are clear, open-ended when they're not.

Focus on:
- What problem does this solve?
- Who is it for?
- What does success look like?
- What are the constraints?

Keep going until you could explain the feature to another engineer and
clearly justify why the chosen approach beats the alternatives.

If the user **can't answer** a question (doesn't know constraints yet,
hasn't decided), propose reasonable defaults and flag them explicitly as
assumptions that can be revised later.

### 3. Propose approaches

Present 2-3 different ways to build it. For each one: what it looks like,
what it's good at, what the trade-offs are. Lead with your recommendation
and say why.

### 4. Present the design

Walk through the design section by section. Scale detail to complexity —
a few sentences for straightforward parts, more for nuanced ones. After
each section, check: does this look right?

Cover what's relevant: architecture, components, data flow, error
handling, testing. Skip sections that don't apply.

### 5. Save and transition

Once approved:

1. Initialize the plan directory:
   ```bash
   bash ~/.codex/skills/lbyl-conductor/scripts/init-plan-dir.sh
   mkdir -p .temp/plan-mode/active/<plan-name>
   ```
2. Write the design to `.temp/plan-mode/active/<plan-name>/design.md`
   using the structure below
3. Invoke `lbyl-writing-plans` to create `plan.json` and `masterPlan.md`
   in the same directory — the design feeds directly into the plan's
   discovery and user-facing proposal

**Stop here.** The next step is the implementation plan, not code.

#### design.md structure

Use these sections (skip any that don't apply):

```markdown
# Design: <Title>

## Problem
What problem this solves and for whom.

## Constraints
Hard requirements, technical limitations, compatibility needs.

## Chosen Approach
The selected approach and why it was chosen over alternatives.

## Alternatives Considered
Other approaches explored and why they were rejected.

## Key Decisions
Important design choices made during brainstorming with rationale.

## Open Questions
Anything unresolved or flagged as an assumption.
```

---

## Principles

- **One question at a time** — don't overwhelm
- **YAGNI** — cut anything that isn't clearly needed
- **Explore before committing** — always consider alternatives
- **Validate incrementally** — get approval as you go, not all at once
- **Stay flexible** — circle back when something doesn't add up
