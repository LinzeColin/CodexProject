import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / "docs" / "pursuing_goal" / "ids_v0_1" / "validate_stage003_finance_meta_rename.py"


class Stage003FinanceMetaRenameTests(unittest.TestCase):
    def _load_module(self):
        spec = importlib.util.spec_from_file_location("stage003_validator", VALIDATOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase2_report_confirms_finance_meta_migration_boundaries(self):
        module = self._load_module()
        report = module.build_report(ROOT)

        self.assertTrue(report["valid"], report["issues"])
        self.assertEqual(report["stage"], "STAGE-003")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-003")
        self.assertIn("FinanceMetaDatabase", report["canonical_name"])
        self.assertGreater(report["finance_meta_hits"], 0)
        self.assertGreater(report["product_meta_hits"], 0)
        self.assertEqual(report["runtime_target_hits"], [])
        self.assertEqual(report["product_meta_path_touched"], [])
        self.assertEqual(report["issues"], [])


if __name__ == "__main__":
    unittest.main()
