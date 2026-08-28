## 1. Regression Contracts

- [x] 1.1 Add failing offline runtime/discovery tests for absent, empty, unparseable, and schema-invalid lane outputs; degraded/failed status details; and coexistence of attempt history with final diagnostics
- [x] 1.2 Add failing offline adjudication tests for all-invalid attempts and non-empty UNCERTAIN reasons
- [x] 1.3 Add failing CLI fixtures proving `adjudicate --run` reuses persisted artifacts, rejects missing inputs precisely, and preserves prior outcome/report after failure

## 2. Failure Propagation

- [x] 2.1 Normalize runtime failure reasons while preserving process, spawn, and artifact diagnostics
- [x] 2.2 Implement strict failed-lane and run-summary models with atomic persistence while preserving current ordered retry-attempt coverage
- [x] 2.3 Derive complete, degraded, and failed discovery status and expose it in report and review JSON output
- [x] 2.4 Make all-invalid adjudication passes raise a typed infrastructure error, preserve retry feedback and every failed attempt, and enforce non-empty UNCERTAIN reasons
- [x] 2.5 Persist adjudication failures and render an explicit failed partial report without outcome verdicts

## 3. Recovery

- [x] 3.1 Implement artifact-only `rvw adjudicate --run` with a repository checkout and atomic fresh outcome/report writes
- [x] 3.2 Preserve any pre-existing outcome/report when re-adjudication fails

## 4. Specification and Verification

- [x] 4.1 Synchronize affected main specs and contexts with the implemented contract
- [x] 4.2 Run focused tests and review the implementation diff for strict schema and legacy-read compatibility
- [x] 4.3 Run delta-parity for every touched capability, all required bare verification gates, and strict change validation
- [x] 4.4 Create local conventional commits on the origin/main-based feature branch without pushing
