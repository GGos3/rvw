# Cloud app platform context

The A0 feasibility spike built a Cloudflare Sandbox Worker outside this repository. This scaffold ports that path into version control while preserving the owner decision that real credentials are injected by `outboundByHost` at egress and never placed in a sandbox process. Wrangler 4.128.0 confirms `image_build_context` is a supported container field; the cloud Dockerfile therefore uses repository-root context for source installation.

The future A1 architecture is webhook → Queue → Sandbox job → GitHub Check Runs API. The GitHub App permissions are checks write, pull requests write, contents read, and metadata read, with pull_request, check_suite, installation, and installation_repositories events. Check-run state starts at `in_progress` and resolves to `success`, `failure`, or `neutral`. Job messages carry a job identifier, installation/repository/PR identifiers, head SHA, source event, attempt, and timestamps. Artifacts are planned for R2 with D1 metadata, but neither is consumed by this change.

Cloudflare API credentials with Containers permissions are not available during this change. CI intentionally uses dry-runs, local Terraform validation, typechecking, and Docker build only. The release deployment is repository-variable gated until the owner provisions credentials and secrets.
