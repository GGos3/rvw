## Context

See proposal.md and the cloud-app-platform requirements. The A0 spike already builds a Worker and Sandbox container outside this repository; this change ports that path while keeping credentials at Cloudflare's egress proxy.

## Goals / Non-Goals

**Goals:** provide one source tree for spike and production environments, deterministic offline validation, minimal planned storage declarations, and an opt-in release deployment path.

**Non-Goals:** implementing webhook verification, Queue consumers, Check Runs calls, D1 schema, dashboard, real deployment, secret creation, or App registration.

## Decisions

- **Worker + Sandbox SDK:** use `@cloudflare/sandbox` 0.12.9 and the matching `cloudflare/sandbox:0.12.9` image tag. Extend the SDK Sandbox class and export `ContainerProxy`; route A0 lifecycle calls through a small Worker router.
- **Egress injection:** use `outboundByHost` keyed by `CODEX_PROXY_HOST`; build the Authorization header from the Worker secret on each proxied request. Sandbox variables contain placeholders only.
- **Image build context:** place `cloud/Dockerfile` and cloud source under `cloud/`; Wrangler's `image_build_context` support is checked against the installed schema. If unavailable, the Dockerfile uses `cloud/` as its build context and copies the repository source from the parent only where Wrangler permits it; the README records the finding.
- **Terraform scope:** pin `cloudflare/cloudflare` to `~> 5.0`, use a local backend, and declare only an R2 bucket and Queue with environment-suffixed names. These are planned A1 targets and are not referenced by Worker code yet.
- **Release ordering:** deploy the Worker first so code/bindings are live before Terraform applies storage and queue declarations; the job is skipped by default through `vars.RVW_CLOUD_DEPLOY`.
- **A1 message contract:** design (not implementation) models webhook → Queue → Sandbox job → GitHub Check Runs. Job messages carry `job_id`, installation/repository/PR identifiers, head SHA, event, attempt, and timestamps. Check states map `in_progress` to `success`, `failure`, or `neutral`; artifacts target R2 with D1 metadata declared for a later change.

## Risks / Trade-offs

- [Cloudflare API permissions unavailable] → keep all CI gates offline and make release deployment opt-in.
- [Sandbox SDK or Wrangler schema drift] → pin versions, inspect the local config schema, and document any unsupported image-context field.
- [Planned resources are not yet consumed] → label Terraform resources planned and avoid binding them to runtime code until A1 implementation.

## Migration Plan

Run offline gates on every pull request. After the owner provisions token permissions and secrets, set `RVW_CLOUD_DEPLOY=true` and run a tagged release; rollback uses Wrangler version rollback and Terraform state-aware reversal.

## Open Questions

None that change the scaffold or its contracts; webhook processing and persistence schemas remain future A1 work.
