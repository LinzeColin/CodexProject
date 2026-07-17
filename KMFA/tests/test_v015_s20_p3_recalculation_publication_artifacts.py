from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s20_p3_recalculation_publication as builder


class RecalculationPublicationArtifactsTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_impact_graph_and_recalculation_contracts_are_narrow(self) -> None:
        graph = self.load(builder.IMPACT_GRAPH_PATH)
        recalculation = self.load(builder.RECALCULATION_PATH)
        self.assertEqual((graph["node_count"], graph["edge_count"]), (16, 18))
        self.assertEqual((graph["affected_fact_count"], graph["affected_metric_count"], graph["synchronized_view_count"]), (2, 2, 4))
        self.assertEqual(graph["unaffected_ref_count"], 7)
        self.assertTrue(recalculation["only_affected_chain_recalculated"])
        for key in ("unrelated_cash_mutation_count", "raw_root_access_count", "raw_source_mutation_count", "source_value_edit_count"):
            self.assertEqual(recalculation[key], 0, key)

    def test_comparison_and_publication_fail_closed(self) -> None:
        comparison = self.load(builder.COMPARISON_PATH)
        publication = self.load(builder.PUBLICATION_PATH)
        self.assertTrue(comparison["difference_explanation_required"])
        self.assertEqual((comparison["minimum_numeric_change_count"], comparison["report_change_count"]), (3, 4))
        self.assertEqual((comparison["difference_explanation_missing_count"], comparison["unexplained_publish_success_count"]), (0, 0))
        self.assertEqual((publication["view_count"], publication["event_type_count"]), (4, 3))
        self.assertTrue(publication["consistency"]["consistent"])
        self.assertEqual(publication["page_mismatch_publish_success_count"], 0)
        self.assertFalse(publication["external_publication_performed"])

    def test_checks_browser_human_and_manifest_evidence(self) -> None:
        checks = self.load(builder.PUBLIC_CHECKS_PATH)
        browser = self.load(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual((checks["check_count"], checks["pass_count"], checks["fail_count"]), (63, 63, 0))
        self.assertEqual((browser["browser_flow_count"], browser["visual_evidence_count"]), (8, 6))
        self.assertEqual(browser["minimum_touch_target_px"], 44)
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertTrue(path.is_file())
            self.assertGreater(len(path.read_text(encoding="utf-8")), 120)
        manifest = self.load(builder.MANIFEST_PATH)
        final, run_id, head = builder.final_binding(builder.receipts())
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["phase_task_accepted_count"], 3 if final else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 58 if final else 57)
        self.assertEqual((manifest["validation_run_id"], manifest["validation_head"]), (run_id, head))
        self.assertFalse(manifest["s20_stage_review_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
