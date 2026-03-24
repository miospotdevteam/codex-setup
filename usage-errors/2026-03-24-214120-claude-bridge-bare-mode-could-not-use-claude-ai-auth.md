- Date: 2026-03-24
- Source repo: `/Users/robertobortolaso/Projects/codex-setup`
- Skill(s): `lbyl-conductor`, `lbyl-writing-plans`, `claude-bridge`
- Model: Codex GPT-5

## What happened

`claude-bridge` verification and plan-attack were changed to run Claude with
`--bare` in order to avoid plugin hook side effects. That looked safe, but it
made the bridge incompatible with the user's actual Claude authentication
model.

The user was logged in to Claude Code with a Claude Max / `claude.ai` account,
and `claude auth status` reported `loggedIn: true`. But every bridge call run
with `--bare` still failed with `Not logged in · Please run /login` and
`apiKeySource: "none"`.

## Expected behavior

The bridge should have used a Claude invocation model that works with the
user's real authentication setup while still preventing plugin hooks from
mutating Codex-side plan state.

## Why this is a skill issue

This failure came from the Codex-side bridge design, not from the target repo.
The repo assumed `--bare` was the right isolation primitive without checking
that Claude's own docs/changelog say `--bare` disables OAuth and keychain auth
and only supports `ANTHROPIC_API_KEY` or `apiKeyHelper`.

That assumption made `claudeVerify` fail even though the user was correctly
logged in for normal Claude CLI use.

## Proposed fix

Use authenticated non-`--bare` `claude -p` calls with:

- `--settings '{"disableAllHooks":true}'`
- `--setting-sources project,local`
- `--plugin-dir <local look-before-you-leap checkout>`

This keeps Claude skill availability and Claude.ai auth while disabling the
hook layer that was causing plan-state interference.

## Evidence

- `claude auth status` returned `loggedIn: true`, `authMethod: "claude.ai"`,
  `subscriptionType: "max"`.
- `claude --help` documents that `--bare` disables OAuth and keychain auth.
- Non-`--bare` calls with `disableAllHooks: true` and the local plugin dir
  succeeded in this repo during bridge design verification.
