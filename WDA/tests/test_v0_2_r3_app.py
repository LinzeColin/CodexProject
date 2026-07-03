from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


DATA_CORE = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace/"
    "data_core/wda_v0_2_r2.sqlite"
)
SOURCE_WORKSPACE = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace"
)


class V02R3RuntimeTests(unittest.TestCase):
    def test_build_status_reads_v02_r2_data_core_without_raw_content(self) -> None:
        from WDA.app_api.core import build_status

        status = build_status(DATA_CORE, SOURCE_WORKSPACE)

        self.assertEqual(status["service"], "ready")
        self.assertEqual(status["message_count"], 612664)
        self.assertEqual(status["conversation_count"], 1552)
        self.assertEqual(status["contact_count"], 5870)
        self.assertEqual(status["media_count"], 0)
        self.assertEqual(status["external_drive_required"], False)
        self.assertTrue(status["data_core_path"].endswith("wda_v0_2_r2.sqlite"))
        self.assertNotIn("sample_text", status)

    def test_initialize_runtime_creates_local_state_dashboard_and_logs(self) -> None:
        from WDA.app_api.core import initialize_runtime

        with tempfile.TemporaryDirectory() as tmp:
            runtime_root = Path(tmp)
            result = initialize_runtime(runtime_root, DATA_CORE, SOURCE_WORKSPACE)

            for rel in ["logs", "state", "reports", "dashboard"]:
                self.assertTrue((runtime_root / rel).is_dir(), rel)

            status_path = runtime_root / "state" / "status.json"
            self.assertTrue(status_path.exists())
            status = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(status["message_count"], 612664)
            self.assertEqual(result["runtime_root"], str(runtime_root))

    def test_dashboard_payload_prioritizes_chinese_decisions_over_technical_counts(self) -> None:
        from WDA.app_api.core import build_dashboard_payload, build_status

        status = build_status(DATA_CORE, SOURCE_WORKSPACE)
        payload = build_dashboard_payload(status)

        self.assertEqual(payload["title"], "WDA 今日工作台")
        self.assertIn("立即更新", payload["primary_action"])
        self.assertGreaterEqual(len(payload["top_sections"]), 5)
        section_titles = [item["title"] for item in payload["top_sections"]]
        self.assertIn("行动中心", section_titles)
        self.assertIn("风险中心", section_titles)
        self.assertIn("联系人雷达", section_titles)
        self.assertNotEqual(payload["hero_label"], "612664 messages")

    def test_run_update_writes_run_record_report_index_and_dashboard(self) -> None:
        from WDA.app_api.core import run_update

        with tempfile.TemporaryDirectory() as tmp:
            runtime_root = Path(tmp)
            result = run_update(runtime_root, DATA_CORE, SOURCE_WORKSPACE)

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["message_count"], 612664)
            self.assertTrue((runtime_root / "state" / "last_run.json").exists())
            self.assertTrue((runtime_root / "reports" / "report_index.json").exists())
            self.assertTrue((runtime_root / "dashboard" / "index.html").exists())

            report_index = json.loads(
                (runtime_root / "reports" / "report_index.json").read_text(
                    encoding="utf-8"
                )
            )
            report_titles = [item["title"] for item in report_index["reports"]]
            self.assertIn("今日简报", report_titles)
            self.assertIn("行动中心", report_titles)
            self.assertIn("证据索引", report_titles)


if __name__ == "__main__":
    unittest.main()
