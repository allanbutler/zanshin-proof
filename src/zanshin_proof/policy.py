"""Policy loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from zanshin_proof.models import CheckPolicy, Policy
from zanshin_proof.schema import DocumentValidationError, validate_document


class PolicyError(ValueError):
    """Raised when a policy cannot be safely interpreted."""


SUPPORTED_CHECKS = {"boolean", "metric_regression", "max_value", "min_value"}


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyError(f"{label} must be a mapping")
    return value


def load_policy(path: str | Path) -> Policy:
    source = Path(path)
    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PolicyError(f"Could not load policy {source}: {exc}") from exc

    document = _require_mapping(raw, "policy")
    try:
        validate_document(document, "policy")
    except DocumentValidationError as exc:
        raise PolicyError(str(exc)) from exc
    version = document.get("version")
    project = document.get("project")
    raw_checks = document.get("checks")

    if version != 1:
        raise PolicyError("policy version must be 1")
    if not isinstance(project, str) or not project.strip():
        raise PolicyError("project must be a non-empty string")
    if not isinstance(raw_checks, list) or not raw_checks:
        raise PolicyError("checks must be a non-empty list")

    checks: list[CheckPolicy] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_checks):
        check = _require_mapping(item, f"checks[{index}]")
        check_id = check.get("id")
        check_type = check.get("type")
        if not isinstance(check_id, str) or not check_id.strip():
            raise PolicyError(f"checks[{index}].id must be a non-empty string")
        if check_id in seen:
            raise PolicyError(f"duplicate check id: {check_id}")
        if check_type not in SUPPORTED_CHECKS:
            raise PolicyError(f"unsupported check type for {check_id}: {check_type}")
        required = check.get("required", True)
        if not isinstance(required, bool):
            raise PolicyError(f"{check_id}.required must be a boolean")

        config = {
            key: value
            for key, value in check.items()
            if key not in {"id", "type", "required", "description"}
        }
        checks.append(
            CheckPolicy(
                id=check_id,
                type=check_type,
                required=required,
                description=str(check.get("description", "")),
                config=config,
            )
        )
        seen.add(check_id)

    return Policy(version=version, project=project.strip(), checks=tuple(checks))
