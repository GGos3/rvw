## Why

A review can currently look complete after discovery lanes or the adjudicator produced no usable output, leaving operators and automation with misleading coverage and synthetic UNCERTAIN verdicts. Persisted discovery work also cannot be re-adjudicated, and the semantic version alone cannot identify which source build produced a run.

## What Changes

- **BREAKING**: Add an explicit review status and structured failed-lane details to persisted discovery data and `rvw review --json`; any final invalid lane execution makes the review `degraded` instead of complete while preserving successful-lane findings.
- Render the partial/degraded state and every failed lane with machine-readable reasons in `report.md`.
- Treat an all-invalid adjudication pass, including empty or absent output, as an infrastructure error with attempt diagnostics; never synthesize verdicts from zero valid outputs.
- Enforce non-empty reasons for UNCERTAIN adjudication verdicts.
- Implement `rvw adjudicate --run <id>` from persisted target, discovery, and merge artifacts, replacing `outcome.json` and `report.md` without rerunning discovery.
- Record verifiable build provenance in every run and expose it from `rvw --version`; optionally warn when a source checkout can prove that the installed build is behind.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-contract`: Distinguish missing, empty, unparseable, and schema-invalid runtime responses and retain diagnostics.
- `discovery`: Make final lane execution loss a structured degraded-review condition.
- `adjudication`: Fail when no valid adjudicator response exists and require meaningful UNCERTAIN reasons.
- `reporting`: Persist run status, failed-lane details, and build provenance; render partial reports explicitly.
- `operation-modes`: Implement artifact-based re-adjudication and expose honest build provenance from the CLI.

## Impact

The change affects runtime result classification, discovery and outcome schemas, run persistence, the common pipeline, report rendering, review/adjudicate/version CLI output, and their offline tests. It does not change lane selection, replica counts, concurrency defaults, prompt sizing, the external review registry, or publication policy.
