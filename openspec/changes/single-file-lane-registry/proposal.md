## Why

The review rule source of truth is currently a personal `~/.hermes/review/`
registry whose `layers.yaml` duplicates lane metadata and makes project rules
hard to operate as a team.  Phase 1 moves common rules into the package and
gives repositories a base-ref-pinned `.rvw/` extension point while retaining a
deprecated legacy fallback for migration.

## What Changes

- Define a single Markdown file format in which lane frontmatter contains
  activation, tier, cost, severity, and lifecycle metadata and `## rule:` body
  headings are the only rule-id declaration.
- Ship the current base, scope, and dynamic lanes as packaged defaults.
- Load project lanes and optional policy from `.rvw/` at the resolved base
  revision, with an explicit `--allow-worktree-rules` development escape hatch
  that is visibly stamped as non-SoT.
- Merge packaged, repository, and deprecated external lanes with documented
  collision precedence; keep the external `layers.yaml` parser frozen.
- Add `rvw lanes lint` with machine-readable validation failures.

## Capabilities

### Modified Capabilities

- `lane-registry`: replace the normative lane source with packaged and
  base-ref-pinned repository documents while preserving activation semantics.

## Impact

- `src/rvw/lane.py`, `src/rvw/registry.py`, target loading, CLI lane commands,
  report metadata, packaged lane data, and regression tests.
- No files under `~/.hermes/review/` are modified.
- Discovery, adjudication, and reporting consume the same effective lane set;
  only registry discovery and rule-document format change.
