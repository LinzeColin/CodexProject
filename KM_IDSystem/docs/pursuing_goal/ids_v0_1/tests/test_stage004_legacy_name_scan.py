import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "validate_stage004_legacy_name_scan.py"


class Stage004LegacyNameScanTests(unittest.TestCase):
    def _load_module(self):
        spec = importlib.util.spec_from_file_location("stage004_validator", VALIDATOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase2_report_classifies_current_legacy_name_refs(self):
        module = self._load_module()
        report = module.build_report(ROOT)

        self.assertTrue(report["valid"], report["issues"])
        self.assertEqual(report["stage"], "STAGE-004")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-004")
        self.assertGreater(report["legacy_name_hits"], 0)
        self.assertGreater(report["classification_counts"]["allowed_legacy_context"], 0)
        self.assertEqual(report["active_display_debt_refs"], [])
        self.assertEqual(report["forbidden_changed_paths"], [])
        self.assertEqual(report["issues"], [])

    def test_false_positive_exclusions_keep_accepted_names_out_of_old_name_debt(self):
        module = self._load_module()
        hits = module.find_legacy_hits(
            "ProductMetaDatabase FinanceMetaDatabase standalone MetaDatabase OpMe"
        )
        matched = {hit["pattern"] for hit in hits}

        self.assertIn("legacy_opme_word", matched)
        self.assertIn("legacy_standalone_metadatabase", matched)
        self.assertNotIn("ProductMetaDatabase", matched)
        self.assertNotIn("FinanceMetaDatabase", matched)

    def test_stage039_checker_allows_only_governance_identifiers(self):
        module = self._load_module()
        checker_path = (
            "KM_IDSystem/scripts/check_retry_dead_letter_stage_review.py"
        )

        self.assertEqual(
            "allowed_legacy_context",
            module.classify_hit(
                checker_path,
                'task_id = "TASK-OPME-B-001"',
                "legacy_opme_word",
            ),
        )
        self.assertEqual(
            "active_display_debt",
            module.classify_hit(
                checker_path,
                'display_name = "OpMe"',
                "legacy_opme_word",
            ),
        )


if __name__ == "__main__":
    unittest.main()
