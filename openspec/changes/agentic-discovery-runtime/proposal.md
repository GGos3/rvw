## Why

Discovery currently spends its prompt budget on an inlined diff, preventing the reviewing agent from autonomously inspecting whole files, callers, and tests in the target repository. The controller already has enough immutable target data and checkout machinery to provision a trustworthy workspace, so agentic repository exploration can become the default while preserving the current inline path as a compatibility fallback.

## What Changes

- Make agentic discovery the default selectable mode and retain `inline` discovery as an explicit legacy fallback.
- Provision or use a checkout detached at the target head, ensure the base and head commits resolve, and fail closed with a machine-readable reason unless `git diff <base>...<head>` is computable there.
- Run plain `codex exec` read-only in that checkout with lane rules, a base/head scope statement, and structured-output instructions, without embedding or materializing the diff or adding exclusion guidance.
- Add required `covered` receipts to lane structured output while preserving closed rule-ID and severity enums.
- Compare valid per-lane receipts with controller-parsed target hunks, perform at most one coverage re-dispatch wave for each incomplete lane, and persist any remaining canonical hunk IDs as `LaneCoverage.uncovered`.
- Render uncovered hunks in deterministic coverage reporting.
- Restrict generated-path filtering, diff budgets, and chunk expansion to inline discovery and sampling; agentic discovery does not consult prompt-sizing budgets.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `discovery`: Make checkout-backed autonomous exploration the default, define per-lane receipt verification and one bounded coverage re-dispatch, and scope diff budgeting/chunking to inline mode.
- `runtime-contract`: Require coverage receipts and a provisioned read-only discovery workdir while preserving plain structured `codex exec`.
- `reporting`: Surface canonical uncovered hunks in the generated coverage section.
- `pr-gate`: Extend anchored checkout verification to the base commit and computable three-dot diff, and align exact planned coverage with mode-specific chunking.
- `operation-modes`: Expose agentic-default and inline-fallback discovery mode selection through runtime-executing command paths.
- `lane-registry`: Make plan run counts mode-aware so agentic plans do not invoke the inline diff chunk planner.

## Impact

The change affects discovery orchestration, prompt construction, strict runtime schemas, dispatch workdirs, checkout verification, CLI/pipeline mode propagation, persisted discovery coverage, gate planning, and Markdown reporting. Existing inline prompt, diff-budget, chunking, sampling, and persisted-artifact compatibility paths remain supported; no external registry files or lane checklist structure change.
