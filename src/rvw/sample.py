"""Closed-enum versus free-rule-id sampling gate (ADR-004)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from rvw.lane import Lane
from rvw.prompts import build_lane_prompt
from rvw.runtimes import RunResult, RunStatus, Runtime
from rvw.runtimes.codex import validate_output
from rvw.schema import RuntimeLaneOutput


def free_variant_schema(lane: Lane) -> dict[str, Any]:
    """Return the lane schema with only the closed rule-id enum relaxed."""

    schema = lane.output_schema()
    schema["properties"]["findings"]["items"]["properties"]["rule_id"] = {"type": "string"}
    return schema


def validate_output_free(raw: object) -> RuntimeLaneOutput:
    """Validate lane output without applying lane rule-id membership."""

    return RuntimeLaneOutput.model_validate(raw)


@dataclass(frozen=True)
class SampleReport:
    lane_id: str
    enum_findings: list[tuple[str, int | None]]
    free_findings: list[tuple[str, int | None]]
    enum_only: list[tuple[str, int | None]]
    free_only: list[tuple[str, int | None]]
    verdict: Literal["PASS", "REVIEW"]
    replicas: int


def _sites(
    results: list[RunResult[Any]],
) -> dict[tuple[str, int | None], tuple[str, int | None]]:
    sites: dict[tuple[str, int | None], tuple[str, int | None]] = {}
    for result in results:
        if result.status is not RunStatus.VALID or result.output is None:
            continue
        output = cast(RuntimeLaneOutput, result.output)
        for finding in output.findings:
            sites.setdefault((finding.file, finding.line), (finding.rule_id, finding.line))
    return sites


def _ordered_values(
    sites: dict[tuple[str, int | None], tuple[str, int | None]],
    selected: set[tuple[str, int | None]] | None = None,
) -> list[tuple[str, int | None]]:
    keys = sites.keys() if selected is None else selected
    return [
        sites[key]
        for key in sorted(keys, key=lambda item: (item[0], item[1] is None, item[1] or 0))
    ]


async def sample_lane(
    lane: Lane,
    *,
    fixture_diff: str,
    runtime: Runtime,
    out_root: Path,
    replicas: int = 3,
    deadline_seconds: int = 600,
) -> SampleReport:
    """Run enum and free-schema variants in one wave and compare site recall."""

    if replicas < 1:
        raise ValueError("replicas must be at least 1")
    if deadline_seconds < 1:
        raise ValueError("deadline_seconds must be at least 1")

    prompt = build_lane_prompt(
        lane,
        diff=fixture_diff,
        brief=None,
        brief_source=None,
        covered_rules={},
    )
    semaphore = asyncio.Semaphore(16)

    def validate_enum(raw: object) -> RuntimeLaneOutput:
        return validate_output(lane, raw)

    async def execute_one(variant: Literal["enum", "free"], replica: int) -> RunResult[Any]:
        async with semaphore:
            if variant == "enum":
                schema = lane.output_schema()
                validator = validate_enum
            else:
                schema = free_variant_schema(lane)
                validator = validate_output_free
            return await runtime.execute_raw(
                schema=schema,
                prompt=prompt,
                run_dir=out_root / variant / f"r{replica}",
                deadline_seconds=deadline_seconds,
                validate=validator,
            )

    tasks = [
        asyncio.create_task(execute_one(variant, replica))
        for variant in ("enum", "free")
        for replica in range(1, replicas + 1)
    ]
    all_results = await asyncio.gather(*tasks)
    enum_results = all_results[:replicas]
    free_results = all_results[replicas:]
    enum_sites = _sites(enum_results)
    free_sites = _sites(free_results)
    enum_only_sites = set(enum_sites) - set(free_sites)
    free_only_sites = set(free_sites) - set(enum_sites)
    return SampleReport(
        lane_id=lane.id,
        enum_findings=_ordered_values(enum_sites),
        free_findings=_ordered_values(free_sites),
        enum_only=_ordered_values(enum_sites, enum_only_sites),
        free_only=_ordered_values(free_sites, free_only_sites),
        verdict="PASS" if not free_only_sites else "REVIEW",
        replicas=replicas,
    )


__all__ = ["SampleReport", "free_variant_schema", "sample_lane", "validate_output_free"]
