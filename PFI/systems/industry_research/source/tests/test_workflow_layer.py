from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from doctor import build_workflow_doctor


ROOT = Path(__file__).resolve().parents[1]


def test_workflow_layer_required_files_exist() -> None:
    required = [
        "AGENTS.md",
        "HANDOFF.md",
        "README.md",
        "Makefile",
        "setup.sh",
        "doctor.py",
        "docs/RunContract.md",
        "docs/CodexWorkflowLayer.md",
    ]

    for path in required:
        assert (ROOT / path).exists(), path


def test_workflow_doctor_reports_required_commands_and_files() -> None:
    payload = build_workflow_doctor("2026-06-06", root=ROOT)
    checks = {row["check_id"]: row for row in payload["checks"]}

    assert payload["audit_status"] in {"Pass", "Review"}
    assert checks["required_file:AGENTS.md"]["status"] == "pass"
    assert checks["required_file:docs/RunContract.md"]["status"] == "pass"
    assert checks["cli_command:evidence-decision-audit"]["status"] == "pass"
    assert checks["cli_command:data-trust-audit"]["status"] == "pass"


def test_doctor_json_cli_is_machine_readable() -> None:
    result = subprocess.run(
        [sys.executable, "doctor.py", "--date", "2026-06-06", "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema"] == "AIResearchCodexWorkflowDoctorV1"
    assert payload["system"] == "AI-Research-System"
    assert payload["check_count"] > 0


def test_makefile_exposes_stable_targets() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")

    for target in ["doctor:", "setup:", "audit-stack:", "test:", "test-monitoring:", "clean-cache:"]:
        assert target in text
