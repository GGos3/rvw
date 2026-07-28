## Why

Repository predicates currently require one exact `owner/name` string, while path predicates support multiple glob patterns. This prevented project-tier review rules from activating for provider repositories covered by an existing repository family, including the 2026-07-28 APIFuse provider review incident.

## What Changes

- Interpret a string `when.repo` value as a case-sensitive fnmatch glob pattern.
- Accept a list of repository glob patterns and match when any pattern matches.
- Preserve the AND relationship between configured repository and changed-path predicates.
- Add regression coverage for exact strings, globs, list OR behavior, mismatches, and combined repository/path predicates.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `lane-registry`: Define case-sensitive repository glob matching and list-OR semantics for layer activation predicates.

## Impact

- `src/rvw/registry.py`: `LayerPredicate.repo` schema and `Registry.activate` matching.
- `tests/test_registry.py`: activation and schema regression coverage.
- `openspec/specs/lane-registry/spec.md`: resulting repository predicate contract after implementation and archive.
- No runtime registry content under `~/.hermes/review/` is changed.
