from pathlib import Path

import pytest

from zanshin_proof.policy import PolicyError, load_policy


def test_loads_policy(tmp_path: Path) -> None:
    path = tmp_path / "policy.yml"
    path.write_text(
        """version: 1
project: demo
checks:
  - id: compatible
    type: boolean
    path: facts.compatible
""",
        encoding="utf-8",
    )

    policy = load_policy(path)

    assert policy.project == "demo"
    assert policy.checks[0].required is True


def test_rejects_duplicate_check_ids(tmp_path: Path) -> None:
    path = tmp_path / "policy.yml"
    path.write_text(
        """version: 1
project: demo
checks:
  - {id: same, type: boolean, path: a}
  - {id: same, type: boolean, path: b}
""",
        encoding="utf-8",
    )

    with pytest.raises(PolicyError, match="duplicate check id"):
        load_policy(path)


def test_schema_rejects_check_without_required_configuration(tmp_path: Path) -> None:
    path = tmp_path / "policy.yml"
    path.write_text(
        """version: 1
project: demo
checks:
  - id: incomplete
    type: max_value
    path: metrics.candidate.ece
""",
        encoding="utf-8",
    )

    with pytest.raises(PolicyError, match="policy schema violation"):
        load_policy(path)
