import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from salary_logic import WEIGHT_KEYS, projects, resolve_weights  # noqa: E402


class SalaryLogicWeightTests(unittest.TestCase):
    def test_configured_project_weights_are_complete_non_negative_and_sum_to_one(self) -> None:
        for province in projects:
            with self.subTest(province=province):
                weights = resolve_weights(province=province)
                self.assertEqual(set(weights), set(WEIGHT_KEYS))
                self.assertTrue(all(value >= 0 for value in weights.values()))
                self.assertAlmostEqual(sum(weights.values()), 1.0, places=9)

    def test_explicit_weights_reject_missing_extra_negative_and_bad_total(self) -> None:
        valid = resolve_weights(province="湖北")

        missing = dict(valid)
        missing.pop("业绩")
        with self.assertRaisesRegex(ValueError, "权重键不完整"):
            resolve_weights(weights=missing)

        extra = dict(valid)
        extra["额外"] = 0.0
        with self.assertRaisesRegex(ValueError, "权重键不完整"):
            resolve_weights(weights=extra)

        negative = dict(valid)
        negative["业绩"] = -0.1
        with self.assertRaisesRegex(ValueError, "权重必须为非负有限数"):
            resolve_weights(weights=negative)

        bad_total = dict(valid)
        bad_total["业绩"] += 0.01
        with self.assertRaisesRegex(ValueError, "权重合计必须等于 1"):
            resolve_weights(weights=bad_total)

    def test_streamlit_uses_salary_logic_projects_as_single_weight_source(self) -> None:
        text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
        self.assertIn("from salary_logic import projects, calculate", text)
        self.assertIn("list(projects.keys())", text)
        self.assertIn("weights = projects[province]", text)
        self.assertNotIn("province_weights =", text)


if __name__ == "__main__":
    unittest.main()
