from __future__ import annotations

import pytest

from rvw.diffbudget import DiffBudgetExceeded, apply_diff_budget


def diff_segment(path: str, body: str) -> str:
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-old\n+{body}\n"


def test_generated_path_is_excluded_and_announced() -> None:
    generated = diff_segment("runtime-snapshots/contract-graph.json", "generated")
    source = diff_segment("src/app.py", "kept")

    filtered, report = apply_diff_budget(generated + source)

    assert filtered.startswith(
        "# rvw: 1 files excluded from review diff (generated/oversize): "
        "runtime-snapshots/contract-graph.json\n"
    )
    assert generated not in filtered
    assert source in filtered
    assert report.kept_files == ["src/app.py"]
    assert report.excluded_files == ["runtime-snapshots/contract-graph.json"]
    assert report.excluded_reason == {"runtime-snapshots/contract-graph.json": "generated-path"}
    assert report.kept_chars == len(source)
    assert report.excluded_chars == len(generated)
    assert report.kept_chars + report.excluded_chars == len(generated + source)


def test_generated_globs_match_nested_paths() -> None:
    generated = diff_segment("packages/api/runtime-snapshots/graph.json", "generated")

    filtered, report = apply_diff_budget(generated)

    assert "diff --git" not in filtered
    assert report.excluded_reason == {"packages/api/runtime-snapshots/graph.json": "generated-path"}


def test_oversize_file_is_excluded() -> None:
    oversized = diff_segment("src/large.py", "x" * 80)

    filtered, report = apply_diff_budget(oversized, max_file_chars=len(oversized) - 1)

    assert filtered.startswith("# rvw: 1 files excluded")
    assert report.kept_files == []
    assert report.excluded_files == ["src/large.py"]
    assert report.excluded_reason == {"src/large.py": "oversize-file"}
    assert report.excluded_chars == len(oversized)


def test_remaining_total_over_budget_raises_with_largest_offenders() -> None:
    small = diff_segment("src/small.py", "x")
    large = diff_segment("src/large.py", "x" * 20)

    with pytest.raises(DiffBudgetExceeded) as raised:
        apply_diff_budget(
            small + large,
            max_file_chars=10_000,
            max_total_chars=len(small + large) - 1,
        )

    assert raised.value.offenders == [
        ("src/large.py", len(large)),
        ("src/small.py", len(small)),
    ]
    assert "src/large.py" in str(raised.value)
    assert str(len(large)) in str(raised.value)


def test_no_exclusions_preserves_diff_exactly() -> None:
    diff = diff_segment("src/app.py", "kept")

    filtered, report = apply_diff_budget(diff)

    assert filtered == diff
    assert report.model_dump() == {
        "kept_files": ["src/app.py"],
        "excluded_files": [],
        "excluded_reason": {},
        "kept_chars": len(diff),
        "excluded_chars": 0,
    }
