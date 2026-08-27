"""Domain models for policies and evidence reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Status(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    ERROR = "error"


@dataclass(frozen=True)
class CheckPolicy:
    id: str
    type: str
    required: bool = True
    description: str = ""
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Policy:
    version: int
    project: str
    checks: tuple[CheckPolicy, ...]


@dataclass(frozen=True)
class CheckResult:
    id: str
    status: Status
    required: bool
    message: str
    observed: Any = None
    expected: Any = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class EvaluationReport:
    project: str
    verdict: Status
    checks: tuple[CheckResult, ...]
    summary: dict[str, int]
    policy_version: int
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "verdict": self.verdict.value,
            "policy_version": self.policy_version,
            "provenance": self.provenance,
            "summary": self.summary,
            "checks": [result.to_dict() for result in self.checks],
        }
