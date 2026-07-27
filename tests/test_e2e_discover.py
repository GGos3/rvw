from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from rvw.discover import discover
from rvw.registry import Registry
from rvw.runtimes.codex import CodexRuntime
from rvw.schema import Severity
from rvw.target import ResolvedTarget

FIXTURE = Path(__file__).parent / "fixtures" / "deep.ts"
PRODUCTION_LANES = Path.home() / ".hermes" / "review" / "lanes"


def new_file_diff(path: Path) -> str:
    completed = subprocess.run(
        ["git", "diff", "--no-index", "--", "/dev/null", str(path)],
        cwd=Path.cwd(),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1, completed.stderr
    assert completed.stdout
    return completed.stdout


def has_any(body: str, keywords: list[str]) -> bool:
    lowered = body.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


@pytest.mark.live
async def test_discover_real_deep_fixture(tmp_path: Path) -> None:
    diff = new_file_diff(FIXTURE.relative_to(Path.cwd()))
    review_target = ResolvedTarget(
        kind="commit",
        repo="fixture/local",
        base_sha="a" * 40,
        head_sha="b" * 40,
        changed_paths=["tests/fixtures/deep.ts"],
        diff=diff,
    )
    registry = Registry.model_validate(
        {
            "layers": [
                {
                    "id": "base",
                    "tier": "base",
                    "lanes": ["slop-hygiene", "unscoped-sweep"],
                }
            ]
        }
    )

    result = await discover(
        registry=registry,
        lanes_root=PRODUCTION_LANES,
        target=review_target,
        runtime=CodexRuntime(),
        out_root=tmp_path,
        replicas=3,
    )

    slop = [finding for finding in result.findings if finding.lane_id == "slop-hygiene"]
    sweep = [finding for finding in result.findings if finding.lane_id == "unscoped-sweep"]
    assert any(finding.rule_id == "slop/duplicate-object-key" for finding in slop)
    assert any(finding.rule_id == "slop/dead-assignment" for finding in slop)

    assert any(
        finding.rule_id.startswith("unscoped/")
        and finding.anchorable
        and has_any(finding.body, ["limit", "cursor", "dropped", "pageNo"])
        for finding in sweep
    )
    assert any(
        finding.rule_id.startswith("unscoped/")
        and finding.anchorable
        and has_any(finding.body, ["ok: true", "hides", "exception", "catch", "swallow"])
        for finding in sweep
    )
    assert all(finding.severity is not Severity.BLOCKER for finding in sweep)

    per_replica: dict[int, set[tuple[str, str]]] = {
        replica: {
            (finding.rule_id, finding.hunk_id) for finding in slop if finding.replica == replica
        }
        for replica in range(1, 4)
    }
    union = {(finding.rule_id, finding.hunk_id) for finding in slop}
    assert len(union) >= max(len(identities) for identities in per_replica.values())

    coverage = {entry.lane_id: entry for entry in result.coverage}
    assert coverage["slop-hygiene"].dispatched == 3
    assert coverage["unscoped-sweep"].dispatched == 3

    assert all(
        finding.anchorable for finding in result.findings if not finding.hunk_id.endswith(":*")
    )
