## Context

The package is built by `uv_build`, but the installed module has no immutable
identity beyond its version. Runtime source-control inspection is unsafe: a
checkout can be moved or dirtied after installation and an executable would
then report mutable state as if it described the artifact.

## Goals / Non-Goals

- Goal: every wheel and sdist carries a deterministic digest of the packaged
  source and optional Git facts captured while building.
- Goal: direct source imports remain usable through fallback digest identity.
- Goal: summaries, JSON, reports, and `--version` expose the same immutable
  identity; stale guidance is conservative and non-fatal.
- Non-goal: changing fail-closed status derivation, review mechanics, package
  version, release workflows, or the external registry.

## Decisions

### Build-time embedding and fallback identity

`_build_provenance.py` contains nullable fallback constants. The PEP 517
wrapper computes a SHA-256 over sorted source/package metadata bytes while
excluding the generated provenance module itself, captures `HEAD` and a
scoped porcelain dirty check when Git can verify them, writes the generated
module only while delegating wheel/sdist construction to `uv_build`, and
restores the fallback bytes afterward. Editable builds continue to point at
the checkout and therefore use the runtime fallback identity.

### Strict runtime model

`BuildProvenance` is a frozen Pydantic model with `extra="forbid"`. The cached
accessor reads only embedded constants and package bytes; it never invokes Git.
When no build ID was embedded it computes the same SHA-256 digest over the
installed package's Python files. `version_label()` prints version, build ID,
and only captured source/timestamp facts.

### Conservative stale-install warning

At new-run creation, the pipeline may call `stale_install_warning()`. It first
requires an embedded clean commit, then reads local `direct_url.json`, verifies
the URL names an existing checkout, and proves the checkout `HEAD` is a strict
descendant with `git merge-base --is-ancestor`. Any unavailable, dirty,
non-local, malformed, or unrelated state suppresses the warning. A positive
warning includes the exact reinstall command and is sent through the existing
warning sink once for that run.

### Summary integration without status changes

`RunSummary.build` stores the provenance captured when the run starts. Summary
construction accepts an optional existing build so recovery/reporting preserve
the original identity, while status and failed-lane calculations remain byte-
for-byte the existing fail-closed rules. CLI JSON and report footers project the
same model rather than recomputing identity.

## Risks / Trade-offs

- Build timestamps are intentionally non-deterministic metadata; the source
  digest and commit identity remain stable and auditable.
- Source checkouts can be unavailable or rewritten; conservative suppression is
  preferable to a false stale warning.
- Adding a required summary field expands persisted JSON, but direct model
  construction remains safe through a computed default.

## Migration Plan

New runs write the build field. Report and re-adjudication readers retain the
existing legacy fallback when an older `run.json` has no build data. No version
or registry migration is needed.
