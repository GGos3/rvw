## MODIFIED Requirements

### Requirement: Target gate anchors one disposable review

The `rvw gate --target <pr>` command MUST accept only a pull-request target, MUST capture its base and head SHA, MUST provision a disposable checkout detached at that head with both commits resolvable, MUST verify the checkout's HEAD equals the captured head and its porcelain status is empty, MUST verify `git diff <base>...<head>` is computable inside it, and MUST execute the shared review pipeline exactly once in that checkout. Checkout verification failures MUST be fail-closed and carry a machine-readable reason.

#### Scenario: Checkout does not match PR head

- **WHEN** the provisioned checkout resolves to a commit other than the captured head or has tracked or untracked changes
- **THEN** gate fails closed before executing review with a checkout-verification reason

#### Scenario: Base cannot be resolved

- **WHEN** the captured base commit is unavailable in the provisioned checkout
- **THEN** gate fails closed before executing review with reason `base-unresolvable`

#### Scenario: Target review starts

- **WHEN** checkout HEAD, cleanliness, commit resolution, and three-dot diff validations pass
- **THEN** gate invokes one review pipeline and persists its ordinary stage artifacts under one run ID

### Requirement: Coverage exactly matches the activated plan

Gate MUST require a nonempty activated lane plan with a positive inline chunk count or one agentic scope, MUST derive every planned `(lane, discovery replica, chunk)` combination, MUST require exact equality with the distinct persisted planned coverage run entries, and MUST require every planned entry to be VALID. It MUST reject missing, duplicate, unexpected, invalid, or aggregate-inconsistent planned coverage and MUST NOT use the adjudication replica count for discovery coverage. Informational agentic `uncovered` receipts MUST remain visible in gate artifacts without inventing additional planned identities.

#### Scenario: Vacuous run has no dispatches

- **WHEN** discovery contains no coverage rows or a lane reports zero dispatched runs
- **THEN** gate fails coverage and cannot publish

#### Scenario: One planned lane is absent

- **WHEN** the activated plan contains a lane absent from discovery coverage
- **THEN** gate fails even if aggregate valid and dispatched counts are equal

#### Scenario: One inline chunk combination is missing

- **WHEN** a planned inline lane-replica-chunk entry is absent while another entry is duplicated or aggregate counts otherwise appear complete
- **THEN** gate fails exact coverage comparison

#### Scenario: One planned result is invalid

- **WHEN** every planned combination is present but one entry is INVALID
- **THEN** gate fails with that lane, replica, chunk, and machine-readable invalid reason in persisted coverage

#### Scenario: Agentic receipt remains uncovered

- **WHEN** planned agentic runs are valid but bounded receipt verification leaves a hunk uncovered
- **THEN** exact execution coverage remains structurally valid and the uncovered hunk remains visible in the gate evidence
