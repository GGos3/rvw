from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import BaseModel

from rvw.lane import Lane
from rvw.runtimes import RunResult, RunStatus
from rvw.sample import SampleSiteVariance, free_variant_schema, sample_lane, validate_output_free
from rvw.schema import RuntimeFinding, RuntimeLaneOutput, Severity, Tier


def lane_fixture() -> Lane:
    return Lane(
        lane="test-lane",
        tier=Tier.BASE,
        rules=["test/one", "test/two"],
        prompt_body="Find issues.",
    )


def output(*findings: tuple[str, str, int]) -> RuntimeLaneOutput:
    return RuntimeLaneOutput(
        verdict="findings" if findings else "pass",
        findings=[
            RuntimeFinding(
                rule_id=rule_id,
                file=file,
                line=line,
                severity=Severity.WARNING,
                body=f"{file}:{line}",
            )
            for rule_id, file, line in findings
        ],
    )


class FakeRuntime:
    name = "fake"

    def __init__(
        self,
        enum_outputs: Sequence[RuntimeLaneOutput | None],
        free_outputs: Sequence[RuntimeLaneOutput | None],
    ) -> None:
        self.outputs = {"enum": list(enum_outputs), "free": list(free_outputs)}
        self.calls: list[tuple[str, Path, str]] = []

    async def execute_raw(
        self,
        *,
        schema: dict[str, Any],
        prompt: str,
        run_dir: Path,
        deadline_seconds: int,
        workdir: Path | None = None,
        validate: Callable[[object], BaseModel],
    ) -> RunResult[BaseModel]:
        del schema, deadline_seconds, workdir
        variant = run_dir.parent.name
        replica = int(run_dir.name.removeprefix("r"))
        self.calls.append((variant, run_dir, prompt))
        scripted = self.outputs[variant][replica - 1]
        if scripted is None:
            return RunResult(
                lane_id="test-lane",
                replica=replica,
                status=RunStatus.INVALID,
                output=None,
                invalid_reason="scripted invalid",
                wall_seconds=0,
                artifact_dir=run_dir,
            )
        validated = validate(scripted.model_dump())
        return RunResult(
            lane_id="test-lane",
            replica=replica,
            status=RunStatus.VALID,
            output=validated,
            invalid_reason=None,
            wall_seconds=0,
            artifact_dir=run_dir,
        )

    async def execute(self, **kwargs: object) -> RunResult:
        raise AssertionError(f"execute must not be used: {kwargs}")


def assert_strict_required(node: object) -> None:
    if isinstance(node, dict):
        node_dict = cast(dict[str, object], node)
        properties = node_dict.get("properties")
        if node_dict.get("type") == "object" and isinstance(properties, dict):
            assert set(cast(list[str], node_dict["required"])) == set(properties)
        for value in node_dict.values():
            assert_strict_required(value)
    elif isinstance(node, list):
        for value in node:
            assert_strict_required(value)


def test_free_variant_schema_relaxes_only_rule_id_enum() -> None:
    schema = free_variant_schema(lane_fixture())
    rule_schema = schema["properties"]["findings"]["items"]["properties"]["rule_id"]
    assert rule_schema == {"type": "string"}
    assert_strict_required(schema)
    validate_output_free(output(("invented/rule", "a.py", 1)).model_dump())


@pytest.mark.parametrize("replicas", [1, 3])
async def test_identical_sites_pass(replicas: int, tmp_path: Path) -> None:
    enum = [output(("test/one", "a.py", 4)) for _ in range(replicas)]
    free = [output(("test/one", "a.py", 4)) for _ in range(replicas)]
    runtime = FakeRuntime(enum, free)
    report = await sample_lane(
        lane_fixture(),
        fixture_diff="diff --git a/a.py b/a.py\n",
        runtime=runtime,
        out_root=tmp_path,
        replicas=replicas,
    )
    assert report.verdict == "PASS"
    assert report.enum_only == []
    assert report.free_only == []
    assert report.novel_rule_ids == []
    assert report.site_variance == []
    assert len(runtime.calls) == replicas * 2
    assert len({prompt for _, _, prompt in runtime.calls}) == 1


async def test_free_extra_site_requires_review(tmp_path: Path) -> None:
    runtime = FakeRuntime(
        [output(("test/one", "a.py", 4))],
        [output(("free/same", "a.py", 4), ("free/extra", "b.py", 9))],
    )
    report = await sample_lane(
        lane_fixture(),
        fixture_diff="fixture",
        runtime=runtime,
        out_root=tmp_path,
        replicas=1,
    )
    assert report.verdict == "REVIEW"
    assert report.free_only == [("free/extra", 9)]
    assert report.novel_rule_ids == ["free/extra", "free/same"]
    assert report.site_variance == []


async def test_novel_rule_at_shared_site_requires_review(tmp_path: Path) -> None:
    runtime = FakeRuntime(
        [output(("test/one", "a.py", 4))],
        [output(("invented/rule", "a.py", 4))],
    )

    report = await sample_lane(
        lane_fixture(),
        fixture_diff="fixture",
        runtime=runtime,
        out_root=tmp_path,
        replicas=1,
    )

    assert report.enum_only == []
    assert report.free_only == []
    assert report.novel_rule_ids == ["invented/rule"]
    assert report.verdict == "REVIEW"


async def test_in_enum_site_difference_is_non_failing_variance(tmp_path: Path) -> None:
    runtime = FakeRuntime(
        [output(("test/one", "a.py", 4))],
        [output(("test/one", "b.py", 9))],
    )

    report = await sample_lane(
        lane_fixture(),
        fixture_diff="fixture",
        runtime=runtime,
        out_root=tmp_path,
        replicas=1,
    )

    assert report.verdict == "PASS"
    assert report.novel_rule_ids == []
    assert report.site_variance == [
        SampleSiteVariance(variant="enum_only", rule_id="test/one", file="a.py", line=4),
        SampleSiteVariance(variant="free_only", rule_id="test/one", file="b.py", line=9),
    ]


async def test_generated_other_rule_is_not_novel(tmp_path: Path) -> None:
    runtime = FakeRuntime(
        [output(("test/one", "a.py", 4))],
        [output(("test/other", "b.py", 9))],
    )

    report = await sample_lane(
        lane_fixture(),
        fixture_diff="fixture",
        runtime=runtime,
        out_root=tmp_path,
        replicas=1,
    )

    assert report.verdict == "PASS"
    assert report.novel_rule_ids == []
    assert [item.rule_id for item in report.site_variance] == ["test/one", "test/other"]


async def test_invalid_replicas_are_ignored_in_union(tmp_path: Path) -> None:
    runtime = FakeRuntime(
        [None, output(("test/one", "a.py", 4)), None],
        [None, output(("test/one", "a.py", 4)), None],
    )
    report = await sample_lane(
        lane_fixture(),
        fixture_diff="fixture",
        runtime=runtime,
        out_root=tmp_path,
        replicas=3,
    )
    assert report.verdict == "PASS"
    assert report.enum_findings == [("test/one", 4)]
    assert report.free_findings == [("test/one", 4)]
