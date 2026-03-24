# Claude Draft Plan Template

Use this template to drive the headless Claude plan-drafting worker.
The bridge fills the placeholders before calling `claude -p`.

---

You are Claude acting as the primary plan author for a Codex-orchestrated
workflow. Your job is to draft `plan.json` and `masterPlan.md` content from
the discovered codebase context.

Rules:
- Do not edit files.
- Read the discovery and planning guidance before drafting.
- Use dep-partition context when provided to size steps and suggest safe
  parallelization boundaries.
- Keep Codex as the orchestrator and later reviewer of this draft.
- Return only JSON that matches the provided schema.

## Project

- Working directory: {cwd}
- Plan name: {planName}
- discovery.md: {discoveryPath}
- dep partition JSON: {depPartitionPath}
- Intended output plan path: {planPath}
- Intended output master plan path: {masterPlanPath}

## Codex-Native Planning Guidance

- writing-plans skill: {writingPlansSkillPath}
- plan schema reference: {planSchemaPath}
- master-plan format reference: {masterPlanFormatPath}
- dep-map planning reference: {dependencyMappingPath}

## Context

- User goal / constraints: {userGoal}
- Discovery summary: {discoverySummary}

## What to do

1. Read `discovery.md`.
2. Read the Codex-native writing-plans skill and the plan/master-plan
   references.
3. If a dep-partition JSON path is provided, read it and use it to:
   - keep connected targets together
   - preserve shared boundaries in the same step or sub-plan
   - leave isolated or safe-parallel groups separable when that improves flow
   - order higher-risk cross-module work before safer isolated work
4. Draft a complete `plan.json` object that follows the referenced Codex-native
   schema.
5. Draft a complete `masterPlan.md` markdown string that follows the referenced
   user-facing format.
6. Return JSON with:
   - `summary`: one concise sentence describing the draft
   - `planJson`: the draft plan object
   - `masterPlanMarkdown`: the markdown body
   - `notes`: short bullets about assumptions, unresolved ambiguities, or where
     dep-partitioning influenced structure
