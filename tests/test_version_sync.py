"""Guard: the packaged version and the runtime version string must agree.

Regression for the v0.2.0 release failure (2026-07-28): ``_version.py`` was
bumped without ``pyproject.toml``, so the release workflow rebuilt and tried
to upload a stale-versioned wheel, and PyPI rejected it with
"400 File already exists". A version bump must change both surfaces together.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from rvw import __version__


def test_pyproject_version_matches_runtime_version() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    assert data["project"]["version"] == __version__
