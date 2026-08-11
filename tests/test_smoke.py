import json

from typer.testing import CliRunner

from rvw.cli import app

runner = CliRunner()


def test_version() -> None:
    r = runner.invoke(app, ["--version"])
    assert r.exit_code == 0
    assert "rvw 0.4.1" in r.stdout
    assert "build " in r.stdout


def test_schema_is_valid_json() -> None:
    r = runner.invoke(app, ["--schema"])
    assert r.exit_code == 0
    payload = json.loads(r.stdout)
    assert "models" in payload
    assert payload["exit_codes"]["0"] == "ok"


def test_bare_invocation_shows_help() -> None:
    r = runner.invoke(app, [])
    assert r.exit_code != 0
    assert "Usage" in r.stdout


def test_stub_exits_system_error() -> None:
    r = runner.invoke(app, ["publish", "--run", "r-x"])
    assert r.exit_code == 3
