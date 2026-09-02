## ADDED Requirements

### Requirement: Agentic discovery reviews an anchored repository range

Agentic discovery MUST be the default discovery mode, MUST require non-null base and head SHAs plus a verified checkout at the head, and MUST plan one logical run per active lane and requested replica without applying generated-path exclusions, per-file limits, aggregate diff budgets, or diff chunking. Each agentic prompt MUST contain only the lane document, a minimal statement identifying the `<base>...<head>` repository range, and structured-output instructions; it MUST NOT contain unified-diff content, a materialized diff path, exclusion-glob guidance, a dynamic brief, or an already-covered-rules section.

#### Scenario: Large target uses one autonomous scope

- **WHEN** an agentic target diff is larger than the inline aggregate budget
- **THEN** discovery plans one run per lane and replica, reports no prompt budget, and gives each run the same verified repository range without embedding diff content

#### Scenario: Agentic target has no base

- **WHEN** an uncommitted or root-commit target without a base SHA is selected in agentic mode
- **THEN** discovery fails closed before runtime dispatch with a machine-readable checkout-verification reason

### Requirement: Coverage receipts are verified and retried once

For each activated lane, discovery MUST union `covered` receipts only from VALID outputs, MUST treat a whole-file receipt as covering every controller-parsed hunk for that exact path, and MUST treat a `file:start-end` receipt as covering intersecting new-side hunk ranges for that exact path. If the per-lane union omits any target hunk after the initial dispatch and ordinary invalid-result retry, discovery MUST dispatch exactly one additional coverage wave containing one run for each incomplete lane, MUST preserve that wave in a distinct artifact directory, and MUST NOT coverage-redispatch again. Discovery MUST enrich findings from valid coverage-wave outputs, recompute the receipt union, and persist every still-uncovered canonical hunk ID in the owning `LaneCoverage.uncovered` list.

#### Scenario: Initial receipt misses one hunk

- **WHEN** a lane's valid initial replicas collectively omit one controller hunk and its single coverage-wave run reports that hunk
- **THEN** that lane is coverage-redispatched once and persists an empty uncovered list

#### Scenario: Coverage remains incomplete

- **WHEN** the coverage-wave output still omits a controller hunk
- **THEN** discovery performs no third coverage wave and persists that canonical hunk ID as uncovered

#### Scenario: Invalid output claims coverage

- **WHEN** an INVALID run artifact contains or previously contained receipt-like data
- **THEN** none of that data contributes to verified coverage

## MODIFIED Requirements

### Requirement: Sweep prompts receive covered rules

In inline mode, a lane declaring `covered_by_others: inject` MUST receive every other active lane's rule IDs in an already-covered section and MUST be instructed not to re-report those classes. Agentic mode MUST omit this separate section to preserve its minimal prompt contract.

#### Scenario: Two other lanes are active inline

- **WHEN** the sweep runs in inline mode beside security and schema lanes
- **THEN** its prompt names both lanes and their rule IDs as already covered

#### Scenario: Sweep runs agentically

- **WHEN** the sweep runs in agentic mode
- **THEN** its prompt contains its lane document and no separately injected already-covered section

### Requirement: Discovery dispatch defaults to one replica

The DISCOVER stage MUST plan one run per active lane per inline diff chunk or per active lane agentic scope by default, independently of the adjudication replica count, and MUST dispatch all planned lane-replica-scope runs through one shared wave. It MUST preserve the requested positive discovery count when callers explicitly request multiple replicas.

#### Scenario: Four inline lanes activate over two chunks

- **WHEN** inline discovery uses its default replica count while adjudication uses three replicas
- **THEN** it submits eight planned runs without waiting for one lane or chunk to finish before submitting another

#### Scenario: Four agentic lanes activate

- **WHEN** agentic discovery uses its default replica count while adjudication uses three replicas
- **THEN** it submits four planned initial runs regardless of target diff size

#### Scenario: Three replicas are explicitly requested

- **WHEN** agentic discovery is called with three replicas for four active lanes
- **THEN** it submits 12 planned initial runs through the existing shared wave regardless of the adjudication replica count

### Requirement: Dynamic brief falls back to PR claims

In inline mode, dynamic lanes MUST use an operator-supplied brief when present, SHALL otherwise use the PR title and body when available, and MUST label the PR-derived brief as an UNVERIFIED claim of intent. Agentic mode MUST omit a separately injected brief from the runtime prompt.

#### Scenario: No operator brief for an inline PR

- **WHEN** an inline PR target has a title and body but no `--dynamic-brief`
- **THEN** dynamic prompts contain the title/body and the UNVERIFIED note

#### Scenario: No brief source exists inline

- **WHEN** an inline commit target has no operator brief
- **THEN** dynamic prompts state that the brief is unavailable and findings should be marked inconclusive

#### Scenario: Agentic dynamic lane runs

- **WHEN** a dynamic lane executes in agentic mode
- **THEN** its prompt omits operator and PR-derived brief sections

### Requirement: Generated and oversized files are visibly excluded

Inline discovery MUST exclude default generated globs (`**/runtime-snapshots/**`, `**/*.generated.*`, `**/generated/**`, lockfiles, `**/dist/**`, and `**/__snapshots__/**`) and per-file diffs above 200,000 characters, MUST retain exact kept/excluded character accounting, and MUST prepend a visible exclusion header to the review diff. Agentic discovery MUST NOT apply these prompt-sizing exclusions.

#### Scenario: Generated snapshot dominates an inline diff

- **WHEN** a generated snapshot matches a configured glob in inline mode
- **THEN** it is absent from lane diff content, appears in the exclusion report with reason `generated-path`, and is named in the visible header

#### Scenario: Generated path exists in agentic range

- **WHEN** an agentic target changes a path that matches an inline exclusion glob
- **THEN** the controller gives no exclusion instruction and the agent may inspect the path from the checkout

### Requirement: Diff budget plans ordered file chunks

In inline discovery, after generated-path and oversized-file exclusions, discovery MUST partition complete kept file segments with order-preserving greedy next-fit packing, MUST place every kept file in exactly one chunk, and MUST keep each chunk's retained segment characters at or below 400,000. The inline planner MUST return one chunk when the retained diff fits, MUST preserve that filtered diff byte-for-byte, and MUST record ordered chunk count, file placement, and character accounting. The same module MUST additionally expose an unpartitioned reviewed-diff projection that returns the concatenated kept segments behind the visible exclusion header together with the same exclusion report, so post-discovery stages apply one shared exclusion policy rather than re-implementing it. Agentic discovery MUST NOT consult this planner for prompt sizing.

#### Scenario: Ordinary inline diff fits one chunk

- **WHEN** inline retained file segments total at most 400,000 characters
- **THEN** the planner returns one chunk whose diff bytes equal the previously filtered result

#### Scenario: Large inline source diff requires multiple chunks

- **WHEN** inline retained file segments total about 735,000 characters and every file is at most 200,000 characters
- **THEN** the planner returns at least two chunks in source order, every chunk is at most 400,000 retained characters, and every kept file appears exactly once

#### Scenario: A post-discovery stage requests the reviewed diff

- **WHEN** a caller requests the reviewed-diff projection for a target whose diff contains one generated file and one kept file
- **THEN** it receives the kept segment behind the exclusion header plus the exclusion report, and the generated segment is absent

#### Scenario: Large agentic source range

- **WHEN** the same source range is reviewed agentically
- **THEN** discovery performs no diff-budget planning and retains one logical scope per lane and replica

### Requirement: Chunk prompts expose the whole file plan

Every inline discovery prompt MUST identify its `chunk k/N`, MUST list every kept file path in source order, MUST mark which listed files are present in the current chunk, and MUST include only that chunk's complete diff segments in its unified-diff section. Agentic prompts MUST contain neither chunk context nor a unified-diff section.

#### Scenario: Inline lane reviews the first of two chunks

- **WHEN** the first inline chunk contains `src/a.py` and the second contains `src/b.py`
- **THEN** the first prompt says `chunk 1/2`, lists both paths, marks `src/a.py` as included, and embeds no `src/b.py` diff segment

#### Scenario: Agentic lane reviews both paths

- **WHEN** the agentic range changes `src/a.py` and `src/b.py`
- **THEN** the prompt identifies only the base/head range and the agent discovers both paths from the checkout

### Requirement: Discovery records per-lane coverage

Discovery MUST record each activated lane's aggregate planned dispatched, valid, and finding counts, MUST record exactly one strict run entry for every planned `(replica, chunk)` combination including zero-finding and INVALID results, and MUST record whether a bounded coverage re-dispatch occurred plus the ordered canonical hunk IDs still uncovered after it. Coverage-wave executions MUST remain separately inspectable without changing the planned run identity set.

#### Scenario: One chunk remains invalid

- **WHEN** a two-chunk, three-replica inline lane has five VALID final results and one INVALID final result
- **THEN** coverage reports six dispatched, five valid, and six distinct run entries identifying the invalid replica-chunk combination

#### Scenario: Agentic lane remains incomplete

- **WHEN** an agentic lane's initial and coverage-wave receipts omit one hunk
- **THEN** coverage retains its planned lane-replica run entries, marks coverage re-dispatch true, and lists the omitted canonical hunk ID
