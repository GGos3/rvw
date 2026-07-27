"""Single-wave, longest-processing-time-first run dispatcher."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from rvw.lane import Lane
from rvw.runtimes import RunResult, RunStatus, Runtime

_COST_ORDER = {"heavy": 0, "normal": 1, "light": 2}


@dataclass(frozen=True, slots=True)
class PlannedRun:
    lane: Lane
    prompt: str
    replica: int

    def __post_init__(self) -> None:
        if self.replica < 1:
            raise ValueError("replica must be at least 1")


async def dispatch(
    runs: Sequence[PlannedRun],
    runtime: Runtime,
    *,
    out_root: Path,
    concurrency: int = 16,
    deadline_seconds: int = 600,
    on_progress: Callable[[RunResult], None] | None = None,
) -> list[RunResult]:
    """Dispatch all planned runs in one wave, retrying all-invalid lanes once."""

    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")
    if deadline_seconds < 1:
        raise ValueError("deadline_seconds must be at least 1")

    semaphore = asyncio.Semaphore(concurrency)

    async def execute_one(run: PlannedRun) -> RunResult:
        async with semaphore:
            lane_slug = run.lane.id.replace("/", "--")
            run_dir = out_root / lane_slug / f"r{run.replica}"
            run_dir.mkdir(parents=True, exist_ok=True)
            result = await runtime.execute(
                lane=run.lane,
                prompt=run.prompt,
                run_dir=run_dir,
                deadline_seconds=deadline_seconds,
            )
            if on_progress is not None:
                on_progress(result)
            return result

    async def execute_wave(wave_runs: Sequence[PlannedRun]) -> list[RunResult]:
        ordered = sorted(wave_runs, key=lambda run: _COST_ORDER[run.lane.cost])
        tasks = [asyncio.create_task(execute_one(run)) for run in ordered]
        return list(await asyncio.gather(*tasks))

    main_results = await execute_wave(runs)
    results_by_lane: dict[str, list[RunResult]] = {}
    for result in main_results:
        results_by_lane.setdefault(result.lane_id, []).append(result)

    retry_lane_ids = {
        lane_id
        for lane_id, lane_results in results_by_lane.items()
        if all(result.status is RunStatus.INVALID for result in lane_results)
    }
    retry_runs = [run for run in runs if run.lane.id in retry_lane_ids]
    retry_results = await execute_wave(retry_runs)

    final_by_key = {
        (result.lane_id, result.replica): result for result in [*main_results, *retry_results]
    }
    return sorted(final_by_key.values(), key=lambda result: (result.lane_id, result.replica))


__all__: list[str] = ["PlannedRun", "dispatch"]
