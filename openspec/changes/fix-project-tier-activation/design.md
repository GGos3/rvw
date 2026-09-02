## Context

See [proposal.md](proposal.md) for motivation. The effective registry builds one activation layer per lane document. It currently bypasses predicate evaluation for base, dynamic, and project tiers, while scope lanes already use the shared changed-path glob matcher.

## Goals / Non-Goals

**Goals:**

- Apply the existing scope path-matching behavior to project-tier lane documents.
- Preserve unconditional activation for base and dynamic tiers and predicate-free project and scope lanes.

**Non-Goals:**

- Change lane frontmatter schemas or glob semantics.
- Add repository predicates to single-file lanes.
- Change the legacy layered-registry activation path.

## Decisions

Treat only base and dynamic tiers as intrinsically unconditional, allowing project and scope tiers to share the existing path-predicate branch. This is the smallest change and reuses `_glob_match`, avoiding a second activation implementation. An alternative tier-specific project branch was rejected because it would duplicate scope semantics and could drift later.

Exercise activation through repository lane Markdown fixtures in a temporary worktree. This covers frontmatter parsing and effective-registry activation together while leaving packaged and external registry content untouched.

## Risks / Trade-offs

- [Previously over-activated project lanes stop running on unrelated changes] → This is the intended correction and only affects lanes that explicitly declare `when.paths`.
- [Project and scope semantics could diverge in a future edit] → Keep both tiers on the same predicate-evaluation path and cover project behavior with regression assertions.
