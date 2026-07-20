"""承重：governance_setup_doctor 的 workflow_entry_gates 必须全通过（含 pinned-SHA 工作流）。

背景：CI『Write CI attestation』步骤（workflow_dispatch scope=all）末尾跑
`governance_setup_doctor.py --json --check-github`；其 workflow_entry_gates 有一项
`ci_attestation_uploaded_as_artifact` 用正则 `actions/upload-artifact@v[4-9]` 判定，
只认版本标签。本仓工作流按安全最佳实践把 action pin 成 commit SHA（`@043fb46… # v7`），
导致该项误判 false -> entry_gates FAIL -> setup_doctor 非零退出 -> 该 CI 步骤红。已把正则
放宽为同时接受标签与 40 位 SHA。本测试锁死『entry_gates 全过』，防再引入只认标签的检查。
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _doctor():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "setup_doctor_entry_gate_test", SCRIPTS / "governance_setup_doctor.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["setup_doctor_entry_gate_test"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowEntryGatesTests(unittest.TestCase):
    def test_all_entry_gate_checks_pass(self) -> None:
        """★承重★：workflow_entry_gates 每一项都必须 true（含 pinned-SHA 的 upload-artifact）。"""
        doctor = _doctor()
        gate = doctor.workflow_entry_gate_status()
        failing = sorted(name for name, ok in gate.get("checks", {}).items() if not ok)
        self.assertEqual(
            gate.get("status"), "PASS",
            f"workflow_entry_gates 未全过，失败项：{failing}",
        )
        self.assertEqual(failing, [], f"以下 entry-gate 检查为 false：{failing}")

    def test_upload_artifact_check_accepts_pinned_sha(self) -> None:
        """★承重★：ci_attestation_uploaded_as_artifact 对 pinned SHA 的工作流必须判 true。

        直接断言当前工作流（已 pin SHA）通过该项——防正则回退为只认 @vN 标签。
        """
        doctor = _doctor()
        checks = doctor.workflow_entry_gate_status().get("checks", {})
        self.assertTrue(
            checks.get("ci_attestation_uploaded_as_artifact"),
            "ci_attestation_uploaded_as_artifact 应对 pinned-SHA 工作流判 true",
        )


if __name__ == "__main__":
    unittest.main()
