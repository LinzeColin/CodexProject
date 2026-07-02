import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "check_storage_budget.py"
GIB = 1024**3


class Stage009StorageBudgetTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage009_storage_budget", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _create_complete_slots(self, root: Path) -> None:
        for index in range(100):
            if index == 0:
                name = "00_ORIGINAL_RAW_DATA"
            elif index == 99:
                name = "99_ARCHIVE"
            else:
                name = f"{index:02d}_SLOT"
            (root / name).mkdir()

    def test_budget_ok_and_warn_are_operations_only(self):
        module = self._load_module()

        ok = module.evaluate_storage_budget(
            internal_total_bytes=1000 * GIB,
            internal_free_bytes=300 * GIB,
            planned_output_bytes=20 * GIB,
            job_kind="bounded_preflight",
            require_external_root=False,
        )
        warn = module.evaluate_storage_budget(
            internal_total_bytes=500 * GIB,
            internal_free_bytes=150 * GIB,
            planned_output_bytes=20 * GIB,
            job_kind="bounded_preflight",
            require_external_root=False,
        )

        self.assertEqual(ok["state"], "BUDGET_OK")
        self.assertFalse(ok["safe_mode"])
        self.assertTrue(ok["bounded_preflight_only"])
        self.assertFalse(ok["customer_visible"])
        self.assertEqual(ok["entrance"], "IDS 系统运营入口")
        self.assertEqual(ok["budget_defaults"]["internal_min_free_gib"], 100)
        self.assertTrue(ok["does_not_start_services"])
        self.assertTrue(ok["does_not_create_ids_data_root"])
        self.assertTrue(ok["does_not_generate_outputs"])
        self.assertTrue(ok["does_not_scan_external_drive_contents"])

        self.assertEqual(warn["state"], "BUDGET_WARN")
        self.assertFalse(warn["safe_mode"])
        self.assertTrue(warn["requires_operator_confirmation"])
        self.assertTrue(warn["large_jobs_require_review"])
        self.assertIn("operator_review_before_large_job", warn["operator_actions"])

    def test_low_free_high_waterline_unknown_and_unbounded_output_fail_closed(self):
        module = self._load_module()

        low_free = module.evaluate_storage_budget(
            internal_total_bytes=1000 * GIB,
            internal_free_bytes=50 * GIB,
            planned_output_bytes=1 * GIB,
            job_kind="bounded_preflight",
            require_external_root=False,
        )
        high_waterline = module.evaluate_storage_budget(
            internal_total_bytes=1000 * GIB,
            internal_free_bytes=120 * GIB,
            planned_output_bytes=1 * GIB,
            job_kind="bounded_preflight",
            require_external_root=False,
        )
        unknown = module.evaluate_storage_budget(
            internal_total_bytes=None,
            internal_free_bytes=None,
            planned_output_bytes=1 * GIB,
            job_kind="bounded_preflight",
            require_external_root=False,
            allow_real_disk_fallback=False,
        )
        unbounded = module.evaluate_storage_budget(
            internal_total_bytes=1000 * GIB,
            internal_free_bytes=300 * GIB,
            planned_output_bytes=None,
            job_kind="embedding",
            require_external_root=False,
        )

        self.assertEqual(low_free["state"], "BUDGET_BLOCKED_LOW_FREE")
        self.assertEqual(high_waterline["state"], "BUDGET_BLOCKED_HIGH_WATERLINE")
        self.assertEqual(unknown["state"], "BUDGET_UNKNOWN")
        self.assertEqual(unbounded["state"], "UNBOUNDED_OUTPUT_RISK")
        for report in [low_free, high_waterline, unknown, unbounded]:
            self.assertTrue(report["safe_mode"])
            self.assertIn("embedding", report["paused_workflows"])
            self.assertIn("batch_report_generation", report["paused_workflows"])
            self.assertFalse(report["auto_resume"])

    def test_external_root_not_ready_blocks_cold_data_jobs_without_creating_root(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            complete = Path(tmp) / "IDS_DATA_ROOT"
            complete.mkdir()
            self._create_complete_slots(complete)
            missing = Path(tmp) / "MISSING_IDS_DATA_ROOT"

            blocked = module.evaluate_storage_budget(
                ids_data_root=str(missing),
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=5 * GIB,
                job_kind="bulk_import",
                require_external_root=True,
            )
            online = module.evaluate_storage_budget(
                ids_data_root=str(complete),
                internal_total_bytes=1000 * GIB,
                internal_free_bytes=300 * GIB,
                planned_output_bytes=5 * GIB,
                job_kind="bulk_import",
                require_external_root=True,
            )

        self.assertEqual(blocked["state"], "EXTERNAL_ROOT_NOT_READY")
        self.assertTrue(blocked["safe_mode"])
        self.assertEqual(blocked["removable_drive_state"], "OFFLINE")
        self.assertFalse(missing.exists())
        self.assertIn("reconnect_or_configure_ids_data_root", blocked["operator_actions"])
        self.assertTrue(blocked["does_not_create_ids_data_root"])
        self.assertTrue(blocked["does_not_scan_recursively"])

        self.assertEqual(online["state"], "BUDGET_OK")
        self.assertFalse(online["safe_mode"])
        self.assertEqual(online["removable_drive_state"], "ONLINE_VALIDATED")
        self.assertFalse(online["auto_resume"])

    def test_phase3_scenario_report_covers_budget_states_output_risk_and_safe_mode_pauses(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            complete = Path(tmp) / "IDS_DATA_ROOT"
            complete.mkdir()
            self._create_complete_slots(complete)
            absent = Path(tmp) / "ABSENT_IDS_DATA_ROOT"

            report = module.build_stage009_scenario_report(
                online_root=str(complete),
                absent_root=str(absent),
                storage_ok_total_bytes=1000 * GIB,
                storage_ok_free_bytes=300 * GIB,
                storage_warn_total_bytes=500 * GIB,
                storage_warn_free_bytes=150 * GIB,
                storage_low_total_bytes=1000 * GIB,
                storage_low_free_bytes=50 * GIB,
                storage_high_total_bytes=1000 * GIB,
                storage_high_free_bytes=120 * GIB,
                planned_output_ok_bytes=20 * GIB,
                planned_output_too_large_bytes=250 * GIB,
            )

        states = report["scenario_states"]

        self.assertTrue(report["overall_valid"])
        self.assertEqual(report["schema_version"], "ids.stage009.phase3_scenarios.v1")
        self.assertEqual(report["stage"], "STAGE-009")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-009")
        self.assertFalse(report["customer_visible"])
        self.assertEqual(states["ok"], "BUDGET_OK")
        self.assertEqual(states["warn"], "BUDGET_WARN")
        self.assertEqual(states["low_free_space"], "BUDGET_BLOCKED_LOW_FREE")
        self.assertEqual(states["high_waterline"], "BUDGET_BLOCKED_HIGH_WATERLINE")
        self.assertEqual(states["unknown"], "BUDGET_UNKNOWN")
        self.assertEqual(states["external_root_not_ready"], "EXTERNAL_ROOT_NOT_READY")
        self.assertEqual(states["unbounded_output_missing_cap"], "UNBOUNDED_OUTPUT_RISK")
        self.assertEqual(states["planned_output_exceeds_budget"], "UNBOUNDED_OUTPUT_RISK")
        for workflow in ["bulk_import", "ocr", "embedding", "index_rebuild", "batch_report_generation"]:
            self.assertIn(workflow, report["safe_mode_pauses"])
        self.assertTrue(report["does_not_start_services"])
        self.assertTrue(report["does_not_create_ids_data_root"])
        self.assertTrue(report["does_not_scan_external_drive_contents"])
        self.assertTrue(report["does_not_generate_outputs"])
        self.assertTrue(report["does_not_write_runtime_data"])

    def test_cli_json_contract_is_stage009_operations_only(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--internal-total-gib",
                "1000",
                "--internal-free-gib",
                "300",
                "--planned-output-gib",
                "20",
                "--job-kind",
                "bounded_preflight",
                "--no-require-external-root",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "ids.stage009.storage_budget.v1")
        self.assertEqual(payload["stage"], "STAGE-009")
        self.assertEqual(payload["acceptance_id"], "ACC-STAGE-009")
        self.assertEqual(payload["state"], "BUDGET_OK")
        self.assertEqual(payload["entrance"], "IDS 系统运营入口")
        self.assertFalse(payload["customer_visible"])
        self.assertFalse(payload["safe_mode"])
        self.assertTrue(payload["bounded_preflight_only"])
        self.assertTrue(payload["does_not_start_services"])
        self.assertTrue(payload["does_not_create_ids_data_root"])
        self.assertTrue(payload["does_not_scan_external_drive_contents"])
        self.assertTrue(payload["does_not_generate_outputs"])


if __name__ == "__main__":
    unittest.main()
