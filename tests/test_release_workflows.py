"""Regression contracts for automated and emergency release entry points.

History (2026-07-28, v0.3.0):

The first shape of this rail routed release-please -> workflow_call ->
release.yml so it could work without any PAT (GITHUB_TOKEN-created tags do
not trigger workflows). That failed in production: PyPI Trusted Publishing
rejects OIDC tokens whose claims identify a reusable workflow
("Reusable workflows are not currently supported"), so the publish job got
a 400 Invalid attestations. The rail now follows the codex-lb pattern:
release-please runs with a required RELEASE_PLEASE_TOKEN PAT, the tags it
pushes trigger release.yml directly via the tag event, and release.yml is
NOT reusable. These tests pin that shape.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _release_workflow() -> dict[str, Any]:
    workflow_path = ROOT / ".github/workflows/release.yml"
    return cast(dict[str, Any], yaml.safe_load(workflow_path.read_text(encoding="utf-8")))


def test_release_workflow_is_tag_triggered_and_not_reusable() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    # PyPI Trusted Publishing rejects reusable-workflow OIDC claims — the
    # publish path must be a plain tag-push workflow.
    assert "workflow_call" not in workflow
    assert 'tags: ["v*"]' in workflow
    assert "RELEASE_TAG: ${{ github.ref_name }}" in workflow
    assert "ref: ${{ env.RELEASE_TAG }}" in workflow
    assert 'TAG_VERSION="${RELEASE_TAG#v}"' in workflow
    assert 'tomllib.load(open("pyproject.toml", "rb"))["project"]["version"]' in workflow
    assert "from rvw._version import __version__" in workflow
    assert "id-token: write" in workflow


def test_release_please_uses_required_pat_and_no_call_chain() -> None:
    workflow = (ROOT / ".github/workflows/release-please.yml").read_text(encoding="utf-8")

    # A PAT is required: github.token fallback would create tags that never
    # trigger release.yml (silent-dead releases), and a workflow_call chain
    # cannot publish to PyPI (see module docstring).
    assert "secrets.RELEASE_PLEASE_TOKEN }}" in workflow
    assert "github.token" not in workflow
    assert "workflow_call" not in workflow
    assert "uses: ./.github/workflows/release.yml" not in workflow


def test_release_please_syncs_uv_lock_on_the_release_branch() -> None:
    workflow = (ROOT / ".github/workflows/release-please.yml").read_text(encoding="utf-8")

    # The release-please toml extra-file updater does not rewrite uv.lock
    # (observed 2026-07-28 on v4 and v5), so the workflow must regenerate it
    # on the release branch itself, and push with the PAT so the release PR's
    # CI retriggers.
    assert "ref: release-please--branches--main" in workflow
    assert "uv lock" in workflow
    assert "git push origin HEAD:release-please--branches--main" in workflow
    assert workflow.count("token: ${{ secrets.RELEASE_PLEASE_TOKEN }}") == 2


def test_release_assets_handle_preexisting_release() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    # release-please pre-creates the GitHub release; the tag-triggered run
    # must upload assets into it instead of failing on create.
    assert 'gh release view "$RELEASE_TAG"' in workflow
    assert 'gh release upload "$RELEASE_TAG" dist/* --clobber' in workflow
    assert 'gh release create "$RELEASE_TAG" dist/*' in workflow


def test_release_publishes_traceable_ghcr_image_independently() -> None:
    workflow = _release_workflow()
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    image_job = jobs["publish-image"]
    assert isinstance(image_job, dict)

    # The registry rails are siblings after shared gates: neither registry can
    # suppress the other one's attempt.
    assert image_job["needs"] == "gates"
    assert jobs["build"]["needs"] == "gates"
    assert jobs["publish"]["needs"] == "build"

    assert image_job["permissions"] == {"contents": "read", "packages": "write"}
    assert image_job["outputs"]["digest"] == "${{ steps.image.outputs.digest }}"

    steps = image_job["steps"]
    action_revisions = [
        str(step["uses"]).rsplit("@", maxsplit=1)[1] for step in steps if "uses" in step
    ]
    assert action_revisions
    assert all(len(revision) == 40 for revision in action_revisions)
    assert all(
        all(character in "0123456789abcdef" for character in revision)
        for revision in action_revisions
    )

    checkout = next(
        step for step in steps if str(step.get("uses", "")).startswith("actions/checkout@")
    )
    assert checkout["with"]["persist-credentials"] is False
    assert checkout["with"]["ref"] == "${{ env.RELEASE_TAG }}"

    version = next(step for step in steps if step.get("id") == "version")
    version_script = version["run"]
    assert 'TAG_VERSION="${RELEASE_TAG#v}"' in version_script
    assert "pyproject.toml" in version_script
    assert "from rvw._version import __version__" in version_script
    assert "version=%s\\n" in version_script
    assert '"$GITHUB_OUTPUT"' in version_script

    login = next(
        step for step in steps if str(step.get("uses", "")).startswith("docker/login-action@")
    )
    assert login["with"] == {
        "registry": "ghcr.io",
        "username": "${{ github.actor }}",
        "password": "${{ github.token }}",
    }

    image = next(step for step in steps if step.get("id") == "image")
    assert str(image["uses"]).startswith("docker/build-push-action@")
    assert image["with"]["context"] == "."
    assert image["with"]["push"] is True
    assert image["with"]["tags"].splitlines() == [
        "ghcr.io/soju06/rvw:${{ env.RELEASE_TAG }}",
        "ghcr.io/soju06/rvw:latest",
    ]
    assert image["with"]["build-args"].splitlines() == [
        "CODEX_BASE_URL=",
        "RVW_IMAGE_VERSION=${{ steps.version.outputs.version }}",
    ]

    summary = next(step for step in steps if step.get("name") == "Record published image")
    assert "${{ steps.image.outputs.digest }}" in summary["env"].values()
    assert "ghcr.io/soju06/rvw@${IMAGE_DIGEST}" in summary["run"]
    assert '"$GITHUB_STEP_SUMMARY"' in summary["run"]

    # The image path receives only the repository token used for GHCR login;
    # Codex/PyPI secrets and OIDC are not part of this job.
    assert "secrets." not in str(image_job)
    assert "id-token" not in image_job["permissions"]
