import {optionalFile, processPayload, sandboxFor} from "./sandbox";

const MAX_LOG_CHARS = 24_000;
const TARGET_SHA = "d4f2869";
const REVIEW_SCRIPT = String.raw`#!/usr/bin/env bash
set -u
LOG=/workspace/rvw-a0.log
RESULT=/workspace/result
OUT=/workspace/rvw-out
TARGET=/workspace/target
ADJ=/workspace/adjudication
mkdir -p "$RESULT" "$OUT"
exec > >(tee -a "$LOG") 2>&1
printf 'A0_PROCESS_FIRST_LOG_TS=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
printf 'A0_REVIEW_TARGET=%s\n' '${TARGET_SHA}'
printf 'A0_RUN_STARTED_EPOCH_MS=%s\n' "$(date +%s%3N)"
python --version; rvw --version; codex --version; node --version; git --version; rg --version | head -1; gh --version | head -1
rvw lanes list
printenv | grep -i -E 'codex|api_key|token' | sort | tee "$RESULT/credential-env.txt"
python -m rvw.container_entrypoint --version
sed -E 's/(CODEX_API_KEY|api_key|token)[^[:space:]]*/\1=[REDACTED]/Ig' /root/.codex/config.toml | tee "$RESULT/codex-config-sanitized.toml"
set +e
timeout 180s codex exec --sandbox read-only --skip-git-repo-check 'Reply with exactly CF_SANDBOX_PROBE_OK. Do not modify any files.' > "$RESULT/inner-sandbox-probe.txt" 2>&1
probe_rc=$?
printf '%s\n' "$probe_rc" > "$RESULT/inner-sandbox-probe-exit-code.txt"
set -e
git clone https://github.com/Soju06/rvw "$TARGET"; git -C "$TARGET" checkout --detach '${TARGET_SHA}'
git clone https://github.com/Soju06/rvw "$ADJ"; git -C "$ADJ" checkout --detach '${TARGET_SHA}'
cd "$TARGET"
set +e
python -m rvw.container_entrypoint review --target '${TARGET_SHA}' --repo-dir "$ADJ" --out "$OUT" --json > "$RESULT/review-command-output.txt" 2>&1
review_rc=$?
run_dir="$(find "$OUT" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)"
if [[ -n "$run_dir" ]]; then
  printf '%s\n' "$run_dir" > "$RESULT/run-dir.txt"
  for artifact in report.md discover.json outcome.json run.json; do [[ -f "$run_dir/$artifact" ]] && cp "$run_dir/$artifact" "$RESULT/$artifact"; done
fi
printf 'A0_REVIEW_EXIT_CODE=%s\n' "$review_rc"
printf '%s\n' "$review_rc" > /workspace/process-exit-code
exit "$review_rc"
`;

function json(value: unknown, init?: ResponseInit): Response { return Response.json(value, init); }
function errorMessage(error: unknown): string { return error instanceof Error ? error.message : String(error); }
function required(url: URL, key: string): string | null { return url.searchParams.get(key); }

export async function start(env: Env): Promise<Response> {
  const sandboxId = `rvw-spike-${crypto.randomUUID()}`;
  const sandbox = sandboxFor(env, sandboxId);
  await sandbox.writeFile("/workspace/run-review.sh", REVIEW_SCRIPT);
  await sandbox.exec("chmod 0755 /workspace/run-review.sh");
  const process = await sandbox.startProcess("/workspace/run-review.sh", {env: {CODEX_API_KEY: "placeholder-not-a-secret", CODEX_BASE_URL: "", HOME: "/root"}});
  return json({sandboxId, processId: process.id, target: TARGET_SHA}, {status: 202});
}

export async function status(env: Env, url: URL): Promise<Response> {
  const sandboxId = required(url, "sandboxId");
  const processId = required(url, "processId");
  if (!sandboxId || !processId) return json({error: "sandboxId and processId are required"}, {status: 400});
  const sandbox = sandboxFor(env, sandboxId);
  const process = await sandbox.getProcess(processId);
  let logs = {stdout: "", stderr: ""};
  try { logs = await sandbox.getProcessLogs(processId); } catch (error) { logs.stderr = `getProcessLogs failed: ${errorMessage(error)}`; }
  const marker = await optionalFile(sandbox, "/workspace/process-exit-code");
  return json({sandboxId, process: processPayload(process), marker: marker ? {exitCode: Number.parseInt(marker.trim(), 10)} : null, logTail: {stdout: logs.stdout.slice(-MAX_LOG_CHARS), stderr: logs.stderr.slice(-MAX_LOG_CHARS)}, observedAt: new Date().toISOString()});
}

export async function result(env: Env, url: URL): Promise<Response> {
  const sandboxId = required(url, "sandboxId");
  if (!sandboxId) return json({error: "sandboxId is required"}, {status: 400});
  const sandbox = sandboxFor(env, sandboxId);
  const artifacts: Record<string, string | null> = {};
  for (const name of ["report.md", "discover.json", "outcome.json", "run.json", "process-exit-code"] as const) artifacts[name] = await optionalFile(sandbox, `/workspace/${name}`);
  return json({sandboxId, artifacts, observedAt: new Date().toISOString()});
}

export async function destroy(env: Env, url: URL): Promise<Response> {
  const sandboxId = required(url, "sandboxId");
  if (!sandboxId) return json({error: "sandboxId is required"}, {status: 400});
  await sandboxFor(env, sandboxId).destroy();
  return json({sandboxId, destroyed: true, observedAt: new Date().toISOString()});
}

export function handleRoute(request: Request, env: Env): Promise<Response> | Response {
  const url = new URL(request.url);
  if (env.RVW_ENV !== "spike") return json({error: "not found"}, {status: 404});
  try {
    if (request.method === "POST" && url.pathname === "/start") return start(env);
    if (request.method === "GET" && url.pathname === "/status") return status(env, url);
    if (request.method === "GET" && url.pathname === "/result") return result(env, url);
    if (request.method === "POST" && url.pathname === "/destroy") return destroy(env, url);
  } catch (error) { return json({error: errorMessage(error)}, {status: 500}); }
  return json({error: "not found"}, {status: 404});
}
