---
lane: contracts
tier: base
cost: heavy
severity_cap: blocker
validation: pending
---

# contracts

One question: can every consumer of this change — a human reader, a calling
function, or an LLM agent — determine exactly what shape goes in and comes
out? Two sections: data modeling always applies; the agent-tool section only
applies when the diff touches agent tools, tool schemas, or tool dispatch.

## Data modeling

Find places where data flows without a declared model, making shapes
unknowable from the code.

- `modeling/shapeless-data` — data whose shape cannot be determined by reading
  the code: untyped payloads passed around, JSON parsed into anonymous
  structures and consumed field-by-field far from the parse site.
- `modeling/dict-overuse` — map/dict used where a model/dataclass/typed object
  belongs: multi-field business data living in raw dicts, especially when the
  same dict shape is rebuilt in several places.
- `modeling/unclear-function-contract` — functions passing ambiguous shapes
  between each other: parameters like `data`, `info`, `payload` with no type or
  a type so loose (`dict[str, Any]`) the caller contract is guesswork.

The question for every finding: "can a reader determine this value's full shape
from the code?" If yes, do not report it. Type inference counts as declared;
prose comments do not.

## Agent tool surfaces

Adversarial review of LLM agent / tool-call surfaces: tool definitions, input
schemas, descriptions, and error feedback. Skip this section (report nothing
from it) when the diff does not touch agent tools, tool schemas, or tool
dispatch.

- `agent-tool/unsupported-schema-construct` — schema constructs that break or
  silently degrade on real providers: non-object root (root union/enum);
  `oneOf`/`allOf`/`not` anywhere; root-level `anyOf`; `$ref`/`$defs`;
  `default`/`const`/`pattern`/numeric length constraints in the wire schema
  (several providers strip or reject these keywords, so the schema lies —
  defaults and constraints belong in description prose plus server-side
  validation); nesting deeper than ~10 levels; tool names outside
  `^[a-zA-Z0-9_-]{1,64}$`. Nested `anyOf` is the one broadly portable
  composition — flag it only when the target stack includes providers with no
  published keyword support matrix.
- `agent-tool/ambiguous-optionality` — optional/nullable/list fields where the
  model cannot tell what "not providing" looks like: is it `null`, omit the
  field, or `[]`? Flag any optional field whose absent-value convention is not
  pinned down in the schema (defaults declared, null vs omit vs empty
  explicitly resolved). Models reliably confuse these three. Also flag
  dishonest `required`: params marked required that the caller may not have —
  models hallucinate plausible values for required fields the user never
  mentioned. Required must be honest and minimal.
- `agent-tool/needless-llm-choice` — decisions delegated to the LLM that the
  system can resolve deterministically: enum parameters the caller already
  knows, "mode" flags derivable from context, ordering/formatting choices with
  one correct answer. Every removable choice is removed error surface.
- `agent-tool/stale-or-sloppy-description` — tool or field descriptions that
  are missing, wrong after a behavior change (stale), or so thin the model must
  guess semantics.
- `agent-tool/scoped-detail-in-global-tool` — the inverse failure:
  case-specific instructions written into an always-loaded global tool
  description, or descriptions bloated with edge-case prose that taxes every
  call. Global surface gets the general contract; specific cases belong in
  scoped docs/prompts.
- `agent-tool/unrecoverable-error-feedback` — when the tool errors or the model
  passes a bad value, the feedback loop fails: system swallows the error,
  returns an opaque message, or omits what a self-recovering model would need
  (which field, what was wrong, what a valid value looks like). Error messages
  to LLMs must be sufficient and concise — enough to self-correct in one turn,
  short enough not to flood context.
- `agent-tool/noisy-output` — tool OUTPUT is prompting surface, same as the
  description. Flag outputs carrying information the model does not need:
  debug dumps, internal ids/fields never consumed downstream, redundant
  envelope repetition, unpaginated bulk payloads. Every needless output token
  taxes the model's context on every call.
- `agent-tool/complex-value-relay` — parameters that make the model combine,
  normalize, reformat, or derive values when relaying them between calls
  (puzzle contracts). A follow-up tool must accept EXACTLY what the earlier
  tool returned, same field name, verbatim. Flag any contract where the model
  must assemble `"tokyo/A1301"` from `area` + `code`, strip prefixes, or
  re-encode values.
- `agent-tool/high-entropy-token-relay` — requiring the model to transcribe
  LONG random/opaque strings verbatim between calls (session tokens, UUIDs
  over ~20 chars, signed URLs, base64 blobs). Models mistranscribe
  high-entropy strings at a meaningful rate. Prefer short ids, indices into a
  returned list, or system-side resolution; flag every contract whose failure
  mode is "the model retyped a random string wrong".
- `agent-tool/lenient-coercion-union` — a type-coercion bug "fixed" by
  widening the schema instead of failing closed: `boolean | "true" | "false"`
  unions, `z.coerce` on agent-facing fields, accepting aliases/variant
  spellings of typed values. This duplicates the contract, propagates to every
  downstream consumer of the generated schema, and diverges this tool's value
  representation from its siblings (a selection-confusion source in itself).
  The correct fix is a strict type that rejects the malformed value with an
  actionable error so the model self-corrects. Flag any schema union whose
  extra branches exist only to absorb type mistakes.
- `agent-tool/open-set-enum` — enum used on a set that is not genuinely
  closed: high-cardinality vocabularies, values that grow with data (place
  names, product categories, provider ids), or lists already stale against
  the backing source. Open sets belong in a plain string plus a
  resolver/lookup operation; enums are for small stable sets, where they are
  the strongest constraint available. Also flag numeric enums where string
  enums are portable.
- `agent-tool/undiscoverable-vocabulary` — the dual of open-set-enum: a plain
  string (or pattern-only) input whose valid values the model has NO in-band
  path to obtain. For every such field demand at least one of: (a) a closed
  enum, (b) a discovery/resolver operation returning the value under the SAME
  field name, (c) an earlier response field that feeds it verbatim, or (d) a
  complete example list in the description. None of the four ⇒ dead
  parameter: schema-valid, never 400s, effectively non-functional because
  callers cannot learn its vocabulary. Two "such as X" examples are not a
  path (vocabulary size and the remaining values stay unknowable). A live
  probe returning 200 proves nothing — the prober already knew the value.
  Display-name response fields (e.g. localized labels) do NOT count as
  feedback for slug/code inputs unless the mapping is returned too.
- `agent-tool/breaking-schema-evolution` — changes to an existing shipped tool
  that break callers in flight: a new REQUIRED parameter (additive changes
  must be optional), repurposing an existing field's meaning under the same
  tool name (meaning change requires a new tool name plus deprecation), or
  renaming/re-typing a field that earlier tool responses feed verbatim.
  Description-only edits are cheap to ship but still behavior changes —
  flag semantic edits with no corresponding eval/test touch in the diff.

## rule: modeling/shapeless-data

The rule is defined by the lane guidance above.

## rule: modeling/dict-overuse

The rule is defined by the lane guidance above.

## rule: modeling/unclear-function-contract

The rule is defined by the lane guidance above.

## rule: agent-tool/unsupported-schema-construct

The rule is defined by the lane guidance above.

## rule: agent-tool/ambiguous-optionality

The rule is defined by the lane guidance above.

## rule: agent-tool/needless-llm-choice

The rule is defined by the lane guidance above.

## rule: agent-tool/stale-or-sloppy-description

The rule is defined by the lane guidance above.

## rule: agent-tool/scoped-detail-in-global-tool

The rule is defined by the lane guidance above.

## rule: agent-tool/unrecoverable-error-feedback

The rule is defined by the lane guidance above.

## rule: agent-tool/noisy-output

The rule is defined by the lane guidance above.

## rule: agent-tool/complex-value-relay

The rule is defined by the lane guidance above.

## rule: agent-tool/high-entropy-token-relay

The rule is defined by the lane guidance above.

## rule: agent-tool/lenient-coercion-union

The rule is defined by the lane guidance above.

## rule: agent-tool/open-set-enum

The rule is defined by the lane guidance above.

## rule: agent-tool/undiscoverable-vocabulary

The rule is defined by the lane guidance above.

## rule: agent-tool/breaking-schema-evolution

The rule is defined by the lane guidance above.
