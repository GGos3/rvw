## MODIFIED Requirements

### Requirement: Invalidity is machine-readable

Every INVALID result MUST have no output, a non-empty machine-readable `invalid_reason`, and retained artifact diagnostics, while every VALID result MUST have validated non-empty output, no invalid reason, and no invalid diagnostic. Output classification MUST distinguish `missing`, `empty`, `unparseable`, and `schema-invalid`; process and completion failures MUST remain distinct from output-content failures.

#### Scenario: Artifact is missing

- **WHEN** a zero-exit execution creates no `out.json`
- **THEN** the result is INVALID with reason `missing` and cannot be represented as VALID

#### Scenario: Artifact is empty

- **WHEN** an execution creates a zero-byte `out.json`
- **THEN** the result is INVALID with reason `empty` rather than being treated as a valid empty response

#### Scenario: Artifact is malformed or violates its schema

- **WHEN** a non-empty `out.json` cannot be decoded as JSON or fails strict schema validation
- **THEN** the result is INVALID with reason `unparseable` or `schema-invalid` respectively
