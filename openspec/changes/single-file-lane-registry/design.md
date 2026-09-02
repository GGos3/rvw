## Design

`Lane` gains a strict activation model and the parser derives rule IDs from
`## rule:` headings.  The compatibility loader remains available for documents
owned by the deprecated external registry; packaged and repository documents are
validated through the strict path.

`EffectiveRegistry` is a small facade over `LaneSource` records.  It discovers
package resources with `importlib.resources`, reads repository blobs with
`git ls-tree`/`git show` at `ResolvedTarget.base_sha` (or `head_sha` for an
uncommitted target), and applies repository > external > packaged replacement
semantics.  Legacy activation is evaluated before conversion so its repository
predicates remain frozen.

Discovery accepts either registry facade and loads lanes by source path or by
the facade's typed map.  This leaves dispatch, adjudication, merge, and report
contracts unchanged.  The worktree flag is threaded only through plan/review;
when enabled, a metadata artifact and report header carry the non-SoT warning.

`rvw lanes lint` uses the strict parser and emits `{ok, errors, lanes}` JSON on
request.  Each error has a stable `reason` code (`malformed-frontmatter`,
`unknown-frontmatter-key`, `stale-rules`, `duplicate-rule-id`,
`empty-rule-body`, or `duplicate-lane-id`).
