# PR gate context

## Purpose and scope

This capability replaces a prose-and-copy-paste PR gate sequence with one artifact-backed command. It owns anchor capture and revalidation, isolated checkout, exact review invocation count, coverage and disposition validation, verdict rendering, and COMMENT-only publication. Normative behavior is in [spec.md](spec.md).

## Key decisions and measured basis

- Six apifuse dogfood rounds found unbound shell variables, captured-but-unchecked SHAs, count-only disposition checks, missing coverage checks, double review ambiguity, and manual 40-character SHA relay.
- Target mode performs one review with one replica by default and writes `gate-plan.json`, including the replica and planner-derived chunk counts. Explicit `--replicas N` enables heavy verification. Coverage validation compares the exact lane x replica x chunk Cartesian product rather than relying on aggregate counts. When findings need a human decision, `gate-dispositions.yaml` contains the deterministic group keys and resume mode consumes the same run without invoking models again.
- The repository-admin permission returned by GitHub is the verifiable owner authority for blocker acceptance. rvw records that actor and the human reason but does not decide or publish an approval.
- `accepted` and `must_fix` are deliberately small disposition states. The latter keeps the gate blocked; the former records explicit risk acceptance subject to blocker authority.
- Gate publication reuses the ordinary publish implementation, so COMMENT hardcoding, dry-run default, inline selection, and the bounded bulk 422 fallback have one code path.
- Six tabelog PR #27 rounds (runs 051207 through 111704 on 2026-07-29) did not converge because every changed-head review forgot prior owner dispositions. Round 5 contained 55 actionable findings, about 45 of which were accepted re-detections or re-critiques of the immediately preceding fixes. Carrying validated acceptances is therefore a convergence mechanism, not merely a template convenience.
- Runs 105629 and 111704 both reviewed head `f9936ad`. An unchanged head uses the existing artifact-backed resume path and MUST NOT be re-targeted for a fresh review; re-targeting an identical head is operator error. A changed head starts a new target run and may inherit from the prior run's validated verdict.
- A completed persisted gate verdict is the inheritance source because its dispositions have already passed exact-ID, completeness, duplicate, unknown-ID, and owner checks. Typed `pause` and `failure` artifacts are never carry sources even if malformed or copied data gives them accepted finding records. Completed BLOCK verdicts remain useful sources: their `must_fix` records never carry, but remain in the source set so mixed-disposition duplicate pairs stay ambiguous.
- In target mode, `--inherit` source validation follows PR target resolution and precedes checkout provisioning and review execution.
- Exact finding IDs encode diff coordinates rather than content, and an unchanged hunk still does not prove that nondeterministic replicas produced the same diagnosis set. Tier-one carry therefore requires equal severity and compares SHA-256 digests of both the canonical hunk text and the complete order-insensitive set of collapsed finding bodies. Body identity uses an outer SHA-256 over the concatenated raw inner SHA-256 blocks of bodies in sorted order, avoiding delimiter ambiguity. Severity changes demote as `severity_changed`; missing source and current digests, changed hunk content, and changed diagnosis bodies demote as `source_digest_missing`, `current_digest_missing`, `content_changed`, and `diagnosis_changed`. Older first-body and delimiter-joined digests remain readable but conservatively demote as changed diagnoses. An empty body set is corrupt merge state and persists a correlated invariant BLOCK verdict. Outcome verdict keys must equal merged group keys exactly so orphan outcomes cannot inflate actionable counts or auto-certify inheritance. Duplicate `(file, rule_id)` pairs are counted before exact matching across all inherited findings and all current actionable findings, so exact IDs can never bypass ambiguity.
- Optional provenance remains backward compatible, but it is authoritative only after validation binds it to the selected source and a recomputed carried or prefilled match. Hand-authored provenance without that proof is rejected.
- Partial-inheritance artifacts retain source-correlated carried, prefilled, and reasoned blank counts under a closed reason vocabulary. Final finding records retain the tier and blank or demotion reason, so a manually re-accepted tier-two prefill is distinguishable from a tier-one automatic carry. Template comments distinguish changed-ID prefills, unmatched findings, prior-must-fix findings, ambiguity, and content-digest outcomes without weakening the strict YAML schema.
- Verdict `kind` is the authoritative inheritance-completeness signal after legacy inference. Inheritance rejects every pause or failure kind and directs the operator to finish that run first; a completed clean verdict with no actionable counts remains valid. At this source boundary, counts must still have exactly the three verdict keys with integer values, and accepted reasons must be nonblank even though the historical artifact model stays permissive.
- Run IDs are restricted to a conservative ASCII direct-child alphabet before any filesystem lookup. `RunStore.open` pins the validated run directory descriptor with directory and no-follow flags; inheritance artifact reads then use final-component no-follow opens relative to that descriptor, verify the opened artifact descriptor is regular, and parse JSON from it. Replacing the run's pathname after open therefore cannot redirect reads. Resume rejects self-inheritance before loading to preserve acyclic provenance and the source evidence.
- Gate verdicts persist an explicit `pause`, `failure`, or `completed` kind. Legacy artifacts infer pause from one shared domain marker, completed from nonempty findings, and failure otherwise. Pause and failure verdicts remain replaceable so corrected dispositions and transient failures can retry. Completed verdicts reject disposition or inheritance regeneration, but `--execute` with neither option republishes the completed evidence. The pinned JSON verdict is authoritative for the republish body: gate renders it afresh, consults the Markdown only through a pinned no-follow regular-file read, uses equal Markdown as a cache, ignores missing or stale regular cache bytes, and rejects a symlinked or non-regular cache. It does not rewrite completed evidence while repairing the publish payload.
- Each gate publication call writes `publish-status.json` independently from `GateVerdict`, recording the attempt timestamp, dry-run or execute mode, success, a bounded redacted failure detail when applicable, and whether the call republishes completed evidence. This preserves retry observability without changing verdict completeness or its schema.
- Authorization subprocess failures are evidence-bearing gate outcomes: the BLOCK artifact records affected blockers, the lookup step, a resolved actor when actor lookup completed, and a bounded diagnostic. Empty successful actor or permission output is an operational lookup failure. Because the same detail fans out to console, JSON, Markdown, and CI logs, Unicode format controls and C0/C1 controls are normalized before token, authorization-header, bearer, and long hexadecimal, base64, or base64url value redaction; encoded candidates retain the existing length threshold and require both a letter and a digit to reduce false positives. Only then is detail capped at 500 characters. Pydantic source-target and source-verdict validation errors pass through the same boundary before stderr output.
- GitHub repository slugs are compared case-insensitively while pull-request numbers and run IDs remain exact. Target and verdict identity failures name the first differing field with safe expected and observed identifiers so copied artifacts can be diagnosed without exposing payload content.

## Constraints

- Gate targets GitHub pull requests and requires working `gh` and `git` commands plus authenticated repository access.
- The checkout clone fetches GitHub's `refs/pull/<number>/head` before detaching at the captured SHA so fork pull requests do not depend on the base branch advertising the commit.
- Public finding IDs include hunk coordinates but not content or diagnosis; automatic inheritance additionally requires equal known canonical hunk and complete body-set digests on an unambiguous pair.
- Resume requires the ordinary run stages and `gate-plan.json` written by target mode.
- A coverage failure identifies the missing, unexpected, or invalid replica-chunk identity from persisted artifacts.
- Inheritance is limited to persisted verdicts for the same repository and pull-request number. Base and head anchors may differ between the source and inheriting runs.
- Run IDs are direct child names beneath the configured artifact root and match `^[A-Za-z0-9._-]+$` except for `.` and `..`. Separators, controls, Markdown-active characters, symlinked entries or inheritance artifacts, and resolved escapes are invalid lookup inputs.

## Failure modes

- A large repository makes disposable cloning more expensive than reusing a checkout; isolation is favored over speed for the gate path.
- GitHub installations without the pull-request ref namespace cannot use the current checkout provisioner.
- Repository-admin authority may be narrower than an organization's informal owner group; configurable authority sources are outside this version.
- `accepted` records a human judgment and cannot prove the judgment was substantively correct.
- Legacy verdicts may lack hunk or body digests, may contain older first-body or delimiter-joined body digests, and may lack per-finding inheritance diagnostics. They remain readable, but exact-ID findings are conservatively handled as tier two with the component-specific demotion reason whenever the required current digest bindings do not match.

## Concrete example

```bash
rvw gate --target 1134
# edit /tmp/rvw/<run-id>/gate-dispositions.yaml
rvw gate --run <run-id> \
  --dispositions /tmp/rvw/<run-id>/gate-dispositions.yaml
```

The first command reviews once and exits 1 when actionable findings need dispositions. The second command revalidates the PR anchors and saved coverage, produces `gate-verdict.json` and `gate-verdict.md`, and writes a dry-run COMMENT payload without repeating review.

For a changed head, inherit the previous run's accepted dispositions while creating the new run:

```bash
rvw gate --target 1134 --inherit <prior-run-id>
# if the generated template contains prefilled or blank records, edit it and resume
rvw gate --run <new-run-id> \
  --dispositions /tmp/rvw/<new-run-id>/gate-dispositions.yaml \
  --inherit <prior-run-id>
```

If the pull request head still equals an existing run's captured head, resume that run instead: `rvw gate --run <existing-run-id>`. Never use `--target` to repeat review at an unchanged head.

## Historical deltas

Before this capability, checkout ownership and anchor freshness were external concerns, and ordinary publish had no pre-publication stale-target guard. Those limitations remain for standalone `review` and `publish`; `gate` adds the stronger composed contract without changing their behavior.
