from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.test_s07p1_economic_proxy import ATLASCTL_SCRIPT, REPO_ROOT, SCRIPTS_ROOT, run_json
from OpenAIDatabase.tests.test_s08p2_agent_authorization import write_authorization_fixtures


STAGE_FLIGHT_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_stage_flight.py"
STAGE_FLIGHT_CONFIG = REPO_ROOT / "机器治理" / "证据与日志" / "stage_flight_recorder_fields.v1_2_s08_p3.json"


def load_stage_flight_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_stage_flight", STAGE_FLIGHT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_stage_flight_fixtures(root: Path) -> None:
    write_authorization_fixtures(root)
    target = root / "机器治理" / "证据与日志" / "stage_flight_recorder_fields.v1_2_s08_p3.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(STAGE_FLIGHT_CONFIG, target)
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "agent-authorization",
        "--database-dir",
        str(root),
        "--apply",
    ])


class S08P3StageFlightTest(unittest.TestCase):
    def test_builds_lightweight_stage_flight_recorder(self) -> None:
        module = load_stage_flight_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_stage_flight_fixtures(root)
            output = root / "data/derived/agent_collaboration/stage_flight_recorder.json"
            result = module.build_stage_flight_recorder(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S08P3")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S08P3")
            self.assertEqual(result["status"], "phase_s08_p3_stage_flight_recorder_completed_pending_s08_review")
            self.assertFalse(output.exists())
            self.assertEqual(result["machine_output_check_summary"]["check_count"], 4)
            self.assertLessEqual(result["machine_output_check_summary"]["required_field_count"], 12)
            self.assertEqual(result["machine_output_check_summary"]["phase_record_count"], 3)
            self.assertFalse(result["machine_output_check_summary"]["bulky_human_documentation"])
            self.assertTrue(result["phase_boundary"]["lightweight_stage_flight_recorder"])
            self.assertTrue(result["phase_boundary"]["does_not_include_raw_or_transcript_payloads"])
            self.assertTrue(result["phase_boundary"]["does_not_generate_bulky_human_docs"])
            self.assertTrue(result["phase_boundary"]["records_necessary_info_in_development_records"])
            self.assertEqual(result["phase_boundary"]["next_phase"], "S08 Review")
            self.assertEqual({item["phase_id"] for item in result["phase_records"]}, {"S08 P1", "S08 P2", "S08 P3"})
            for record in result["phase_records"]:
                self.assertTrue(record["evidence_refs"])
                self.assertTrue(record["validation_refs"])
                self.assertFalse(record["boundary_flags"]["raw_mutation"])
                self.assertFalse(record["boundary_flags"]["github_main_upload"])

    def test_atlasctl_stage_flight_apply_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_stage_flight_fixtures(root)
            output = root / "data/derived/agent_collaboration/stage_flight_recorder.json"
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "stage-flight",
                "--database-dir",
                str(root),
                "--dry-run",
            ])
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertFalse(output.exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "stage-flight",
                "--database-dir",
                str(root),
                "--apply",
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S08P3")
            self.assertTrue(output.exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "stage-flight",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertEqual(audit["required_field_count"], 10)
            self.assertEqual(audit["phase_record_count"], 3)
            self.assertEqual(audit["machine_output_check_count"], 4)
            self.assertFalse(audit["bulky_human_documentation"])
            self.assertFalse(audit["raw_mutation"])
            self.assertFalse(audit["github_main_upload"])
            self.assertEqual(audit["next_phase"], "S08 Review")


if __name__ == "__main__":
    unittest.main()
