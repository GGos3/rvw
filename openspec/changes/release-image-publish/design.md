## Context

The existing tag-triggered release workflow gates, verifies, builds, and publishes the
Python distribution, while the stacked container-packaging change provides a secret-free
Dockerfile and a reusable workflow whose callers pin `ghcr.io/soju06/rvw:v<version>`.
See [proposal.md](proposal.md) for the publication gap. The image path must retain the
existing release trigger, concurrency group, tagged checkout, and least-privilege job
permissions without changing PyPI trusted publishing.

## Goals / Non-Goals

**Goals:**

- Make the GHCR path independently runnable after the same release gates as the Python
  build, including its own fail-closed version check.
- Publish one build under the normalized version tag and `latest`, and surface the
  registry digest in machine-readable and human-readable forms.
- Preserve a secret-free, non-personal image build.

**Non-Goals:**

- Coordinating rollback between PyPI and GHCR or making the two registries transactional.
- Changing release-please, package visibility, branch protection, or target-repository
  required checks.
- Adding multi-platform builds, provenance policy, signing, or a manual image workflow.

## Decisions

### Add a sibling `publish-image` job after gates

`publish-image` will declare `needs: gates`; the existing Python `build` remains another
sibling after `gates`, and `publish` continues to depend only on `build`. This gives both
publication paths the shared quality gate without making either registry depend on the
other. Depending on the Python build was rejected because an image failure must not
block PyPI and the requested release topology is parallel after gates.

### Verify and normalize the tag inside the image job

Jobs do not share workspaces, and the existing Python version check occurs in a sibling
job. The image job will repeat the lightweight package/runtime/tag comparison before
building, then expose the normalized version as a step output. Skipping this check was
rejected because it could publish an image for a mismatched tag while the Python path
correctly failed closed.

### Build and push once through Docker's maintained actions

The job will check out `RELEASE_TAG` with persisted credentials disabled, authenticate
to `ghcr.io` as `github.actor` with `github.token`, and perform one build-and-push with
both tags. Build arguments explicitly set the normalized `RVW_IMAGE_VERSION` and an
empty `CODEX_BASE_URL`; no repository secret is passed to the build. A hand-written
`docker build`/`docker push` sequence was rejected because the build action directly
provides the registry digest needed for the output contract.

### Publish the digest as both a job output and step summary

The build step's registry digest becomes `jobs.publish-image.outputs.digest`. A final
step writes both mutable tag references and the immutable
`ghcr.io/soju06/rvw@<digest>` reference to `GITHUB_STEP_SUMMARY`. Editing the GitHub
Release from this parallel job was rejected because it introduces write contention with
the existing downstream release-assets job; the summary satisfies human discovery while
the job output preserves composition for future consumers.

## Risks / Trade-offs

- **[PyPI can succeed while GHCR fails, or vice versa]** → The workflow makes each
  failure visible and retryable; independence is deliberate because cross-registry
  transactions are unavailable.
- **[`latest` is mutable]** → Documentation keeps version tags as the upgrade surface
  and shows digest pinning for immutable use.
- **[A first package may default to private visibility]** → Document the one-time owner
  visibility check; workflow automation cannot safely choose repository administration
  policy.
- **[Repeated release runs can move the same tags]** → The same immutable tagged source
  and explicit version arguments make the build reproducible in shape, while the emitted
  digest remains the authoritative pin.

## Migration Plan

Merge the workflow, tests, specifications, and documentation before the next release.
The next `v*` tag creates the GHCR package and both image tags automatically. The owner
then verifies or changes the package visibility once in GHCR. Rollback removes or
disables only `publish-image`; the existing PyPI path remains structurally independent.
