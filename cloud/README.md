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
npm test
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

```bash
scripts/drive-spike.sh https://<worker-host> https://github.com/<owner>/<repo> <target-sha> [deadline-seconds]
```

The optional observer deadline defaults to 1,500 seconds (25 minutes). The
driver polls until it sees the process completion marker or the deadline,
fetches available result artifacts, prints a final outcome summary, and always
attempts `/destroy` via an EXIT trap.

Exit status `0` means the completion marker reported review exit `0`. Usage
errors exit `2`; transport, API, or malformed-response failures exit `3`; a
review still running at the observer deadline exits `4`; a terminal process
without a valid completion marker exits `5`; and a completed review with a
non-zero process exit exits `6`. A healthy job reaching the observer deadline
is an observer failure, not evidence that the review itself failed. This bounded
A0 driver still destroys its sandbox on exit, so production-sized work needs
the planned durable A1 job lifecycle.

## Rollout readiness and cleanup

Container application rollout is asynchronous. A Worker deployment can finish
before existing application instances refresh, and a newly requested sandbox
can briefly run the previous image. Before measuring a new image, inspect the
container application and its instances, verify the expected image/digest, and
wait for refreshed instances to become healthy.

Cloudflare retains three independently managed resource classes. Removing a
Worker does not remove its container application or registry images. For a full
spike cleanup, inspect targets first and then remove all three explicitly:

```bash
npx wrangler delete --env spike
npx wrangler containers list
npx wrangler containers delete <container-application-id>
npx wrangler containers images list
npx wrangler containers images delete <image>:<tag>
```

Repeat the image deletion command for every spike tag that is no longer needed.
These commands require Cloudflare credentials and are operator actions, not
offline checks.

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
