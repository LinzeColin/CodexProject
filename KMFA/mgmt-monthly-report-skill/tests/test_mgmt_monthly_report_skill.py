from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ManagementMonthlyReportSkillTests(unittest.TestCase):
    def test_skill_package_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "KMFA/mgmt-monthly-report-skill/tools/validate_skill_package.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "passed")

    def test_v6_spec_sheet_order_is_fixed(self) -> None:
        spec = json.loads((ROOT / "KMFA/mgmt-monthly-report-skill/config/v6_spec.json").read_text(encoding="utf-8"))
        self.assertEqual(
            spec["visible_sheet_order"],
            [
                "00_首页总览",
                "01_回款应收项目",
                "02_开票纳税汇总",
                "03_2026年销售回款",
                "04_2026年资金汇总",
                "05_客户市场",
                "06_资质人力产能",
                "07_保证金履约",
                "08_趋势预测",
                "09_经营口径核对",
                "10_口径说明与分析方向",
            ],
        )


if __name__ == "__main__":
    unittest.main()
