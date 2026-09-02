# Container CI packaging context

## Purpose and scope

This context records the owner decisions and live evidence behind the container image
and reusable GitHub Actions surface. Normative deltas are under [specs](specs/).

## Settled system boundary

- VOOY-757 (2026-09-01) selected GitHub Actions jobs using a prebuilt, version-tagged
  image rather than a webhook application or e2b.
- Target repositories own a protected `pull_request_target` caller and protect it plus
  `.rvw/**` with CODEOWNERS. The event selects the base-side workflow definition; the
  job checks out the immutable head SHA for review.
- The reusable job targets the PR number because commit targets cannot publish COMMENTs
  and use the commit parent rather than GitHub's recorded PR base. The event head remains
  immutable through checkout, and rvw fails closed if live PR resolution no longer
  matches that checkout.
- The `rvw auto` 0/1 process result is the check. COMMENT publication remains the
  narrative channel and is not initially configured as required.
- The image combines the engine, packaged common lanes and pinned Codex runtime.
  Project lanes and auto policy come from the target repository's base-side `.rvw/`.

## Image measurement

The final local `rvw:phase2-local` image was built from
`python:3.12-slim-bookworm`, `node:24-bookworm-slim`, and
`ghcr.io/astral-sh/uv:0.11.21`. Its inspected size is 297,754,398 bytes. It reports
Python 3.12.14, Node 24.20.0, Codex CLI 0.152.0, and rvw 0.4.1, and contains all seven
Markdown lanes under the installed `rvw/lanes` package tree. The image environment has
an empty build-default base URL and no credential.

## Headless bori smoke evidence

Both external clones were clean and detached at
`5d4d3cb64be031c23adaf834774a04b462bd7b34`. Credentials were supplied to Docker by
environment name; the image contained neither an API key nor Codex `auth.json`.

The first run preserved `--sandbox read-only`. Codex authenticated and completed model
responses using only the env-key provider, but its repository commands failed with
`bwrap: No permissions to create a new namespace`. Because those responses were still
schema-valid, rvw exited zero, but all 6 lanes needed coverage redispatch and each
retained all 18 hunks uncovered (108 lane-hunks total). This is an unusable review, not
a smoke pass. Evidence:

- `/tmp/rvw-phase2-smoke-20260902/evidence/read-only-transcript.log`
- `/tmp/rvw-phase2-smoke-20260902/evidence/run/rvw-20260902-025328-383170-commit-5d4d3cb64/discover.json`
- `/tmp/rvw-phase2-smoke-20260902/evidence/run/rvw-20260902-025328-383170-commit-5d4d3cb64/discover-runtime/contracts/r1/run.log`

The measured fallback sets `RVW_CODEX_SANDBOX=danger-full-access` in the project image
while preserving host-installed rvw's read-only default. The outer container root and
both repository mounts remained read-only. The retry completed with 6/6 valid discovery
lanes, one finding, zero uncovered hunks, no coverage redispatch, one merged group, and
one CONFIRMED adjudication. The mounted Codex home contains a mode-0600 `config.toml`
declaring `env_key = "CODEX_API_KEY"` and contains no `auth.json`. Evidence:

- `/tmp/rvw-phase2-smoke-20260902/evidence/danger-full-access-transcript.log`
- `/tmp/rvw-phase2-smoke-20260902/evidence/fallback-run/rvw-20260902-030319-226798-commit-5d4d3cb64/discover.json`
- `/tmp/rvw-phase2-smoke-20260902/evidence/fallback-run/rvw-20260902-030319-226798-commit-5d4d3cb64/outcome.json`
- `/tmp/rvw-phase2-smoke-20260902/evidence/fallback-run/rvw-20260902-030319-226798-commit-5d4d3cb64/report.md`
- `/tmp/rvw-phase2-smoke-20260902/evidence/codex-home/config.toml`

No `danger-full-access` default is applied to host CLI installations. Unsupported
`RVW_CODEX_SANDBOX` values fail before Codex is spawned.
