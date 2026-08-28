## ADDED Requirements

### Requirement: Run summaries carry immutable build identity

Every persisted and exposed `RunSummary` MUST contain a frozen,
extra-forbidden `BuildProvenance` value identifying the artifact that produced
the run. Summary creation MUST capture the identity once for a new run and
preserve that value when loading or re-rendering an existing run; adding the
field MUST NOT alter fail-closed status or failed-lane derivation.

#### Scenario: JSON and report agree on build identity

- **WHEN** a review run is summarized and rendered
- **THEN** `rvw review --json`, `run.json`, and the report generator footer expose
  the same build identifier

#### Scenario: Legacy summary is rendered

- **WHEN** an older run has no build field in `run.json`
- **THEN** loading or rendering uses the current immutable fallback identity
  without changing the persisted status semantics
