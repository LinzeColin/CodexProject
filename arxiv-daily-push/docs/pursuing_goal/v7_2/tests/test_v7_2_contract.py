from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V72ContractTests(unittest.TestCase):
    def test_v7_2_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/validate_v7_2_contract.py"), "--root", str(ROOT)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")

    def test_current_pointer_names_v7_2(self) -> None:
        current = (ROOT.parent / "CURRENT.yaml").read_text(encoding="utf-8")
        self.assertIn("version: ADP-PRODUCT-CONTRACT-V7.2", current)
        self.assertIn("version: ADP-PRODUCT-CONTRACT-V7.1", current)
        self.assertIn("agent_revalidation_required: true", current)

    def test_v7_1_directory_is_not_replaced(self) -> None:
        v71 = ROOT.parent / "v7_1" / "V7_1_ROOT_LOCK.yaml"
        self.assertTrue(v71.is_file())
        text = v71.read_text(encoding="utf-8")
        self.assertIn("ADP-PRODUCT-CONTRACT-V7.1", text)

    def test_inherited_v7_1_audit_blockers_stay_production_blocking(self) -> None:
        contract = (ROOT / "machine_readable" / "product_contract_v7_2.yaml").read_text(encoding="utf-8")
        lock = (ROOT / "V7_2_ROOT_LOCK.yaml").read_text(encoding="utf-8")
        self.assertIn("inherited_v7_1_open_findings:", contract)
        self.assertIn("P0: 8", contract)
        self.assertIn("P1: 37", contract)
        self.assertIn("inherited_v7_1_audit_blockers:", lock)
        self.assertIn("open_p0_findings: 8", lock)
        self.assertIn("open_p1_findings: 37", lock)


if __name__ == "__main__":
    unittest.main()
