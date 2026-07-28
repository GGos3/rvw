## MODIFIED Requirements

### Requirement: Collapse identity is deterministic

The merge stage MUST collapse findings by the tuple `(file, hunk_id, rule_id)`, MUST expose the lowercase SHA-1 digest of `file:hunk_id:rule_id` as the group key, and MUST treat that group key as the stable public finding ID for artifacts and dispositions bound to the same base and head anchors.

#### Scenario: Replicas report the same rule in one hunk

- **WHEN** three replicas report the same rule ID, file, and hunk
- **THEN** merge produces one collapse group with one deterministic key

#### Scenario: Gate renders a finding

- **WHEN** a merged group is included in a gate verdict or disposition template
- **THEN** its public `finding_id` equals the group's deterministic key without transcription or a separately generated identifier
