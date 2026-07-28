## 1. Sample signal refinement

- [x] 1.1 Add failing regression tests for novel rule IDs, same-enum site variance, report JSON fields, and PASS/REVIEW exit codes.
- [x] 1.2 Implement novel-rule and structured site-variance classification while preserving legacy sample fields and verdict strings.
- [x] 1.3 Update human sample rendering and compatibility assertions, then run the focused sample tests.

## 2. Stable finding identity and gate domain

- [x] 2.1 Add failing tests that expose collapse keys as public finding IDs in reports and gate artifacts.
- [x] 2.2 Add strict disposition, anchor, coverage, finding, and verdict models plus artifact persistence and Markdown rendering.
- [x] 2.3 Add failing tests and implement exact actionable-ID validation, duplicate/unknown/omitted rejection, must-fix blocking, and owner-authorized blocker acceptance.

## 3. Anchored gate orchestration

- [x] 3.1 Add failing tests for disposable checkout provisioning, exact HEAD/clean verification, and operational failure handling.
- [x] 3.2 Add failing tests and implement exact plan-to-coverage validation including non-vacuity and per-lane replica validity.
- [x] 3.3 Add failing CLI/orchestration tests for target-mode single execution, artifact-resume without execution, mutual exclusion, and post-run stale-anchor failure.
- [x] 3.4 Implement `rvw gate` target/resume orchestration, disposition-template handoff, exit mapping, and artifact output.

## 4. Publication and synchronized specifications

- [x] 4.1 Add failing tests that gate publication is artifact-derived, dry-run by default, COMMENT-only, blocked after stale/coverage failures, and uses the bounded 422 fallback.
- [x] 4.2 Reuse the existing publish path for generated gate verdicts and expose no approval-capable gate option.
- [x] 4.3 Synchronize the affected main specs and context documents with the implemented sample and gate contracts.

## 5. Verification

- [x] 5.1 Run focused tests during TDD and inspect the final diff for accidental registry or unrelated changes.
- [x] 5.2 Run `uv run ruff check .` and `uv run ruff format --check .` as bare commands.
- [x] 5.3 Run `uv run ty check` and `uv run pytest -q -m "not live"` as bare commands.
- [x] 5.4 Run `openspec validate --specs` as a bare command and resolve every validation error.
