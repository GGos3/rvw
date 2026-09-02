# rvw Cloudflare App platform scaffold

This directory is the Cloudflare Worker + Sandbox SDK execution-plane scaffold.
The default Wrangler environment is local development (`RVW_ENV=dev`); `spike`
enables the bounded A0 lifecycle endpoints with `standard-2` and two instances;
`prod` uses the same `RvwSandbox` class with ten instances and keeps those
endpoints disabled (404). A1 webhook, Queue consumer, Check Runs, and persistence
logic are design-only; Terraform resources are explicitly planned and not bound
to the Worker yet.

## Offline checks

```bash
npm ci
npx tsc --noEmit
npx wrangler deploy --dry-run --outdir dist --env spike
npx wrangler deploy --dry-run --outdir dist --env prod
(cd infra && terraform fmt -check && terraform init -backend=false && terraform validate)
docker build -f cloud/Dockerfile .
```

Wrangler 4.128.0's schema supports `containers[].image_build_context`; this config
sets it to `..` so Wrangler builds from the repository root and installs rvw from
checked-out source. Consequently the equivalent local Docker command uses
`-f cloud/Dockerfile .`; `docker build cloud/` alone cannot access the parent
Python source and is not a valid source build context.

## A0 driver

After an owner deploys the `spike` environment, run
`scripts/drive-spike.sh https://<worker-host>`. It polls for at most 25 minutes,
fetches result artifacts, and always attempts `/destroy` via an EXIT trap.

## Bootstrap and one-time manual steps

Bootstrap Cloudflare API token permission checklist (owner performs once; store
the resulting values as GitHub repository secrets):

- [ ] Workers Scripts: Edit
- [ ] Workers Containers / Registry image: Write
- [ ] Durable Objects: Edit (as needed)
- [ ] Queues: Edit (as needed)
- [ ] R2: Edit (as needed)
- [ ] Account Settings: Read
- [ ] Save token as `CLOUDFLARE_API_TOKEN`
- [ ] Save account identifier as `CLOUDFLARE_ACCOUNT_ID`

Set the Codex credential per environment with `wrangler secret put CODEX_API_KEY`
(run once with `--env spike` and once with `--env prod`). The Worker injects this
secret only at the `CODEX_PROXY_HOST` egress boundary; Sandbox processes receive a
placeholder value.

Register the GitHub App through the manifest flow by opening
`github-app.manifest.json` in GitHub and completing the one-time click-through.
Store the generated App private key and webhook secret as Worker secrets
`GITHUB_APP_PRIVATE_KEY` and `GITHUB_WEBHOOK_SECRET`; they are declared for A1 and
are not consumed by this scaffold.
