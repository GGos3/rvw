#!/usr/bin/env bash
set -euo pipefail
[[ $# -eq 1 ]] || { echo "usage: $0 https://worker.example.workers.dev" >&2; exit 2; }
base_url=${1%/}; evidence="spike-evidence/run"; mkdir -p "$evidence/status"; sandbox_id=""; process_id=""; destroyed=0
cleanup() { if [[ -n "$sandbox_id" && "$destroyed" -eq 0 ]]; then curl --fail-with-body --silent --show-error -X POST "$base_url/destroy?sandboxId=$sandbox_id" -o "$evidence/destroy.json" || true; destroyed=1; fi; }
trap cleanup EXIT
curl --fail-with-body --silent --show-error -X POST "$base_url/start" -o "$evidence/start.json"
sandbox_id=$(jq -er '.sandboxId' "$evidence/start.json"); process_id=$(jq -er '.processId' "$evidence/start.json")
for poll in $(seq 0 74); do
  status_file=$(printf '%s/status/%03d.json' "$evidence" "$poll"); curl --fail-with-body --silent --show-error "$base_url/status?sandboxId=$sandbox_id&processId=$process_id" -o "$status_file"
  if jq -e '(.marker.exitCode? != null) or (.process.status? | IN("completed", "failed", "killed", "error"))' "$status_file" >/dev/null; then break; fi
  sleep 20
done
curl --fail-with-body --silent --show-error "$base_url/result?sandboxId=$sandbox_id" -o "$evidence/result.json"
