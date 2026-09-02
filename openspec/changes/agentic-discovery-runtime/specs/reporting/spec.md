## MODIFIED Requirements

### Requirement: Coverage proves lane participation

Every report MUST include a per-lane table of planned dispatched runs, valid runs, findings, and uncovered controller hunk count plus the canonical IDs of any uncovered hunks. It MUST include kept/excluded diff character accounting and chunk count only when an inline budget report exists.

#### Scenario: One two-chunk inline lane fails entirely

- **WHEN** an activated inline lane has three replicas over two chunks and zero valid outputs
- **THEN** the coverage table contains that lane with `6 / 0 / 0` and the budget summary identifies two chunks rather than making the lane indistinguishable from an omitted lane

#### Scenario: Agentic lane leaves one hunk uncovered

- **WHEN** bounded coverage verification ends with one canonical hunk ID uncovered for a lane
- **THEN** the coverage table gives that lane an uncovered count of one and the report renders the canonical hunk ID without a diff-budget summary
