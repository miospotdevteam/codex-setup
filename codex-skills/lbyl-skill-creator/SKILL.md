---
name: lbyl-skill-creator
description: "Create new Codex skills, improve existing SKILL.md files, package reusable skill folders, and evaluate skill quality with qualitative review plus optional metadata-trigger experiments. Use when the user wants to author a skill, port a skill into Codex, tighten a skill description, add scripts/references/assets to a skill, or benchmark competing skill drafts. Do NOT use for general docs, application code changes that are not skill work, or one-off prompt writing with no intent to create or maintain a reusable skill."
---

# LBYL Skill Creator

Use this skill when the task is to create, port, refine, package, or evaluate
another skill. The goal is not just to write `SKILL.md`, but to leave behind a
reusable skill folder with clear triggers, bounded scope, and enough bundled
resources to keep future sessions deterministic.

Announce at the start: "I'm using the lbyl-skill-creator skill."

## What this bundle provides

- `scripts/quick_validate.py` for frontmatter and metadata sanity checks
- `scripts/package_skill.py` for creating a distributable `.skill` archive
- `scripts/aggregate_benchmark.py` plus `eval-viewer/` for human review of eval
  runs
- `scripts/run_eval.py`, `scripts/improve_description.py`, and
  `scripts/run_loop.py` for optional description-trigger experiments using the
  OpenAI API

Important limitation:
- The trigger-eval scripts are a **Codex-oriented approximation**, not a
  perfect measurement of Codex runtime behavior. They ask an OpenAI model
  whether a skill should trigger from name + description + query. Use them to
  compare candidate descriptions, not as absolute truth.

## Workflow

### 1. Capture the intent

Figure out what the skill should enable, when it should trigger, what artifacts
it should produce, and whether the task needs deterministic scripts,
references, or assets.

Start with concrete questions:
1. What should the skill help Codex do?
2. What user requests should trigger it?
3. What should the final output look like?
4. Which parts need deterministic scripts vs plain instructions?
5. Should the skill be evaluated with test prompts?

If the conversation already contains examples, mine them before asking new
questions.

### 2. Plan the reusable package

Map the skill into the usual shape:

```text
skill-name/
├── SKILL.md
├── scripts/
├── references/
├── assets/
└── agents/
```

Use this rule:
- Put core workflow and trigger rules in `SKILL.md`
- Put detailed domain material in `references/`
- Put fragile or repetitive logic in `scripts/`
- Put output resources in `assets/`

Do not add stray repo-style docs such as `README.md`, changelogs, or design
notes inside the skill folder.

### 3. Author or revise the skill

Write the frontmatter first:
- `name`
- `description`

The description is the primary trigger surface. Make it concrete about:
- what the skill does
- when to use it
- when not to use it

Keep the description under the platform hard limit of 1024 characters.

Then write the body as an operational workflow, not vague advice. A good skill:
- has ordered steps
- names prerequisites before action
- defines fallbacks when tools are unavailable
- sets autonomy limits and destructive-action boundaries
- explains how success is verified

### 4. Validate the structure

Run the bundled validator after major edits:

```bash
python3 scripts/quick_validate.py <path-to-skill>
```

Fix all metadata and frontmatter failures before doing deeper review.

For a final quality gate, review the draft against `skill-review-standard`.

### 5. Evaluate the skill

Choose the lightest evaluation method that matches the task.

#### Qualitative loop

Use this by default for most skills:
1. Draft 2-5 realistic test prompts
2. Run the skill on those prompts
3. Save outputs in `<skill-name>-workspace/iteration-N/...`
4. Generate a human-review viewer with `eval-viewer/generate_review.py`
5. Gather feedback and revise

If baseline comparison matters, include a run without the skill or with the
previous skill version.

#### Quantitative benchmark

Use this when assertions are objectively checkable:
1. Save eval metadata and assertions
2. Grade outputs with the grader agent or scripts
3. Aggregate with:

```bash
python3 -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

4. Review the benchmark and surface patterns, not just totals

#### Description-trigger experiments

Use this only when the user wants to tighten metadata triggering.

Prerequisites:
- `OPENAI_API_KEY`
- a model ID suitable for cheap repeated calls

Commands:

```bash
python3 -m scripts.run_eval --eval-set <evals.json> --skill-path <skill-dir> --model <model>
python3 -m scripts.run_loop --eval-set <evals.json> --skill-path <skill-dir> --model <model> --verbose
```

Again: this is a model-based approximation of skill triggering, not the exact
Codex runtime. Treat it as comparative signal.

### 6. Iterate and package

After each review cycle:
1. Generalize from feedback instead of overfitting to one prompt
2. Remove bloated instructions that are not pulling their weight
3. Promote repeated logic into reusable scripts
4. Re-run validation and the relevant evals

When the user wants a distributable artifact:

```bash
python3 -m scripts.package_skill <path-to-skill>
```

## Output Contract

When using this skill, structure your response like this:

1. What phase you are in
2. What you changed or evaluated
3. What evidence you have
4. What remains or what decision you need from the user

For skill reviews, list findings before summaries.

## Boundaries

Do not:
- silently broaden the skill scope beyond the user's intent
- leave Claude-specific or platform-specific instructions unadapted when
  porting a skill to Codex
- claim a trigger experiment measures real Codex behavior exactly
- package or ship a skill that still fails validation without telling the user
- add bundled files that are just workspace junk or prior run outputs

## Acceptance Criteria

- [ ] `SKILL.md` has precise trigger boundaries and explicit "do not use when"
- [ ] Bundled scripts/references/assets match the workflow and are not junk
- [ ] `python3 scripts/quick_validate.py <skill-dir>` passes
- [ ] Any evaluation method used is explained accurately, including limits
- [ ] Remaining risks or gaps are reported explicitly
