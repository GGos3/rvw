const TARGET_SHA_PATTERN = /^[0-9a-f]{7,40}$/;
const GITHUB_REPOSITORY_URL_PATTERN =
  /^https:\/\/github\.com\/[A-Za-z0-9][A-Za-z0-9._-]*\/[A-Za-z0-9][A-Za-z0-9._-]*(?:\.git)?$/;

export const RESULT_ARTIFACT_NAMES = [
  "report.md",
  "discover.json",
  "outcome.json",
  "run.json",
  "review-command-output.txt",
  "credential-env.txt",
  "codex-config-sanitized.toml",
  "inner-sandbox-probe.txt",
  "inner-sandbox-probe-exit-code.txt",
  "run-dir.txt",
] as const;

export type ResultArtifactName = (typeof RESULT_ARTIFACT_NAMES)[number];

export interface SpikeTarget {
  repoUrl: string;
  targetSha: string;
}

export function validateTargetInput(
  repoUrl: string | null,
  targetSha: string | null,
): SpikeTarget | null {
  if (
    !repoUrl ||
    !targetSha ||
    !GITHUB_REPOSITORY_URL_PATTERN.test(repoUrl) ||
    !TARGET_SHA_PATTERN.test(targetSha)
  ) {
    return null;
  }
  return {repoUrl, targetSha};
}

export function buildSandboxProcessEnv(
  proxyHost: string,
): Record<"CODEX_API_KEY" | "CODEX_BASE_URL", string> {
  return {
    CODEX_API_KEY: "placeholder-not-a-secret",
    CODEX_BASE_URL: `https://${proxyHost}/backend-api/codex`,
  };
}

export function resultArtifactPath(name: ResultArtifactName): string {
  return `/workspace/result/${name}`;
}
