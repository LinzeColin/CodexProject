"""承重：arxiv-daily-push 迁出后，ADP 供应链 A-020 门必须短路为不运行。

背景：project-governance.yml 的『Run ADP supply-chain A-020 gate』步跑
`arxiv-daily-push/tests/test_security_boundary.py`。arxiv-daily-push 已迁往
LinzeColin/MetaDatabase，本仓不再持有该测试；预检若 fail-closed 成 run_gate=true，
Run 步就会 ModuleNotFoundError 拖红 push CI。本测试锁死：本仓无 arxiv-daily-push 目录时
run_gate 必须为 False。
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _lean():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("lean_a020_test", SCRIPTS / "lean_governance.py")
    m = importlib.util.module_from_spec(spec); sys.modules["lean_a020_test"] = m
    assert spec.loader is not None; spec.loader.exec_module(m)
    return m


class AdpA020GateAfterMigrationTests(unittest.TestCase):
    def test_gate_does_not_run_when_adp_absent(self) -> None:
        lean = _lean()
        if (ROOT / lean.ADP_A020_PROJECT_PATH).is_dir():
            self.skipTest("arxiv-daily-push 仍在本仓（未迁出）；本守卫针对迁出后状态")
        decision = lean.adp_a020_gate_decision_from_git(base_ref=None)
        self.assertFalse(
            decision["run_gate"],
            f"arxiv-daily-push 已迁出，A-020 门应短路 run_gate=False，实际 {decision}",
        )
        self.assertEqual(decision["reason"], "adp_project_migrated_out_of_repository")


if __name__ == "__main__":
    unittest.main()
