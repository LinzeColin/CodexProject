import importlib.util
import unittest
from pathlib import Path


PRODUCT_META_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PRODUCT_META_ROOT.parent


def load_validator():
    validator_path = PRODUCT_META_ROOT / "validate_product_meta_database.py"
    spec = importlib.util.spec_from_file_location("product_meta_database_validator", validator_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load validator from {validator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProductMetaDatabaseContractTests(unittest.TestCase):
    def test_metadata_skeleton_is_parseable_and_policy_bound(self) -> None:
        validator = load_validator()

        report = validator.validate_repository(PRODUCT_META_ROOT)

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["product_id"], "IDS")
        self.assertEqual(report["subsystem"], "ProductMetaDatabase")
        self.assertEqual(report["stage"], "STAGE-002")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-002")
        self.assertEqual(report["external_api_policy"], "denied")
        self.assertEqual(report["raw_material_policy"], "forbidden")
        self.assertIn("product_metadata_schema", report["contracts"])
        self.assertIn("product_manifest_template", report["contracts"])
        self.assertIn("governance_rules", report["contracts"])
        self.assertIn("taskpack_input", report["contracts"])
        self.assertGreaterEqual(len(report["future_lineage_fields"]), 5)
        self.assertFalse(report["forbidden_runtime_paths_present"], report)

    def test_metadata_files_do_not_embed_raw_material_or_secret_markers(self) -> None:
        validator = load_validator()

        report = validator.validate_repository(PRODUCT_META_ROOT)

        self.assertEqual(report["forbidden_markers"], [], report)
        self.assertLessEqual(report["max_contract_file_bytes"], 65536)
        for relative_path in report["contract_files"]:
            self.assertFalse(relative_path.startswith(("data/", "reports/", "outputs/")))


if __name__ == "__main__":
    unittest.main()
