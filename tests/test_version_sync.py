"""Guard: the packaged version and the runtime version string must agree.

Regression for the v0.2.0 release failure (2026-07-28): ``_version.py`` was
bumped without ``pyproject.toml``, so the release workflow rebuilt and tried
to upload a stale-versioned wheel, and PyPI rejected it with
"400 File already exists". A version bump must change both surfaces together.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from rvw import __version__


def test_pyproject_version_matches_runtime_version() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    assert data["project"]["version"] == __version__

    with (root / "uv.lock").open("rb") as handle:
        lock = tomllib.load(handle)
    rvw_packages = [package for package in lock["package"] if package["name"] == "rvw"]
    assert len(rvw_packages) == 1
    assert rvw_packages[0]["version"] == __version__


def test_release_please_manages_every_version_surface() -> None:
    root = Path(__file__).resolve().parents[1]
    version_line = next(
        line
        for line in (root / "src/rvw/_version.py").read_text(encoding="utf-8").splitlines()
        if line.startswith("__version__ = ")
    )
    assert version_line.endswith("  # x-release-please-version")

    config = json.loads((root / ".github/release-please-config.json").read_text(encoding="utf-8"))
    package = config["packages"]["."]
    assert config["release-type"] == package["release-type"] == "python"
    assert package["changelog-path"] == "CHANGELOG.md"
    assert "src/rvw/_version.py" in package["extra-files"]
    assert {
        "type": "toml",
        "path": "uv.lock",
        "jsonpath": "$.package[?(@.name=='rvw')].version",
    } in package["extra-files"]

    manifest = json.loads(
        (root / ".github/release-please-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest == {".": __version__}
