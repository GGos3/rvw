## Why

A review can currently look complete after discovery lanes or the adjudicator produced no usable output, leaving operators and automation with misleading coverage and synthetic UNCERTAIN verdicts. Persisted discovery work also cannot be safely re-adjudicated after an infrastructure failure.

## What Changes

- **BREAKING**: Add an explicit review status and structured failed-lane details to persisted run data and `rvw review --json`; any final invalid lane execution makes the review `degraded` instead of complete while preserving successful-lane findings.
- Render the partial/degraded state and every failed lane with machine-readable reasons in `report.md`.
- Treat an all-invalid adjudication pass, including empty or absent output, as an infrastructure error with attempt diagnostics; never synthesize verdicts from zero valid outputs.
- Enforce non-empty reasons for UNCERTAIN adjudication verdicts.
- Implement `rvw adjudicate --run <id>` from persisted target, discovery, and merge artifacts, replacing `outcome.json` and `report.md` only after successful re-adjudication.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-contract`: Distinguish missing, empty, unparseable, and schema-invalid runtime responses and retain diagnostics.
- `discovery`: Make final lane execution loss a structured degraded-review condition.
- `adjudication`: Fail when no valid adjudicator response exists and require meaningful UNCERTAIN reasons.
- `reporting`: Persist run status and failed-lane details and render partial reports explicitly.
- `operation-modes`: Implement artifact-based re-adjudication with failure-safe artifact replacement.

## Impact

The change affects runtime result classification, discovery and outcome schemas, run persistence, the common pipeline, report rendering, review/adjudicate CLI output, and their offline tests. It does not change lane selection, replica counts, concurrency defaults, deadlines, host-global gating, prompt sizing, the external review registry, packaging, build provenance, or publication policy.
