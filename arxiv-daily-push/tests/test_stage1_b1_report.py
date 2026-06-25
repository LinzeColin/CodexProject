from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arxiv_daily_push.arxiv_adapter import ArxivQuery
from arxiv_daily_push.cli import main
from arxiv_daily_push.daily_input import build_daily_input_package
from arxiv_daily_push.source_ingest import ingest_latest_arxiv
from arxiv_daily_push.stage1_b1_report import (
    STAGE1_B1_REPORT_MODEL_ID,
    build_b1_report_email_package,
    validate_b1_report_email_package,
)
from arxiv_daily_push.mail_templates import EMAIL_LEARNING_V1_CONTRACT_ID, EMAIL_LEARNING_V1_TEMPLATE_MARKER


ROOT = Path(__file__).resolve().parents[2]
ARXIV_FIXTURE = ROOT / "arxiv-daily-push/tests/fixtures/arxiv_atom_sample.xml"


def fixture_fetcher(query: ArxivQuery) -> str:
    assert query.search_query == "cat:cs.AI"
    return ARXIV_FIXTURE.read_text(encoding="utf-8")


def daily_input_report() -> dict:
    batch = ingest_latest_arxiv(
        search_query="cat:cs.AI",
        generated_at="2026-07-01T05:00:00+10:00",
        max_results=1,
        fetcher=fixture_fetcher,
    )
    return build_daily_input_package(
        batch,
        date="2026-07-01",
        generated_at="2026-07-01T05:00:00+10:00",
    )


class Stage1B1ReportTests(unittest.TestCase):
    def test_build_b1_report_email_package_is_chinese_text_first(self) -> None:
        package = build_b1_report_email_package(
            daily_input_report(),
            generated_at="2026-07-01T05:15:00+10:00",
        )

        self.assertEqual(package["model_id"], STAGE1_B1_REPORT_MODEL_ID)
        self.assertEqual(package["status"], "pass")
        self.assertEqual(package["board_id"], "B1")
        self.assertRegex(package["email_subject"], r"^20260701 -- arXiv Daily Push -- M1 -- .+")
        self.assertEqual(package["email_template_contract"], EMAIL_LEARNING_V1_CONTRACT_ID)
        self.assertEqual(package["mail_product_id"], "M1")
        self.assertIn("【先把论文讲成人话】", package["email_plain"])
        self.assertIn("【学习成果导航】", package["email_plain"])
        self.assertIn("【真正的新知识】", package["email_plain"])
        self.assertIn("候选队列摘要", package["email_plain"])
        self.assertIn(EMAIL_LEARNING_V1_TEMPLATE_MARKER, package["email_html"])
        self.assertIn("claim:arxiv:2401.00001", package["report_markdown"])
        self.assertNotIn("Claim Ledger", package["email_plain"])
        self.assertNotIn("ROI", package["email_plain"])
        self.assertNotIn("project:", package["email_plain"])
        self.assertNotIn(".mp4", package["email_plain"])
        self.assertNotIn("100.0%", package["email_plain"])
        self.assertTrue(package["quality_gates"]["key_claim_evidence_binding_100_percent"])
        self.assertTrue(package["quality_gates"]["email_learning_v1_template"])
        self.assertTrue(package["quality_gates"]["no_video_required"])
        self.assertFalse(package["side_effect_policy"]["real_smtp_sent"])
        self.assertFalse(validate_b1_report_email_package(package))

    def test_build_b1_report_email_blocks_unsupported_p0_claim(self) -> None:
        payload = daily_input_report()
        blocked = copy.deepcopy(payload)
        blocked["daily_input"]["claims"][0]["support_status"] = "unsupported"

        package = build_b1_report_email_package(
            blocked,
            generated_at="2026-07-01T05:15:00+10:00",
        )

        self.assertEqual(package["status"], "blocked")
        self.assertIn("P0 support_status must be supported", " ".join(package["blocking_reasons"]))

    def test_b1_report_blocks_zero_critical_claim_coverage(self) -> None:
        payload = daily_input_report()
        no_critical = copy.deepcopy(payload)
        for claim in no_critical["daily_input"]["claims"]:
            claim["priority"] = "P2"

        package = build_b1_report_email_package(
            no_critical,
            generated_at="2026-07-01T05:15:00+10:00",
        )

        self.assertEqual(package["status"], "blocked")
        self.assertIn("critical claim evidence coverage must be 100.0", " ".join(package["blocking_reasons"]))

    def test_b1_report_validation_rejects_unsafe_source_url(self) -> None:
        package = build_b1_report_email_package(
            daily_input_report(),
            generated_at="2026-07-01T05:15:00+10:00",
        )
        package["email_learning_content_v1"]["source_meta"]["source_url"] = "javascript:alert(1)"

        errors = validate_b1_report_email_package(package)

        self.assertIn("email source URL must be safe", errors)

    def test_cli_build_b1_report_email_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "daily-input.json"
            artifact_dir = tmp_path / "artifacts"
            input_path.write_text(json.dumps(daily_input_report(), ensure_ascii=False), encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = main(
                    [
                        "build-b1-report-email",
                        "--daily-input",
                        str(input_path),
                        "--generated-at",
                        "2026-07-01T05:15:00+10:00",
                        "--artifact-dir",
                        str(artifact_dir),
                        "--write",
                        "--json",
                    ]
                )

            payload = json.loads(buffer.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(payload["status"], "pass")
            self.assertTrue(Path(payload["artifact_files"]["report_markdown"]["path"]).is_file())
            self.assertTrue(Path(payload["artifact_files"]["email_html"]["path"]).is_file())
            self.assertTrue(Path(payload["artifact_files"]["audit_json"]["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
