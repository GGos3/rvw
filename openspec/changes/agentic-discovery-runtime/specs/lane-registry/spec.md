## MODIFIED Requirements

### Requirement: Plan exposes mode-expanded execution counts

`rvw plan` MUST display the selected discovery mode. In inline mode it MUST apply the shared diff chunk planner and report total runs as active lanes multiplied by replicas multiplied by chunks. In agentic mode it MUST NOT apply that planner, MUST report one logical scope, and MUST report initial total runs as active lanes multiplied by replicas; a possible bounded coverage wave is reactive and MUST NOT be included in the initial total.

#### Scenario: Three inline lanes span two chunks

- **WHEN** inline planning uses three replicas for three active lanes and the target diff produces two chunks
- **THEN** plan displays inline mode, two chunks, and 18 initial runs

#### Scenario: Large target uses agentic planning

- **WHEN** agentic planning uses three replicas for three active lanes regardless of target diff size
- **THEN** plan displays agentic mode, one logical scope, and nine initial runs without consulting the diff budget
