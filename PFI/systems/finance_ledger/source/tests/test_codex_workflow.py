from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "doctor.py"


def load_doctor_module():
    spec = importlib.util.spec_from_file_location("doctor", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load doctor.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["doctor"] = module
    spec.loader.exec_module(module)
    return module


class CodexWorkflowTests(unittest.TestCase):
    def test_doctor_current_project_has_required_workflow_files(self) -> None:
        doctor = load_doctor_module()

        checks = doctor.run_checks(require_output=False)
        status_by_name = {item.name: item.status for item in checks}

        self.assertEqual(status_by_name["file:AGENTS.md"], "ok")
        self.assertEqual(status_by_name["file:docs/codex_workflow_contract.md"], "ok")
        self.assertEqual(status_by_name["file:docs/run_contract_template.md"], "ok")
        self.assertEqual(status_by_name["file:scripts/doctor.py"], "ok")
        self.assertFalse(doctor.has_failures(checks))

    def test_doctor_detects_missing_required_workflow_file(self) -> None:
        doctor = load_doctor_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in doctor.REQUIRED_DIRS:
                (root / relative).mkdir(parents=True, exist_ok=True)
            for relative in doctor.REQUIRED_FILES:
                if relative == "AGENTS.md":
                    continue
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("placeholder", encoding="utf-8")

            checks = doctor.run_checks(root=root, db_path=root / "missing.sqlite", output_dir=root / "missing-output")
            missing = [item for item in checks if item.name == "file:AGENTS.md"]

            self.assertEqual(len(missing), 1)
            self.assertEqual(missing[0].status, "fail")
            self.assertTrue(doctor.has_failures(checks))

    def test_doctor_json_payload_contains_counts_and_checks(self) -> None:
        doctor = load_doctor_module()

        checks = [doctor.WorkflowCheck("example", "ok", "done"), doctor.WorkflowCheck("watch", "warn", "missing taskpack")]
        payload = doctor._payload(checks, Path("out"), Path("db.sqlite"))

        self.assertEqual(payload["counts"]["ok"], 1)
        self.assertEqual(payload["counts"]["warn"], 1)
        self.assertEqual(payload["counts"]["fail"], 0)
        self.assertEqual(payload["checks"][0]["name"], "example")


if __name__ == "__main__":
    unittest.main()
