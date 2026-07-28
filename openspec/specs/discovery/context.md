# Discovery context

## Purpose and scope

DISCOVER resolves active lanes into bounded runtime work, supplies each lane the right diff and intent context, and enriches only valid runtime output. Normative behavior is in [spec.md](spec.md).

## Key decisions and measured basis

- ADR-005 makes `unscoped-sweep` the structural coverage net. On a six-defect fixture, the scoped slop lane found 0/3 deep defects in both enum and free-ID conditions, while the sweep found 3/3. Its warning cap contains the higher expected false-positive rate.
- ADR-006 chooses three replicas. Eight repeated runs showed an individual run recovered about 88% of the union; three replicas raised expected union recall to about 99%. Four replicas added little beyond that.
- Concurrency tests on a 22-core host found N=4, 8, and 16 completed in 49.1, 50.0, and 50.6 seconds. The implemented cap remains 16, with one wave and heavy-first LPT ordering.
- A real PR #1119 run dispatched 13 lanes x 3 replicas and completed DISCOVER in about 410 seconds with all 39 runs valid. ADJUDICATE then took about 197 seconds.
- The same PR contained a 2.84 MB generated `contract-graph.json` inside a 2.87 MB diff. Excluding it left 26,195 characters of reviewable source and motivated visible, file-level diff budgeting.

## Constraints

- The code does not hardcode `unscoped-sweep`; its mandatory status depends on the external default registry keeping it in a predicate-free base layer.
- The covered-rules section is prompt guidance. The strict schema prevents foreign IDs but cannot prove the model avoided semantically duplicate findings.
- The default aggregate limits are characters, not tokens or bytes.
- Concurrency above 16 has not been measured and is not the default.
- PR fallback uses title and body; linked issues from ADR-010 are not resolved by the current target model.

## Failure modes

- A base registry missing `unscoped-sweep` creates a silent coverage gap.
- A generated file not matched by the default globs may consume the aggregate budget.
- If all replicas remain invalid after the replacement wave, the lane contributes no findings but remains visible with zero valid coverage.
- A PR body can be wrong or adversarial; it is intent provenance, not correctness evidence.
- Empty or malformed diffs can fail file segmentation instead of reaching a runtime.

## Concrete example

Given active lanes `security-exposure`, `dynamic/edge-cases`, and `unscoped-sweep`, discovery builds nine planned runs. The sweep prompt lists both other lanes' closed rule IDs as already covered. If one security replica times out, its two valid outputs are still enriched with hunk IDs; no security retry occurs. If all three dynamic replicas are invalid, only that lane gets one replacement wave.

For a diff containing `runtime-snapshots/contract-graph.json` plus `src/client.ts`, the generated segment is excluded and the prompt begins with a line such as:

```text
# rvw: 1 files excluded from review diff (generated/oversize): runtime-snapshots/contract-graph.json
```

## Historical deltas

ADR-010 specified title, body, and linked issues; the implementation carries only title/body. The historical plan also described a single wave as if every run were simultaneously active, while the implemented semaphore queues a single submitted wave at concurrency 16.
