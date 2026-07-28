# Finding model context

## Purpose and scope

This capability turns runtime-authored claims into deterministic, inspectable merge units and then builds presentation views over those units. See [spec.md](spec.md) for the normative model.

## Key decisions and measured basis

- ADR-003 separates true duplicate collapse from same-site corroboration. The collapse key includes the rule; the site key does not.
- The first real PR smoke produced 21 runtime findings and 13 collapse groups. Combining pattern and region edges transitively created an unusable eight-group/four-rule mega-cluster, so the two fold layers remain independent.
- Amendment A originally used shared backtick identifiers. The implemented threshold was re-measured on PR #1119: genuine edge populations were 0.50-1.00, incidental `proxy_connect_failed` links were 0.25-0.333, and 0.40 separated them with margin.
- Repetition is independent of agreement and cross-layer support. Four one-of-three findings across four providers can be meaningful as one repeated pattern without pretending replica agreement increased.
- The same PR smoke completed DISCOVER in about 410 seconds and ADJUDICATE in about 197 seconds; deterministic merge/folding reduced the final presentation to five report items without changing the 13 adjudication identities.

## Constraints

- Hunk identity changes with the reviewed diff, so findings are head-specific.
- Pattern tokens come only from text inside backticks.
- A pattern component cannot contain two groups from the same file.
- Line-less findings cannot enter region folds.
- SHA-1 is used as a stable compact identifier, not as a security boundary.
- Public finding IDs are stable only for unchanged base/head anchors because the hunk ID is part of the digest input. Gate dispositions therefore bind to an anchored run and cannot survive a stale rebase silently.

## Failure modes

- Two distinct defects of the same rule within one large hunk collapse together.
- Incidental identifier overlap can over-fold if the similarity threshold is too low; semantically identical prose with no shared backtick tokens will not fold.
- Region components use adjacent-distance chaining, so the first and last member may be more than 15 lines apart.
- Display folds can obscure member-specific reasons unless rendering preserves per-member content.

## Concrete example

Three replicas emit `bug/severe-defect` for `src/a.py` in hunk `src/a.py@@-1,2+1,3@@`. Merge creates one group whose key is:

```text
sha1("src/a.py:src/a.py@@-1,2+1,3@@:bug/severe-defect")
```

If a second lane reports another rule in that hunk, it becomes another collapse group in the same site. If matching `bug/severe-defect` groups in `src/b.py` and `src/c.py` share sufficiently similar backtick identifiers, those groups form a pattern fold while all verdicts remain attached to their original keys.

## Historical deltas

- ADR-003 said merged bodies were appended verbatim; the implementation removes exact duplicate body strings while preserving the first occurrence and all raw member findings.
- The Amendment's phrase "no transitive chaining" is implemented as no connectivity shared between pattern and region layers. Each layer may form its own graph component; region components specifically chain adjacent groups.
- The initial shared-identifier rule was tightened to Jaccard `>= 0.40` after fixture re-measurement.
