# Claude Findings

This directory stores machine-generated JSON findings from the
`claude-bridge` verification gate.

Rules:

- PASS rounds do not create a file here.
- Non-PASS rounds write one JSON file per verification round.
- Re-verification rounds use `-reverify-N` suffixes.
- These files are not usage-error incident reports. Keep human-written skill
  incident reports in the parent `usage-errors/` directory.
