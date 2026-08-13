## Context

Gate already auto-selects the newest completed same-PR disposition source. Exact-ID inheritance is intentionally strict: it requires equal identity, severity, canonical hunk digest, and body-set digest. Any content movement or model diagnosis variation demotes a unique `(file, rule_id)` match to tier two, whose present behavior restores `must_fix` and only copies the reason.

That fail-closed default protects against silent acceptance after meaningful changes, but it makes deliberate-design and low-ROI decisions non-durable. The goal is to keep the operator's prior decision visible and selected without allowing stale acceptance to pass unattended.

## Goals / Non-Goals

**Goals:**

- Preserve a prior non-blocker acceptance as the selected decision for one unambiguous same-file, same-rule recurrence.
- Keep a mandatory human checkpoint whenever identity or evidence changed.
- Preserve machine-readable provenance and explain why the finding did not qualify for exact carry.
- Keep blocker, ambiguity, severity-change, and `must_fix` behavior fail-closed.

**Non-Goals:**

- Automatically pass a gate from sticky tier-two acceptances.
- Carry blockers below exact-ID matching.
- Infer that two different rules express the same product decision.
- Inject repository decision history into adjudication prompts.
- Change `rvw review`; this change applies to the disposition-aware `rvw gate` path.

## Decisions

### Sticky is a distinct tier, not relaxed exact carry

Introduce `InheritanceTier.UNIQUE_PAIR_STICKY`. A unique accepted source and current actionable finding sharing `(file, rule_id)` is eligible only when severity is equal and not `blocker`. The generated decision is `accepted`, the prior reason and source run are retained, and the applicable digest or identity demotion cause remains attached.

Treating this as exact carry was rejected because moved or rediagnosed evidence has not been mechanically proven identical.

### Sticky always pauses

The fully inherited fast path remains restricted to `EXACT_ID`. A sticky result is complete enough to avoid retyping the decision but not complete enough to create a verdict. Gate persists the generated template and exits nonzero for operator review and resume.

Automatic continuation was rejected because a same rule in a changed hunk can represent a materially different risk even when the prior acceptance remains a useful default.

### Blockers and changed severity remain must-fix

A blocker never becomes sticky. Any severity mismatch also keeps `must_fix`, even if the prior and current pair is unique. These cases retain the inherited reason as context and expose `severity_changed` when applicable.

### Ambiguity remains blank

If either source or current run has multiple findings for the pair, no sticky decision is generated. Existing source/current ambiguity reasons remain authoritative.

### Summaries expose sticky separately

`InheritanceSummary` gains `sticky`. It is not folded into `carried`, because carried means mechanically identical and eligible for no-pause continuation. It is not folded into `prefilled`, because prefilled means the prior reason was copied while the decision stayed `must_fix`.

## Risks / Trade-offs

- [A changed finding is accepted by default] → sticky always pauses and requires the operator to submit the generated disposition document before a verdict exists.
- [Rule IDs are too broad] → require unique pair, equal severity, non-blocker status, preserve the prior reason and demotion cause, and leave ambiguity fail-closed.
- [Operators overlook sticky provenance] → render sticky tier, source run, and demotion reason directly beside the YAML entry and in the pause summary.
- [Counts are misread as carried] → use a dedicated `sticky` summary counter and keep the no-pause predicate exact-tier-only.

## Migration Plan

Add the enum value and summary field with defaults so existing artifacts continue to load. Update matcher and rendering behind regression tests. Existing disposition files require no migration.
