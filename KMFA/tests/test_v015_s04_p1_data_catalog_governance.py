from __future__ import annotations

import csv
import json
import re
import unittest
from pathlib import Path

from KMFA.tools import build_v015_s04_p1_data_catalog as builder
from KMFA.tools import v015_s04_p1_data_catalog as catalog


class V015S04P1DataCatalogGovernanceTests(unittest.TestCase):
    def test_static_outputs_match_deterministic_builder(self) -> None:
        self.assertEqual(builder.check_outputs(), [])

    def test_manifest_keeps_stage_and_later_work_closed(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        final = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(manifest["phase_execution_status"], "EXECUTION_COMPLETE")
        self.assertIn(manifest["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(manifest["evidence_validation_status"], "PASS" if final else "PENDING")
        self.assertEqual(manifest["stage_lifecycle_status"], "IN_PROGRESS")
        self.assertEqual(manifest["stage_acceptance_status"], "PENDING")
        self.assertEqual(manifest["stage_execution_percentage"], 33)
        self.assertEqual(manifest["decision"], "CONTINUE_TO_S04_P2_ONLY" if final else "REMAIN_IN_S04_P1")
        self.assertEqual(manifest["s04_p2_entry_allowed"], final)
        self.assertFalse(manifest["s04_p2_started"])
        self.assertFalse(manifest["s04_p3_entry_allowed"])
        self.assertFalse(manifest["s04_stage_review_entry_allowed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])
        self.assertEqual(manifest["raw_root_access_count"], 0)

    def test_task_matrix_covers_exact_three_roadmap_tasks(self) -> None:
        path = builder.MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
        tasks = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual([row["task_id"] for row in tasks], ["S04P1T01", "S04P1T02", "S04P1T03"])
        self.assertTrue(all(row["execution_status"] == "EXECUTION_COMPLETE" for row in tasks))
        self.assertTrue(all(row["acceptance_status"] == "PASSED" for row in tasks))
        self.assertTrue(all(row["evidence_refs"] for row in tasks))

    def test_protocol_outputs_have_exact_counts_and_fail_closed_gates(self) -> None:
        coverage = json.loads(
            (builder.MACHINE_ROOT / "catalog_coverage_verification_public_safe.json").read_text(encoding="utf-8")
        )
        status = json.loads(
            (builder.MACHINE_ROOT / "status_machine_verification_public_safe.json").read_text(encoding="utf-8")
        )
        imports = json.loads(
            (builder.MACHINE_ROOT / "import_registration_verification_public_safe.json").read_text(encoding="utf-8")
        )
        self.assertEqual((coverage["catalog_record_count"], coverage["source_system_count"], coverage["hierarchy_level_count"]), (21, 7, 9))
        self.assertFalse(coverage["formal_report_allowed"])
        self.assertEqual(status["status_count"], 5)
        self.assertTrue(status["frontend_direct_transition_blocked"])
        self.assertEqual(imports["required_field_count"], 6)
        self.assertTrue(imports["exact_replay_idempotent"])
        self.assertTrue(imports["duplicate_file_new_parser_detected"])
        self.assertTrue(imports["different_file_version_coexists"])
        self.assertTrue(imports["missing_source_quarantined"])
        self.assertTrue(imports["missing_hash_quarantined"])

    def test_public_outputs_have_no_local_path_or_private_digest_value(self) -> None:
        paths = list((builder.PROJECT_ROOT / "metadata/catalog").glob("v015_s04_p1_*.json"))
        paths.extend(
            path
            for path in builder.OUTPUT_ROOT.rglob("*")
            if path != builder.VALIDATION_RESULTS_PATH
        )
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in paths
            if path.is_file()
        )
        self.assertNotIn("/" + "Users" + "/", combined)
        self.assertNotIn("/Volumes/", combined)
        self.assertIsNone(re.search(r"sha256:[a-f0-9]{64}", combined))
        self.assertNotIn(".xlsx", combined)
        self.assertNotIn(".xls", combined)

    def test_parameter_registry_has_exact_new_range_and_column_count(self) -> None:
        path = builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row["parameter_id"] in {f"PARAM-KMFA-{value}" for value in range(1884, 1892)}]
        self.assertEqual([row["parameter_id"] for row in selected], [f"PARAM-KMFA-{value}" for value in range(1884, 1892)])
        self.assertTrue(all(row["formula_id"] == "FORM-KMFA-V015-S04-P1-DATA-CATALOG-001" for row in selected))
        self.assertEqual([row["active_value"] for row in selected], ["21", "7", "9", "5", "6", "2", "2", "0"])

    def test_formula_model_and_human_governance_are_synchronized(self) -> None:
        required = (
            "docs/governance/model_registry.yaml",
            "docs/governance/formula_registry.yaml",
            "docs/governance/project.yaml",
            "docs/governance/roadmap.yaml",
            "metadata/project/project.yaml",
            "AGENTS.md",
            "README.md",
            "功能清单.md",
            "开发记录.md",
            "模型参数文件.md",
            "HANDOFF.md",
        )
        for relative in required:
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(catalog.RUN_PHASE_ID, text, msg=relative)
        formula = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S04-P1-DATA-CATALOG-001", formula)
        self.assertIn("PARAM-KMFA-1884", (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8"))

    def test_append_only_status_and_event_records_current_state(self) -> None:
        status = json.loads((builder.PROJECT_ROOT / "metadata/stage_status.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        event = json.loads((builder.PROJECT_ROOT / "docs/governance/events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        final = status["phase_acceptance_status"] == "PASSED"
        self.assertEqual(status["phase_id"], catalog.RUN_PHASE_ID)
        self.assertEqual(event["phase_id"], catalog.RUN_PHASE_ID)
        self.assertIn(status["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual(event["phase_acceptance_status"], status["phase_acceptance_status"])
        self.assertEqual(status["raw_root_access_count"], 0)
        self.assertEqual(event["s04_p2_entry_allowed"], final)


if __name__ == "__main__":
    unittest.main()
