import pytest

from zanshin_proof.evaluator import EvidenceError, evaluate
from zanshin_proof.models import CheckPolicy, Policy, Status


def policy(*checks: CheckPolicy) -> Policy:
    return Policy(version=1, project="recommendation", checks=checks)


def evidence(
    *, facts: dict | None = None, metrics: dict | None = None
) -> dict:
    return {
        "provenance": {
            "commit_sha": "521134ee3e9602a0e04843e2f5d1f60909df3173",
            "collected_at": "2026-08-26T23:45:00Z",
            "collector": {"name": "pytest", "version": "1"},
            "model": {"name": "recommendation", "version": "candidate"},
            "run": {"system": "mlflow", "id": "run-42"},
            "sources": [
                {"type": "table", "uri": "table://recommendation", "version": "42"}
            ],
        },
        "facts": facts or {},
        "metrics": metrics or {},
    }


def test_required_failure_blocks_release() -> None:
    gate = policy(
        CheckPolicy(
            id="auc",
            type="metric_regression",
            config={
                "candidate": "metrics.candidate.auc",
                "baseline": "metrics.baseline.auc",
                "tolerance": 0.005,
            },
        )
    )

    report = evaluate(
        gate,
        evidence(metrics={"candidate": {"auc": 0.80}, "baseline": {"auc": 0.82}}),
    )

    assert report.verdict == Status.FAIL
    assert report.checks[0].status == Status.FAIL


def test_optional_failure_warns_without_blocking() -> None:
    gate = policy(
        CheckPolicy(
            id="diversity",
            type="min_value",
            required=False,
            config={"path": "metrics.candidate.diversity", "minimum": 0.7},
        )
    )

    report = evaluate(gate, evidence(metrics={"candidate": {"diversity": 0.6}}))

    assert report.verdict == Status.WARN
    assert report.checks[0].status == Status.WARN


def test_missing_required_evidence_is_an_error_and_blocks() -> None:
    gate = policy(
        CheckPolicy(id="schema", type="boolean", config={"path": "facts.schema_compatible"})
    )

    report = evaluate(gate, evidence())

    assert report.verdict == Status.FAIL
    assert report.checks[0].status == Status.ERROR


def test_all_checks_pass() -> None:
    gate = policy(
        CheckPolicy(id="schema", type="boolean", config={"path": "facts.schema_compatible"}),
        CheckPolicy(
            id="ece",
            type="max_value",
            config={"path": "metrics.candidate.ece", "maximum": 0.03},
        ),
    )

    report = evaluate(
        gate,
        evidence(
            facts={"schema_compatible": True},
            metrics={"candidate": {"ece": 0.02}},
        ),
    )

    assert report.verdict == Status.PASS
    assert report.summary["pass"] == 2
    assert report.provenance["run"]["id"] == "run-42"


def test_missing_provenance_is_rejected_before_checks_run() -> None:
    gate = policy(
        CheckPolicy(id="schema", type="boolean", config={"path": "facts.schema_compatible"})
    )

    with pytest.raises(EvidenceError, match="provenance"):
        evaluate(gate, {"facts": {"schema_compatible": True}, "metrics": {}})


def test_report_retains_an_independent_provenance_snapshot() -> None:
    gate = policy(CheckPolicy(id="ready", type="boolean", config={"path": "facts.ready"}))
    document = evidence(facts={"ready": True})

    report = evaluate(gate, document)
    document["provenance"]["run"]["id"] = "mutated-after-evaluation"

    assert report.provenance["run"]["id"] == "run-42"
