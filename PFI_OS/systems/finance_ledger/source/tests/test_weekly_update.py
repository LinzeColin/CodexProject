from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "weekly_update.py"


ALIPAY_SAMPLE = """支付宝交易明细
交易时间,交易分类,交易对方,对方账号,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商家订单号,备注
2026-06-03 09:00:00,餐饮美食,早餐店,,早餐,支出,8.00,余额,交易成功,ali001,,
"""


def load_weekly_update_module():
    spec = importlib.util.spec_from_file_location("weekly_update", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load weekly_update.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["weekly_update"] = module
    spec.loader.exec_module(module)
    return module


class WeeklyUpdateTests(unittest.TestCase):
    def test_expand_weekly_inputs_recurses_nested_bill_directories(self) -> None:
        weekly_update = load_weekly_update_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "sources" / "archive_hash"
            nested.mkdir(parents=True)
            bill = nested / "alipay.csv"
            ignored = nested / "notes.txt"
            bill.write_text(ALIPAY_SAMPLE, encoding="utf-8")
            ignored.write_text("ignore", encoding="utf-8")

            expanded = weekly_update._expand_weekly_inputs([str(root / "sources")])

            self.assertEqual(expanded, [str(bill.resolve())])

    def test_weekly_update_writes_manifest_and_preserves_review_boundary_note(self) -> None:
        weekly_update = load_weekly_update_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bill = root / "支付宝交易明细(20260601-20260607).csv"
            ledger_db = root / "finance_ledger.sqlite"
            output = root / "outputs"
            source_root = root / "sources"
            manifest = root / "weekly_update_manifest.json"
            bill.write_text(ALIPAY_SAMPLE, encoding="utf-8")

            exit_code = weekly_update.main(
                [
                    "--input",
                    str(bill),
                    "--ledger-db",
                    str(ledger_db),
                    "--output",
                    str(output),
                    "--source-root",
                    str(source_root),
                    "--manifest",
                    str(manifest),
                    "--skip-validation",
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_type"], "weekly_update")
            self.assertEqual(payload["import_result"]["transaction_count"], 1)
            self.assertTrue(Path(payload["next_report_portal"]).exists())
            self.assertTrue(Path(payload["next_review_workbench"]).exists())
            self.assertIn("候选复核只用于下拉选择加速", "\n".join(payload["notes"]))


if __name__ == "__main__":
    unittest.main()
