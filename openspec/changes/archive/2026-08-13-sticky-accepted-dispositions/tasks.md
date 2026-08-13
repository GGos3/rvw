## 1. Regression Tests

- [x] 1.1 Add failing matcher tests showing a unique non-blocker accepted finding with changed hunk or diagnosis becomes `accepted` at `unique_pair_sticky` with prior reason, source run, and demotion cause
- [x] 1.2 Add failing tests proving blockers, changed severity, prior `must_fix`, and source/current pair ambiguity remain `must_fix` or blank under existing fail-closed rules
- [x] 1.3 Add failing gate-flow tests proving sticky-only runs persist a template and pause, while exact-ID-only runs retain automatic continuation
- [x] 1.4 Add failing rendering and schema-compatibility tests for the sticky summary counter and template provenance

## 2. Implementation

- [x] 2.1 Add `unique_pair_sticky` to `InheritanceTier` and a defaulted `sticky` count to `InheritanceSummary`
- [x] 2.2 Update tier-two matching to select sticky acceptance only for unique, equal-severity, non-blocker accepted pairs while preserving machine-readable demotion reasons
- [x] 2.3 Keep the no-pause predicate restricted to exact-ID carries and update summaries/template rendering to distinguish sticky from reason-only prefill

## 3. Specification and Verification

- [x] 3.1 Synchronize the pr-gate main spec and context after implementation
- [x] 3.2 Run focused inheritance/gate regressions
- [x] 3.3 Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, `uv run pytest -q -m "not live"`, and `openspec validate --specs` as bare commands
