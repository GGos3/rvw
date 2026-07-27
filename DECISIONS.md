# rvw — Decision Records

Layered, replicated, self-adjudicating code review orchestrator.

Append-only. Never edit a committed ADR in place; supersede it with a new one.

---

## ADR-001 — Five-axis review vocabulary (2026-07-27)

**Status:** Decided
**Type:** Domain model / contract

### Context

The existing Hermes review skills (`github-code-review`, `vooy-bori-codebase`,
`apifuse-codebase`, `dev-delegation`) use the word "lane" for two unrelated
things: a rule-shaped review axis ("security lane", "contract lane") and a
review execution pass. They also conflate runtime facts (codex stall handling,
`multi_agent=false`) and publication policy (who may post an approval) with
review rules, so all four live in one undifferentiated pile of prose.

User directive, verbatim:

> 레인이라는 개념은 리뷰 시스템 1개를 말하며, 리뷰 시스템은 codex review 같은 것을 의미함

then refined:

> 정확히는 레인이 규칙 같은 느낌이고, 이 레인을 실행하기 위한 런타임이 codex같은 느낌이야
> 기존 rule은 레인과 레이어로 명확하게 구분해야해

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | **Rule** = one atomic check statement | Smallest unit; never executed alone |
| D2 | **Lane** = named bundle of rules + prompt + output contract | *What* is inspected |
| D3 | **Layer** = activation tier that owns lanes | *When* it runs |
| D4 | **Runtime** = execution engine for a lane | *Who* runs it |
| D5 | **Run** = one (lane x runtime x replica) execution | Produces exactly one artifact |

Derived: **Plan** = deterministically resolved execution set. **Report** =
merged, adjudicated markdown.

Relations: `Rule ⊂ Lane`, `Lane ∈ Layer`, `Lane × Runtime → Run`.

### Anti-goals

- Not adopting "agent" as a first-class term. Runtimes are engines, not actors;
  naming them agents invites per-agent state and memory that this system
  deliberately does not have.
- Not keeping "lane" as a rule-axis synonym for backward compatibility with the
  existing skills. The skills get rewritten to this vocabulary instead.

### Pitfalls

1. Runtime facts and publication policy are NOT lanes. Codex stall handling
   belongs to a runtime profile; approval pre-authorization belongs to a
   publish policy. Mixing them back into lane docs recreates the original mess.

### Verification

- `rvw lanes list` output contains no entry whose content is a runtime fact or
  a publication rule.

### References

- `~/.hermes/executors/README.md` (role→executor pointer pattern this mirrors)

---

## ADR-002 — Four-tier layer pyramid with monotone specificity (2026-07-27)

**Status:** Decided
**Type:** Architecture
**Depends on:** ADR-001

### Context

Review rules differ in how universally they apply. A duplicate-object-key check
is valid in every repo; an ApiFuse provider-registry gate is valid in one repo;
an agent-prompt-surface check is valid only when agent code changed; "does this
PR do what it claims" is valid only for one specific PR.

User directive, verbatim:

> 베이스 레이어는 어떠한 프로젝트 리뷰든 공통적으로 하는 것임
> 프로젝트 레이어는 특정 프로젝트에 대한 특화된 리뷰를 진행하는 것임
> 다이나믹 레이어는 리뷰할 pr이나 어떤 무언가의 맥락과 목적에 맞춰 의도대로 올바르게 동작하는지,
> 엣지케이스나 의도 하지 않은 범위/동작은 없는지 리뷰하는 것임

and:

> 전역 레이어가 아닌 scoped 레이어도 만들수 있어야 해, 하위 레이어일 수록 반드시 돌지만
> 상위레이어로 갈수록 조건이 세분화되어 예를 들어 에이전트쪽 코드를 건드리면
> 에이전트쪽 리뷰 레인이 돌아가는 구조인거지

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | Four tiers: `base(0)` → `project(1)` → `scope(2)` → `dynamic(3)` | Activation predicate narrows monotonically |
| D2 | `base` has no predicate | Always active, in every repo |
| D3 | `project` keyed on repo identity | One repo |
| D4 | `scope` keyed on changed paths/symbols; multiple may activate | One domain within a repo |
| D5 | `dynamic` always active, content generated per target | One PR |

Layers own lanes; they do not own rules directly. A lane belongs to exactly one
layer.

### Why a pyramid over flat tagging?

A flat `tags: [security, apifuse, agent]` model cannot express "must always
run". Tier ordering makes the guarantee structural: tier 0 activation is
unconditional and cannot be disabled per-target, which is what makes ADR-005's
safety net actually a safety net.

### Dynamic tier asymmetry (accepted)

`dynamic` is the one tier whose *predicate* is always true while its *content*
is the narrowest. It sits at the top because specificity is ordered by content,
not by activation frequency. This was considered as a fourth orthogonal axis and
rejected: an orthogonal dynamic axis would make "run only base+project" a
first-class cheap mode, which is an anti-goal — the intent check is the
system's differentiator, not an optional extra.

### Anti-goals

- No per-target disabling of tier 0.
- No user-defined tier depth. Four is fixed; deeper nesting belongs in scope
  predicates, not new tiers.

### Pitfalls

1. Multiple `scope` layers can activate simultaneously and their lanes may
   overlap. That is intended (see ADR-003 site grouping), not a bug to dedupe
   away at the layer level.
2. A scope predicate written against a path that later moves silently stops
   activating. `rvw doctor` must flag scope layers whose predicates matched
   nothing across recent runs.

### Verification

- `rvw plan --target <x> --json` lists activated layers with the predicate that
  fired for each.
- A plan for any target always includes every tier-0 lane.

---

## ADR-003 — Two-level finding identity: collapse key vs site group (2026-07-27)

**Status:** Decided
**Type:** Contract
**Depends on:** ADR-001, ADR-002

### Context

With many lanes active, the same source location gets reported repeatedly. Two
different phenomena were initially conflated under "duplicate":

- The *same* lane reporting the *same* rule at the same place across replicas —
  genuine duplication, should merge into one adjudication unit.
- *Different* lanes reporting the same place for different reasons — not
  duplication; independent corroboration, and merging it destroys signal.

A first draft used a single key `(file, line, rule_id)` while also claiming
cross-layer corroboration. Those are mutually exclusive: different lanes emit
different `rule_id`s, so such a key can never collide across lanes, making the
corroboration counter permanently 1.

User directive on merge sophistication, verbatim:

> 사실 LLM이 적절히 병합해주는게 이쁘긴 한데, 당장은 코멘트 그냥 string append 만 해도 될듯

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | Finding collapse key = `sha1(file : hunk_id : rule_id)` | Merges true duplicates only |
| D2 | Site group key = `(file, hunk_id)` | Counts independent lanes hitting one place |
| D3 | `agreement` = replica count that produced a finding | Confidence signal |
| D4 | `corroboration` / `cross_layer` computed on the site, not the finding | Prioritization signal |
| D5 | Merged bodies are string-appended verbatim | No semantic merging in v1 |

Adjudication operates on findings. Sites are display/priority only and are never
adjudicated.

### Anti-goals

- No LLM-driven semantic merging in v1. Deferred; if added it ships as
  `rvw suggest-merges` producing proposals only, never auto-applied.

### Pitfalls

1. Two distinct defects of the *same rule* inside one large hunk collapse into
   one finding and share a single verdict. Mitigation: both bodies are retained
   so the adjudicator sees both. Accepted as a cost of hunk granularity; if it
   fires often, add `--anchor-granularity line`.

### Verification

- A fixture where two lanes report the same hunk yields 2 findings, 1 site,
  `cross_layer: true`.
- A fixture where 3 replicas of one lane report the same defect yields 1
  finding with `agreement: 3`.

---

## ADR-004 — Closed-enum rule ids, hunk anchoring, schema-enforced JSON (2026-07-27)

**Status:** Decided
**Type:** Contract
**Depends on:** ADR-003

### Context

ADR-003's collapse key requires `rule_id` and the anchor to be stable. Both are
LLM-authored and were therefore unstable: models invent arbitrary rule strings,
and line numbers drift between reports of the same defect. The existing bori
review gate uses a `SUMMARY / ISSUES / VERDICT` prose format that must be
regex-parsed.

User raised the central risk, verbatim:

> enum 같이 자유도를 억제하는건 리뷰의 퀄리티도 억제될 수 있어서, 잘 샘플링해야할 듯

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | Every lane declares a closed `rules:` enum; runtime output is schema-constrained to it | Exact matching becomes meaningful |
| D2 | Out-of-enum values coerce to `<lane>/other` and are counted, not discarded | Fail-soft + feedback signal |
| D3 | Collapse anchor is the diff hunk, not the line | Deterministic, derived from diff |
| D4 | `line` retained solely as the GitHub inline anchor | Publication concern, not identity |
| D5 | Lane output is strict JSON via `--output-schema`, not prose | Parse reliability |
| D6 | Findings outside the diff are kept with `anchorable: false` | Never dropped |

### Evidence (measured 2026-07-27, codex-cli 0.145.0)

Schema enforcement is API-level and beats the prompt: a prompt explicitly
instructing `security/sql-injection` still produced only in-enum values.

Enum does not suppress quality. Same fixture, same prompt, two schemas:

| Condition | `rule_id` schema | Findings |
|---|---|---|
| enum | closed list of 6 | 5 |
| free | `minLength: 1` | 5, near-identical text |

The suppressing factor is the lane's rule scope, not the id format. Both
conditions missed the same three deep defects, which motivated ADR-005.

`severity` caps are enforceable the same way.

### Anti-goals

- No prose fallback parser. An unparseable artifact is INVALID, never
  best-effort salvaged into a PASS.

### Pitfalls

1. `<lane>/other` becoming a dumping ground. `rvw doctor` reports the `other`
   ratio per lane; a high ratio means the enum is under-specified.
2. Hunk ids change when the head SHA changes. Findings are only valid for the
   head they were produced against; `rvw finish` must re-verify head identity.

### Verification

- `rvw sample --lane <id> --fixture <f> --compare-free` shows an empty delta
  between enum and free-string runs before a new lane is accepted.

---

## ADR-005 — Mandatory unscoped sweep lane at tier 0 (2026-07-27)

**Status:** Decided
**Type:** Quality strategy
**Depends on:** ADR-002, ADR-004

### Context

Closed enums make each lane precise but structurally blind outside its rule
list. A defect covered by no lane's enum is not merely missed — its absence is
invisible, which is worse than noise because nothing signals the gap.

### Evidence (measured 2026-07-27)

Fixture with 6 planted defects: 3 shallow (duplicate key, dead assignment,
copy-paste remnant) and 3 deep (public inputs `limit`/`cursor`/`fields`/`locale`
silently dropped before the upstream call; a catch block converting any
exception into `{ok: true, orders: []}`; a cache key missing inputs that
`recompute()` depends on).

| Lane | Deep defects found |
|---|---|
| slop-hygiene (enum) | 0 / 3 |
| slop-hygiene (free string) | 0 / 3 |
| unscoped-sweep | **3 / 3** |

A separate probe confirmed lane discipline holds: a security-only fixture
reviewed by slop-hygiene returned `PASS` with zero findings rather than dumping
into `other`.

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | `unscoped-sweep` is a tier-0 lane, always active | Structural gap coverage |
| D2 | Its prompt receives every other active lane's rule list as "already covered" | Suppresses re-reporting |
| D3 | Its enum is broad (`unscoped/security`, `/correctness`, `/contract`, `/scope-creep`, `/other`) | Open-ended by design |
| D4 | Schema caps its severity at `warning` | Higher FP rate must not produce blockers |
| D5 | Repeated sweep hits on one theme are a promotion signal to a real rule | Registry self-corrects |

### Why not conditional activation?

Considered activating sweep only when few lanes are active. Rejected: the
measurement above had 5 rules active and still missed 3 of 3 deep defects. Lane
count does not predict coverage, so a conditional safety net is not a safety
net.

### Pitfalls

1. Sweep is open-ended and will have a higher false-positive rate than scoped
   lanes. ADR-007's adjudication pass is what makes this acceptable.

---

## ADR-006 — Replication N=3, single wave, no hedging (2026-07-27)

**Status:** Decided
**Type:** Architecture / performance

### Context

User constraints, verbatim:

> 솔직히 비용은 전혀 상관이 없어서, 속도와 리뷰 퀄리티만 보면 돼

and:

> 병렬을 통한 전체 리뷰시간 단축도 꽤 중요해서

### Evidence (measured 2026-07-27, 22-core host, codex-cli 0.145.0)

Total wall time for N identical concurrent `codex exec` runs:

| N | Total wall | Throughput |
|---|---|---|
| 1 | 25.7s | 1x |
| 4 | 49.1s | 2.1x |
| 8 | 50.0s | 4.1x |
| 16 | 50.6s | 8.1x |

Flat from 4 to 16 — the bottleneck is upstream API latency, not local
resources. Validity was 16/16. Tail dominates: at N=16 individual walls spanned
22.4s–50.6s and the slowest single run set the total.

Recall from replication, 8 runs of an identical prompt (individual sizes
4,5,5,5,5,6,6,6; union 6; intersection 3):

| Replicas | Expected union | vs single |
|---|---|---|
| 1 | 5.25 | — |
| 2 | 5.79 | +10.3% |
| 3 | 5.93 | +13.0% |
| 4 | 5.99 | +14.1% |

A single run recovers 88% of findings. Three recover 99%.

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | Every lane runs with 3 replicas by default | 88% → 99% recall |
| D2 | All lanes x all replicas dispatch in ONE wave | Wall time stays ~one run's tail |
| D3 | Heavy lanes dispatch first (LPT ordering via `cost:` field) | Keeps the heavy lane off the tail |
| D4 | Tail hedging is rejected | Replication already subsumes it |
| D5 | A replica failing validity is discarded, not retried, unless all 3 fail | Replication is its own retry |

### Why not hedging?

Hedging existed to cut the tail cheaply. With cost irrelevant, replication cuts
the same tail *and* raises recall 13%, for the same dispatch. Hedging is
strictly dominated and adds a scheduler.

### Why not staged waves?

Making `dynamic` consume other layers' results would serialize the pipeline and
roughly double wall time. Both sweep and dynamic need only the *rule lists* of
other lanes, which are known before execution, so no wave dependency exists.

### Pitfalls

1. Identical prompts return varying results (5 ± 1 over 8 runs). Any claim
   derived from a single run under-reports; never benchmark a lane with N=1.
2. N=16 was the highest measured concurrency. A 12-lane x 3-replica plan is 36
   concurrent runs — beyond the measured range. Re-measure before raising the
   default concurrency cap above 16.

---

## ADR-007 — Discovery and adjudication are separate lanes, not human-in-the-loop (2026-07-27)

**Status:** Decided
**Type:** Architecture / quality strategy
**Resolves:** an earlier draft that assigned adjudication to the human operator

### Context

An earlier draft of this design locked "blocking verdicts are the human's job",
which baked HITL into the architecture and capped the tool's quality at the
operator's attention.

User correction, verbatim:

> 애초에 리뷰 시스템은 hitl이 목적이 아니라 자동에서도 퀄리티 좋게 나오냐가 목적이여서,
> 애초에 hitl을 가정하면 안됨, 해봤자 사람과 가까운 너가 리뷰하는 것 정도

Statistical filters (`agreement`, `cross_layer`) reject flakes but cannot reject
a confident, well-written, factually wrong finding.

### Evidence (measured 2026-07-27)

An adjudication lane was given 9 candidates against real source: 6 genuine and 3
fabricated (a false TDZ claim about a variable that *is* reassigned; a
speculative PII claim; a claim that an `await`ed call was missing `await`).

| Outcome | Count |
|---|---|
| Genuine confirmed | 5 / 6 |
| Genuine wrongly rejected | **0 / 6** |
| Fabricated rejected | **3 / 3** |
| Fabricated leaked | **0 / 3** |
| Genuine → UNCERTAIN | 1 |

Every verdict cited the exact source line.

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | The separation being preserved is **discovery lane vs adjudication lane**, not machine vs human | Original intent, correctly located |
| D2 | Adjudication is a pipeline stage, replicated like any lane, majority-voted | Deterministic merge of a non-deterministic verdict |
| D3 | Adjudicator verdicts are `CONFIRMED` / `REJECTED` / `UNCERTAIN` and must quote source | Evidence-bearing |
| D4 | The adjudicator may not introduce new findings | Role isolation |
| D5 | Human review is an optional `--pause`, never a pipeline requirement | Usage habit, not architecture |

Resulting pipeline: DISCOVER → MERGE → ADJUDICATE → REPORT. Measured stage
estimate ~80s total.

### Anti-goals

- The adjudicator does not rank, prioritize, or write the summary. It answers
  exactly one question per candidate: does this defect exist as described.

### Pitfalls

1. Same-runtime adjudication shares the discovery model's blind spots. If FP
   leakage appears in practice, pin the adjudicator to a different runtime.
2. `UNCERTAIN` must never silently collapse into `REJECTED`; see ADR-008.

---

## ADR-008 — UNCERTAIN escalates with widened context, residue is surfaced (2026-07-27)

**Status:** Decided
**Type:** Quality strategy
**Depends on:** ADR-007

### Context

In the ADR-007 measurement the single `UNCERTAIN` verdict was a *genuine*
defect (the cache-key correctness bug). Its stated cause was missing context:
the adjudicator could not see `recompute()`'s definition. Dropping UNCERTAIN
would have discarded a real finding.

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | UNCERTAIN findings escalate to a second adjudication pass | Cause is usually missing context |
| D2 | The second pass is explicitly permitted to read referenced symbol definitions beyond the diff | Widen, don't repeat |
| D3 | Still-uncertain findings publish under `## 검증 미확정` | Honest residue, never hidden |
| D4 | Residue never counts as a blocker | Unproven claims cannot block |

### Pitfalls

1. Unbounded context widening turns pass 2 into a whole-repo read. Cap it to
   symbols directly referenced by the finding body and the hunk.

---

## ADR-009 — Two operating modes over one pipeline; auto mode adjudicates by policy (2026-07-27)

**Status:** Decided
**Type:** Operational
**Depends on:** ADR-007

### Context

User directive, verbatim:

> cli가 file로 리뷰 보고서 내보내는 기능 추가하고, 너가 정제 및 cli를 통한 업로드
> 아니면 간단하게 너가 안봐도 그냥 올리는 기능도 추가하면 좋을 것 같고

and:

> B가 우리가 쓸 방식이고 아래 말한 완전 자동화는 오픈소스로 풀 때 사람들이 원하는 기능일 듯

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | One pipeline, two entry points: `rvw review` (default auto) and `--pause` | No forked code paths |
| D2 | `--pause` stops after ADJUDICATE, emits `findings.json` + `draft.md`, performs no external action | Single stop point |
| D3 | Auto mode's severity/inclusion thresholds come from a declarative policy file | Deterministic, user-tunable |
| D4 | `approve` is never auto-emitted; `--allow-approve` is explicit opt-in | Irreversible-ish social action |
| D5 | Both modes export the report to a file before any upload | File is the artifact of record |

Default policy: `agreement >= 2` to include; `agreement == 1 && suggestion` to
drop; `cross_layer` promotes priority; default publish state `comment`.

### Why thresholds rather than an LLM triage?

ADR-007 already places factual verification in the adjudication lane.
Thresholds handle only ranking and inclusion, which are policy, not judgment,
and must be reproducible across runs.

### Pitfalls

1. A policy that drops everything produces a silent empty review. `rvw doctor`
   must warn when a policy would drop >90% of a recent run's findings.

---

## ADR-010 — Dynamic brief falls back to the PR body, marked unverified (2026-07-27)

**Status:** Decided
**Type:** Contract
**Depends on:** ADR-002, ADR-009

### Context

The `dynamic` tier's only input is a statement of intent. In `--pause` mode the
operator writes it. Auto mode has no operator, which would leave tier 3 dead —
removing the system's differentiating check.

Existing Hermes review policy says PR bodies are untrusted.

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | Without `--dynamic-brief`, use PR title + body + linked issues | Free intent source |
| D2 | Always record `brief_source` in the report | Provenance visible |
| D3 | A derived brief is labeled `unverified` | Honors PR-body distrust |
| D4 | Tier-3 rules are framed as *consistency* checks against the claim | Robust to a wrong brief |
| D5 | Generating a brief from the diff itself is forbidden | Circular |

Tier-3 rules: `dynamic/goal-parity`, `dynamic/undeclared-change`,
`dynamic/declared-not-done`, `dynamic/edge-cases`.

### Why this does not violate PR-body distrust

Distrust means "not admissible as evidence of correctness", not "unusable as a
declaration of intent". A mismatch between a claimed intent and the diff is
itself the finding — `dynamic/undeclared-change` is valuable precisely when the
body is inaccurate.

### Pitfalls

1. An empty PR body yields a vacuous brief. Mark tier 3 lanes inconclusive in
   the coverage table rather than reporting a spurious pass.

---

## ADR-011 — Named-indirection documentation SoT (2026-07-27)

**Status:** Decided
**Type:** Repo structure

### Context

User directive, verbatim:

> 문서도 sot를 관리하여 명칭으로 관리하도록 (추후 방식 변경에 용의하도록)

### Decision

Registry rooted at `~/.hermes/review/`:

```
README.md              index + vocabulary; pointers only, no content
layers.yaml            tiers, predicates, lane id lists
lanes/{base,project/<repo>,scope/<repo>/<scope>,dynamic}/<lane-id>.md
runtimes/<runtime-id>.md
policies/publish/<repo>.yaml
policies/auto.yaml
report/template.md
```

| # | 결정 | 핵심 |
|---|---|---|
| D1 | Everything is referenced by id; call sites never inline content | Swap implementation without touching callers |
| D2 | Runtime docs bind lanes to executors by role; they do not restate executor facts | `~/.hermes/executors/` stays the executor SoT |
| D3 | Publication policy is data, not lane prose | Machine-checkable before posting |
| D4 | `rvw doctor` validates registry integrity and predicate conflicts | Registry rot is detectable |

### Anti-goals

- Registry does not live inside a reviewed repo. It is cross-repo by nature.

### Pitfalls

1. Duplicating executor invocation details into `runtimes/` creates two SoTs
   that drift. Runtimes reference `~/.hermes/executors/README.md` by role.

---

## ADR-012 — File-first report, then upload with inline anchors (2026-07-27)

**Status:** Decided
**Type:** Contract
**Depends on:** ADR-004, ADR-009

### Context

User directive, verbatim:

> 최종 리뷰는 깃허브 등에 markdown으로 먼저 /tmp에 작성 후 업로드 및 github의 코드 맨션 기능을 활용함

and on synthesis:

> 리뷰는 모든 레인을 종합 한 결과가 나와야해

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | The report is written to a file before any network call | Inspectable, replayable |
| D2 | Default `/tmp/rvw/<run-id>/`, overridable via `--out` | Predictable |
| D3 | Findings with `anchorable: true` post as GitHub inline comments; others go in the body | Line-accurate where possible |
| D4 | A coverage table is mandatory: layer, lane, replicas dispatched/valid, findings | Proof that all lanes were synthesized |
| D5 | Only the `## 종합` narrative is free-form; everything else is generated | Bounded authorship |
| D6 | Pre-publication guard: `state=open`, head matches, `merged_at=null`, not BEHIND/DIRTY | Refuse to post onto a moved target |

### Why the coverage table is mandatory

"All lanes synthesized" is a claim that must be falsifiable. A lane that died
entirely is otherwise indistinguishable from a lane that found nothing — the
most dangerous silent failure in the system.

### Pitfalls

1. GitHub rejects inline anchors on lines outside the diff with HTTP 422.
   Determine `anchorable` locally from the diff before posting rather than
   catching the error.

---

## ADR-013 — Python + uv + Typer + Pydantic v2, distributed on PyPI as `rvw` (2026-07-27)

**Status:** Decided
**Type:** Repo structure / packaging

### Context

User directive, verbatim:

> 이거 projects/로 만들어서 pypi cli로 만들자

Reviewed repos are TypeScript (bori: pnpm, apifuse: bun), but the orchestrator
lives outside any reviewed repo and must not couple to their toolchains.

Name availability checked 2026-07-27: `pypi.org/pypi/rvw/json` → 404 (free).
`lanes` → 200 (taken). Host has Python 3.12.3, `uv`, `pipx`.

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | Python 3.11+, `uv init --package`, Typer + Pydantic v2 | Matches the house CLI bootstrap |
| D2 | Distribution name `rvw`; entry point `rvw = "rvw.cli:app"` | Available, short |
| D3 | Location `~/projects/rvw` | Standalone, not a worktree of a reviewed repo |
| D4 | Agentic surface `--json` / `--schema` / `--examples` is first-class | Primary caller is an agent |
| D5 | Exit codes 0/1/2/3 = ok/not-found/user-error/system-error | House convention |
| D6 | Strict gates: ruff, pyright strict, pytest | Bootstrap default |

### Anti-goals

- No Docker requirement for local use.
- No repo-specific dependency (no pnpm/bun invocation from the core).

### Pitfalls

Carried from `python-tooling-and-validation`:

1. `[project.scripts]` must target the Typer app object, not `main()`.
2. Typer 0.25+ removed `CliRunner(mix_stderr=False)`.
3. pyright strict flags `@app.callback()` as `reportUnusedFunction`; ignore on
   that line only.
4. Write `dependencies` before the first `uv sync`.
5. `uv sync` does not evict removed deps; use `--reinstall`.

---

## ADR-014 — rvw absorbs review execution mechanics; executor profiles keep implementation delegation (2026-07-27)

**Status:** Decided
**Type:** Operational

### Context

User observation, verbatim:

> 근데 이거 시스템 만들어지면 굳이 codex 직접 실행하는 방법 같은거 지워서 다이어트 할 수 있을 듯?

Separately, the legacy process-isolation block in `~/.hermes/executors/codex.md`
(global `flock`, `systemd-run --scope`, `TasksMax=512`, feature disables, the
2026-07-20 context7 and 2026-07-21 HTTP 405 incidents) was removed on user
instruction as obsolete:

> 저 레거시 룰 지워줘, 딱히 필요 없음, 저게 codex에 프로세스 실행 버그 있었을 때 그랬던거같은데
> 이제 저런 조건 필요 없음

It was replaced with the ADR-004 and ADR-006 measurements. That removal is what
makes 36 concurrent runs legal.

### Decision

| # | 결정 | 핵심 |
|---|---|---|
| D1 | Review *execution* mechanics migrate into rvw runtimes | Stall handling, replication, schema enforcement |
| D2 | Implementation *delegation* stays in `~/.hermes/executors/` | Task shaping, diff verification — not review |
| D3 | Skill diet happens only after rvw is proven on real PRs | No premature deletion |
| D4 | Migrated content is deleted, not duplicated | Two SoTs is worse than a verbose one |

Diet candidates once proven: bori's whole-diff stall protocol (structurally
solved by sharding + replication), the manual 5-lane orchestration recipe in
`github-code-review/references/delegated-review-system.md`, and the scattered
rule prose that becomes lane documents.

Not diet candidates: executor invocation, prompting quirks, post-delegation
diff/gate verification, publication policy.

### Pitfalls

1. Deleting a skill section before rvw covers that repo leaves a coverage hole
   with no fallback. Delete per-repo, only after that repo has a green rvw run.

### Verification

- Before any skill deletion: `rvw review` completes on a real PR in that repo
  with a coverage table showing every intended lane valid.
