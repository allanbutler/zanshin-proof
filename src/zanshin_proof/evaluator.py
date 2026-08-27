"""Deterministic evaluation of evidence against a Zanshin policy."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from zanshin_proof.models import CheckPolicy, CheckResult, EvaluationReport, Policy, Status
from zanshin_proof.schema import DocumentValidationError, validate_document


class EvidenceError(ValueError):
    """Raised for an invalid evidence document."""


def _resolve(document: Mapping[str, Any], path: str) -> Any:
    value: Any = document
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise EvidenceError(f"missing evidence path: {path}")
        value = value[part]
    return value


def _number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceError(f"evidence at {path} must be numeric")
    return float(value)


def _result(
    check: CheckPolicy,
    passed: bool,
    message: str,
    observed: Any,
    expected: Any,
) -> CheckResult:
    status = Status.PASS if passed else (Status.FAIL if check.required else Status.WARN)
    return CheckResult(check.id, status, check.required, message, observed, expected)


def _evaluate_check(check: CheckPolicy, evidence: Mapping[str, Any]) -> CheckResult:
    config = check.config
    if check.type == "boolean":
        path = str(config.get("path", ""))
        expected = config.get("equals", True)
        if not isinstance(expected, bool):
            raise EvidenceError(f"{check.id}.equals must be a boolean")
        observed = _resolve(evidence, path)
        if not isinstance(observed, bool):
            raise EvidenceError(f"evidence at {path} must be a boolean")
        return _result(
            check,
            observed is expected,
            f"{path} is {observed}; expected {expected}",
            observed,
            expected,
        )

    if check.type == "metric_regression":
        candidate_path = str(config.get("candidate", ""))
        baseline_path = str(config.get("baseline", ""))
        tolerance = _number(config.get("tolerance", 0), f"{check.id}.tolerance")
        candidate = _number(_resolve(evidence, candidate_path), candidate_path)
        baseline = _number(_resolve(evidence, baseline_path), baseline_path)
        floor = baseline - tolerance
        return _result(
            check,
            candidate >= floor,
            f"candidate {candidate:g}; minimum allowed {floor:g}",
            candidate,
            {"baseline": baseline, "tolerance": tolerance, "minimum": floor},
        )

    path = str(config.get("path", ""))
    observed = _number(_resolve(evidence, path), path)
    threshold_key = "maximum" if check.type == "max_value" else "minimum"
    threshold = _number(config.get(threshold_key), f"{check.id}.{threshold_key}")
    passed = observed <= threshold if check.type == "max_value" else observed >= threshold
    operator = "<=" if check.type == "max_value" else ">="
    return _result(
        check,
        passed,
        f"{path} is {observed:g}; expected {operator} {threshold:g}",
        observed,
        {threshold_key: threshold},
    )


def evaluate(policy: Policy, evidence: Mapping[str, Any]) -> EvaluationReport:
    if not isinstance(evidence, Mapping):
        raise EvidenceError("evidence must be a mapping")
    try:
        validate_document(evidence, "evidence")
    except DocumentValidationError as exc:
        raise EvidenceError(str(exc)) from exc

    results: list[CheckResult] = []
    for check in policy.checks:
        try:
            results.append(_evaluate_check(check, evidence))
        except (EvidenceError, TypeError, ValueError) as exc:
            results.append(
                CheckResult(
                    id=check.id,
                    status=Status.ERROR,
                    required=check.required,
                    message=str(exc),
                )
            )

    required_blocker = any(
        result.required and result.status in {Status.FAIL, Status.ERROR} for result in results
    )
    warning = any(result.status in {Status.WARN, Status.ERROR} for result in results)
    verdict = Status.FAIL if required_blocker else (Status.WARN if warning else Status.PASS)
    summary = {
        status.value: sum(result.status == status for result in results) for status in Status
    }
    return EvaluationReport(
        project=policy.project,
        verdict=verdict,
        checks=tuple(results),
        summary=summary,
        policy_version=policy.version,
        provenance=deepcopy(evidence["provenance"]),
    )
