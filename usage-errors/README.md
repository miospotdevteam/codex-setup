# Usage Errors

Use this directory to capture failures caused by the LBYL skill pack itself
when those failures show up in other sessions or repos.

## Directory layout

- Keep open incidents at the top level of `usage-errors/`.
- Move fixed incidents into `usage-errors/resolved/`.
- Do not delete resolved incidents unless you are explicitly pruning repo
  history; they are part of the feedback trail.

One file per incident. Prefer the helper script:

```bash
bash ~/Projects/codex-setup/scripts/log-usage-error.sh "short title"
```

If this repo lives somewhere else, set:

```bash
export LBYL_CODEX_SETUP_REPO=/absolute/path/to/codex-setup
bash "$LBYL_CODEX_SETUP_REPO/scripts/log-usage-error.sh" "short title"
```

## When to log

Log an incident here when the problem is about the skill pack, not just the
target repo. Examples:

- the conductor or companion skills push the model into the wrong workflow
- the instructions conflict with the target repo strongly enough to waste time
- the skill guidance causes a missed requirement, broken plan flow, or harmful
  assumption
- the user explicitly points out that an LBYL rule created friction or caused
  a mistake

Do not use this directory for ordinary project bugs that are unrelated to the
skill guidance.

## Filename format

Use:

```text
YYYY-MM-DD-HHMMSS-short-slug.md
```

The helper script generates this automatically.

## Required sections

Every report should be concrete and short. Keep these sections:

- front matter bullets for date, source repo, skill(s), and model
- `## What happened`
- `## Expected behavior`
- `## Why this is a skill issue`
- `## Proposed fix`
- `## Evidence`

## Workflow

1. Finish or stabilize the user's main task first when possible.
2. Create the report with the helper.
3. Fill in the sections with repo-specific evidence and the smallest plausible
   fix to the skill/docs/process.
4. Once the underlying issue is fixed, move the report into `resolved/` and
   add a short note about what resolved it.
5. Mention in the final closeout that the usage error was logged here, or say
   explicitly if you could not log it because this repo was unavailable.
