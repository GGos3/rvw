## ADDED Requirements

### Requirement: Discovery requires a reviewable diff

Discovery MUST fail with a machine-readable `empty-review-diff` error containing every excluded file's reason when generated-path and oversized-file exclusions retain zero review characters, and MUST do so before constructing or dispatching runtime work.

#### Scenario: Every changed file is excluded

- **WHEN** all target diff segments match generated paths or exceed the per-file character limit
- **THEN** discovery dispatches no lane replicas and reports the `excluded_reason` mapping instead of producing zero-finding coverage
