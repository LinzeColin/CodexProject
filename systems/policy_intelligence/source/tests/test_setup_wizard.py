from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.content_db import connect_content, init_content_database, upsert_external_reference_gaps
from source_registry.setup_wizard import (
    build_setup_wizard,
    render_setup_wizard_dashboard,
    write_setup_wizard_dashboard,
)


class SetupWizardTest(unittest.TestCase):
    def test_build_setup_wizard_has_steps_and_sanitized_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(conn)
            wizard = build_setup_wizard(content_conn=conn, secure_dir="~/.policy-intelligence")
            conn.close()
        self.assertEqual(len(wizard["steps"]), 14)
        self.assertEqual(len(wizard["input_matrix"]), 4)
        self.assertEqual(wizard["input_matrix"][0]["priority"], "P0")
        self.assertIn("搜索 API", wizard["input_matrix"][0]["target"])
        self.assertIn("setup_config", wizard["commands"])
        self.assertIn("bulk_import_search", wizard["commands"])
        self.assertIn("search-secret-bulk-import", wizard["commands"]["bulk_import_search"])
        self.assertIn("import_bing_key", wizard["commands"])
        self.assertIn("search-secret-import", wizard["commands"]["import_bing_key"])
        self.assertIn("auth_intake", wizard["commands"])
        self.assertIn("bundle_import_cookies", wizard["commands"])
        self.assertIn("platform-auth-bundle-import", wizard["commands"]["bundle_import_cookies"])
        self.assertIn("bulk_import_cookies", wizard["commands"])
        self.assertIn("platform-auth-bulk-import", wizard["commands"]["bulk_import_cookies"])
        self.assertIn("import_chrome_session_reference", wizard["commands"])
        self.assertIn("platform-auth-session-import", wizard["commands"]["import_chrome_session_reference"])
        self.assertIn("import_bilibili_cookie", wizard["commands"])
        self.assertIn("platform_auth_validate", wizard["commands"])
        self.assertIn("access_readiness", wizard["commands"])
        self.assertIn("access-readiness", wizard["commands"]["access_readiness"])
        self.assertIn("crawl_policy", wizard["commands"])
        self.assertIn("crawl-policy", wizard["commands"]["crawl_policy"])
        self.assertIn("platform_parsers", wizard["commands"])
        self.assertIn("platform-parsers", wizard["commands"]["platform_parsers"])
        self.assertIn("platform_parser_validate", wizard["commands"])
        self.assertIn("platform-parser-validate", wizard["commands"]["platform_parser_validate"])
        self.assertIn("platform_parser_samples", wizard["commands"])
        self.assertIn("platform-parser-samples", wizard["commands"]["platform_parser_samples"])
        self.assertIn("attachment_parsers", wizard["commands"])
        self.assertIn("attachment-parsers", wizard["commands"]["attachment_parsers"])
        self.assertTrue(any(step["command_key"] == "crawl_policy" for step in wizard["steps"]))
        self.assertTrue(any(step["command_key"] == "platform_parsers" for step in wizard["steps"]))
        self.assertTrue(any(step["command_key"] == "platform_parser_validate" for step in wizard["steps"]))
        self.assertTrue(any(step["command_key"] == "platform_parser_samples" for step in wizard["steps"]))
        self.assertTrue(any(step["command_key"] == "attachment_parsers" for step in wizard["steps"]))
        self.assertTrue(wizard["setup_paths"]["search_secrets_path"].startswith("~/.policy-intelligence"))
        self.assertIn("search_api_bundle.example.json", wizard["setup_paths"]["search_api_bundle_example_path"])
        self.assertIn("platform_auth_bundle.example.json", wizard["setup_paths"]["platform_auth_bundle_example_path"])
        encoded = json.dumps(wizard, ensure_ascii=False)
        self.assertNotIn("API_KEY=", encoded)
        self.assertNotIn("sk-", encoded)

    def test_setup_wizard_marks_template_step_done_when_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            search = root / "policy-search-secrets.json"
            auth = root / "policy-platform-auth.json"
            search.write_text("{}", encoding="utf-8")
            auth.write_text(json.dumps({"platforms": {}}), encoding="utf-8")
            conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(conn)
            wizard = build_setup_wizard(
                content_conn=conn,
                secure_dir=root / "secure",
                search_secrets_file=search,
                platform_auth_file=auth,
            )
            conn.close()
        self.assertEqual(wizard["steps"][0]["status"], "done")
        self.assertIn("platform_auth_configured", wizard["readiness_summary"])

    def test_render_setup_wizard_dashboard_contains_copy_controls(self) -> None:
        wizard = {
            "generated_at": "2026-06-04T00:00:00",
            "readiness_summary": {
                "search_api_ready": 0,
                "platform_auth_configured": 0,
                "platform_auth_available": 0,
                "chinese_search_entries": 3,
                "pending_gaps": 19,
            },
            "coverage_summary": {"ready": 0, "blocked": 10},
            "steps": [
                {"number": 1, "title": "生成本地模板", "status": "todo", "body": "创建模板", "command_key": "setup_config"}
            ],
            "commands": {"setup_config": "PYTHONPATH=src python3 -m source_registry setup-config"},
            "setup_paths": {"secure_dir": "~/.policy-intelligence"},
            "input_matrix": [
                {
                    "priority": "P0",
                    "target": "搜索 API",
                    "provide": "本地 key 文件",
                    "verify": "search-validate",
                    "value": "补齐外部参考",
                }
            ],
            "next_actions": [],
            "security_boundary": "不要在聊天中发送账号密码、API key 或 cookie 内容。",
        }
        rendered = render_setup_wizard_dashboard(wizard)
        self.assertIn("本地接入验收向导", rendered)
        self.assertIn("命令矩阵", rendered)
        self.assertIn("接入优先级矩阵", rendered)
        self.assertIn("补齐外部参考", rendered)
        self.assertIn("data-copy", rendered)
        self.assertIn("安全与合规边界", rendered)
        self.assertNotIn("cookie_file", rendered)
        self.assertNotIn("API_KEY=", rendered)
        self.assertNotIn("SESSDATA", rendered)

    def test_write_setup_wizard_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conn = connect_content(root / "policy_documents.sqlite")
            init_content_database(conn)
            output = root / "setup.html"
            result = write_setup_wizard_dashboard(output, content_conn=conn, secure_dir=root / "secure")
            conn.close()
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())
            self.assertIn("接入步骤", output.read_text(encoding="utf-8"))

    def test_cli_setup_wizard_generates_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_db = root / "source_registry.sqlite"
            content_db = root / "policy_documents.sqlite"
            output = root / "setup.html"
            conn = connect_content(content_db)
            init_content_database(conn)
            upsert_external_reference_gaps(
                conn,
                [
                    {
                        "gap_id": "gap_1",
                        "run_id": "2026060401",
                        "document_id": None,
                        "interpretation_source_id": None,
                        "platform": "bing",
                        "gap_type": "missing_api_key",
                        "title": "Bing key missing",
                        "url": "https://www.bing.com/search?q=test",
                        "query": "test",
                        "evidence_status": "missing_api_key:bing",
                        "required_action": "provide_search_api_key",
                        "priority_score": 95,
                    }
                ],
            )
            conn.close()
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(source_db),
                        "setup-wizard",
                        "--content-db",
                        str(content_db),
                        "--secure-dir",
                        str(root / "secure"),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertEqual(payload["readiness_summary"]["pending_gaps"], 1)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
