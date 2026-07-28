# discovery

## Purpose

Define target preparation, gap-coverage prompting, replicated dispatch, dynamic-brief fallback, and bounded diff handling for the DISCOVER stage.

## Requirements

### Requirement: The unscoped sweep is an always-active base lane

The runtime registry MUST register `unscoped-sweep` in a predicate-free base layer, and its lane schema MUST cap emitted severity at `warning`.

#### Scenario: Project has many scoped lanes

- **WHEN** a target activates project, scope, and dynamic lanes
- **THEN** `unscoped-sweep` is still dispatched and cannot emit a blocker-severity finding

### Requirement: Sweep prompts receive covered rules

A lane declaring `covered_by_others: inject` MUST receive every other active lane's rule IDs in an already-covered section and MUST be instructed not to re-report those classes.

#### Scenario: Two other lanes are active

- **WHEN** the sweep runs beside security and schema lanes
- **THEN** its prompt names both lanes and their rule IDs as already covered

### Requirement: Discovery dispatches three replicas by default

The DISCOVER stage MUST plan three runs per active lane by default and MUST dispatch all lane-replica runs through one shared wave.

#### Scenario: Four lanes activate

- **WHEN** discovery uses the default replica count
- **THEN** it submits 12 planned runs without waiting for one lane to finish before submitting another

### Requirement: Dispatch is bounded and heavy-first

The dispatcher MUST sort runs heavy, normal, then light, and MUST bound concurrent runtime executions with a semaphore whose default capacity is 16.

#### Scenario: Heavy and light lanes share a plan

- **WHEN** semaphore capacity becomes available at the start of a wave
- **THEN** heavy lane runs are queued before normal and light lane runs while in-flight work never exceeds 16 by default

### Requirement: Invalid replicas use one all-lane retry

An invalid replica MUST be excluded from finding enrichment, and the dispatcher MUST retry a lane exactly once only when every initial replica for that lane is INVALID.

#### Scenario: One of three replicas is invalid

- **WHEN** two replicas are VALID and one is INVALID
- **THEN** discovery keeps the two valid outputs and does not retry the lane

#### Scenario: All replicas are invalid

- **WHEN** all three initial replicas for one lane are INVALID
- **THEN** the dispatcher executes one replacement wave for that lane and performs no further retry

### Requirement: Dynamic brief falls back to PR claims

Dynamic lanes MUST use an operator-supplied brief when present, SHALL otherwise use the PR title and body when available, and MUST label the PR-derived brief as an UNVERIFIED claim of intent.

#### Scenario: No operator brief for a PR

- **WHEN** a PR target has a title and body but no `--dynamic-brief`
- **THEN** dynamic prompts contain the title/body and the UNVERIFIED note

#### Scenario: No brief source exists

- **WHEN** a commit target has no operator brief
- **THEN** dynamic prompts state that the brief is unavailable and findings should be marked inconclusive

### Requirement: Generated and oversized files are visibly excluded

Discovery MUST exclude default generated globs (`**/runtime-snapshots/**`, `**/*.generated.*`, `**/generated/**`, lockfiles, `**/dist/**`, and `**/__snapshots__/**`) and per-file diffs above 200,000 characters, MUST retain exact kept/excluded character accounting, and MUST prepend a visible exclusion header to the review diff.

#### Scenario: Generated snapshot dominates a diff

- **WHEN** a generated snapshot matches a configured glob
- **THEN** it is absent from lane diff content, appears in the exclusion report with reason `generated-path`, and is named in the visible header

### Requirement: Aggregate diff overage fails loudly

Discovery MUST raise `DiffBudgetExceeded` when the remaining non-excluded diff exceeds 400,000 characters and MUST identify the largest remaining file offenders.

#### Scenario: Source diff remains too large

- **WHEN** individually allowed source files total more than 400,000 characters after exclusions
- **THEN** discovery stops with the total, the configured limit, and size-sorted offender paths instead of truncating silently

### Requirement: Discovery records per-lane coverage

Discovery MUST record each activated lane's planned replica count, valid-result count, and enriched finding count, including lanes that produced zero findings or only INVALID runs.

#### Scenario: Lane returns no findings

- **WHEN** all three replicas are valid PASS-like outputs with empty findings
- **THEN** coverage reports dispatched 3, valid 3, findings 0 for that lane
