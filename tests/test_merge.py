from __future__ import annotations

import hashlib
import json
from pathlib import Path

from rvw.discover import EnrichedFinding
from rvw.merge import merge
from rvw.schema import Severity, Tier

FIXTURE = Path(__file__).parent / "fixtures" / "smoke_1119_findings.json"
SMOKE_TIERS = {
    "slop-hygiene": Tier.BASE,
    "test-ci-integrity": Tier.BASE,
    "unscoped-sweep": Tier.BASE,
    "dynamic/edge-cases": Tier.DYNAMIC,
}


def finding(
    *,
    rule_id: str = "lane/rule",
    file: str = "src/app.py",
    hunk_id: str = "src/app.py@@-1,1+1,1@@",
    line: int | None = 1,
    severity: Severity = Severity.WARNING,
    body: str = "body",
    lane_id: str = "lane",
    replica: int = 1,
    anchorable: bool = True,
) -> EnrichedFinding:
    return EnrichedFinding(
        rule_id=rule_id,
        file=file,
        hunk_id=hunk_id,
        line=line,
        severity=severity,
        body=body,
        anchorable=anchorable,
        lane_id=lane_id,
        replica=replica,
    )


def smoke_findings() -> list[EnrichedFinding]:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return [EnrichedFinding.model_validate(item) for item in raw]


def key(file: str, hunk_id: str, rule_id: str) -> str:
    return hashlib.sha1(f"{file}:{hunk_id}:{rule_id}".encode()).hexdigest()


def test_collapse_counts_distinct_replicas_and_deduplicates_bodies_in_order() -> None:
    findings = [
        finding(replica=1, body="first"),
        finding(replica=1, body="first"),
        finding(replica=1, body="second"),
        finding(replica=2, body="second"),
        finding(replica=3, body="third"),
    ]

    result = merge(findings, lane_tiers={"lane": Tier.BASE})

    assert len(result.groups) == 1
    group = result.groups[0]
    assert group.agreement == 3
    assert group.bodies == ["first", "second", "third"]
    assert group.findings == findings
    assert group.key == key(group.file, group.hunk_id, group.rule_id)


def test_collapse_uses_max_severity_and_any_anchorable() -> None:
    result = merge(
        [
            finding(severity=Severity.SUGGESTION, anchorable=False),
            finding(severity=Severity.BLOCKER, anchorable=True, replica=2),
            finding(severity=Severity.WARNING, anchorable=False, replica=3),
        ],
        lane_tiers={"lane": Tier.BASE},
    )

    assert result.groups[0].severity is Severity.BLOCKER
    assert result.groups[0].anchorable is True


def test_site_cross_layer_requires_distinct_tiers() -> None:
    hunk_id = "src/app.py@@-1,1+1,2@@"
    findings = [
        finding(rule_id="base/rule", hunk_id=hunk_id, lane_id="base"),
        finding(rule_id="dynamic/rule", hunk_id=hunk_id, lane_id="dynamic"),
    ]

    cross_layer = merge(
        findings,
        lane_tiers={"base": Tier.BASE, "dynamic": Tier.DYNAMIC},
    ).sites[0]
    same_layer = merge(
        findings,
        lane_tiers={"base": Tier.BASE, "dynamic": Tier.BASE},
    ).sites[0]

    assert cross_layer.lanes == ["base", "dynamic"]
    assert cross_layer.corroboration == 2
    assert cross_layer.cross_layer is True
    assert same_layer.cross_layer is False


def test_smoke_pattern_folds_match_measured_fixture_clusters() -> None:
    result = merge(smoke_findings(), lane_tiers=SMOKE_TIERS)

    assert sorted((fold.rule_id, fold.repetition) for fold in result.pattern_folds) == [
        ("slop/sot-violation", 4),
        ("test-ci/critical-flaw", 2),
    ]

    fold = next(fold for fold in result.pattern_folds if fold.rule_id == "slop/sot-violation")
    groups = {group.key: group for group in result.groups}
    assert len({groups[group_key].file for group_key in fold.group_keys}) == 4
    assert fold.shared_identifiers == ["errorCodes"]

    catchtable = next(
        fold for fold in result.pattern_folds if fold.rule_id == "test-ci/critical-flaw"
    )
    assert catchtable.shared_identifiers == ["retry"]
    assert not any(
        "proxy_connect_failed" in fold.shared_identifiers for fold in result.pattern_folds
    )


def test_pattern_fold_never_repeats_a_file() -> None:
    findings = [
        finding(
            rule_id="repeat/rule",
            file="a.py",
            hunk_id="a.py@@-1,1+1,1@@",
            body="First `shared`.",
        ),
        finding(
            rule_id="repeat/rule",
            file="b.py",
            hunk_id="b.py@@-1,1+1,1@@",
            body="Bridge `shared` and `other`.",
        ),
        finding(
            rule_id="repeat/rule",
            file="a.py",
            hunk_id="a.py@@-10,1+10,1@@",
            line=10,
            body="Second `other`.",
        ),
    ]

    result = merge(findings, lane_tiers={"lane": Tier.BASE})
    groups = {group.key: group for group in result.groups}

    assert result.pattern_folds
    assert all(
        len({groups[group_key].file for group_key in fold.group_keys}) == len(fold.group_keys)
        for fold in result.pattern_folds
    )


def test_smoke_region_folds_are_line_bounded_and_transitive() -> None:
    result = merge(smoke_findings(), lane_tiers=SMOKE_TIERS)
    groups = {group.key: group for group in result.groups}
    regions = [
        [groups[group_key] for group_key in fold.group_keys]
        for fold in result.region_folds
        if fold.file == "providers/naver-map/index.ts"
    ]

    near_1700 = next(
        region for region in regions if {group.line for group in region} == {1721, 1722, 1733}
    )
    near_2100 = next(
        region for region in regions if {group.line for group in region} == {2124, 2127}
    )
    assert near_1700
    assert near_2100
    assert not any(
        1733 in {group.line for group in region} and 2124 in {group.line for group in region}
        for region in regions
    )


def test_pattern_and_region_edges_never_form_smoke_mega_cluster() -> None:
    result = merge(smoke_findings(), lane_tiers=SMOKE_TIERS)

    assert max(len(fold.group_keys) for fold in result.pattern_folds) == 4
    assert max(len(fold.group_keys) for fold in result.region_folds) == 3
    assert all(
        len(
            {
                result_group.rule_id
                for result_group in result.groups
                if result_group.key in fold.group_keys
            }
        )
        == 1
        for fold in result.pattern_folds
    )
    assert not any(
        len(fold.group_keys) >= 8 for fold in [*result.pattern_folds, *result.region_folds]
    )


def test_groups_without_lines_do_not_join_region_folds() -> None:
    result = merge(
        [
            finding(rule_id="lane/a", line=None),
            finding(rule_id="lane/b", line=None),
            finding(rule_id="lane/c", line=10),
            finding(rule_id="lane/d", line=20),
        ],
        lane_tiers={"lane": Tier.BASE},
    )

    assert len(result.region_folds) == 1
    region_keys = set(result.region_folds[0].group_keys)
    assert all(group.key not in region_keys for group in result.groups if group.line is None)


def test_smoke_priority_starts_with_cross_layer_site_then_agreement() -> None:
    result = merge(smoke_findings(), lane_tiers=SMOKE_TIERS)
    hunk_id = "providers/naver-map/index.ts@@-2097,7+2124,7@@"

    assert [group.key for group in result.groups[:2]] == [
        key("providers/naver-map/index.ts", hunk_id, "dynamic/unhandled-edge"),
        key("providers/naver-map/index.ts", hunk_id, "unscoped/correctness"),
    ]
    assert result.groups[0].priority == [1, 3, 1, 2]
    assert result.groups[1].priority == [1, 1, 1, 2]
    assert result.groups[2].agreement == 3


def test_priority_uses_repetition_then_severity_after_agreement() -> None:
    findings = [
        finding(
            rule_id="repeat/rule",
            file="a.py",
            hunk_id="a.py@@-1,1+1,1@@",
            body="Uses `shared`.",
        ),
        finding(
            rule_id="repeat/rule",
            file="b.py",
            hunk_id="b.py@@-1,1+1,1@@",
            body="Also `shared`.",
        ),
        finding(
            rule_id="solo/rule",
            file="c.py",
            hunk_id="c.py@@-1,1+1,1@@",
            severity=Severity.BLOCKER,
        ),
    ]

    result = merge(findings, lane_tiers={"lane": Tier.BASE})

    assert [group.rule_id for group in result.groups] == [
        "repeat/rule",
        "repeat/rule",
        "solo/rule",
    ]
