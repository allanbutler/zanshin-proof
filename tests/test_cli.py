import json
from pathlib import Path

from zanshin_proof.cli import main


def test_cli_writes_report(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yml"
    evidence = tmp_path / "evidence.json"
    output = tmp_path / "report.json"
    policy.write_text(
        """version: 1
project: demo
checks:
  - id: ready
    type: boolean
    path: facts.ready
""",
        encoding="utf-8",
    )
    evidence.write_text(
        json.dumps(
            {
                "provenance": {
                    "commit_sha": "521134ee3e9602a0e04843e2f5d1f60909df3173",
                    "collected_at": "2026-08-26T23:45:00Z",
                    "collector": {"name": "pytest", "version": "1"},
                    "model": {"name": "demo", "version": "candidate"},
                    "run": {"system": "pytest", "id": "run-1"},
                    "sources": [
                        {"type": "file", "uri": "file://evidence.json", "version": "1"}
                    ],
                },
                "facts": {"ready": True},
                "metrics": {},
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        ["evaluate", "--policy", str(policy), "--evidence", str(evidence), "--output", str(output)]
    )

    assert exit_code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["verdict"] == "pass"
    assert report["provenance"]["commit_sha"].startswith("521134e")
