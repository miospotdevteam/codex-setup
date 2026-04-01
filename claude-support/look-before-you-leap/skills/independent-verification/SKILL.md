---
name: independent-verification
description: "Use when Claude is asked to independently verify work completed by Codex or by another Claude worker. Review diffs and touched files, run the provided verification commands or obvious project checks, compare the implementation against the exact acceptance criteria, and return structured PASS/FAIL findings without editing files. Do NOT use for implementation, planning, brainstorming, or code changes."
---

# Independent Verification

Review completed work with fresh eyes. You are not the implementer. Your job
is to verify whether the current state satisfies the written acceptance
criteria and to report concrete findings when it does not.

**Announce at start:** "I'm using the independent-verification skill to review
the completed work."

## Rules

- Do not edit files.
- Review the acceptance criteria exactly as written.
- Treat pre-existing failures as real failures when the acceptance criteria
  require the relevant checks to pass.
- Be concrete and file-specific.
- Prefer project-native verification commands when they are provided.

## What to read

Read these in order:

1. the acceptance criteria
2. the expected files in scope
3. the current diff and touched files
4. `references/verification-commands.md` when you need ecosystem-specific
   command hints

## What to check

- Is the requested behavior fully implemented?
- Were any shared consumers missed?
- Are there type-safety or contract regressions?
- Were relevant tests or verification commands run?
- Is any scope silently missing?

## Output

Return a structured PASS/FAIL result only. If you fail the work, include:

- severity
- category
- file
- line when available
- summary
- detail
- whether the issue looks preventable through better instructions
