## ADDED Requirements

### Requirement: Project-tier lane path predicates narrow activation

Project and scope lane documents without a `when` predicate MUST activate for every target. When a project or scope lane document declares `when.paths`, the lane MUST activate if and only if at least one changed path matches at least one declared pattern using the registry's changed-path glob semantics. Base and dynamic lane documents MUST remain unconditionally active.

#### Scenario: Scoped project lane does not match the changed paths

- **WHEN** a project-tier lane declares `when.paths: ["src/**"]` and the target changes only `README.md`
- **THEN** that project-tier lane is not activated

#### Scenario: Scoped project lane matches a changed path

- **WHEN** a project-tier lane declares `when.paths: ["src/**"]` and the target changes `src/app.py`
- **THEN** that project-tier lane is activated

#### Scenario: Predicate-free project lane remains unconditional

- **WHEN** a project-tier lane declares no `when` predicate
- **THEN** that project-tier lane activates for every target
