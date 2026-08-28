## 1. OpenSpec and regression contracts

- [x] 1.1 Create the provenance change artifacts and parity-safe deltas for
  `operation-modes` and `reporting`.
- [x] 1.2 Add failing offline tests for frozen strict provenance, fallback
  digest identity, embedded/runtime identity, stale-warning positive and
  negative cases, summary/report/JSON integration, and backend rewriting.

## 2. Build and runtime implementation

- [x] 2.1 Add fallback constants and implement the provenance model, cached
  accessor, version label, and conservative stale-install warning.
- [x] 2.2 Add the PEP 517 backend wrapper, deterministic source digest, scoped
  Git capture, temporary rewrite/restore path, and build-system configuration.
- [x] 2.3 Add `RunSummary.build`, preserve the existing status derivation, and
  wire provenance through pipeline creation, recovery, CLI JSON, and reports.

## 3. Verification and handoff

- [x] 3.1 Run focused provenance and affected integration tests, then update
  all task checkboxes as behavior is verified.
- [x] 3.2 Run every required bare lint/type/test/OpenSpec gate and the
  delta-parity script for each touched capability.
- [ ] 3.3 Inspect the complete diff, write `/tmp/provenance-report.md`, and
  create local conventional commits without pushing or archiving.
