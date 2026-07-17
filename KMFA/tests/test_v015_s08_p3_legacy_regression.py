from __future__ import annotations

import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from KMFA.tools import check_v014_s08_p3_entity_matching_quality as legacy_checker
from KMFA.tools import v014_s08_p3_entity_matching_quality as legacy_generator


class LegacyMatchingQualityIsolatedRegressionTests(unittest.TestCase):
    def test_legacy_generator_and_validator_run_without_mutating_tracked_evidence(self) -> None:
        tracked_manifest = legacy_generator.MANIFEST_PATH
        before = tracked_manifest.read_bytes()
        with tempfile.TemporaryDirectory(prefix="kmfa-s08p3-legacy-") as temporary:
            root = Path(temporary)
            replacements = {
                "MANIFEST_PATH": root / "entity_matching_quality_manifest.json",
                "REPORT_PATH": root / "implementation_report_zh.md",
                "TEST_RESULTS_PATH": root / "test_results_zh.md",
                "RISK_REGISTER_PATH": root / "risk_register_zh.md",
                "ROLLBACK_PATH": root / "rollback_plan_zh.md",
            }
            with ExitStack() as stack:
                for module in (legacy_generator, legacy_checker):
                    for name, path in replacements.items():
                        stack.enter_context(patch.object(module, name, path))
                generated = legacy_generator.generate()
                validated = legacy_checker.validate_v014_s08_p3_entity_matching_quality(
                    replacements["MANIFEST_PATH"]
                )
        self.assertEqual(generated["phase_id"], "S08-P3")
        self.assertEqual(validated["entity_matching_quality_summary"]["quality_case_count"], 4)
        self.assertFalse(validated["phase_boundaries"]["stage8_review_scope_included"])
        self.assertEqual(tracked_manifest.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
