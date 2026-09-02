# Containerized GitHub Actions review

rvw's reusable workflow makes the `rvw auto` process the check: policy PASS exits
zero and policy BLOCK exits one. Finding narratives can still be published as a GitHub
COMMENT when the repository's base-side `.rvw/policies/auto.yaml` selects `comment`.
COMMENT publication is evidence, not a second check, and this initial integration is
not configured as a required check.

## Trust and working-directory contract

The thin caller uses `pull_request_target` so GitHub loads the base-side workflow definition.
This is the self-bypass boundary: a PR cannot change its own active workflow or
base-side `.rvw/**` rules and then gain those changes in the same run. Protect both paths
with CODEOWNERS and require owner review. The reusable job checks out the event's exact
head SHA without persisted credentials, fetches the recorded base SHA, and mounts that
checkout read-only at `/workspace`. It passes the PR number to `rvw auto` so the CLI
retains recorded-base `.rvw/` reading and COMMENT publication; checkout verification
fails closed if the currently resolved PR head differs from the event SHA.

The image entry point forwards every argument to `rvw`. For direct use, mount the target
checkout and set it as the working directory:

```bash
docker run --rm \
  --workdir /workspace \
  --volume "$PWD:/workspace:ro" \
  --env CODEX_API_KEY \
  --env CODEX_BASE_URL \
  ghcr.io/soju06/rvw:v0.4.1 \
  auto --target HEAD_SHA --repo-dir /workspace
```

`CODEX_API_KEY` is read only by the provider declared in the generated Codex config.
`CODEX_BASE_URL` is optional and selects the endpoint at startup; the image has no
personal proxy URL or credential baked into it. The GitHub job additionally maps its
job-scoped token as both `GITHUB_TOKEN` and `GH_TOKEN` for target resolution and COMMENT
publication.

The image sets `RVW_CODEX_SANDBOX=danger-full-access` for Codex inside the container.
A real nested read-only attempt failed because bubblewrap could not create a user
namespace; the fallback completed with full receipt coverage. The outer container root
and `/workspace` mount remain read-only and are the isolation boundary. Host-installed
rvw still defaults to `--sandbox read-only`.

## Target repository caller

Pin both the reusable workflow ref and image tag. The image shown below is the intended
release shape; this change builds it locally but does not publish it.

```yaml
# .github/workflows/rvw.yml
name: rvw

on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    uses: Soju06/rvw/.github/workflows/rvw-review.yml@v0.4.1
    with:
      image: ghcr.io/soju06/rvw:v0.4.1
      codex_base_url: ${{ vars.CODEX_BASE_URL }}
    secrets:
      CODEX_API_KEY: ${{ secrets.CODEX_API_KEY }}
      # Use this instead of codex_base_url when the endpoint itself is secret:
      # CODEX_BASE_URL: ${{ secrets.CODEX_BASE_URL }}
```

Add matching ownership rules in the target repository (replace the example team):

```text
.rvw/** @your-org/review-owners
.github/workflows/rvw.yml @your-org/review-owners
```

Repository settings do not need a required-check change for initial adoption. Upgrades
are explicit edits to both version pins and receive the same base-side owner review.
