## ADDED Requirements

### Requirement: Discovery mode is selectable and agentic by default

Runtime-executing review, auto, gate, stack-review, and plan paths MUST select `agentic` discovery by default and MUST accept `inline` as an explicit fallback. The selected mode MUST propagate unchanged through planning and discovery. Sampling MUST continue to use the inline fixture path.

#### Scenario: Operator uses the default

- **WHEN** an ordinary review command omits discovery mode
- **THEN** it provisions or verifies a checkout and runs agentic discovery

#### Scenario: Operator selects legacy fallback

- **WHEN** an ordinary review command selects `inline`
- **THEN** the existing embedded-diff, exclusion, budget, and chunk behavior is used without requiring an agentic checkout

#### Scenario: Uncommitted review uses inline mode

- **WHEN** an operator selects inline discovery for an uncommitted target
- **THEN** the existing in-memory target diff remains reviewable
