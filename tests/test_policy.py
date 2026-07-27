from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from rvw.adjudicate import AdjudicationOutcome
from rvw.discover import EnrichedFinding
from rvw.merge import CollapseGroup, MergeResult, merge
from rvw.policy import AutoPolicy, PolicyNotFound, evaluate, load_policy
from rvw.schema import Severity, Tier, Verdict

FIXTURES = Path(__file__).parent / "fixtures"


def group(key: str, severity: Severity, agreement: int) -> CollapseGroup:
    return CollapseGroup(
        key=key,
        rule_id=f"test/{key}",
        file=f"{key}.py",
        hunk_id=f"{key}.py:1",
        line=1,
        severity=severity,
        lane_ids=["test"],
        agreement=agreement,
        bodies=[key],
        anchorable=True,
        findings=[],
        priority=[0, agreement, 0, 1],
    )


def merged(*groups: CollapseGroup) -> MergeResult:
    return MergeResult(groups=list(groups), sites=[], pattern_folds=[], region_folds=[])


def outcome(
    verdicts: dict[str, Verdict], *, unresolved: list[str] | None = None
) -> AdjudicationOutcome:
    return AdjudicationOutcome(
        verdicts=verdicts,
        reasons={},
        evidence={},
        replica_votes={},
        unresolved=unresolved or [],
        coerced_rejections=0,
    )


def policy(**overrides: object) -> AutoPolicy:
    raw: dict[str, object] = {
        "promote_to_blocker": {
            "agreement_at_least": 2,
            "severity_at_least": "warning",
        },
        "drop": {"agreement_at_most": 1, "severity_at_most": "suggestion"},
        "block_when": {"severity_at_least": "blocker"},
        "publish_state": "comment",
    }
    raw.update(overrides)
    return AutoPolicy.model_validate(raw)


def test_load_policy_and_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "auto.yaml"
    path.write_text(
        """promote_to_blocker:
  agreement_at_least: 2
  severity_at_least: warning
drop:
  agreement_at_most: 1
  severity_at_most: suggestion
block_when:
  severity_at_least: blocker
publish_state: none
""",
        encoding="utf-8",
    )
    loaded = load_policy(path)
    assert loaded.publish_state == "none"
    assert loaded.block_when.confirmed_only is True
    with pytest.raises(PolicyNotFound, match=str(tmp_path / "missing.yaml")):
        load_policy(tmp_path / "missing.yaml")


def test_policy_models_forbid_extra_fields() -> None:
    with pytest.raises(ValidationError):
        policy(extra_setting=True)


def test_drop_uses_original_severity_and_agreement() -> None:
    dropped = group("dropped", Severity.SUGGESTION, 1)
    kept = group("kept", Severity.WARNING, 1)
    result = evaluate(
        policy(),
        merged(dropped, kept),
        outcome({dropped.key: Verdict.CONFIRMED, kept.key: Verdict.CONFIRMED}),
    )
    assert result.dropped == ["dropped"]
    assert result.considered == 1


def test_promote_then_block() -> None:
    promoted = group("promoted", Severity.WARNING, 2)
    result = evaluate(policy(), merged(promoted), outcome({promoted.key: Verdict.CONFIRMED}))
    assert result.promoted == ["promoted"]
    assert result.blocking == ["promoted"]
    assert result.verdict == "BLOCK"


def test_uncertain_only_blocks_when_confirmed_only_is_false() -> None:
    blocker = group("blocker", Severity.BLOCKER, 1)
    default_result = evaluate(policy(), merged(blocker), outcome({}))
    permissive_result = evaluate(
        policy(block_when={"severity_at_least": "blocker", "confirmed_only": False}),
        merged(blocker),
        outcome({blocker.key: Verdict.UNCERTAIN}),
    )
    assert default_result.verdict == "PASS"
    assert default_result.considered == 1
    assert permissive_result.blocking == ["blocker"]


def test_rejected_is_excluded_and_unresolved_is_uncertain() -> None:
    rejected = group("rejected", Severity.BLOCKER, 3)
    unresolved = group("unresolved", Severity.BLOCKER, 3)
    result = evaluate(
        policy(),
        merged(rejected, unresolved),
        outcome(
            {rejected.key: Verdict.REJECTED, unresolved.key: Verdict.CONFIRMED},
            unresolved=[unresolved.key],
        ),
    )
    assert result.verdict == "PASS"
    assert result.considered == 1
    assert result.blocking == []


def real_fixture() -> tuple[MergeResult, AdjudicationOutcome]:
    raw_findings = json.loads((FIXTURES / "smoke_1119_findings.json").read_text(encoding="utf-8"))
    findings = [EnrichedFinding.model_validate(item) for item in raw_findings]
    lane_tiers = {
        finding.lane_id: (Tier.DYNAMIC if finding.lane_id.startswith("dynamic/") else Tier.BASE)
        for finding in findings
    }
    merged_fixture = merge(findings, lane_tiers=lane_tiers)
    raw_outcome = json.loads((FIXTURES / "smoke_1119_outcome.json").read_text(encoding="utf-8"))
    adjudicated = AdjudicationOutcome(
        verdicts={key: Verdict(value) for key, value in raw_outcome["verdicts"].items()},
        reasons=raw_outcome["reasons"],
        evidence=raw_outcome["evidence"],
        replica_votes={
            key: [Verdict(value) for value in votes]
            for key, votes in raw_outcome["replica_votes"].items()
        },
        unresolved=raw_outcome["unresolved"],
        coerced_rejections=raw_outcome["coerced_rejections"],
    )
    return merged_fixture, adjudicated


def test_default_policy_on_real_1119_fixture() -> None:
    merged_fixture, adjudicated = real_fixture()
    result = evaluate(policy(), merged_fixture, adjudicated)
    assert result.verdict == "BLOCK"
    assert result.considered == 13
    assert result.dropped == []
    assert result.promoted == [
        "481b74e181cca5bab3b2e7252c300f8d526b67fd",
        "428ab652ab58581e91e63909766c63f78f14fb2b",
    ]
    assert set(result.blocking) >= {
        "293eeebae652d78e971b9285f9a8548837db9393",
        "caa45924521108ea0d13acdf359734087dd99f58",
        "0679c0ea818933a9a399e8ceb79f45e384429027",
        "7a0b9e94abd6446c02beca0f648b5877dfb2e75a",
        "411f0fa92e9569bcdb4736d14da6389757e63194",
    }


def test_outcome_none_treats_every_group_as_uncertain() -> None:
    merged_fixture, _ = real_fixture()
    result = evaluate(policy(), merged_fixture, None)
    assert result.verdict == "PASS"
    assert result.considered == 13
    assert result.blocking == []
