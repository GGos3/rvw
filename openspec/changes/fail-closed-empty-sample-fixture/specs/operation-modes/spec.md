## MODIFIED Requirements

### Requirement: Sampling compares enum and free variants

The sampling gate MUST accept both unified-diff fixtures and ordinary source-file fixtures, MUST pass a fixture that starts with a `diff --git ` or `--- ` file header to the shared exclusion and chunk planner without wrapping it in another diff, and MUST convert an ordinary source-file fixture to a `/dev/null` unified diff before planning. It MUST fail before runtime dispatch with a machine-readable `empty-review-diff` user error containing every excluded file's reason when budgeting retains zero review characters. Otherwise, it MUST execute closed-enum and free-rule-ID variants with equal replica counts for every chunk in one bounded wave, MUST report sorted free-variant rule IDs absent from the lane's closed enum as `novel_rule_ids`, and MUST report in-enum enum-only and free-only `(file, line)` sites separately as site variance. It MUST retain the `PASS` and `REVIEW` verdict values, MUST report `REVIEW` and exit 1 only when `novel_rule_ids` is nonempty, and MUST otherwise report `PASS` and exit 0 even when site variance exists.

#### Scenario: Unified diff fixture is sampled directly

- **WHEN** a fixture starts with a supported unified-diff file header and contains multiple file segments
- **THEN** sampling budgets and chunks those original segments without a containing diff-of-diff layer

#### Scenario: Ordinary source file is sampled

- **WHEN** a fixture does not start with a supported unified-diff file header
- **THEN** sampling reviews the unified diff produced by comparing `/dev/null` with that fixture

#### Scenario: Every fixture segment is excluded

- **WHEN** generated-path and oversized-file exclusions leave zero retained fixture characters
- **THEN** sampling dispatches no runtime work, cannot report `PASS`, and exits in the user-error class with error code `empty-review-diff` and the `excluded_reason` mapping

#### Scenario: Free variant invents a rule ID

- **WHEN** any valid free-variant replica on any fixture chunk emits a rule ID outside the lane's generated closed enum
- **THEN** sampling lists that ID in `novel_rule_ids`, reports `REVIEW`, and exits 1

#### Scenario: Replicas find an existing rule at different sites

- **WHEN** free-only or enum-only sites use rule IDs contained in the lane's closed enum and no novel rule ID is emitted
- **THEN** sampling records those sites as variance, reports `PASS`, and exits 0

#### Scenario: Novel rule appears at an enum-covered site

- **WHEN** the free variant emits an out-of-enum rule ID at a `(file, line)` also found by the enum variant
- **THEN** sampling still reports that rule ID as novel because gap detection is independent of site-set difference

#### Scenario: Large fixture uses production chunk semantics

- **WHEN** a sampling fixture exceeds the per-prompt aggregate character budget after exclusions
- **THEN** both variants execute every replica on every planner-produced chunk while one-chunk fixture artifact paths remain unchanged
