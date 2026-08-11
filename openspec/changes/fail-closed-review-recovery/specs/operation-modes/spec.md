## ADDED Requirements

### Requirement: Existing runs can be re-adjudicated

`rvw adjudicate --run <run-id>` MUST load the run's persisted target, discovery, and merge artifacts, execute adjudication against an explicitly supplied repository checkout, and atomically replace `outcome.json` and `report.md` after success without executing discovery. Missing required inputs MUST fail with a precise message naming the missing artifact.

#### Scenario: Re-adjudication succeeds

- **WHEN** a run contains valid `target.json`, `discover.json`, and `merge.json` and the adjudicator returns valid output
- **THEN** fresh outcome and report artifacts are written while discovery artifacts and runtime calls remain unchanged

#### Scenario: Merge input is missing

- **WHEN** `rvw adjudicate --run` opens a run without `merge.json`
- **THEN** the command fails with an error that names `merge.json` and does not invoke the adjudicator

### Requirement: CLI exposes honest build identity

`rvw --version` MUST show the semantic version and embedded build identifier, MUST show source provenance only when it was captured at build time, and MUST never claim a source commit or stale state that cannot be verified. A source-build comparison MAY emit one non-fatal warning per run only when the installed provenance and current source history prove the installed commit is behind, and that warning MUST include `uv tool install --reinstall --from <repo> rvw`.

#### Scenario: Commit provenance is unavailable

- **WHEN** the running distribution lacks verifiable build-time commit data
- **THEN** version output identifies the build without fabricating a commit and no ahead/behind warning is emitted

