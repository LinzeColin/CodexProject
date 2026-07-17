from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s22_p3_operations_governance as builder


class OperationsGovernanceArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_stays_inside_s22_p3_and_stops_before_review(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertIn(
            value["phase_acceptance_status"],
            {"PENDING_FINAL_VALIDATION", "PASSED"},
        )
        self.assertEqual(
            (value["run_phase_id"], value["roadmap_phase_id"], value["phase_task_count"]),
            ("V015_S22_P3_OPERATIONS_GOVERNANCE", "S22-P3", 3),
        )
        self.assertEqual(
            (
                value["raw_root_access_count"],
                value["raw_write_count"],
                value["external_network_request_count"],
            ),
            (0, 0, 0),
        )
        self.assertTrue(value["s22_p3_started"])
        self.assertFalse(
            value["s22_stage_review_started"]
            or value["s22_stage_review_performed"]
            or value["s23_started"]
            or value["github_upload_performed"]
            or value["app_reinstall_performed"]
        )

    def test_health_backup_and_migration_contracts_fail_closed(self) -> None:
        health = self.value(builder.HEALTH_CONTRACT_PATH)
        backup = self.value(builder.BACKUP_CONTRACT_PATH)
        migration = self.value(builder.MIGRATION_CONTRACT_PATH)
        self.assertEqual(
            (
                health["service_count"],
                health["monitored_service_count"],
                health["unmonitored_service_count"],
                health["critical_unmonitored_production_accept_count"],
            ),
            (6, 6, 0, 0),
        )
        self.assertEqual(
            (
                backup["dataset_type_count"],
                backup["restore_difference_count"],
                backup["restore_permission_difference_count"],
                backup["backup_tamper_accept_count"],
                backup["unverified_restore_accept_count"],
            ),
            (3, 0, 0, 0, 0),
        )
        self.assertEqual(
            (
                migration["surface_count"],
                migration["change_count"],
                migration["idempotent_noop_count"],
                migration["rollback_difference_count"],
                migration["permission_difference_count"],
                migration["irreversible_without_approval_accept_count"],
            ),
            (4, 4, 1, 0, 0, 0),
        )

    def test_browser_public_checks_and_task_matrix_are_complete(self) -> None:
        browser = self.value(builder.BROWSER_PATH)
        checks = self.value(builder.PUBLIC_CHECKS_PATH)
        matrix = self.value(builder.TASK_MATRIX_PATH)
        self.assertEqual(
            (
                browser["browser_flow_count"],
                browser["visual_evidence_count"],
                browser["external_network_request_count"],
            ),
            (9, 7, 0),
        )
        self.assertEqual(
            (
                checks["status"],
                checks["public_check_count"],
                checks["public_check_pass_count"],
                checks["public_check_failed_count"],
            ),
            ("PASS", 62, 62, 0),
        )
        self.assertEqual((matrix["phase_task_count"], len(matrix["tasks"])), (3, 3))
        self.assertTrue(all(row["status"] == "PASS" for row in matrix["tasks"]))

    def test_seven_screenshots_have_expected_dimensions(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertTrue(all(width >= 1000 and height >= 700 for width, height in sizes[:6]))
        self.assertEqual(sizes[6][0], 390)
        self.assertGreaterEqual(sizes[6][1], 800)

    def test_human_documents_are_plain_chinese_and_present(self) -> None:
        for path in (
            builder.IMPLEMENTATION_REPORT_PATH,
            builder.USER_GUIDE_PATH,
            builder.TEST_RESULTS_PATH,
            builder.RISKS_ROLLBACK_PATH,
        ):
            self.assertGreater(len(path.read_text(encoding="utf-8")), 150)
        self.assertIn("零差异", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))
        self.assertIn("62 项", builder.TEST_RESULTS_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
