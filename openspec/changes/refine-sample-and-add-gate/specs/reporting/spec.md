## ADDED Requirements

### Requirement: Gate verdict publication is artifact-derived

The gate MUST generate its publishable verdict from persisted target, discovery, merge, adjudication, coverage, and disposition data, and the verdict MUST contain the run ID, base and head anchors, aggregate verdict counts, per-lane dispatched and valid counts, and each actionable finding's public ID, severity, adjudication verdict, disposition, and reason.

#### Scenario: Later audit reconstructs a gate decision

- **WHEN** a gate verdict contains accepted and must-fix findings across multiple lanes
- **THEN** the saved JSON and Markdown identify every decision and the exact anchored run without relying on aggregate counts alone

### Requirement: Gate publication preserves COMMENT safety

Gate publication MUST be dry-run by default, MUST use the existing COMMENT-only payload construction, MUST NOT expose an APPROVE or REQUEST_CHANGES mode, and MUST retry at most once without inline comments after an HTTP 422 response.

#### Scenario: Gate publication is inspected

- **WHEN** an operator runs gate without `--execute`
- **THEN** rvw writes the COMMENT payload and makes no GitHub publication call

#### Scenario: Gate inline comment is rejected

- **WHEN** GitHub returns HTTP 422 for the first gate payload containing inline comments
- **THEN** rvw performs one final body-only COMMENT attempt and no third request
