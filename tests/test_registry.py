from pathlib import Path

from rvw.registry import TIER_ORDER, load_registry

FIXTURE = Path(__file__).parent / "fixtures" / "layers_minimal.yaml"


def test_base_layer_always_activates() -> None:
    reg = load_registry(FIXTURE)
    active = reg.activate(repo="unrelated/repo", changed_paths=["README.md"])
    assert "base" in [layer.id for layer in active]


def test_project_layer_requires_repo_match() -> None:
    reg = load_registry(FIXTURE)
    ids = [layer.id for layer in reg.activate(repo="other/repo", changed_paths=["x.ts"])]
    assert "project/bori" not in ids


def test_scope_layer_requires_path_match() -> None:
    reg = load_registry(FIXTURE)
    off = reg.activate(repo="clawroid/bori", changed_paths=["apps/web/page.tsx"])
    on = reg.activate(repo="clawroid/bori", changed_paths=["apps/agent-backend/src/agent.ts"])
    assert "scope/bori/agent" not in [layer.id for layer in off]
    assert "scope/bori/agent" in [layer.id for layer in on]


def test_dynamic_layer_always_activates() -> None:
    reg = load_registry(FIXTURE)
    ids = [layer.id for layer in reg.activate(repo="any/repo", changed_paths=["a.py"])]
    assert "dynamic" in ids


def test_activation_is_tier_ordered() -> None:
    reg = load_registry(FIXTURE)
    tiers = [
        layer.tier
        for layer in reg.activate(
            repo="clawroid/bori", changed_paths=["apps/agent-backend/src/agent.ts"]
        )
    ]
    assert tiers == sorted(tiers, key=TIER_ORDER.index)
