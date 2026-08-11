## ADDED Requirements

### Requirement: Run summaries are strict and fail closed

Every review that reaches a terminal state MUST persist and expose a strict run summary containing `status`, `failed_lanes`, build provenance, coverage totals, and any run-level error. Terminal `status` MUST be exactly `complete`, `degraded`, or `failed`; `rvw review --json` MUST emit the same status and failed-lane detail used by the persisted summary.

#### Scenario: Automation receives partial coverage

- **WHEN** one final lane execution is invalid and another is valid
- **THEN** JSON output and the persisted summary both contain `status: "degraded"` and structured `failed_lanes` rather than presenting the review as complete

### Requirement: Reports disclose incomplete execution

Every report for a degraded or failed run MUST state prominently that the review is partial or failed and MUST list each failed lane with every normalized machine-readable reason. The report MUST retain successful findings and ordinary coverage counts without relabeling invalid executions as valid.

#### Scenario: Missing and malformed lanes coexist

- **WHEN** one lane has missing output and another has unparseable output
- **THEN** `report.md` names both lanes, renders reasons `missing` and `unparseable`, and labels any surviving findings as partial

### Requirement: Runs record build provenance

Every run MUST persist build provenance that identifies the installed build independently of the semantic version, including a deterministic build identifier and source commit, source-dirty state, and build timestamp when those values were verifiably available at build time. Unavailable provenance fields MUST be represented as unknown rather than inferred at runtime.

#### Scenario: Local source build is recorded

- **WHEN** a wheel is built from a Git checkout
- **THEN** new runs identify the build using embedded build-time data and do not substitute the checkout's later HEAD as the producing commit

