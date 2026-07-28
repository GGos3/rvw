## Context

The sample gate unions replicas but currently compares `(file, line)` sites and treats every free-only site as evidence that the enum reduced recall. The 19-lane batch showed that this confounds rule-vocabulary coverage with expected replica variation: all eight `REVIEW` lanes had zero free-only rule IDs outside their closed enums.

The PR gate is currently an external runbook. Its shell sequence separately resolves SHAs, provisions a checkout, invokes rvw, counts coverage, accepts dispositions, and publishes. Dogfood found fail-open seams at each handoff. rvw already persists the target, discovery, merge, adjudication, report, and publish payload, and merge already computes a deterministic SHA-1 group key. The new gate composes those existing seams and makes the checks typed and artifact-driven.

## Goals / Non-Goals

**Goals:**

- Separate rule-vocabulary gaps from in-enum site variance in sample reports and exits.
- Preserve the existing sample verdict strings for batch-script compatibility.
- Make a target-mode gate perform one anchored review in a verified disposable checkout.
- Make coverage, staleness, disposition completeness, blocker acceptance, verdict rendering, and publication machine-verifiable.
- Support a resume mode that applies dispositions to an existing run without executing review again.

**Non-Goals:**

- Changing registry documents or adding lane policy to `~/.hermes/review/`.
- Approving or requesting changes on GitHub.
- Automatically deciding that a blocker is acceptable.
- Modifying a reviewed checkout or PR branch.
- Replacing the ordinary `review`, `auto`, or `publish` commands.

## Decisions

### Keep `PASS` and `REVIEW`, but redefine the signal

`SampleReport.verdict` remains `PASS | REVIEW`. `REVIEW` means at least one rule ID emitted by the free variant is absent from the lane's actual closed enum, including its generated `<namespace>/other` member. `PASS` includes runs with in-enum site variance. The report adds sorted `novel_rule_ids` and structured `site_variance` records while retaining `enum_findings`, `free_findings`, `enum_only`, and `free_only` for existing JSON consumers.

Adding a third `VARIANCE` or renaming `REVIEW` to `GAP` would make the distinction visible in the scalar verdict, but would break consumers that branch on the two existing strings. The explicit fields carry the new distinction without expanding that compatibility surface.

### Gate has target and artifact-resume modes

`rvw gate --target <pr>` captures the target, creates a temporary clone detached at the captured head, verifies exact HEAD and an empty porcelain status, and calls the shared review pipeline once. If actionable findings need human disposition and no disposition file is supplied, it writes a strict template under the run and exits blocked.

`rvw gate --run <run-id> --dispositions <path>` reopens the persisted artifacts, revalidates the current PR anchor, and completes the gate without invoking discovery or adjudication. This avoids a second model review merely to relay stable IDs into a disposition file. `--target` and `--run` are mutually exclusive.

### The existing collapse key is the public finding ID

The lowercase SHA-1 of `file:hunk_id:rule_id` is already deterministic for one anchored diff and is the key used by merge and adjudication. Gate artifacts and reports label it `finding_id`; the underlying `CollapseGroup.key` field remains unchanged to preserve disk compatibility. Dispositions must match this ID exactly, so duplicate, unknown, and omitted records are detectable.

### Dispositions are strict keyed decisions

The input is strict YAML with `schema_version: 1` and a list of records containing `finding_id`, `decision`, and nonblank `reason`. The only decisions are `accepted` and `must_fix`. Every CONFIRMED and UNCERTAIN group must have exactly one record, and no other ID may appear. `must_fix` produces a gate `BLOCK`; accepted findings can pass the disposition phase.

An accepted blocker additionally requires the authenticated GitHub actor to have repository `admin` permission. The actor is queried by rvw and recorded in the verdict rather than trusted from the YAML. This operationally defines “owner” using an authority GitHub can verify. The acceptance reason remains human-authored input; rvw validates and records it but never generates or approves it.

### Coverage is compared as an exact mapping

Before execution, gate derives the activated lane plan and expected replica count. After execution it requires a nonempty expected lane set, exactly one coverage row per expected lane, no extra or missing lanes, positive dispatched counts equal to the configured replica count, and `valid == dispatched` for every lane. This rejects duplicate rows and vacuous 0/0 totals, not just aggregate count mismatches.

### Gate artifacts drive publication

Every completed validation attempt writes `gate-verdict.json` and `gate-verdict.md` with run ID, immutable base/head anchors, aggregate verdict counts, per-lane validity, and every actionable finding's public ID, location, severity, adjudication verdict, disposition, and reason. A missing-disposition template is also persisted when needed.

The gate passes its generated Markdown through the existing `publish_review` path. Publication remains dry-run unless `--execute` is supplied, hardcodes `COMMENT`, emits no approval-capable option, and retains the single bulk 422 fallback. Coverage or stale-anchor failures cannot reach publication.

### Exit codes distinguish decisions from invocation failures

Sample exits 0 for `PASS`, including site variance, and 1 only for a novel-rule `REVIEW`. Gate exits 0 only for a fully validated `PASS`, 1 for a valid gate `BLOCK` or fail-closed invariant such as stale anchors, incomplete dispositions, or invalid coverage, 2 for invalid CLI/input usage, and 3 for operational failures such as checkout or GitHub command failure.

## Risks / Trade-offs

- [A hunk boundary changes after rebasing, so finding IDs change] → dispositions bind to base/head anchors, and resume fails closed when either anchor moves.
- [Repository admins are a narrower owner definition than some teams use] → the check is explicit and auditable; broader owner policy can be introduced later as a separate configured authority source.
- [A human can claim `accepted` without sufficient technical basis] → rvw requires identity and a written reason but deliberately does not automate the judgment.
- [Temporary cloning costs network and disk] → the checkout is disposable and removed after the target-mode invocation; correctness and isolation take priority for the gate path.
- [Preserved legacy sample fields are lossy because they omit file names] → the new structured site-variance field is authoritative for the distinction; legacy fields remain compatibility-only.

## Migration Plan

Existing sample consumers can continue parsing `PASS`/`REVIEW` and the old finding arrays. They will observe fewer `REVIEW` exits because site-only variance now exits 0. New consumers should inspect `novel_rule_ids` and `site_variance`.

Gate is additive. Operators can first run target mode without `--execute`, edit the generated disposition template when necessary, resume the same run, and inspect `gate-verdict.json`, `gate-verdict.md`, and `publish-payload.json` before enabling publication.

## Open Questions

None for this change. Configurable non-admin owner authorities and cryptographic disposition signatures remain future policy work.
