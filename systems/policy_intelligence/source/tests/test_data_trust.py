from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.content_db import connect_content, init_content_database
from source_registry.data_trust import build_data_trust_audit, write_data_trust_audit
from source_registry.db import connect, init_database, review_source, seed_sources


class DataTrustLayerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data").mkdir()
        (self.root / "reports").mkdir()
        (self.root / "HANDOFF.md").write_text("# Handoff\n", encoding="utf-8")
        (self.root / "README.md").write_text("# Policy System\n", encoding="utf-8")
        (self.root / "pyproject.toml").write_text("[project]\nname='source-registry'\n", encoding="utf-8")
        (self.root / "reports" / "latest_report.md").write_text("# Report\n", encoding="utf-8")

        self.source_db = self.root / "data" / "source_registry.sqlite"
        source_conn = connect(self.source_db)
        init_database(source_conn)
        source_id = seed_sources(source_conn, [_central_source()])[0]
        review_source(source_conn, source_id, final_score=92, status="user_confirmed", reviewer="test")
        source_conn.close()

        self.content_db = self.root / "data" / "policy_documents.sqlite"
        content_conn = connect_content(self.content_db)
        init_content_database(content_conn)
        content_conn.execute(
            "INSERT INTO pipeline_runs(run_id, status, mode, report_path) VALUES (?, ?, ?, ?)",
            ("run_ok", "completed", "manual", "reports/latest_report.md"),
        )
        content_conn.execute(
            "INSERT INTO pipeline_runs(run_id, status, mode, error_summary) VALUES (?, ?, ?, ?)",
            ("run_failed", "failed", "manual", "network blocked"),
        )
        content_conn.execute(
            """
            INSERT INTO documents(
                document_id, source_id, source_name, source_url, title, url, canonical_url,
                first_seen_run_id, last_seen_run_id, status, content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "doc_1",
                source_id,
                "中国政府网",
                "https://www.gov.cn/",
                "测试政策文件",
                "https://www.gov.cn/test",
                "https://www.gov.cn/test",
                "run_ok",
                "run_ok",
                "analyzed",
                "abc123",
            ),
        )
        content_conn.execute(
            """
            INSERT INTO external_reference_gaps(
                gap_id, document_id, platform, gap_type, title, url, query, evidence_status,
                required_action, first_seen_run_id, last_seen_run_id, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "gap_1",
                "doc_1",
                "bilibili",
                "missing_auth",
                "缺少授权",
                "https://www.bilibili.com/",
                "政策 解读",
                "auth_blocked",
                "提供本地授权后复核。",
                "run_ok",
                "run_ok",
                "pending",
            ),
        )
        content_conn.commit()
        content_conn.close()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_audit_flags_missing_control_files_and_pending_gaps(self) -> None:
        audit = build_data_trust_audit(root=self.root, as_of="2026-06-06")
        records = audit["records"]
        status_by_path = {row["source_path"]: row["trust_status"] for row in records}
        gap_records = [row for row in records if "external_reference_gaps:gap_1" in row["source_path"]]

        self.assertEqual(audit["schema"], "PolicyDataTrustAuditV1")
        self.assertEqual(status_by_path["AGENTS.md"], "NEEDS_REVIEW")
        self.assertEqual(status_by_path["PLANS.md"], "NEEDS_REVIEW")
        self.assertEqual(status_by_path["CODEX_TASK_PACK.md"], "NEEDS_REVIEW")
        self.assertEqual(status_by_path["CODEX_PROMPTS.md"], "NEEDS_REVIEW")
        self.assertEqual(gap_records[0]["trust_status"], "NEEDS_REVIEW")
        self.assertEqual(gap_records[0]["source_type"], "sqlite_row")
        self.assertEqual(audit["audit_status"], "Blocked")
        self.assertGreater(audit["record_count"], 0)

    def test_write_audit_creates_machine_and_pdf_outputs(self) -> None:
        audit = write_data_trust_audit(root=self.root, as_of="2026-06-06")
        outputs = audit["outputs"]

        for path in outputs.values():
            self.assertTrue(Path(path).exists(), path)
        self.assertTrue(Path(outputs["pdf"]).read_bytes().startswith(b"%PDF"))
        saved = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
        self.assertEqual(saved["outputs"]["pdf"], outputs["pdf"])

    def test_cli_data_trust_audit_outputs_json(self) -> None:
        output_dir = self.root / "reports" / "cli_audit"
        self.source_db.chmod(0o444)
        self.content_db.chmod(0o444)
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = cli_main(
                [
                    "--db",
                    str(self.source_db),
                    "data-trust-audit",
                    "--content-db",
                    str(self.content_db),
                    "--report-dir",
                    str(self.root / "reports"),
                    "--output-dir",
                    str(output_dir),
                    "--as-of",
                    "2026-06-06",
                    "--json",
                ]
            )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema"], "PolicyDataTrustAuditV1")
        self.assertTrue(Path(payload["outputs"]["pdf"]).exists())


def _central_source() -> dict:
    return {
        "name": "中国政府网",
        "country_code": "CN",
        "country_name": "China",
        "region": "China",
        "administrative_level": "national",
        "source_type": "government_portal",
        "sponsor_unit": "国务院办公厅",
        "supervisor_unit": "国务院办公厅",
        "official_url": "https://www.gov.cn/",
        "publishes_original_documents": True,
        "crawl_enabled": True,
        "crawl_priority": 1,
        "status": "active",
        "evidence": [
            {"type": "official_directory", "value": "中央人民政府门户网站", "url": "https://www.gov.cn/"},
            {"type": "sponsor_unit", "value": "国务院办公厅"},
        ],
    }


if __name__ == "__main__":
    unittest.main()
