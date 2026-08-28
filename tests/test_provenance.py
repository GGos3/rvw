from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import rvw.build_backend as build_backend
import rvw.provenance as provenance_module
from rvw.provenance import BuildProvenance, current_build_provenance, stale_install_warning


@pytest.fixture(autouse=True)
def clear_provenance_cache() -> Iterator[None]:
    current_build_provenance.cache_clear()
    yield
    current_build_provenance.cache_clear()


def test_build_provenance_is_frozen_and_forbids_extra() -> None:
    value = BuildProvenance(
        version="0.5.0",
        build_id="sha256:" + "a" * 64,
        source_commit=None,
        source_dirty=None,
        built_at=None,
    )
    with pytest.raises(ValidationError):
        field_name = "build_id"
        setattr(value, field_name, "changed")
    with pytest.raises(ValueError):
        BuildProvenance.model_validate({**value.model_dump(), "extra": True})


def test_fallback_digest_identity_is_stable_and_does_not_consult_git(monkeypatch) -> None:
    monkeypatch.setattr(provenance_module, "BUILD_ID", None)
    monkeypatch.setattr(provenance_module, "SOURCE_COMMIT", None)
    monkeypatch.setattr(provenance_module, "SOURCE_DIRTY", None)
    monkeypatch.setattr(provenance_module, "BUILT_AT", None)
    monkeypatch.setattr(
        provenance_module.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("git consulted")),
    )

    first = current_build_provenance()
    second = current_build_provenance()

    assert first == second
    assert first.build_id.startswith("sha256:")
    assert len(first.build_id.removeprefix("sha256:")) == 64
    assert first.source_commit is None
    assert first.source_dirty is None
    assert first.built_at is None


def test_embedded_constants_are_reported_without_runtime_git(monkeypatch) -> None:
    monkeypatch.setattr(provenance_module, "BUILD_ID", "sha256:" + "1" * 64)
    monkeypatch.setattr(provenance_module, "SOURCE_COMMIT", "a" * 40)
    monkeypatch.setattr(provenance_module, "SOURCE_DIRTY", False)
    monkeypatch.setattr(provenance_module, "BUILT_AT", "2026-08-28T00:00:00Z")
    monkeypatch.setattr(
        provenance_module.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("git consulted")),
    )

    value = current_build_provenance()

    assert value.build_id == "sha256:" + "1" * 64
    assert value.source_commit == "a" * 40
    assert value.source_dirty is False
    assert value.built_at == "2026-08-28T00:00:00Z"


def test_generated_provenance_contains_digest_and_build_facts(monkeypatch) -> None:
    def fake_git(args: list[str]) -> str | None:
        if args == ["rev-parse", "HEAD"]:
            return "a" * 40
        raise AssertionError(args)

    monkeypatch.setattr(build_backend, "_git", fake_git)
    monkeypatch.setattr(build_backend, "_git_status_dirty", lambda: True)

    generated = build_backend._generated_provenance()

    assert generated is not None
    assert f"SOURCE_COMMIT: str | None = {'a' * 40!r}" in generated
    assert "SOURCE_DIRTY: bool | None = True" in generated
    assert "BUILT_AT: str | None = '" in generated
    assert "BUILD_ID: str | None = 'sha256:" in generated


def test_generated_provenance_still_embeds_digest_without_git(monkeypatch) -> None:
    monkeypatch.setattr(build_backend, "_git", lambda _args: None)
    monkeypatch.setattr(build_backend, "_embedded_commit", lambda: None)
    monkeypatch.setattr(
        build_backend,
        "_git_status_dirty",
        lambda: (_ for _ in ()).throw(AssertionError("dirty state is unverifiable")),
    )

    generated = build_backend._generated_provenance()

    assert generated is not None
    assert "BUILD_ID: str | None = 'sha256:" in generated
    assert "SOURCE_COMMIT: str | None = None" in generated
    assert "SOURCE_DIRTY: bool | None = None" in generated


def test_sdist_stamped_commit_survives_wheel_build_without_git(monkeypatch) -> None:
    """`uv build` makes an sdist, then builds the wheel from it.

    That unpacked sdist has no .git, so regenerating provenance there would
    replace an already proven commit with None. Measured on release v0.6.0:
    the published wheel carried SOURCE_COMMIT = None while a --wheel build of
    the same tree carried the real commit.
    """

    monkeypatch.setattr(build_backend, "_git", lambda _args: None)
    monkeypatch.setattr(build_backend, "_embedded_commit", lambda: "a" * 40)
    monkeypatch.setattr(
        build_backend,
        "_git_status_dirty",
        lambda: (_ for _ in ()).throw(AssertionError("dirty state is unverifiable")),
    )

    assert build_backend._generated_provenance() is None


def test_embedded_commit_reads_a_stamped_module(monkeypatch, tmp_path: Path) -> None:
    stamped = tmp_path / "_build_provenance.py"
    stamped.write_text(
        "BUILD_ID: str | None = 'sha256:abc'\n"
        f"SOURCE_COMMIT: str | None = {'c' * 40!r}\n"
        "SOURCE_DIRTY: bool | None = False\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(build_backend, "_PROVENANCE_MODULE", stamped)
    assert build_backend._embedded_commit() == "c" * 40

    stamped.write_text("SOURCE_COMMIT: str | None = None\n", encoding="utf-8")
    assert build_backend._embedded_commit() is None


def test_embedded_provenance_is_a_noop_when_generation_declines(monkeypatch) -> None:
    path = Path(build_backend._PROVENANCE_MODULE)
    before = path.read_bytes()
    monkeypatch.setattr(build_backend, "_generated_provenance", lambda: None)

    with build_backend._embedded_provenance():
        assert path.read_bytes() == before

    assert path.read_bytes() == before


def test_backend_rewrites_provenance_during_wheel_build(monkeypatch, tmp_path: Path) -> None:
    path = Path(build_backend._PROVENANCE_MODULE)
    before = path.read_bytes()
    generated = "BUILD_ID = 'temporary-build'\n"
    monkeypatch.setattr(build_backend, "_generated_provenance", lambda: generated)

    class FakeUvBuild:
        @staticmethod
        def build_wheel(*_args: object) -> str:
            assert path.read_text(encoding="utf-8") == generated
            return "rvw.whl"

    monkeypatch.setattr(build_backend, "_uv_build", lambda: FakeUvBuild())

    assert build_backend.build_wheel(str(tmp_path)) == "rvw.whl"
    assert path.read_bytes() == before


def test_stale_warning_requires_provable_clean_commit(monkeypatch) -> None:
    monkeypatch.setattr(
        provenance_module,
        "current_build_provenance",
        lambda: BuildProvenance(
            version="0.5.0",
            build_id="sha256:" + "0" * 64,
            source_commit=None,
            source_dirty=None,
            built_at=None,
        ),
    )

    def forbidden_distribution(name: str):
        raise AssertionError(f"unverifiable build consulted installation source: {name}")

    monkeypatch.setattr(provenance_module, "distribution", forbidden_distribution)

    assert stale_install_warning() is None


def test_stale_warning_names_proven_descendant_and_concrete_reinstall(
    monkeypatch, tmp_path: Path
) -> None:
    source = tmp_path / "source checkout"
    source.mkdir()
    installed = "a" * 40
    head = "b" * 40
    monkeypatch.setattr(
        provenance_module,
        "current_build_provenance",
        lambda: BuildProvenance(
            version="0.5.0",
            build_id="sha256:" + "1" * 64,
            source_commit=installed,
            source_dirty=False,
            built_at="2026-08-28T00:00:00Z",
        ),
    )

    class Distribution:
        def read_text(self, name: str) -> str:
            assert name == "direct_url.json"
            return json.dumps({"url": source.as_uri()})

    monkeypatch.setattr(provenance_module, "distribution", lambda name: Distribution())
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object):
        del kwargs
        calls.append(command)
        if command[1:3] == ["rev-parse", "HEAD"]:
            return SimpleNamespace(stdout=f"{head}\n", returncode=0)
        assert command[1:3] == ["merge-base", "--is-ancestor"]
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr(provenance_module.subprocess, "run", fake_run)

    warning = stale_install_warning()

    assert warning is not None
    assert installed in warning
    assert head in warning
    assert f"uv tool install --reinstall --from '{source}' rvw" in warning
    assert len(calls) == 2


@pytest.mark.parametrize("dirty", [True, None])
def test_stale_warning_suppressed_for_dirty_or_unknown_build(
    monkeypatch, dirty: bool | None
) -> None:
    monkeypatch.setattr(
        provenance_module,
        "current_build_provenance",
        lambda: BuildProvenance(
            version="0.5.0",
            build_id="sha256:" + "1" * 64,
            source_commit="a" * 40,
            source_dirty=dirty,
            built_at=None,
        ),
    )
    monkeypatch.setattr(
        provenance_module,
        "distribution",
        lambda _name: (_ for _ in ()).throw(AssertionError("should not inspect direct_url")),
    )

    assert stale_install_warning() is None


def test_stale_warning_suppressed_for_equal_or_unrelated_head(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "checkout"
    source.mkdir()
    commit = "a" * 40
    monkeypatch.setattr(
        provenance_module,
        "current_build_provenance",
        lambda: BuildProvenance(
            version="0.5.0",
            build_id="sha256:" + "1" * 64,
            source_commit=commit,
            source_dirty=False,
            built_at=None,
        ),
    )

    class Distribution:
        def read_text(self, _name: str) -> str:
            return json.dumps({"url": source.as_uri()})

    monkeypatch.setattr(provenance_module, "distribution", lambda _name: Distribution())
    monkeypatch.setattr(
        provenance_module.subprocess,
        "run",
        lambda command, **_kwargs: (
            SimpleNamespace(stdout=f"{commit}\n", returncode=0)
            if command[1:3] == ["rev-parse", "HEAD"]
            else (_ for _ in ()).throw(AssertionError("ancestry must not run for equal head"))
        ),
    )
    assert stale_install_warning() is None

    monkeypatch.setattr(
        provenance_module.subprocess,
        "run",
        lambda command, **_kwargs: (
            SimpleNamespace(stdout=f"{'b' * 40}\n", returncode=0)
            if command[1:3] == ["rev-parse", "HEAD"]
            else SimpleNamespace(stdout="", returncode=1)
        ),
    )
    assert stale_install_warning() is None
