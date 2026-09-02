## 1. Contracts and regression tests

- [x] 1.1 Add failing tests for the required `covered` schema field and the separate agentic prompt's exact no-diff/minimal-scope contract.
- [x] 1.2 Add failing tests for checkout base/head/diff verification, workdir propagation, and machine-readable fail-closed errors.
- [x] 1.3 Add failing tests for receipt-to-hunk matching, one bounded per-lane coverage re-dispatch wave, and residual uncovered persistence.
- [x] 1.4 Add failing tests for agentic-default/inline-fallback planning and execution plus deterministic uncovered report rendering.

## 2. Runtime and workspace foundations

- [x] 2.1 Add `covered` to strict lane output and update runtime fixtures without weakening closed rule-ID or severity schemas.
- [x] 2.2 Thread optional workdirs through planned lane dispatch and plain read-only `codex exec`.
- [x] 2.3 Extract and extend shared checkout verification/provisioning for exact head, clean state, resolvable anchors, and computable three-dot diff with typed failure reasons.

## 3. Agentic discovery

- [x] 3.1 Add typed `agentic`/`inline` discovery modes and the minimal agentic prompt builder.
- [x] 3.2 Branch agentic discovery before diff budgeting, run one logical scope in the verified checkout, and preserve inline behavior unchanged.
- [x] 3.3 Implement deterministic per-lane receipt coverage, one representative re-dispatch wave under separate artifacts, retry finding enrichment, and final `LaneCoverage.uncovered` state.

## 4. Pipeline, CLI, and reporting integration

- [x] 4.1 Propagate discovery mode through review, auto, gate, stack review, and plan with agentic defaults and inline fallback.
- [x] 4.2 Provision or verify agentic workspaces before run creation and preserve inline operation for targets without a base.
- [x] 4.3 Make gate and plan chunk expectations mode-aware while preserving exact planned-run validation.
- [x] 4.4 Persist legacy-compatible coverage fields and render uncovered canonical hunk IDs in ordinary and gate evidence.

## 5. Specification synchronization and verification

- [x] 5.1 Synchronize the implemented delta requirements and adjacent rationale into the main OpenSpec specs without archiving any active change.
- [x] 5.2 Run focused tests and both `openspec validate agentic-discovery-runtime --strict` and `openspec validate --specs`, fixing every failure.
- [x] 5.3 Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, and `uv run pytest -q -m "not live"` as bare commands.
- [x] 5.4 Write `/tmp/rvw-phase15-report.md` with changed files, gate outcomes, verbatim prompt/schema fragments, bounded retry behavior, deviations, and open questions.
