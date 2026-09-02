## Why

rvw currently assumes a personally provisioned host, so repositories cannot run the
review gate reproducibly in GitHub Actions. A versioned container contract and a
base-controlled reusable workflow make the existing `rvw auto` pass/block contract
portable without introducing a webhook service or trusting workflow changes from a PR.

## What Changes

- Add a multi-stage Linux image that installs rvw and its packaged common lanes from
  source alongside Python 3.12, Node 24, Codex CLI 0.152.0, Git, GitHub CLI, and the
  minimal shell tools needed by agentic review.
- Add secret-free Codex configuration materialization: the image declares an env-key
  provider and resolves its optional base URL at container startup.
- Add a reusable GitHub Actions workflow that checks out the immutable PR head from a
  `pull_request_target` caller, fetches its base, runs a caller-pinned image, publishes
  COMMENT findings when policy requests it, and reports PASS/BLOCK as the job exit.
- Document the target-repository caller, working-directory and mount conventions,
  CODEOWNERS boundary, token mapping, image pinning, and non-required-check posture.
- Measure the headless container boundary with a real bori review, including env-only
  authentication, Codex sandbox availability, and valid receipt coverage.

## Capabilities

### New Capabilities

- `container-ci-packaging`: Define the runnable image, startup configuration, reusable
  workflow, caller trust boundary, and headless smoke contract.

### Modified Capabilities

- `operation-modes`: Extend the installed CLI packaging contract to the container entry
  point and define how CI invokes the existing auto exit and COMMENT publication modes.
- `release-automation`: Add the versioned container artifact surface while keeping image
  publication outside this local-only implementation change.
- `runtime-contract`: Preserve read-only host execution while adding the measured,
  closed container-only sandbox selection needed when nested bubblewrap is unavailable.

## Impact

This affects the repository build context, container startup code, GitHub Actions and
CODEOWNERS metadata, tests, operator documentation, and OpenSpec contracts. Target
repositories supply only a thin base-side caller workflow, `.rvw/` project lanes and
policy, a pinned image reference, and GitHub/Codex credentials; no target repository,
external review registry, image registry, branch protection, or webhook service is
modified by this change.
