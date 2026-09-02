## Context

See [proposal.md](proposal.md) for motivation and the delta specs for the behavior
contract. The current wheel already carries `src/rvw/lanes/`, and PR #38 makes target
repository `.rvw/` rules resolve from the immutable base side. `rvw auto` accepts a
commit SHA plus a verified `--repo-dir`, resolves GitHub identity through `gh`, uses
plain Codex with an explicit read-only sandbox, publishes through `gh api`, and returns
0/1 for PASS/BLOCK.

The trust boundary is one Linux container per GitHub Actions job. A target repository
owns a very small `pull_request_target` caller on its base branch and protects that file
plus `.rvw/**` with CODEOWNERS. The called workflow checks out untrusted head contents
for reading but its workflow definition and image selection come from the base side.

## Goals / Non-Goals

**Goals:**

- Produce one locally buildable image whose toolchain and common lanes can be inspected.
- Keep credentials runtime-only and make the endpoint generic and operator-selected.
- Make the immutable event SHA, target checkout, token permissions, and auto status
  propagation explicit in the reusable workflow.
- Preserve enough artifacts and logs to audit the live container measurement.

**Non-Goals:**

- Publishing an image, selecting a registry, or changing the existing PyPI release rail.
- Installing a caller in bori, changing branch protection, or declaring a required check.
- Modifying the external review registry or providing a webhook/application service.

## Decisions

### Debian-compatible multi-stage tool composition

Use Python 3.12 slim as the final stage, copy the uv binaries from a pinned uv image,
and copy Node plus the globally installed `@openai/codex@0.152.0` tree from a Node 24
builder. Install Git, GitHub CLI, Bash, coreutils, ripgrep, CA certificates, and
`util-linux` in the final stage. Keeping builder and runtime stages on the same Debian
family avoids a second package manager and lets the final image retain only runtime
assets. rvw is installed non-editably from the source build context so wheel-data
packaging is exercised.

Alternative considered: install Codex dynamically at container startup. That makes the
job network-dependent and defeats the pinned image contract.

### A static template plus a Python startup materializer

Bake `/etc/rvw/codex-config.toml` with `model_provider = "rvw"` and a provider table
whose `env_key` is `CODEX_API_KEY`. A small stdlib-only module reads that template,
TOML-quotes an optional runtime `CODEX_BASE_URL` (preferred) or build default, writes
`$HOME/.codex/config.toml` atomically with user-only permissions, and `exec`s `rvw`.
The API key is never interpolated or logged. No base URL is emitted when neither source
is configured, and the build argument defaults empty.

Alternative considered: shell substitution. Correctly escaping arbitrary TOML strings
and testing atomic secret-safe behavior is clearer in Python.

### Reusable workflow with a thin base-side caller

Implement `.github/workflows/rvw-review.yml` as `workflow_call` with a required string
`image` and required `CODEX_API_KEY` plus optional `CODEX_BASE_URL` secrets. It uses the
caller event context to check out `pull_request.head.sha` from the head repository with
credentials disabled, fetches `pull_request.base.sha`, then runs the supplied image with
the checkout mounted read-only at `/workspace` and that path as both working directory
and `--repo-dir`. Auto receives the PR number rather than the SHA because the current
CLI requires a PR target to read the recorded-base policy and publish a COMMENT;
checkout verification requires the live resolved head to equal the immutable event
checkout and fails closed on a synchronization race. `GITHUB_TOKEN` is also mapped to
`GH_TOKEN` because the rvw target and publication paths execute GitHub CLI, while the
documented external contract retains the generic `GITHUB_TOKEN` name.

The Docker step contains no status masking, so it is the check. `pull_request_target`
belongs only in the thin caller because reusable workflows cannot add an event trigger
to their caller. This event is chosen for its base-side workflow definition and
self-bypass resistance, not for merge-ref execution.

Alternative considered: a composite action. A reusable workflow can own permissions,
checkout shape, secrets, and the complete job contract in one reviewable file.

### Host read-only default with a closed container fallback

The initial bori smoke preserved the runtime adapter's explicit `--sandbox read-only`.
Every Codex call authenticated and returned a structured payload, but repository shell
reads failed because bundled bubblewrap reported `No permissions to create a new
namespace`; all six lanes retained 18 uncovered hunks after redispatch. The adapter
therefore reads `RVW_CODEX_SANDBOX` from a closed two-value vocabulary, keeps
`read-only` as the host default, and the project image sets `danger-full-access`.
Unsupported values fail before spawn. The checkout mount and outer root filesystem stay
read-only, so the container becomes the measured isolation boundary.

Alternative considered: add Docker namespace capabilities until nested bubblewrap works.
That expands the outer container's privilege surface; the settled fallback instead
keeps the outer boundary restricted and disables only the unavailable inner boundary.

### Two detached clones separate target resolution and agent workspace

The live smoke clones bori twice outside Docker and detaches both clones at
`5d4d3cb64`. One read-only mount is the command working directory used to resolve the
commit; the adjacent read-only mount is passed as `--repo-dir` for discovery and
adjudication. A third writable evidence mount receives `/tmp/rvw` artifacts, and the
container stdout/stderr transcript stays in the same host evidence directory.

## Risks / Trade-offs

- **[A fork PR supplies adversarial repository text]** → Keep workflow/image selection on
  the protected base, persist no checkout credential, mount source and container root
  read-only, and grant the job only contents-read/pull-requests-write.
- **[Git rejects a host-owned mount as dubious]** → Supply an exact `/workspace` safe
  directory through Git's per-process environment rather than mutating the target repo.
- **[GitHub CLI does not consume the generic token name consistently]** → Map the same
  job token to both `GITHUB_TOKEN` and `GH_TOKEN` inside the container.
- **[A mutable image reference weakens reproducibility]** → Require an explicit workflow
  input and document a release-version tag; registry policy remains a later owner task.
- **[Inner read-only sandbox is unavailable under Docker]** → Preserve the exact failure
  log, use the measured container-scoped danger fallback, and record the outer isolation
  decision in adjacent context and the completion report.
- **[Container artifacts disappear after the job]** → COMMENT output is the user-facing
  narrative; local smoke mounts an evidence directory, while hosted artifact upload is
  left out until retention requirements are settled.

## Migration Plan

1. Land the image, entry point, workflow, tests, docs, and synchronized specs without
   publishing or installing anything externally.
2. Build and inspect a local version-tagged image, then run the two-clone bori smoke.
3. A later release task publishes the immutable tag. A target repository can then add
   the documented protected caller and explicitly pin that tag.
4. Rollback consists of removing the target repository's caller; no rvw host registry,
   branch protection, or target source state needs migration.
