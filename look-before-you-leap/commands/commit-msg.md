---
description: "Generate a 1-liner git commit message for the current staged or unstaged changes."
allowed-tools: ["Bash"]
---

# Generate Commit Message

Run `git diff --cached --stat` and `git diff --cached` to see staged changes.
If nothing is staged, fall back to `git diff --stat` and `git diff` for
unstaged changes. Also run `git status` to see untracked files.

From the diff, produce a single-line commit message that:

- Starts with a lowercase verb (add, fix, update, remove, refactor, etc.)
- Summarizes the **why**, not the **what** — the diff already shows the what
- Is under 72 characters
- Does not use a period at the end
- Does not use a conventional-commits prefix (no `feat:`, `fix:`, etc.)
  unless the project's recent `git log --oneline -10` shows that convention

Output ONLY the commit message line — no explanation, no quotes, no markdown
formatting. Just the raw message text the user can copy-paste.
