## Why

Path-scoped project lanes currently activate for every change because the effective registry treats all project-tier lanes as unconditional. This makes repository-owned specialist lanes run outside the paths declared in their frontmatter.

## What Changes

- Make project-tier lanes honor `when.paths` with the same changed-path glob semantics as scope-tier lanes.
- Keep base and dynamic lanes always active.
- Keep project and scope lanes without `when` active for every target.
- Add regression coverage for matched, unmatched, and predicate-free project lanes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `lane-registry`: Require project-tier lane activation to honor optional changed-path predicates.

## Impact

- `src/rvw/registry.py`: effective lane activation.
- Registry activation tests for repository-owned project lanes.
- No schema, CLI, dependency, or external registry changes.
