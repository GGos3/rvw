"""Command-line surface for rvw."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, cast

import typer
from rich.console import Console

from rvw import __version__
from rvw.schema import finding_schema, lane_output_schema

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_USER_ERROR = 2
EXIT_SYSTEM_ERROR = 3

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

_console = Console()
_error_console = Console(stderr=True)
Option = cast(Callable[..., object], typer.Option)  # pyright: ignore[reportUnknownMemberType]
Argument = cast(Callable[..., object], typer.Argument)  # pyright: ignore[reportUnknownMemberType]


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
def main(  # pyright: ignore[reportUnusedFunction]
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
    target: Annotated[str | None, Option("--target")] = None,
    json_output: Annotated[bool, Option("--json")] = False,
    pause: Annotated[bool, Option("--pause")] = False,
    dynamic_brief: Annotated[Path | None, Option("--dynamic-brief")] = None,
) -> None:
    _stub(1)


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


@app.command()
def lanes(action: Annotated[str | None, Argument()] = None) -> None:
    _stub(1)


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
