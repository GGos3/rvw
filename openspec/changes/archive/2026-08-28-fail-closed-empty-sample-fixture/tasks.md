## 1. Regression Tests

- [x] 1.1 Add fixture-loading tests proving multi-file unified diffs pass through with original chunk/accounting semantics and ordinary files retain `/dev/null` conversion.
- [x] 1.2 Add a 767K single-segment sampling regression that expects a structured empty-review failure before any runtime call.
- [x] 1.3 Add discovery and CLI regressions for no-dispatch fail-closed behavior, exit 2, and JSON `excluded_reason` output.
- [x] 1.4 Run the focused tests and confirm the new behavioral assertions fail before implementation.

## 2. Implementation

- [x] 2.1 Detect supported unified-diff headers in `_fixture_diff` and pass matching fixture content through unchanged.
- [x] 2.2 Add the shared typed `empty-review-diff` error and budget assertion helper with deterministic excluded-reason reporting.
- [x] 2.3 Apply the guard immediately after budgeting in sample and discovery before prompt construction or dispatch.
- [x] 2.4 Map the typed failure to structured output and exit 2 across sample and production discovery CLI entry points.

## 3. Verification

- [x] 3.1 Run all focused regression tests and inspect the final diff for scoped behavior and unchanged planner accounting.
- [x] 3.2 Run `uv run ruff check .` and `uv run ruff format --check .`.
- [x] 3.3 Run `uv run ty check` and `uv run pytest -q -m "not live"`.
- [x] 3.4 Run `openspec validate --specs` and confirm all change tasks are complete.
