from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

import rvw.discover as discover_module
from rvw.discover import discover, resolve_lane_path
from rvw.dispatch import PlannedRun
from rvw.lane import Lane
from rvw.registry import Registry
from rvw.runtimes import RunResult, RunStatus, Runtime
from rvw.schema import RuntimeFinding, RuntimeLaneOutput, Severity, Tier
from rvw.target import ResolvedTarget


def write_lane(root: Path, lane_id: str, tier: Tier, *, cost: str = "normal") -> Path:
    relative_id = lane_id.removeprefix(f"{tier.value}/")
    path = root / tier.value / f"{relative_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = lane_id.split("/", maxsplit=1)[0]
    path.write_text(
        "\n".join(
            [
                "---",
                f"lane: {lane_id}",
                f"tier: {tier.value}",
                f"cost: {cost}",
                "rules:",
                f"  - {prefix}/rule",
                "---",
                "",
                f"Review as {lane_id}.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def target(*, pr: bool = False) -> ResolvedTarget:
    return ResolvedTarget(
        kind="pr" if pr else "commit",
        repo="fixture/local",
        base_sha="a" * 40,
        head_sha="b" * 40,
        changed_paths=["src/a.py"],
        diff=(
            "diff --git a/src/a.py b/src/a.py\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/src/a.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+one = 1\n"
            "+two = 2\n"
        ),
        pr_number=12 if pr else None,
        pr_title="Add a thing" if pr else None,
        pr_body="It should stay correct." if pr else None,
    )


class FakeRuntime(Runtime):
    name = "fake"

    def __init__(
        self,
        *,
        findings: dict[str, list[RuntimeFinding]] | None = None,
        invalid_lanes: set[str] | None = None,
    ) -> None:
        self.findings = findings or {}
        self.invalid_lanes = invalid_lanes or set()
        self.prompts: list[tuple[str, str]] = []
        self.calls: list[tuple[str, int]] = []

    async def execute(
        self,
        *,
        lane: Lane,
        prompt: str,
        run_dir: Path,
        deadline_seconds: int,
    ) -> RunResult:
        del deadline_seconds
        replica = int(run_dir.name.removeprefix("r"))
        self.prompts.append((lane.id, prompt))
        self.calls.append((lane.id, replica))
        if lane.id in self.invalid_lanes:
            return RunResult(
                lane_id=lane.id,
                replica=replica,
                status=RunStatus.INVALID,
                output=None,
                invalid_reason="scripted invalid",
                wall_seconds=0,
                artifact_dir=run_dir,
            )
        return RunResult(
            lane_id=lane.id,
            replica=replica,
            status=RunStatus.VALID,
            output=RuntimeLaneOutput(verdict="PASS", findings=self.findings.get(lane.id, [])),
            invalid_reason=None,
            wall_seconds=0,
            artifact_dir=run_dir,
        )


def registry(*lane_entries: tuple[str, Tier]) -> Registry:
    return Registry.model_validate(
        {
            "layers": [
                {
                    "id": f"layer-{index}",
                    "tier": tier.value,
                    "lanes": [lane_id],
                }
                for index, (lane_id, tier) in enumerate(lane_entries)
            ]
        }
    )


def test_resolve_lane_path_uses_owning_tier_for_all_shapes(tmp_path: Path) -> None:
    base = write_lane(tmp_path, "slop-hygiene", Tier.BASE)
    scope = write_lane(tmp_path, "frontend/skeleton-parity", Tier.SCOPE)
    dynamic = write_lane(tmp_path, "dynamic/goal-parity", Tier.DYNAMIC)

    assert resolve_lane_path(tmp_path, "slop-hygiene", Tier.BASE) == base
    assert resolve_lane_path(tmp_path, "frontend/skeleton-parity", Tier.SCOPE) == scope
    assert resolve_lane_path(tmp_path, "dynamic/goal-parity", Tier.DYNAMIC) == dynamic


def test_resolve_lane_path_error_lists_attempted_path(tmp_path: Path) -> None:
    attempted = tmp_path / "scope" / "frontend" / "missing.md"
    with pytest.raises(FileNotFoundError, match=str(attempted)):
        resolve_lane_path(tmp_path, "frontend/missing", Tier.SCOPE)


async def test_lane_filter_and_dispatch_are_applied_in_one_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    lanes_root = tmp_path / "lanes"
    write_lane(lanes_root, "slop-hygiene", Tier.BASE)
    write_lane(lanes_root, "dynamic/goal-parity", Tier.DYNAMIC)
    reg = registry(("slop-hygiene", Tier.BASE), ("dynamic/goal-parity", Tier.DYNAMIC))
    runtime = FakeRuntime()
    dispatch_calls = 0
    original_dispatch = discover_module.dispatch

    async def counting_dispatch(
        runs: Sequence[PlannedRun],
        dispatch_runtime: Runtime,
        *,
        out_root: Path,
        concurrency: int = 16,
        deadline_seconds: int = 600,
        on_progress: Callable[[RunResult], None] | None = None,
    ) -> list[RunResult]:
        nonlocal dispatch_calls
        dispatch_calls += 1
        return await original_dispatch(
            runs,
            dispatch_runtime,
            out_root=out_root,
            concurrency=concurrency,
            deadline_seconds=deadline_seconds,
            on_progress=on_progress,
        )

    monkeypatch.setattr(discover_module, "dispatch", counting_dispatch)

    result = await discover(
        registry=reg,
        lanes_root=lanes_root,
        target=target(),
        runtime=runtime,
        out_root=tmp_path / "out",
        replicas=2,
        lane_filter=["slop-hygiene"],
    )

    assert dispatch_calls == 1
    assert set(result.lane_results) == {"slop-hygiene"}
    assert runtime.calls == [("slop-hygiene", 1), ("slop-hygiene", 2)]


async def test_pr_brief_fallback_and_operator_brief_wins(tmp_path: Path) -> None:
    lanes_root = tmp_path / "lanes"
    write_lane(lanes_root, "dynamic/goal-parity", Tier.DYNAMIC)
    reg = registry(("dynamic/goal-parity", Tier.DYNAMIC))

    fallback_runtime = FakeRuntime()
    await discover(
        registry=reg,
        lanes_root=lanes_root,
        target=target(pr=True),
        runtime=fallback_runtime,
        out_root=tmp_path / "fallback",
        replicas=1,
    )
    fallback_prompt = fallback_runtime.prompts[0][1]
    assert "Add a thing\n\nIt should stay correct." in fallback_prompt
    assert "UNVERIFIED claim of intent" in fallback_prompt

    operator_runtime = FakeRuntime()
    await discover(
        registry=reg,
        lanes_root=lanes_root,
        target=target(pr=True),
        runtime=operator_runtime,
        out_root=tmp_path / "operator",
        brief="Operator-authored intent",
        brief_source="pr_body",
        replicas=1,
    )
    operator_prompt = operator_runtime.prompts[0][1]
    assert "Operator-authored intent" in operator_prompt
    assert "Add a thing" not in operator_prompt
    assert "UNVERIFIED claim of intent" not in operator_prompt


async def test_enrichment_computes_hunks_anchors_and_off_diff_fallback(tmp_path: Path) -> None:
    lanes_root = tmp_path / "lanes"
    write_lane(lanes_root, "base-review", Tier.BASE)
    raw_findings = [
        RuntimeFinding(
            rule_id="base-review/rule",
            file="src/a.py",
            line=1,
            severity=Severity.WARNING,
            body="Anchored issue",
        ),
        RuntimeFinding(
            rule_id="base-review/rule",
            file="elsewhere.py",
            line=99,
            severity=Severity.SUGGESTION,
            body="Off-diff issue",
        ),
    ]
    runtime = FakeRuntime(findings={"base-review": raw_findings})

    result = await discover(
        registry=registry(("base-review", Tier.BASE)),
        lanes_root=lanes_root,
        target=target(),
        runtime=runtime,
        out_root=tmp_path / "out",
        replicas=1,
    )

    anchored, off_diff = result.findings
    assert anchored.lane_id == "base-review"
    assert anchored.replica == 1
    assert anchored.hunk_id == "src/a.py@@-0,0+1,2@@"
    assert anchored.anchorable is True
    assert anchored.line == 1
    assert off_diff.hunk_id == "elsewhere.py:*"
    assert off_diff.anchorable is False
    assert off_diff.line == 99


async def test_coverage_keeps_all_invalid_lane(tmp_path: Path) -> None:
    lanes_root = tmp_path / "lanes"
    write_lane(lanes_root, "good", Tier.BASE)
    write_lane(lanes_root, "bad", Tier.BASE)
    runtime = FakeRuntime(invalid_lanes={"bad"})

    result = await discover(
        registry=registry(("good", Tier.BASE), ("bad", Tier.BASE)),
        lanes_root=lanes_root,
        target=target(),
        runtime=runtime,
        out_root=tmp_path / "out",
        replicas=2,
    )

    coverage = {entry.lane_id: entry for entry in result.coverage}
    assert coverage["good"].model_dump() == {
        "lane_id": "good",
        "dispatched": 2,
        "valid": 2,
        "findings": 0,
    }
    assert coverage["bad"].model_dump() == {
        "lane_id": "bad",
        "dispatched": 2,
        "valid": 0,
        "findings": 0,
    }
    assert len(runtime.calls) == 6  # two good + two initial bad + two retry bad


async def test_diff_budget_filters_prompt_but_keeps_full_changed_paths(tmp_path: Path) -> None:
    lanes_root = tmp_path / "lanes"
    write_lane(lanes_root, "base-review", Tier.BASE)
    source_diff = target().diff
    generated_path = "runtime-snapshots/contract-graph.json"
    generated_diff = (
        f"diff --git a/{generated_path} b/{generated_path}\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        f"+++ b/{generated_path}\n"
        "@@ -0,0 +1 @@\n"
        "+generated\n"
    )
    budget_target = target().model_copy(
        update={
            "changed_paths": ["src/a.py", generated_path],
            "diff": generated_diff + source_diff,
        }
    )
    runtime = FakeRuntime()

    result = await discover(
        registry=registry(("base-review", Tier.BASE)),
        lanes_root=lanes_root,
        target=budget_target,
        runtime=runtime,
        out_root=tmp_path / "out",
        replicas=1,
    )

    prompt = runtime.prompts[0][1]
    assert source_diff in prompt
    assert generated_diff not in prompt
    assert "# rvw: 1 files excluded from review diff" in prompt
    assert budget_target.changed_paths == ["src/a.py", generated_path]
    assert result.budget is not None
    assert result.budget.kept_files == ["src/a.py"]
    assert result.budget.excluded_reason == {generated_path: "generated-path"}
