from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from rvw.adjudicate import AdjudicationOutcome
from rvw.discover import EnrichedFinding, LaneCoverage
from rvw.gate import (
    DispositionDecision,
    DispositionDocument,
    DispositionRecord,
    GateAnchor,
    GateInvariantError,
    GatePlan,
    PullRequestState,
    build_gate_verdict,
    github_actor_permission,
    load_dispositions,
    load_gate_plan,
    provision_checkout,
    query_pull_request,
    render_gate_verdict,
    save_gate_plan,
    save_gate_verdict,
    validate_coverage,
    verify_pull_request,
    write_disposition_template,
)
from rvw.merge import MergeResult, merge
from rvw.report import render_report
from rvw.schema import Severity, Tier, Verdict
from rvw.target import ResolvedTarget


def target() -> ResolvedTarget:
    return ResolvedTarget(
        kind="pr",
        repo="owner/repo",
        base_sha="a" * 40,
        head_sha="b" * 40,
        changed_paths=["src/a.py", "src/b.py", "src/c.py"],
        diff="",
        pr_number=42,
    )


def merged_outcome() -> tuple[MergeResult, AdjudicationOutcome]:
    findings = [
        EnrichedFinding(
            rule_id="rule/blocker",
            file="src/a.py",
            hunk_id="src/a.py@@-1+1@@",
            line=1,
            severity=Severity.BLOCKER,
            body="blocker",
            anchorable=True,
            lane_id="lane-a",
            replica=1,
        ),
        EnrichedFinding(
            rule_id="rule/uncertain",
            file="src/b.py",
            hunk_id="src/b.py@@-1+1@@",
            line=2,
            severity=Severity.WARNING,
            body="uncertain",
            anchorable=True,
            lane_id="lane-b",
            replica=1,
        ),
        EnrichedFinding(
            rule_id="rule/rejected",
            file="src/c.py",
            hunk_id="src/c.py@@-1+1@@",
            line=3,
            severity=Severity.SUGGESTION,
            body="rejected",
            anchorable=True,
            lane_id="lane-c",
            replica=1,
        ),
    ]
    merged = merge(
        findings,
        lane_tiers={"lane-a": Tier.BASE, "lane-b": Tier.BASE, "lane-c": Tier.BASE},
    )
    by_rule = {group.rule_id: group.key for group in merged.groups}
    verdicts = {
        by_rule["rule/blocker"]: Verdict.CONFIRMED,
        by_rule["rule/uncertain"]: Verdict.UNCERTAIN,
        by_rule["rule/rejected"]: Verdict.REJECTED,
    }
    outcome = AdjudicationOutcome(
        verdicts=verdicts,
        reasons={key: verdict.value.lower() for key, verdict in verdicts.items()},
        evidence={key: "evidence" for key in verdicts},
        replica_votes={key: [verdict] * 3 for key, verdict in verdicts.items()},
        unresolved=[by_rule["rule/uncertain"]],
        coerced_rejections=0,
    )
    return merged, outcome


def complete_coverage() -> list[LaneCoverage]:
    return [
        LaneCoverage(lane_id="lane-a", dispatched=3, valid=3, findings=1),
        LaneCoverage(lane_id="lane-b", dispatched=3, valid=3, findings=1),
        LaneCoverage(lane_id="lane-c", dispatched=3, valid=3, findings=1),
    ]


def dispositions(merged: MergeResult) -> DispositionDocument:
    by_rule = {group.rule_id: group.key for group in merged.groups}
    return DispositionDocument(
        schema_version=1,
        dispositions=[
            DispositionRecord(
                finding_id=by_rule["rule/blocker"],
                decision=DispositionDecision.ACCEPTED,
                reason="owner accepts this release risk",
            ),
            DispositionRecord(
                finding_id=by_rule["rule/uncertain"],
                decision=DispositionDecision.ACCEPTED,
                reason="risk reviewed",
            ),
        ],
    )


def test_report_exposes_group_key_as_public_finding_id() -> None:
    merged, outcome = merged_outcome()
    report = render_report(
        target=target(),
        merged=merged,
        outcome=outcome,
        coverage=complete_coverage(),
        budget=None,
        synthesis=None,
    )

    for group in merged.groups:
        assert f"Finding ID: `{group.key}`" in report


@pytest.mark.parametrize(
    "coverage,match",
    [
        ([], "nonempty"),
        ([LaneCoverage(lane_id="lane-a", dispatched=0, valid=0, findings=0)], "dispatched"),
        ([LaneCoverage(lane_id="lane-a", dispatched=3, valid=2, findings=0)], "valid"),
        (
            [
                LaneCoverage(lane_id="lane-a", dispatched=3, valid=3, findings=0),
                LaneCoverage(lane_id="lane-a", dispatched=3, valid=3, findings=0),
            ],
            "duplicate",
        ),
    ],
)
def test_coverage_rejects_vacuous_invalid_and_duplicate_rows(
    coverage: list[LaneCoverage], match: str
) -> None:
    with pytest.raises(GateInvariantError, match=match):
        validate_coverage(["lane-a"], coverage, replicas=3)


def test_coverage_requires_exact_planned_lane_set() -> None:
    coverage = [LaneCoverage(lane_id="lane-a", dispatched=3, valid=3, findings=0)]

    with pytest.raises(GateInvariantError, match=r"missing.*lane-b"):
        validate_coverage(["lane-a", "lane-b"], coverage, replicas=3)

    with pytest.raises(GateInvariantError, match=r"unexpected.*lane-a"):
        validate_coverage([], coverage, replicas=3)


def test_dispositions_reject_duplicate_omitted_unknown_and_rejected_ids() -> None:
    merged, outcome = merged_outcome()
    by_rule = {group.rule_id: group.key for group in merged.groups}
    duplicate = DispositionDocument(
        schema_version=1,
        dispositions=[
            DispositionRecord(
                finding_id=by_rule["rule/blocker"],
                decision=DispositionDecision.MUST_FIX,
                reason="fix",
            ),
            DispositionRecord(
                finding_id=by_rule["rule/blocker"],
                decision=DispositionDecision.MUST_FIX,
                reason="duplicate",
            ),
        ],
    )

    with pytest.raises(GateInvariantError, match="duplicate"):
        build_gate_verdict(
            run_id="run-1",
            target=target(),
            coverage=complete_coverage(),
            merged=merged,
            outcome=outcome,
            dispositions=duplicate,
        )

    for bad_id, match in [
        ("f" * 40, "unknown"),
        (by_rule["rule/rejected"], "unknown"),
    ]:
        document = DispositionDocument(
            schema_version=1,
            dispositions=[
                *dispositions(merged).dispositions,
                DispositionRecord(
                    finding_id=bad_id,
                    decision=DispositionDecision.MUST_FIX,
                    reason="not actionable",
                ),
            ],
        )
        with pytest.raises(GateInvariantError, match=match):
            build_gate_verdict(
                run_id="run-1",
                target=target(),
                coverage=complete_coverage(),
                merged=merged,
                outcome=outcome,
                dispositions=document,
                actor="owner",
                actor_permission="admin",
            )


def test_dispositions_require_nonblank_reason_and_strict_shape(tmp_path: Path) -> None:
    path = tmp_path / "dispositions.yaml"
    path.write_text(
        "schema_version: 1\ndispositions:\n  - finding_id: abc\n    decision: accepted\n"
        "    reason: '   '\n    forged: true\n",
        encoding="utf-8",
    )

    with pytest.raises((ValidationError, ValueError)):
        load_dispositions(path)


def test_owner_only_blocker_acceptance_and_must_fix_verdict() -> None:
    merged, outcome = merged_outcome()
    document = dispositions(merged)

    with pytest.raises(GateInvariantError, match="admin"):
        build_gate_verdict(
            run_id="run-1",
            target=target(),
            coverage=complete_coverage(),
            merged=merged,
            outcome=outcome,
            dispositions=document,
            actor="contributor",
            actor_permission="write",
        )

    accepted = build_gate_verdict(
        run_id="run-1",
        target=target(),
        coverage=complete_coverage(),
        merged=merged,
        outcome=outcome,
        dispositions=document,
        actor="repo-owner",
        actor_permission="admin",
    )
    assert accepted.verdict == "PASS"
    assert accepted.actor == "repo-owner"

    document.dispositions[0].decision = DispositionDecision.MUST_FIX
    blocked = build_gate_verdict(
        run_id="run-1",
        target=target(),
        coverage=complete_coverage(),
        merged=merged,
        outcome=outcome,
        dispositions=document,
    )
    assert blocked.verdict == "BLOCK"
    assert blocked.actor is None


def test_gate_artifacts_are_reconstructable_and_template_uses_public_ids(
    tmp_path: Path,
) -> None:
    merged, outcome = merged_outcome()
    document = dispositions(merged)
    verdict = build_gate_verdict(
        run_id="run-1",
        target=target(),
        coverage=complete_coverage(),
        merged=merged,
        outcome=outcome,
        dispositions=document,
        actor="repo-owner",
        actor_permission="admin",
    )

    markdown = render_gate_verdict(verdict)
    json_path, md_path = save_gate_verdict(tmp_path, verdict)
    template_path = write_disposition_template(tmp_path, merged, outcome)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-1"
    assert payload["anchor"] == {"base_sha": "a" * 40, "head_sha": "b" * 40}
    assert payload["counts"] == {"CONFIRMED": 1, "REJECTED": 1, "UNCERTAIN": 1}
    assert len(payload["coverage"]) == 3
    assert {item["finding_id"] for item in payload["findings"]} == {
        record.finding_id for record in document.dispositions
    }
    assert "| Finding ID | Severity | Verdict | Disposition | Reason |" in markdown
    assert md_path.read_text(encoding="utf-8") == markdown
    template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    assert {item["finding_id"] for item in template["dispositions"]} == {
        record.finding_id for record in document.dispositions
    }
    assert {item["reason"] for item in template["dispositions"]} == {""}
    with pytest.raises(ValidationError, match="nonblank"):
        load_dispositions(template_path)


def test_disposition_template_does_not_include_rejected_findings(tmp_path: Path) -> None:
    merged, outcome = merged_outcome()
    template_path = write_disposition_template(tmp_path, merged, outcome)
    template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    by_rule = {group.rule_id: group.key for group in merged.groups}

    assert by_rule["rule/rejected"] not in {item["finding_id"] for item in template["dispositions"]}


def test_provision_checkout_clones_detaches_and_verifies_head_and_clean(tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> str:
        commands.append(command)
        if command[-2:] == ["rev-parse", "HEAD"]:
            return f"{'b' * 40}\n"
        return ""

    checkout = provision_checkout(
        repo="owner/repo",
        pr_number=42,
        head_sha="b" * 40,
        destination=tmp_path / "checkout",
        run=fake_run,
    )

    assert checkout == tmp_path / "checkout"
    assert commands == [
        ["gh", "repo", "clone", "owner/repo", str(checkout), "--", "--no-checkout"],
        [
            "git",
            "-C",
            str(checkout),
            "fetch",
            "--no-tags",
            "origin",
            "refs/pull/42/head",
        ],
        ["git", "-C", str(checkout), "checkout", "--detach", "b" * 40],
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        ["git", "-C", str(checkout), "status", "--porcelain=v1", "--untracked-files=all"],
    ]


@pytest.mark.parametrize(
    ("head", "status", "match"), [("c" * 40, "", "HEAD"), ("b" * 40, "?? x", "clean")]
)
def test_provision_checkout_fails_on_wrong_head_or_dirty_tree(
    tmp_path: Path, head: str, status: str, match: str
) -> None:
    def fake_run(command: list[str]) -> str:
        if command[-2:] == ["rev-parse", "HEAD"]:
            return head
        if "status" in command:
            return status
        return ""

    with pytest.raises(GateInvariantError, match=match):
        provision_checkout(
            repo="owner/repo",
            pr_number=42,
            head_sha="b" * 40,
            destination=tmp_path / "checkout",
            run=fake_run,
        )


def test_gate_anchor_is_strict() -> None:
    anchor = GateAnchor(base_sha="a" * 40, head_sha="b" * 40)
    assert anchor.model_dump() == {"base_sha": "a" * 40, "head_sha": "b" * 40}
    with pytest.raises(ValidationError):
        GateAnchor(base_sha="short", head_sha="b" * 40)


def test_gate_plan_round_trip_is_strict(tmp_path: Path) -> None:
    plan = GatePlan(schema_version=1, lane_ids=["lane-a", "lane-b"], replicas=3)
    path = save_gate_plan(tmp_path, plan)

    assert load_gate_plan(tmp_path) == plan
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["extra"] = True
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_gate_plan(tmp_path)


def test_pull_request_requery_and_actor_permission_commands() -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> str:
        commands.append(command)
        if command[:3] == ["gh", "api", "user"]:
            return "repo-owner\n"
        if "collaborators" in command[2]:
            return "admin\n"
        return json.dumps(
            {
                "base": {"sha": "a" * 40},
                "head": {"sha": "b" * 40},
                "state": "open",
                "merged": False,
            }
        )

    state = query_pull_request("owner/repo", 42, run=fake_run)
    actor, permission = github_actor_permission("owner/repo", run=fake_run)

    assert state == PullRequestState(
        base_sha="a" * 40,
        head_sha="b" * 40,
        state="open",
        merged=False,
    )
    assert (actor, permission) == ("repo-owner", "admin")
    assert commands == [
        ["gh", "api", "repos/owner/repo/pulls/42"],
        ["gh", "api", "user", "--jq", ".login"],
        [
            "gh",
            "api",
            "repos/owner/repo/collaborators/repo-owner/permission",
            "--jq",
            ".permission",
        ],
    ]


def test_pull_request_requery_rejects_malformed_api_data() -> None:
    with pytest.raises(ValueError, match="invalid pull-request state"):
        query_pull_request("owner/repo", 42, run=lambda command: "{}")


@pytest.mark.parametrize(
    "state,match",
    [
        (
            PullRequestState(base_sha="a" * 40, head_sha="c" * 40, state="open", merged=False),
            "stale",
        ),
        (
            PullRequestState(base_sha="c" * 40, head_sha="b" * 40, state="open", merged=False),
            "stale",
        ),
        (
            PullRequestState(base_sha="a" * 40, head_sha="b" * 40, state="closed", merged=True),
            "open and unmerged",
        ),
    ],
)
def test_pull_request_verification_fails_closed(state: PullRequestState, match: str) -> None:
    with pytest.raises(GateInvariantError, match=match):
        verify_pull_request(GateAnchor(base_sha="a" * 40, head_sha="b" * 40), state)
