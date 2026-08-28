## ADDED Requirements

### Requirement: Existing runs can be re-adjudicated

`rvw adjudicate --run <run-id>` MUST load the run's persisted target, discovery, and merge artifacts, execute adjudication against an explicitly supplied repository checkout, and atomically replace `outcome.json` and `report.md` only after success without executing discovery. Missing required inputs MUST fail with a precise message naming the missing artifact, and failed re-adjudication MUST retain any pre-existing outcome and report.

#### Scenario: Re-adjudication succeeds

- **WHEN** a run contains valid `target.json`, `discover.json`, and `merge.json` and the adjudicator returns valid output
- **THEN** fresh outcome and report artifacts are written while discovery artifacts and runtime calls remain unchanged

#### Scenario: Merge input is missing

- **WHEN** `rvw adjudicate --run` opens a run without `merge.json`
- **THEN** the command fails with an error that names `merge.json` and does not invoke the adjudicator

#### Scenario: Re-adjudication infrastructure fails

- **WHEN** a run already has `outcome.json` and `report.md` and re-adjudication produces no valid response after retry
- **THEN** the command reports the infrastructure failure and leaves both pre-existing artifacts byte-for-byte intact
