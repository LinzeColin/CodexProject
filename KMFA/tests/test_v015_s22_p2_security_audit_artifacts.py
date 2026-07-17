from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s22_p2_security_audit as builder


class SecurityAuditArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_is_pending_or_final_and_stays_inside_s22_p2(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertIn(value["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual((value["run_phase_id"], value["roadmap_phase_id"], value["phase_task_count"]), ("V015_S22_P2_SECURITY_AUDIT", "S22-P2", 3))
        self.assertEqual((value["high_vulnerability_count"], value["credential_exposure_count"], value["raw_root_access_count"], value["external_network_request_count"]), (0, 0, 0, 0))
        self.assertFalse(value["s22_p3_started"] or value["github_upload_performed"] or value["app_reinstall_performed"])

    def test_auth_audit_and_secret_contracts_fail_closed(self) -> None:
        audit, secret = self.value(builder.AUTH_AUDIT_PATH), self.value(builder.SECRET_CONTRACT_PATH)
        self.assertEqual((audit["role_count"], audit["required_audit_action_type_count"], audit["required_audit_action_type_coverage_count"]), (4, 5, 5))
        self.assertTrue(audit["audit_append_only"] and audit["audit_hash_linked"] and audit["audit_queryable"])
        self.assertEqual((audit["tamper_accept_count"], audit["production_audit_disabled_accept_count"], audit["credential_exposure_count"]), (0, 0, 0))
        self.assertEqual((secret["secret_source_count"], secret["secret_reference_count"], secret["tracked_plaintext_secret_count"], secret["audit_secret_exposure_count"]), (1, 2, 0, 0))

    def test_input_output_browser_and_public_checks_are_complete(self) -> None:
        security, browser = self.value(builder.INPUT_OUTPUT_PATH), self.value(builder.BROWSER_PATH)
        checks, matrix = self.value(builder.PUBLIC_CHECKS_PATH), self.value(builder.TASK_MATRIX_PATH)
        self.assertEqual((security["attack_category_count"], security["rejected_attack_count"], security["high_vulnerability_count"], security["public_link_count"]), (5, 5, 0, 0))
        self.assertEqual((browser["browser_flow_count"], browser["visual_evidence_count"], browser["page_secret_exposure_count"]), (9, 6, 0))
        self.assertEqual((checks["status"], checks["public_check_count"], checks["public_check_pass_count"], checks["public_check_failed_count"]), ("PASS", 60, 60, 0))
        self.assertEqual((matrix["phase_task_count"], len(matrix["tasks"])), (3, 3)); self.assertTrue(all(row["status"] == "PASS" for row in matrix["tasks"]))

    def test_six_screenshots_have_expected_dimensions(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]; self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertTrue(all(width >= 1000 and height >= 700 for width, height in sizes[:5]))
        self.assertEqual(sizes[5][0], 390); self.assertGreaterEqual(sizes[5][1], 800)

    def test_human_documents_are_plain_chinese_and_present(self) -> None:
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertGreater(len(path.read_text(encoding="utf-8")), 150)
        self.assertIn("不显示值", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))
        self.assertIn("高危漏洞", builder.TEST_RESULTS_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
