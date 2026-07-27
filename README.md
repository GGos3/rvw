# rvw

Layered, replicated, self-adjudicating code review orchestrator.

`rvw` plans a review as a pyramid of rule lanes (base → project → scope →
dynamic), executes every lane with N replicas in a single concurrent wave,
merges findings deterministically (hunk-anchored collapse keys, cross-lane
site corroboration), adjudicates each candidate against the actual source,
and publishes a synthesized report with GitHub inline anchors.

## Status

Phase 1 (scaffold + DISCOVER stage). See `DECISIONS.md` for the ADRs and
`.hermes/plans/` for the implementation plan.

## Install (dev)

```bash
uv sync --all-extras
uv run rvw --help
```

## Design at a glance

- **Rule ⊂ Lane ∈ Layer; Lane × Runtime → Run** (ADR-001)
- Closed rule enums enforced via `--output-schema` — measured: schema beats
  prompt, no quality loss vs free-form ids (ADR-004)
- A mandatory tier-0 `unscoped-sweep` lane catches what scoped enums
  structurally miss — measured 3/3 deep defects vs 0/3 (ADR-005)
- 3 replicas per lane, one wave, no hedging — measured recall 88% → 99%
  (ADR-006)
- Discovery and adjudication are separate lanes; adjudication rejected 3/3
  fabricated findings with 0/6 genuine losses (ADR-007)

## License

MIT
