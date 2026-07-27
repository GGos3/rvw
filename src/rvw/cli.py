"""Command-line surface for rvw."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, cast

import typer
from rich.console import Console
from rich.table import Table

from rvw import __version__
from rvw.discover import resolve_lane_path
from rvw.dispatch import PlannedRun, lpt_sort_key
from rvw.lane import Lane, load_lane
from rvw.registry import Registry, load_registry
from rvw.schema import Tier, finding_schema, lane_output_schema
from rvw.target import ResolvedTarget, TargetResolutionError, resolve_target

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_USER_ERROR = 2
EXIT_SYSTEM_ERROR = 3
DEFAULT_REGISTRY_ROOT = Path("~/.hermes/review").expanduser()
_PLAN_REPLICAS = 3

_EXAMPLES: dict[str, list[str]] = {
    "review": [
        "rvw review --target 123",
        "rvw review --target 123 --pause --dynamic-brief /tmp/brief.md",
        "rvw review --target HEAD --json",
    ],
    "plan": ["rvw plan --target 123 --json"],
    "lanes": ["rvw lanes list", "rvw lanes show slop-hygiene"],
    "doctor": ["rvw doctor"],
}

app = typer.Typer(
    name="rvw",
    help="Layered, replicated, self-adjudicating code review orchestrator",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)
lanes_app = typer.Typer(help="Inspect registered review lanes.", no_args_is_help=True)
app.add_typer(lanes_app, name="lanes")

_console = Console()
_error_console = Console(stderr=True)
Option = cast(Callable[..., object], typer.Option)
Argument = cast(Callable[..., object], typer.Argument)


def _write_json(payload: Any) -> None:
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def _schema_payload() -> dict[str, Any]:
    return {
        "cli_version": __version__,
        "models": {
            "Finding": finding_schema(),
            "LaneOutput": lane_output_schema(),
        },
        "exit_codes": {
            "0": "ok",
            "1": "not_found",
            "2": "user_error",
            "3": "system_error",
        },
    }


def _stub(phase: int) -> None:
    _error_console.print(f"not implemented yet (Phase {phase})")
    raise typer.Exit(EXIT_SYSTEM_ERROR)


def _load_registry_root(root: Path) -> tuple[Registry, Path]:
    expanded = root.expanduser()
    return load_registry(expanded / "layers.yaml"), expanded / "lanes"


def _registered_lane_owners(registry: Registry) -> list[tuple[str, Tier]]:
    owners: list[tuple[str, Tier]] = []
    seen: set[str] = set()
    for layer in registry.layers:
        for lane_id in layer.lanes:
            if lane_id not in seen:
                owners.append((lane_id, layer.tier))
                seen.add(lane_id)
    return owners


def _resolve_cli_target(spec: str) -> ResolvedTarget:
    """Resolve target specs, normalizing symbolic Git revisions such as HEAD."""

    cwd = Path.cwd()
    try:
        return resolve_target(spec, cwd=cwd)
    except TargetResolutionError as target_error:
        try:
            return _resolve_local_commit(spec, cwd)
        except (OSError, subprocess.CalledProcessError) as local_error:
            raise target_error from local_error
    except ValueError as direct_error:
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "--verify", f"{spec}^{{commit}}"],
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as git_error:
            raise ValueError(f"unsupported target specification: {spec!r}") from git_error
        resolved_spec = completed.stdout.strip()
        if not resolved_spec:
            raise ValueError(f"could not resolve target specification: {spec!r}") from direct_error
        try:
            return resolve_target(resolved_spec, cwd=cwd)
        except TargetResolutionError:
            return _resolve_local_commit(resolved_spec, cwd)


def _git_output(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _resolve_local_commit(spec: str, cwd: Path) -> ResolvedTarget:
    """Resolve a commit in a local-only repository with no GitHub remote."""

    ancestry = _git_output(["rev-list", "--parents", "-n", "1", spec], cwd).split()
    if not ancestry:
        raise ValueError(f"could not resolve local commit: {spec!r}")
    root = Path(_git_output(["rev-parse", "--show-toplevel"], cwd).strip())
    names = _git_output(["show", spec, "--format=", "--name-only"], cwd)
    return ResolvedTarget(
        kind="commit",
        repo=root.name,
        base_sha=ancestry[1] if len(ancestry) > 1 else None,
        head_sha=ancestry[0],
        changed_paths=[line for line in names.splitlines() if line],
        diff=_git_output(["show", spec, "--format="], cwd),
    )


def _load_active_lanes(registry: Registry, lanes_root: Path, target: ResolvedTarget) -> list[Lane]:
    lanes: list[Lane] = []
    seen: set[str] = set()
    for layer in registry.activate(target.repo, target.changed_paths):
        for lane_id in layer.lanes:
            if lane_id not in seen:
                lanes.append(load_lane(resolve_lane_path(lanes_root, lane_id, layer.tier)))
                seen.add(lane_id)
    return lanes


def _brief_source(target: ResolvedTarget, dynamic_brief: Path | None) -> str | None:
    if dynamic_brief is not None:
        return "operator"
    if target.pr_title is not None or target.pr_body is not None:
        return "pr_body"
    return None


def _plan_payload(
    registry: Registry,
    lanes_root: Path,
    target: ResolvedTarget,
    dynamic_brief: Path | None,
) -> dict[str, Any]:
    active_layers = registry.activate(target.repo, target.changed_paths)
    lanes = _load_active_lanes(registry, lanes_root, target)
    runs = [
        PlannedRun(lane=lane, prompt="", replica=replica)
        for lane in lanes
        for replica in range(1, _PLAN_REPLICAS + 1)
    ]
    ordered_runs = sorted(runs, key=lambda run: lpt_sort_key(run.lane.cost))
    return {
        "target": {
            "kind": target.kind,
            "repo": target.repo,
            "head_sha": target.head_sha,
            "pr_number": target.pr_number,
        },
        "layers": [
            {
                "id": layer.id,
                "tier": layer.tier.value,
                "predicate": (
                    layer.when.model_dump(exclude_none=True) if layer.when is not None else None
                ),
            }
            for layer in active_layers
        ],
        "lanes": [
            {
                "lane": lane.id,
                "tier": lane.tier.value,
                "cost": lane.cost,
                "rules_count": len(lane.rules),
                "replicas": _PLAN_REPLICAS,
            }
            for lane in lanes
        ],
        "dispatch_order": [run.lane.id for run in ordered_runs],
        "total_runs": len(runs),
        "brief_source": _brief_source(target, dynamic_brief),
    }


def _print_plan(payload: dict[str, Any]) -> None:
    target = cast(dict[str, object], payload["target"])
    _console.print(
        f"Target: {target['kind']} {target['repo']} @ {target['head_sha']}", soft_wrap=True
    )
    layers_table = Table(title="Activated layers")
    layers_table.add_column("Layer")
    layers_table.add_column("Tier")
    layers_table.add_column("Predicate")
    for layer_value in cast(list[dict[str, object]], payload["layers"]):
        predicate = layer_value["predicate"]
        layers_table.add_row(
            str(layer_value["id"]),
            str(layer_value["tier"]),
            json.dumps(predicate) if predicate is not None else "unconditional",
        )
    _console.print(layers_table)
    table = Table(title="Review plan")
    table.add_column("Lane")
    table.add_column("Tier")
    table.add_column("Cost")
    table.add_column("Rules", justify="right")
    table.add_column("Replicas", justify="right")
    for lane_value in cast(list[dict[str, object]], payload["lanes"]):
        table.add_row(
            str(lane_value["lane"]),
            str(lane_value["tier"]),
            str(lane_value["cost"]),
            str(lane_value["rules_count"]),
            str(lane_value["replicas"]),
        )
    _console.print(table)
    _console.print(f"Total runs: {payload['total_runs']}")


def _version_callback(value: bool) -> bool:
    if value:
        _console.print(f"rvw {__version__}")
        raise typer.Exit(EXIT_OK)
    return value


def _schema_callback(value: bool) -> bool:
    if value:
        _write_json(_schema_payload())
        raise typer.Exit(EXIT_OK)
    return value


def _examples_callback(value: str | None) -> str | None:
    if value is None:
        return value
    if value == "":
        _write_json(_EXAMPLES)
        raise typer.Exit(EXIT_OK)
    if value not in _EXAMPLES:
        _error_console.print(f"unknown verb: {value}")
        raise typer.Exit(EXIT_USER_ERROR)
    _write_json({value: _EXAMPLES[value]})
    raise typer.Exit(EXIT_OK)


@app.callback()
def main(
    version: Annotated[
        bool,
        Option(
            "--version",
            help="Show the rvw version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
    show_schema: Annotated[
        bool,
        Option(
            "--schema",
            help="Show CLI and model schemas as JSON.",
            callback=_schema_callback,
            is_eager=True,
        ),
    ] = False,
    examples: Annotated[
        str | None,
        Option(
            "--examples",
            metavar="VERB",
            help="Show examples as JSON.",
            callback=_examples_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    pass


@app.command()
def review(
    target: Annotated[str | None, Option("--target")] = None,
    json_output: Annotated[bool, Option("--json")] = False,
    pause: Annotated[bool, Option("--pause")] = False,
    dynamic_brief: Annotated[Path | None, Option("--dynamic-brief")] = None,
) -> None:
    _stub(5)


@app.command()
def plan(
    target: Annotated[str, Option("--target")],
    json_output: Annotated[bool, Option("--json")] = False,
    pause: Annotated[bool, Option("--pause")] = False,
    dynamic_brief: Annotated[Path | None, Option("--dynamic-brief")] = None,
    registry_root: Annotated[
        Path, Option("--registry", help="Registry root containing layers.yaml and lanes/.")
    ] = DEFAULT_REGISTRY_ROOT,
) -> None:
    del pause
    registry, lanes_root = _load_registry_root(registry_root)
    resolved_target = _resolve_cli_target(target)
    payload = _plan_payload(registry, lanes_root, resolved_target, dynamic_brief)
    if json_output:
        _write_json(payload)
    else:
        _print_plan(payload)


@app.command()
def run(run_id: Annotated[str | None, Option("--run")] = None) -> None:
    _stub(1)


@app.command()
def adjudicate(run_id: Annotated[str | None, Option("--run")] = None) -> None:
    _stub(3)


@app.command()
def report(run_id: Annotated[str | None, Option("--run")] = None) -> None:
    _stub(4)


@app.command()
def publish(run_id: Annotated[str | None, Option("--run")] = None) -> None:
    _stub(4)


@lanes_app.command("list")
def lanes_list(
    registry_root: Annotated[
        Path, Option("--registry", help="Registry root containing layers.yaml and lanes/.")
    ] = DEFAULT_REGISTRY_ROOT,
) -> None:
    registry, lanes_root = _load_registry_root(registry_root)
    table = Table(title="Registered review lanes")
    table.add_column("Lane")
    table.add_column("Tier")
    table.add_column("Cost")
    table.add_column("Rules", justify="right")
    table.add_column("Validation")
    for lane_id, tier_value in _registered_lane_owners(registry):
        lane = load_lane(resolve_lane_path(lanes_root, lane_id, tier_value))
        table.add_row(
            lane.id,
            lane.tier.value,
            lane.cost,
            str(len(lane.rules)),
            lane.validation or "validated",
        )
    _console.print(table)


@lanes_app.command("show")
def lanes_show(
    lane_id: Annotated[str, Argument(help="Lane ID to display.")],
    registry_root: Annotated[
        Path, Option("--registry", help="Registry root containing layers.yaml and lanes/.")
    ] = DEFAULT_REGISTRY_ROOT,
) -> None:
    registry, lanes_root = _load_registry_root(registry_root)
    owner = next(
        (
            (registered_id, tier)
            for registered_id, tier in _registered_lane_owners(registry)
            if registered_id == lane_id
        ),
        None,
    )
    if owner is None:
        _error_console.print(f"unknown lane: {lane_id}")
        raise typer.Exit(EXIT_NOT_FOUND)
    path = resolve_lane_path(lanes_root, owner[0], owner[1])
    _console.print(f"Path: {path}", soft_wrap=True)
    _console.print(path.read_text(encoding="utf-8"), markup=False, highlight=False, soft_wrap=True)


@app.command()
def doctor() -> None:
    _stub(5)


@app.command()
def sample(
    lane: Annotated[str | None, Option("--lane")] = None,
    fixture: Annotated[Path | None, Option("--fixture")] = None,
    compare_free: Annotated[bool, Option("--compare-free")] = False,
) -> None:
    _stub(5)
