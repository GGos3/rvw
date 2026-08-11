## ADDED Requirements

### Requirement: Lane execution loss degrades the review

Each final invalid planned lane execution MUST identify its lane as failed and MUST retain its replica, chunk, normalized reason, and available diagnostic. A review with at least one valid lane and at least one failed lane MUST have status `degraded`; a review with planned lanes and no valid lane MUST have status `failed`; only a review with no final invalid lane executions MAY have status `complete`.

#### Scenario: One lane has no output

- **WHEN** one activated lane ends with reason `missing` while another lane returns valid findings
- **THEN** coverage counts only the successful execution as valid, status is `degraded`, and failed-lane detail names the missing-output lane

#### Scenario: Every lane fails

- **WHEN** every activated lane ends with an invalid final execution
- **THEN** status is `failed`, no invalid execution contributes findings, and every lane appears in failed-lane detail

### Requirement: Partial discovery output is preserved

A degraded review MUST preserve and merge findings from valid lane executions, and every machine and human presentation of those findings MUST label the result as partial.

#### Scenario: Valid security lane survives another lane's failure

- **WHEN** a security lane returns usable findings and a correctness lane returns schema-invalid output
- **THEN** the security findings remain in merge and report artifacts under a degraded partial-review status

