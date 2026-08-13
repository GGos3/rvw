## Why

Re-reviews of the same PR repeatedly resurrect findings the operator already accepted. Tier-one carry requires byte-equal hunk and body digests, but adjudication bodies are model prose and vary across runs, and unrelated edits move hunk content. In practice almost every accepted finding demotes to tier two on the next round, where the current contract resets the decision to `must_fix` and prefills only the reason. Operators re-litigate deliberate-design and low-ROI acceptances every round, which is the dominant re-review fatigue today.

## What Changes

- Add a sticky tier-two outcome: when an accepted `(file, rule_id)` candidate is unique on both sides, severities are equal, and the severity is not `blocker`, the generated disposition prefills decision `accepted` with the prior reason at a new inheritance tier `unique_pair_sticky`, stamped with the source run and the machine-readable demotion cause.
- Blockers are excluded from sticky prefill in every tier below exact-ID carry; they keep the current `must_fix` prefill. Pair-matched candidates with differing severities also keep `must_fix` and now record `severity_changed`.
- Sticky entries never satisfy the fully-inherited no-pause path: the gate still writes the template and exits for human completion, so every sticky acceptance is revalidated by an operator before a verdict.
- Inheritance summaries and partial-inheritance pause reports count `sticky` separately from carried, prefilled, and blank. Generated templates render the source run identifier and demotion cause beside each sticky entry.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pr-gate`: Tier-two identity matching gains the sticky accepted outcome, blocker and severity exclusions, pause preservation, summary counts, and template provenance rendering.

## Impact

`gate.py` matching (`match_inherited_dispositions`), `InheritanceTier`, `InheritanceSummary`, template rendering, and gate verdict findings gain the sticky tier; the disposition document schema submitted by operators is unchanged. Exact-ID carry, ambiguity blanking, owner-only blocker acceptance, and the no-pause path for fully exact-carried runs remain authoritative.

Out of scope, tracked separately: review-mode (non-gate) disposition inheritance and report annotation, a repo decision ledger injected into adjudication prompts, and a likelihood/ROI axis on the finding model.
