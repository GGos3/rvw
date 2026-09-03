import {ContainerProxy, Sandbox, getSandbox, type Process} from "@cloudflare/sandbox";

export {ContainerProxy};

export class RvwSandbox extends Sandbox<Env> {
  // A0 measured that @cloudflare/containers 0.3.7 defaults this off, so HTTPS
  // bypasses outboundByHost and the Codex proxy returns 401 unless it is explicit.
  interceptHttps = true;
}

const outboundHandler = (request: Request, env: Env) => {
    const authenticated = new Request(request);
    authenticated.headers.set("Authorization", `Bearer ${env.CODEX_API_KEY}`);
    console.log(JSON.stringify({event: "codex_credential_injected", hostname: new URL(request.url).hostname}));
    return fetch(authenticated);
};

RvwSandbox.outboundByHost = {"codex.nekos.me": outboundHandler};

export function configureOutbound(env: Env): void {
  const host = env.CODEX_PROXY_HOST || "codex.nekos.me";
  RvwSandbox.outboundByHost = {[host]: outboundHandler};
}

export function sandboxFor(env: Env, sandboxId: string): RvwSandbox {
  return getSandbox(env.RVW_SANDBOX, sandboxId, {keepAlive: true, normalizeId: true, containerTimeouts: {instanceGetTimeoutMS: 120_000, portReadyTimeoutMS: 120_000}});
}

export function processPayload(process: Process | null): Record<string, unknown> | null {
  if (!process) return null;
  return {id: process.id, pid: process.pid, command: process.command, status: process.status, startTime: process.startTime, endTime: process.endTime, exitCode: process.exitCode};
}

export async function optionalFile(sandbox: RvwSandbox, path: string): Promise<string | null> {
  try {
    const file = await sandbox.readFile(path);
    return typeof file.content === "string" ? file.content : null;
  } catch {
    return null;
  }
}
