## MODIFIED Requirements

### Requirement: Accepted dispositions carry by tiered identity matching

For each actionable finding of the current run, gate MUST persist optional `hunk_sha256` and `body_sha256` values computed respectively from the run's canonical unified-diff hunk text and the complete, order-insensitive set of collapsed finding bodies. Gate MUST evaluate inherited and current `(file, rule_id)` multiplicity before matching, and any pair duplicated on either side MUST remain blank. On an unambiguous pair, gate MUST auto-carry an accepted decision only when the public finding ID, `(file, rule_id)`, severity, and known hunk and body-set digests all match exactly.

When exact carry is unavailable but one accepted inherited finding and one current actionable finding form a unique `(file, rule_id)` pair, the current severity equals the source severity, and the severity is not `blocker`, gate MUST generate decision `accepted`, copy the prior reason, stamp the inherited run ID, classify the match as `unique_pair_sticky`, and retain the applicable machine-readable demotion reason. A sticky match MUST NOT qualify for automatic continuation and MUST require operator review of the generated disposition template.

When the unique pair is a blocker or its severity changed, gate MUST keep decision `must_fix`, MAY prefill the prior reason, MUST NOT classify the match as sticky, and MUST record the applicable demotion reason. Gate MUST NOT carry or sticky-prefill inherited `must_fix` dispositions. Every persisted verdict finding MUST optionally record its inheritance tier and blank or demotion reason.

#### Scenario: Unique warning recurs in a changed hunk

- **WHEN** a previously accepted warning uniquely matches the current finding by `(file, rule_id)` with equal severity but its known hunk digest changed
- **THEN** the generated record is `accepted` at tier `unique_pair_sticky`, copies the prior reason and source run, records `content_changed`, and gate pauses for operator review

#### Scenario: Unique warning receives a changed diagnosis

- **WHEN** a previously accepted warning uniquely matches the current finding by `(file, rule_id)` with equal severity and hunk digest but its body-set digest changed
- **THEN** the generated record is `accepted` at tier `unique_pair_sticky`, records `diagnosis_changed`, and gate pauses for operator review

#### Scenario: Sticky-only findings do not auto-proceed

- **WHEN** every current actionable finding is covered by a sticky acceptance but none qualifies for exact carry
- **THEN** gate persists a generated disposition template and exits for operator completion rather than creating a completed verdict

#### Scenario: Unique blocker recurs after content changes

- **WHEN** a previously accepted blocker uniquely matches the current blocker by `(file, rule_id)` but does not qualify for exact carry
- **THEN** gate keeps `must_fix`, may prefill the prior reason, and does not classify the record as sticky

#### Scenario: Unique pair changes severity

- **WHEN** a previously accepted finding uniquely matches the current finding by `(file, rule_id)` but their severities differ
- **THEN** gate keeps `must_fix`, records `severity_changed`, and does not classify the record as sticky

#### Scenario: Rule fires twice in one file

- **WHEN** either run contains two findings with the same `(file, rule_id)` pair, including a mixed accepted and must-fix pair in the inherited verdict
- **THEN** no disposition carries or becomes sticky for that pair and the entries remain blank even if one or more public IDs and both digests match exactly

#### Scenario: Prior must-fix finding recurs

- **WHEN** the inherited verdict marked a finding `must_fix` and the new run re-detects the same finding ID
- **THEN** the generated record is a blank `must_fix` template entry without a carried reason and without sticky inheritance

#### Scenario: Exact finding recurs after an unrelated push

- **WHEN** a new run re-detects an accepted finding with the same public finding ID, equal `(file, rule_id)` pair and severity, and equal known canonical hunk and complete body-set digests
- **THEN** the generated record contains the accepted decision, the prior reason, and the inherited run ID

#### Scenario: Exact finding ID has a different identity pair

- **WHEN** an accepted source finding has the current public finding ID but a different file or rule ID
- **THEN** gate leaves the current record blank with `identity_mismatch` and neither carries nor prefills it

#### Scenario: Exact finding ID has changed hunk content

- **WHEN** a public finding ID equals an accepted inherited finding but the known hunk digests differ
- **THEN** gate applies tier-two rules, records `blank_reason: content_changed`, and does not auto-proceed

#### Scenario: Prior verdict has no hunk digest

- **WHEN** an exact-ID inherited finding has no `hunk_sha256`
- **THEN** gate records `source_digest_missing` and applies tier-two rules rather than auto-carrying

#### Scenario: Current finding has no hunk digest

- **WHEN** an exact-ID current finding has no canonical hunk digest
- **THEN** gate records `current_digest_missing` and applies tier-two rules rather than auto-carrying

#### Scenario: Exact finding has a changed diagnosis

- **WHEN** an exact-ID finding has equal known hunk digests but any member of its collapsed body set changes
- **THEN** gate records `diagnosis_changed`, applies tier-two handling, and does not auto-carry

#### Scenario: Exact finding has changed severity

- **WHEN** an exact-ID finding has equal digests but its current severity differs from the source severity
- **THEN** gate records `severity_changed`, prefills through tier two, and does not auto-carry

#### Scenario: Outcome contains an orphan finding key

- **WHEN** an adjudication outcome contains a verdict key absent from the merged finding groups
- **THEN** gate persists a BLOCK gate-invariant verdict naming the orphan key and does not auto-proceed

#### Scenario: Finding bodies recur in another order

- **WHEN** an exact-ID finding has equal known hunk digests and the same nonempty collapsed body set in a different order
- **THEN** the body digest remains equal and the finding remains eligible for tier-one carry

#### Scenario: Collapsed finding has no bodies

- **WHEN** an actionable collapsed finding has an empty body collection
- **THEN** gate raises a gate invariant instead of assigning an ordinary digest

#### Scenario: Same rule moved to a different hunk

- **WHEN** an accepted finding's `(file, rule_id)` pair matches exactly one finding in each run but the finding IDs differ
- **THEN** an equal-severity non-blocker record becomes `accepted` at tier `unique_pair_sticky`, prefills the prior reason, stamps the inherited run ID, and records `finding_id_changed`

### Requirement: Fully inherited runs proceed without pausing

When every actionable finding of the current run is covered by a hunk-and-body-digest-verified exact-ID carried acceptance, gate MUST persist the generated disposition document and continue into disposition validation and verdict construction in the same invocation. Sticky accepted entries MUST count as requiring operator completion even though their generated decisions are `accepted`. A partial-inheritance pause MUST report and persist the source run ID plus exact-carried, sticky, reason-only prefilled, and blank counts grouped by machine-readable reason.

#### Scenario: One finding is sticky

- **WHEN** all other actionable findings exact-carry but one receives `unique_pair_sticky`
- **THEN** gate writes the generated template with sticky provenance and exits for human completion

#### Scenario: Sticky summary is distinct

- **WHEN** inheritance produces exact-carried, sticky, reason-only prefilled, and blank outcomes
- **THEN** the pause summary reports separate counts for all four categories and does not include sticky entries in carried

#### Scenario: Authorization subprocess emits sensitive stderr

- **WHEN** actor or permission lookup fails with stderr containing credentials, control characters, or an oversized response
- **THEN** gate preserves the failed step and exit status while every console, JSON, and Markdown diagnostic contains only the bounded redacted form

#### Scenario: Every actionable finding was previously accepted

- **WHEN** all actionable findings receive tier-one carried acceptances from the inherited verdict
- **THEN** gate validates the persisted generated document and reports a verdict in the same invocation

#### Scenario: One finding is new

- **WHEN** one actionable finding has no match in the inherited verdict
- **THEN** gate writes the partially prefilled template and exits nonzero for human completion

#### Scenario: Carried blocker acceptance without admin actor

- **WHEN** every actionable finding carries but one accepted blocker's re-verified actor lacks repository admin permission
- **THEN** gate fails closed and does not publish
