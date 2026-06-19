from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_chatgpt_reference.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_chatgpt_reference", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load audit_chatgpt_reference.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_chatgpt_reference"] = module
    spec.loader.exec_module(module)
    return module


class ChatGPTReferenceAuditTests(unittest.TestCase):
    def test_explicit_reference_generates_gap_matrix(self) -> None:
        audit = load_audit_module()
        with tempfile.TemporaryDirectory(dir=ROOT / "work") as tmp:
            root = Path(tmp)
            reference = root / "chatgpt_reference_requirements.md"
            reference.write_text(
                "ChatGPT 版本要求：全部报告为 PDF，增加 dashboard 可视化图表，使用 SQLite 数据库，生成 ZIP 交付并做测试验收。",
                encoding="utf-8",
            )
            output = root / "outputs"
            reports = output / "reports"
            audit_dir = output / "audit"
            reports.mkdir(parents=True)
            audit_dir.mkdir()
            for rel in [
                "reports/weekly_report.pdf",
                "reports/monthly_report.pdf",
                "reports/quarterly_report.pdf",
                "reports/half_year_report.pdf",
                "reports/yearly_report.pdf",
                "reports/dashboard.html",
                "reports/visual_quality_acceptance_report.pdf",
                "audit/browser_visual_acceptance.json",
            ]:
                path = output / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"x" * 64)

            result = audit.run_audit(
                Namespace(
                    output_dir=str(output),
                    scan_dir=[],
                    input=[str(reference)],
                    json=False,
                )
            )

            payload = json.loads((audit_dir / "chatgpt_reference_audit.json").read_text(encoding="utf-8"))
            gap_csv = audit_dir / "chatgpt_reference_gap_matrix.csv"
            report_md = reports / "chatgpt_reference_intake_report.md"
            self.assertEqual(result["status"], "found")
            self.assertEqual(payload["candidate_count"], 1)
            self.assertTrue(payload["gap_rows"])
            self.assertTrue(any(row["implementation_status"] == "implemented" for row in payload["gap_rows"]))
            self.assertTrue(gap_csv.exists())
            self.assertIn("## 差距矩阵", report_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
