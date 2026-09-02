import subprocess
from pathlib import Path

import pytest

from rvw.lane import load_new_lane
from rvw.registry import load_effective_registry
from rvw.schema import Tier
from rvw.target import ResolvedTarget


def _target(head: str = "HEAD") -> ResolvedTarget:
    return ResolvedTarget(
        kind="uncommitted",
        repo="owner/repo",
        base_sha=None,
        head_sha=head,
        changed_paths=["x.ts"],
        diff="",
    )


def test_new_lane_derives_rules_and_paths(tmp_path: Path) -> None:
    path = tmp_path / "lane.md"
    path.write_text(
        """---\nlane: local/check\ntier: scope\ncost: light\nwhen:\n  paths: [\"*.ts\"]\n---\n# Check\n\n## rule: local/contract\nMust hold.\n""",
        encoding="utf-8",
    )
    lane = load_new_lane(path)
    assert lane.rules == ["local/contract"]
    assert lane.when is not None and lane.when.paths == ["*.ts"]


def test_new_lane_rejects_stale_rules_key(tmp_path: Path) -> None:
    path = tmp_path / "lane.md"
    path.write_text(
        """---\nlane: local/check\ntier: project\nrules: [local/old]\n---\n# Check\n## rule: local/new\nBody\n""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="stale-rules"):
        load_new_lane(path)


def test_effective_registry_reads_repo_lanes_from_base_not_worktree(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    lane_dir = tmp_path / ".rvw" / "lanes"
    lane_dir.mkdir(parents=True)
    (lane_dir / "base.md").write_text(
        "---\nlane: local/base\ntier: project\n---\n# Base\n## rule: local/base\nBody\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    (lane_dir / "base.md").unlink()
    (lane_dir / "worktree.md").write_text(
        "---\nlane: local/worktree\ntier: project\n---\n# Worktree\n## rule: local/worktree\nBody\n",
        encoding="utf-8",
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    registry = load_effective_registry(_target(head), cwd=tmp_path, external_root=tmp_path / "none")
    assert [item.lane.id for item in registry.sources if item.source == "repo"] == ["local/base"]
    worktree = load_effective_registry(
        _target(head), cwd=tmp_path, external_root=tmp_path / "none", allow_worktree_rules=True
    )
    assert [item.lane.id for item in worktree.sources if item.source == "worktree"] == [
        "local/worktree"
    ]


def test_effective_registry_orders_and_activates_new_scope_lane() -> None:
    registry = load_effective_registry(
        _target(), cwd=Path.cwd(), external_root=Path("/nonexistent")
    )
    layers = registry.activate("owner/repo", ["x.ts"])
    assert [layer.tier for layer in layers] == sorted(
        (layer.tier for layer in layers),
        key=lambda t: (Tier.BASE, Tier.PROJECT, Tier.SCOPE, Tier.DYNAMIC).index(t),
    )


def test_effective_registry_project_lane_paths_narrow_activation(tmp_path: Path) -> None:
    lane_dir = tmp_path / ".rvw" / "lanes"
    lane_dir.mkdir(parents=True)
    (lane_dir / "scoped.md").write_text(
        """---
lane: local/scoped
tier: project
when:
  paths: ["src/**"]
---
# Scoped
## rule: local/scoped
Body
""",
        encoding="utf-8",
    )
    (lane_dir / "unscoped.md").write_text(
        """---
lane: local/unscoped
tier: project
---
# Unscoped
## rule: local/unscoped
Body
""",
        encoding="utf-8",
    )
    registry = load_effective_registry(
        _target(),
        cwd=tmp_path,
        external_root=tmp_path / "none",
        allow_worktree_rules=True,
    )

    unmatched_ids = {layer.id for layer in registry.activate("owner/repo", ["README.md"])}
    matched_ids = {layer.id for layer in registry.activate("owner/repo", ["src/app.py"])}

    assert "local/scoped" not in unmatched_ids
    assert "local/scoped" in matched_ids
    assert "local/unscoped" in unmatched_ids
