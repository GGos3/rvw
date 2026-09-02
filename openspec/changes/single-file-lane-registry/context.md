## Context

The external registry is intentionally left in place for one published release
as a read-only fallback.  Builtin lanes are copied byte-for-byte in rule prose;
the migration only removes the duplicated `rules:` frontmatter and adds rule
headings so IDs can be derived from the body.

For an uncommitted target the base revision is `HEAD`; for a commit it is the
captured parent (or the commit itself when it has no parent); for a PR it is the
resolved PR base SHA.  Git plumbing reads `.rvw/` blobs and trees from that
revision, never from the PR head or working tree unless the explicit escape
hatch is enabled.

`when.repo` remains supported only by the frozen legacy external loader.  New
format lanes are repository-bound by location: base and dynamic lanes are
unconditional, scope lanes use `when.paths`, and project lanes in `.rvw/` are
unconditional.

The lint command reports stable reason codes so CI can consume failures without
parsing prose.  Duplicate lane IDs are errors after all sources are collected;
runtime precedence remains repository over legacy external over packaged.

## Open questions

None for Phase 1.  Removal of the deprecated external fallback is deferred to a
neighbouring migration change after one release.
