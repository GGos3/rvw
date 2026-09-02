## 1. Release publication contract

- [x] 1.1 Add failing repository-contract tests for the independent GHCR job, tagged checkout, least-privilege token use, exact image tags/build arguments, version verification, and digest exposure.
- [x] 1.2 Extend `release.yml` with the post-gates image publication job and make the new contract tests pass.

## 2. Documentation and source of truth

- [x] 2.1 Update the container caller guide and README to describe automatic release publication, digest pinning, and the one-time GHCR visibility check.
- [x] 2.2 Synchronize the main release-automation and container-ci-packaging specs and contexts with the implemented publication behavior.

## 3. Verification and handoff

- [x] 3.1 Strict-validate the OpenSpec change and run `openspec validate --specs`.
- [x] 3.2 Run actionlint on every touched workflow and, if available, dry-parse the release workflow with `act --list`.
- [x] 3.3 Build the image locally with the same release build arguments and record the resulting proof.
- [x] 3.4 Run all five bare repository gates and review the final diff.
- [x] 3.5 Write `/tmp/rvw-cicd-report.md` with changed files, outcomes, the verbatim image job, local proof, owner checklist, and deviations or open questions.
- [x] 3.6 Commit the completed change on `feat/release-image-publish` without pushing or opening a pull request.
