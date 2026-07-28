# finding-model

## Purpose

Define finding identity, enrichment, deterministic collapse, site grouping, and display-only folds without changing adjudication units.

## Requirements

### Requirement: Runtime and enriched findings are separate models

The system MUST accept runtime findings containing `rule_id`, `file`, new-side `line`, `severity`, and `body`, then MUST enrich valid findings with schema version, hunk identity, anchorability, lane ID, and replica number before merge.

#### Scenario: Runtime finding is inside a diff hunk

- **WHEN** a valid runtime finding names an added line in a parsed hunk
- **THEN** discovery emits an enriched finding with that hunk's deterministic ID, `anchorable: true`, and the producing lane and replica

#### Scenario: Runtime finding is outside the diff

- **WHEN** a valid runtime finding names a line outside every parsed hunk
- **THEN** discovery retains it with hunk identity `<file>:*` and `anchorable: false`

### Requirement: Collapse identity is deterministic

The merge stage MUST collapse findings by the tuple `(file, hunk_id, rule_id)`, MUST expose the lowercase SHA-1 digest of `file:hunk_id:rule_id` as the group key, and MUST treat that group key as the stable public finding ID for artifacts and dispositions bound to the same base and head anchors.

#### Scenario: Replicas report the same rule in one hunk

- **WHEN** three replicas report the same rule ID, file, and hunk
- **THEN** merge produces one collapse group with one deterministic key

#### Scenario: Gate renders a finding

- **WHEN** a merged group is included in a gate verdict or disposition template
- **THEN** its public `finding_id` equals the group's deterministic key without transcription or a separately generated identifier

### Requirement: Collapse preserves distinct evidence

A collapse group SHALL retain unique finding bodies in encounter order, SHALL retain all member findings, SHALL choose the highest member severity, and SHALL count agreement by distinct replica number.

#### Scenario: Duplicate and distinct bodies

- **WHEN** three members contain bodies `A`, `A`, and `B` with two replica numbers
- **THEN** the group bodies are `A` then `B` and its agreement is 2

### Requirement: Sites group independent findings by hunk

The merge stage MUST group collapse groups into sites keyed by `(file, hunk_id)`, MUST count distinct lanes as corroboration, and MUST mark `cross_layer` only when those lanes span more than one activation tier.

#### Scenario: Two layers hit one hunk

- **WHEN** a base lane and a dynamic lane produce different rule groups in the same hunk
- **THEN** the groups remain separate adjudication units while their shared site has corroboration 2 and `cross_layer: true`

### Requirement: Pattern folds use measured token similarity

A pattern fold MUST connect same-rule groups in different files only when their backtick-token Jaccard similarity is at least 0.40, MUST include at most one group per file, and MUST expose its location count as repetition.

#### Scenario: Repeated identifier pattern

- **WHEN** same-rule groups in four files form qualifying backtick-token edges without repeating a file
- **THEN** merge emits a display fold with repetition 4 while retaining all four collapse-group verdict identities

#### Scenario: Incidental token overlap

- **WHEN** two groups share an incidental backtick token but have Jaccard similarity below 0.40
- **THEN** they do not form a pattern-fold edge

### Requirement: Region folds are line-bounded within one file

A region fold SHALL connect adjacent line-bearing groups in one file when each neighboring line distance is at most 15 and SHALL keep its members as independent collapse groups.

#### Scenario: Chained nearby findings

- **WHEN** groups occur at lines 10, 20, and 30 in the same file
- **THEN** they form one region component because each adjacent distance is at most 15

### Requirement: Display fold layers do not share connectivity

Pattern and region fold edges MUST be computed independently from raw collapse groups and MUST NOT be combined into one union-find or adjudication group.

#### Scenario: Group participates in both views

- **WHEN** one collapse group belongs to a cross-file pattern and a same-file region
- **THEN** it may appear in both display views without transitively merging the other pattern and region members

### Requirement: Priority exposes independent confidence axes

Every collapse group MUST expose priority axes in descending significance as cross-layer status, replica agreement, pattern repetition, and severity, followed by deterministic location and identity tie-breakers for ordering.

#### Scenario: Repetition strengthens low agreement

- **WHEN** four one-replica groups form one repeated pattern
- **THEN** each retains agreement 1 and receives repetition 4 as a separate priority axis
