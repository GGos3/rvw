## Why

rvw needs a reproducible Cloudflare execution plane for its GitHub App while the A0 Sandbox feasibility measurement remains runnable. Keeping the Worker, Sandbox image, Wrangler environments, Terraform resources, and release gates in-repository makes the cloud path reviewable and releasable without placing credentials in source control.

## What Changes

- Add a `cloud/` Cloudflare Worker + Sandbox SDK scaffold with `dev`, `spike`, and `prod` environments.
- Port the A0 driver and container source, pin Sandbox SDK/image and Codex CLI versions, and add offline TypeScript, Wrangler dry-run, Terraform, Docker, and packaging gates.
- Add Terraform declarations for the planned R2 artifact bucket and review-jobs Queue.
- Add a GitHub App manifest and operational README covering bootstrap permissions and one-time secret setup.
- Add a variable-gated `deploy-cloud` release job that deploys the Worker before Terraform resources.

## Capabilities

### New Capabilities

- `cloud-app-platform`: Cloudflare Worker/Sandbox IaC layout, environment contracts, secret policy, offline gates, and deployment safety.

### Modified Capabilities

- `release-automation`: add the repository-variable-gated cloud deployment job to the tag release rail.

## Impact

New TypeScript/npm and Terraform projects under `cloud/`, new CI and release workflow jobs, and OpenSpec documentation. Python package configuration remains unchanged except for verification that cloud files are excluded from distributions.
