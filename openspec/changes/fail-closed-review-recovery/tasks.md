## 1. Regression Contracts

- [x] 1.1 Add failing offline runtime/discovery tests for absent, empty, unparseable, and schema-invalid lane outputs and degraded/failed status details
- [x] 1.2 Add failing offline adjudication tests for zero-byte all-invalid attempts and non-empty UNCERTAIN reasons
- [x] 1.3 Add a failing CLI fixture proving `adjudicate --run` reuses persisted artifacts and precisely rejects missing inputs
- [x] 1.4 Add failing packaging/version/run-artifact tests for build provenance

## 2. Failure Propagation

- [x] 2.1 Normalize runtime failure reasons while preserving process and artifact diagnostics
- [x] 2.2 Implement strict failed-lane and run-summary models with atomic persistence
- [x] 2.3 Derive complete, degraded, and failed discovery status and expose it in report and review JSON output
- [x] 2.4 Make all-invalid adjudication passes raise a typed infrastructure error and enforce non-empty UNCERTAIN reasons
- [x] 2.5 Persist adjudication failures and render an explicit failed partial report without outcome verdicts

## 3. Recovery and Provenance

- [x] 3.1 Implement artifact-only `rvw adjudicate --run` with a repository checkout and atomic fresh outcome/report writes
- [x] 3.2 Add build-time provenance generation with honest unknown fallbacks and deterministic build identity
- [x] 3.3 Surface provenance in `rvw --version`, `run.json`, and report generator metadata, with only provable best-effort stale warnings

## 4. Specification and Verification

- [x] 4.1 Synchronize affected main specs and contexts with the implemented contract
- [x] 4.2 Run focused tests and review the implementation diff for strict schema and legacy-read compatibility
- [x] 4.3 Run all five bare verification gates and validate a built/installed wheel
- [x] 4.4 Create local commits on the origin/main-based feature branch without pushing
