# Claude Verify Template

Use this reference when Codex needs to call the `claude-bridge` `verify_step`
tool for a completed plan step.

## Required inputs

Pass these fields from `plan.json`:

- `cwd`
- `planName`
- `stepId`
- `stepTitle`
- `description`
- `acceptanceCriteria`
- `filesInScope`
- `discoveryScope`
- `discoveryConsumers`
- `discoveryBlastRadius`

Optional but useful:

- `verificationCommands`
- previous `bridgeSessionId` when re-verifying

## Contract

- Claude is reviewer-only in this flow.
- `claudeVerify: true` means the step cannot be marked `done` until Claude
  returns `PASS`.
- `PASS` writes no findings file.
- Non-PASS rounds write JSON findings to
  `/Users/robertobortolaso/Projects/codex-setup/usage-errors/claude-findings`.
- Re-verification should reuse the same `bridgeSessionId`.

## Result handling

Expected result fields from `verify_step`:

- `status` — `PASS` or `FAIL`
- `summary`
- `findings`
- `bridgeSessionId`
- `claudeSessionId`
- `round`
- `findingsPath` — present only for non-PASS rounds

If `status` is `FAIL`:

1. Read the findings.
2. Fix the issues locally.
3. Re-run `verify_step` on the same `bridgeSessionId`.
4. Do not mark the step `done` until the result is `PASS`.
