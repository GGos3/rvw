from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from typer.testing import CliRunner, Result

import rvw.cli as cli_module
import rvw.publish as publish_module
from rvw.adjudicate import (
    AdjudicationAttempt,
    AdjudicationInfrastructureError,
    AdjudicationOutcome,
)
from rvw.lane import Lane
from rvw.merge import MergeResult
from rvw.runtimes import RunResult, RunStatus
from rvw.schema import RuntimeFinding, RuntimeLaneOutput, Severity, Verdict
from rvw.store import RunStore
from rvw.target import ResolvedTarget

runner = CliRunner()


def pr_target() -> ResolvedTarget:
    return ResolvedTarget(
        kind="pr",
        repo="owner/repo",
        base_sha="a" * 40,
        head_sha="b" * 40,
        changed_paths=["src/app.py"],
        diff=(
            "diff --git a/src/app.py b/src/app.py\n"
            "--- a/src/app.py\n"
            "+++ b/src/app.py\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n"
        ),
        pr_number=42,
        pr_title="Change app",
        pr_body="Body",
    )


@pytest.fixture
def registry_root(tmp_path: Path) -> Path:
    root = tmp_path / "registry"
    lane_root = root / "lanes" / "base"
    lane_root.mkdir(parents=True)
    (root / "layers.yaml").write_text(
        """layers:
  - id: base
    tier: base
    lanes: [test-lane]
""",
        encoding="utf-8",
    )
    (lane_root / "test-lane.md").write_text(
        """---
lane: test-lane
tier: base
cost: light
rules:
  - test/rule
---

# test lane

Find the fixture issue.
""",
        encoding="utf-8",
    )
    return root


class FakeRuntime:
    name = "fake"

    async def execute(
        self,
        *,
        lane: Lane,
        prompt: str,
        run_dir: Path,
        deadline_seconds: int,
    ) -> RunResult[RuntimeLaneOutput]:
        del prompt, deadline_seconds
        replica = int(run_dir.name.removeprefix("r"))
        return RunResult(
            lane_id=lane.id,
            replica=replica,
            status=RunStatus.VALID,
            output=RuntimeLaneOutput(
                verdict="findings",
                findings=[
                    RuntimeFinding(
                        rule_id="test/rule",
                        file="src/app.py",
                        line=1,
                        severity=Severity.WARNING,
                        body="fixture finding",
                    )
                ],
            ),
            invalid_reason=None,
            wall_seconds=0.01,
            artifact_dir=run_dir,
        )


@pytest.fixture
def patched_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_resolve_target(spec: str, *, cwd: Path) -> ResolvedTarget:
        del spec, cwd
        return pr_target()

    async def fake_adjudicate(merged: MergeResult, **kwargs: object) -> AdjudicationOutcome:
        del kwargs
        return AdjudicationOutcome(
            verdicts={group.key: Verdict.CONFIRMED for group in merged.groups},
            reasons={group.key: "verified" for group in merged.groups},
            evidence={group.key: "new" for group in merged.groups},
            replica_votes={group.key: [Verdict.CONFIRMED] * 3 for group in merged.groups},
            unresolved=[],
            coerced_rejections=0,
        )

    monkeypatch.setattr(cli_module, "resolve_target", fake_resolve_target)
    monkeypatch.setattr(cli_module, "CodexRuntime", FakeRuntime)
    monkeypatch.setattr(cli_module, "adjudicate", fake_adjudicate)


def invoke_review(
    out_root: Path, registry_root: Path, *extra: str
) -> tuple[Result, dict[str, object]]:
    result = runner.invoke(
        cli_module.app,
        [
            "review",
            "--target",
            "42",
            "--registry",
            str(registry_root),
            "--out",
            str(out_root),
            *extra,
        ],
    )
    payload = json.loads(result.stdout) if "--json" in extra and result.exit_code == 0 else {}
    return result, payload


@pytest.mark.parametrize(
    ("extra", "expected_replicas"),
    [([], 1), (["--replicas", "3"], 3)],
)
def test_review_replica_default_and_explicit_override(
    monkeypatch: pytest.MonkeyPatch,
    extra: list[str],
    expected_replicas: int,
) -> None:
    calls: list[dict[str, object]] = []

    async def fake_review_pipeline(**kwargs: object) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(cli_module, "_review_pipeline", fake_review_pipeline)

    result = runner.invoke(cli_module.app, ["review", "--target", "HEAD", *extra])

    assert result.exit_code == 0, result.stdout
    assert calls[0]["replicas"] == expected_replicas


def test_review_end_to_end_writes_all_stages_and_json_shape(
    tmp_path: Path, registry_root: Path, patched_pipeline: None
) -> None:
    del patched_pipeline
    out_root = tmp_path / "runs"
    repo_dir = tmp_path / "checkout"
    repo_dir.mkdir()

    result, payload = invoke_review(out_root, registry_root, "--repo-dir", str(repo_dir), "--json")

    assert result.exit_code == 0, result.stdout
    assert set(payload) == {
        "run_id",
        "report_path",
        "status",
        "failed_lanes",
        "verdict_counts",
        "coverage_totals",
        "error",
        "build",
    }
    run_dir = out_root / str(payload["run_id"])
    assert {path.name for path in run_dir.iterdir()} >= {
        "run.json",
        "target.json",
        "discover.json",
        "merge.json",
        "outcome.json",
        "report.md",
        "publish-payload.json",
    }
    assert payload["verdict_counts"] == {
        "CONFIRMED": 1,
        "REJECTED": 0,
        "UNCERTAIN": 0,
    }
    assert payload["coverage_totals"] == {"dispatched": 1, "valid": 1, "findings": 1}
    assert payload["status"] == "complete"
    assert payload["failed_lanes"] == []
    assert payload["error"] is None
    assert cast(dict[str, object], payload["build"])["build_id"]
    assert "## 확정 발견 (CONFIRMED)" in (run_dir / "report.md").read_text()


def test_review_surfaces_failed_lane_as_degraded_partial_result(
    tmp_path: Path,
    registry_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layers = registry_root / "layers.yaml"
    layers.write_text(
        """layers:
  - id: base
    tier: base
    lanes: [test-lane, failed-lane]
""",
        encoding="utf-8",
    )
    (registry_root / "lanes" / "base" / "failed-lane.md").write_text(
        """---
lane: failed-lane
tier: base
cost: light
rules:
  - failed/rule
---

# failed lane
""",
        encoding="utf-8",
    )

    class PartialRuntime(FakeRuntime):
        async def execute(
            self,
            *,
            lane: Lane,
            prompt: str,
            run_dir: Path,
            deadline_seconds: int,
        ) -> RunResult[RuntimeLaneOutput]:
            if lane.id == "test-lane":
                return await super().execute(
                    lane=lane,
                    prompt=prompt,
                    run_dir=run_dir,
                    deadline_seconds=deadline_seconds,
                )
            return RunResult(
                lane_id=lane.id,
                replica=1,
                status=RunStatus.INVALID,
                output=None,
                invalid_reason="missing",
                wall_seconds=0.01,
                artifact_dir=run_dir,
            )

    def fake_resolve_target(spec: str, *, cwd: Path) -> ResolvedTarget:
        del spec, cwd
        return pr_target()

    async def fake_adjudicate(merged: MergeResult, **kwargs: object) -> AdjudicationOutcome:
        del kwargs
        return AdjudicationOutcome(
            verdicts={group.key: Verdict.CONFIRMED for group in merged.groups},
            reasons={group.key: "verified" for group in merged.groups},
            evidence={group.key: "new" for group in merged.groups},
            replica_votes={group.key: [Verdict.CONFIRMED] for group in merged.groups},
            unresolved=[],
            coerced_rejections=0,
        )

    monkeypatch.setattr(cli_module, "resolve_target", fake_resolve_target)
    monkeypatch.setattr(cli_module, "CodexRuntime", PartialRuntime)
    monkeypatch.setattr(cli_module, "adjudicate", fake_adjudicate)
    out_root = tmp_path / "runs"
    repo_dir = tmp_path / "checkout"
    repo_dir.mkdir()

    result, payload = invoke_review(out_root, registry_root, "--repo-dir", str(repo_dir), "--json")

    assert result.exit_code == 0, result.stdout
    assert payload["status"] == "degraded"
    assert payload["coverage_totals"] == {"dispatched": 2, "valid": 1, "findings": 1}
    assert payload["failed_lanes"] == [
        {
            "lane_id": "failed-lane",
            "failures": [
                {
                    "replica": 1,
                    "chunk": 1,
                    "reason": "missing",
                    "diagnostic": None,
                }
            ],
        }
    ]
    run_dir = out_root / str(payload["run_id"])
    summary = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert summary["status"] == "degraded"
    assert summary["failed_lanes"] == payload["failed_lanes"]
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "degraded" in report
    assert "failed-lane" in report
    assert "missing" in report
    assert "partial" in report


def test_review_adjudication_empty_output_is_failed_without_outcome_map(
    tmp_path: Path,
    registry_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_resolve_target(spec: str, *, cwd: Path) -> ResolvedTarget:
        del spec, cwd
        return pr_target()

    async def failed_adjudicate(merged: MergeResult, **kwargs: object) -> AdjudicationOutcome:
        del merged, kwargs
        raise AdjudicationInfrastructureError(
            "initial",
            [
                AdjudicationAttempt(
                    wave="initial",
                    replica=1,
                    reason="empty",
                    artifact_dir="/tmp/adjudicate/initial/r1",
                    log_path="/tmp/adjudicate/initial/r1/run.log",
                    log_bytes=0,
                    output_path="/tmp/adjudicate/initial/r1/out.json",
                    output_bytes=0,
                )
            ],
        )

    monkeypatch.setattr(cli_module, "resolve_target", fake_resolve_target)
    monkeypatch.setattr(cli_module, "CodexRuntime", FakeRuntime)
    monkeypatch.setattr(cli_module, "adjudicate", failed_adjudicate)
    out_root = tmp_path / "runs"
    repo_dir = tmp_path / "checkout"
    repo_dir.mkdir()

    result = runner.invoke(
        cli_module.app,
        [
            "review",
            "--target",
            "42",
            "--registry",
            str(registry_root),
            "--repo-dir",
            str(repo_dir),
            "--out",
            str(out_root),
            "--json",
        ],
    )

    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert payload["error"]["reason"] == "no-valid-output"
    assert payload["error"]["attempts"][0]["reason"] == "empty"
    assert payload["verdict_counts"] == {"CONFIRMED": 0, "REJECTED": 0, "UNCERTAIN": 0}
    run_dir = out_root / str(payload["run_id"])
    assert not (run_dir / "outcome.json").exists()
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "status: `failed`" in report
    assert "no-valid-output" in report


def test_pause_stops_after_merge_with_resume_hint(
    tmp_path: Path, registry_root: Path, patched_pipeline: None
) -> None:
    del patched_pipeline
    out_root = tmp_path / "runs"

    result, _ = invoke_review(out_root, registry_root, "--pause")

    assert result.exit_code == 0, result.stdout
    assert "paused after MERGE — resume: rvw report --run" in result.stdout
    run_dir = next(out_root.iterdir())
    assert (run_dir / "merge.json").is_file()
    assert not (run_dir / "outcome.json").exists()
    assert not (run_dir / "report.md").exists()


def test_without_repo_dir_skips_adjudication_and_renders_unadjudicated(
    tmp_path: Path, registry_root: Path, patched_pipeline: None
) -> None:
    del patched_pipeline
    out_root = tmp_path / "runs"

    result, _ = invoke_review(out_root, registry_root)

    assert result.exit_code == 0, result.stdout
    assert "--repo-dir" in result.stderr
    run_dir = next(out_root.iterdir())
    assert not (run_dir / "outcome.json").exists()
    assert "## 발견 (미판정)" in (run_dir / "report.md").read_text(encoding="utf-8")


def test_adjudicate_run_reuses_persisted_discovery_and_rewrites_outcome_report(
    tmp_path: Path,
    registry_root: Path,
    patched_pipeline: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del patched_pipeline
    out_root = tmp_path / "runs"
    review_result, payload = invoke_review(out_root, registry_root, "--json")
    assert review_result.exit_code == 0
    run_id = str(payload["run_id"])
    run_dir = out_root / run_id
    discover_before = (run_dir / "discover.json").read_bytes()
    merge_before = (run_dir / "merge.json").read_bytes()
    (run_dir / "outcome.json").write_text('{"legacy": "void"}\n', encoding="utf-8")
    (run_dir / "report.md").write_text("# stale report\n", encoding="utf-8")
    repo_dir = tmp_path / "checkout"
    repo_dir.mkdir()
    calls: list[dict[str, object]] = []

    async def fake_readjudicate(merged: MergeResult, **kwargs: object) -> AdjudicationOutcome:
        calls.append(kwargs)
        return AdjudicationOutcome(
            verdicts={group.key: Verdict.REJECTED for group in merged.groups},
            reasons={group.key: "rechecked from preserved merge" for group in merged.groups},
            evidence={group.key: "safe source" for group in merged.groups},
            replica_votes={group.key: [Verdict.REJECTED] for group in merged.groups},
            unresolved=[],
            coerced_rejections=0,
        )

    monkeypatch.setattr(cli_module, "adjudicate", fake_readjudicate)

    result = runner.invoke(
        cli_module.app,
        [
            "adjudicate",
            "--run",
            run_id,
            "--repo-dir",
            str(repo_dir),
            "--out",
            str(out_root),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert len(calls) == 1
    assert calls[0]["repo_dir"] == repo_dir
    runtime_root = cast(Path, calls[0]["out_root"])
    assert runtime_root.parent == run_dir / "adjudicate-runtime"
    assert runtime_root.name.startswith("readjudicate-")
    assert (run_dir / "discover.json").read_bytes() == discover_before
    assert (run_dir / "merge.json").read_bytes() == merge_before
    outcome = json.loads((run_dir / "outcome.json").read_text(encoding="utf-8"))
    assert set(outcome["verdicts"].values()) == {"REJECTED"}
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert report != "# stale report\n"
    assert "safe source" in report
    assert "## 기각 (REJECTED)" in report


def test_failed_readjudication_preserves_current_outcome_and_report(
    tmp_path: Path,
    registry_root: Path,
    patched_pipeline: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del patched_pipeline
    out_root = tmp_path / "runs"
    repo_dir = tmp_path / "checkout"
    repo_dir.mkdir()
    review_result, payload = invoke_review(
        out_root, registry_root, "--repo-dir", str(repo_dir), "--json"
    )
    assert review_result.exit_code == 0
    run_id = str(payload["run_id"])
    run_dir = out_root / run_id
    outcome_before = (run_dir / "outcome.json").read_bytes()
    report_before = (run_dir / "report.md").read_bytes()

    async def failed_readjudicate(merged: MergeResult, **kwargs: object) -> AdjudicationOutcome:
        del merged, kwargs
        raise AdjudicationInfrastructureError(
            "initial",
            [
                AdjudicationAttempt(
                    wave="initial-retry",
                    replica=1,
                    reason="empty",
                    artifact_dir="/tmp/readjudicate/initial-retry/r1",
                    exit_code=0,
                    log_path="/tmp/readjudicate/initial-retry/r1/run.log",
                    log_bytes=0,
                    output_path="/tmp/readjudicate/initial-retry/r1/out.json",
                    output_bytes=0,
                )
            ],
        )

    monkeypatch.setattr(cli_module, "adjudicate", failed_readjudicate)

    result = runner.invoke(
        cli_module.app,
        [
            "adjudicate",
            "--run",
            run_id,
            "--repo-dir",
            str(repo_dir),
            "--out",
            str(out_root),
        ],
    )

    assert result.exit_code == 3
    assert "no valid adjudication output" in result.stderr
    assert (run_dir / "outcome.json").read_bytes() == outcome_before
    assert (run_dir / "report.md").read_bytes() == report_before
    summary = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert summary["error"]["reason"] == "no-valid-output"


@pytest.mark.parametrize("artifact_name", ["target.json", "discover.json", "merge.json"])
def test_adjudicate_run_names_missing_required_artifact_without_runtime_call(
    tmp_path: Path,
    registry_root: Path,
    patched_pipeline: None,
    monkeypatch: pytest.MonkeyPatch,
    artifact_name: str,
) -> None:
    del patched_pipeline
    out_root = tmp_path / "runs"
    review_result, payload = invoke_review(out_root, registry_root, "--json")
    assert review_result.exit_code == 0
    run_id = str(payload["run_id"])
    (out_root / run_id / artifact_name).unlink()
    repo_dir = tmp_path / "checkout"
    repo_dir.mkdir()

    async def forbidden_adjudicate(*args: object, **kwargs: object) -> AdjudicationOutcome:
        raise AssertionError(f"adjudicator called with missing input: {args!r} {kwargs!r}")

    monkeypatch.setattr(cli_module, "adjudicate", forbidden_adjudicate)

    result = runner.invoke(
        cli_module.app,
        [
            "adjudicate",
            "--run",
            run_id,
            "--repo-dir",
            str(repo_dir),
            "--out",
            str(out_root),
        ],
    )

    assert result.exit_code == 1
    assert artifact_name in result.stderr
    assert "not implemented" not in result.stderr


def test_report_resume_injects_synthesis_and_unknown_run_exits_one(
    tmp_path: Path, registry_root: Path, patched_pipeline: None
) -> None:
    del patched_pipeline
    out_root = tmp_path / "runs"
    review_result, payload = invoke_review(out_root, registry_root, "--json")
    assert review_result.exit_code == 0
    synthesis = tmp_path / "synthesis.md"
    synthesis.write_text("정확히 이 종합을 사용합니다.\n\n둘째 문단.\n", encoding="utf-8")

    report_result = runner.invoke(
        cli_module.app,
        [
            "report",
            "--run",
            str(payload["run_id"]),
            "--out",
            str(out_root),
            "--synthesis",
            str(synthesis),
        ],
    )
    unknown = runner.invoke(
        cli_module.app,
        ["report", "--run", "missing-run", "--out", str(out_root)],
    )

    assert report_result.exit_code == 0, report_result.stdout
    report = Path(str(payload["report_path"])).read_text(encoding="utf-8")
    assert synthesis.read_text(encoding="utf-8") in report
    assert unknown.exit_code == 1
    assert "missing-run" in unknown.stderr


@pytest.mark.parametrize(
    ("command", "run_id"),
    [("report", "nested/run"), ("publish", "../x")],
)
def test_run_consumers_reject_invalid_run_ids_as_user_errors(
    tmp_path: Path,
    command: str,
    run_id: str,
) -> None:
    result = runner.invoke(
        cli_module.app,
        [command, "--run", run_id, "--out", str(tmp_path / "runs")],
    )

    assert result.exit_code == 2
    assert "invalid run ID" in result.stderr
    assert "Traceback" not in result.stderr


def test_publish_defaults_to_dry_run_and_non_pr_execute_is_user_error(
    tmp_path: Path,
    registry_root: Path,
    patched_pipeline: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del patched_pipeline
    out_root = tmp_path / "runs"
    review_result, payload = invoke_review(out_root, registry_root, "--json")
    assert review_result.exit_code == 0
    payload_path = out_root / str(payload["run_id"]) / "publish-payload.json"
    payload_path.unlink()

    def forbidden_run(cmd: list[str], input_json: str) -> str:
        del cmd, input_json
        raise AssertionError("dry-run called gh")

    monkeypatch.setattr(publish_module, "_run", forbidden_run)
    dry_run = runner.invoke(
        cli_module.app,
        ["publish", "--run", str(payload["run_id"]), "--out", str(out_root)],
    )

    commit = ResolvedTarget(
        kind="commit",
        repo="owner/repo",
        base_sha="a" * 40,
        head_sha="c" * 40,
        changed_paths=[],
        diff="",
    )
    commit_run = RunStore(out_root / "commit").create(commit)
    commit_run.save_target(commit)
    non_pr = runner.invoke(
        cli_module.app,
        [
            "publish",
            "--run",
            commit_run.run_id,
            "--out",
            str(out_root / "commit"),
            "--execute",
        ],
    )

    assert dry_run.exit_code == 0, dry_run.stdout
    assert str(payload_path) in dry_run.stdout
    assert payload_path.is_file()
    assert json.loads(payload_path.read_text())["event"] == "COMMENT"
    assert non_pr.exit_code == 2
    assert "PR" in non_pr.stderr
