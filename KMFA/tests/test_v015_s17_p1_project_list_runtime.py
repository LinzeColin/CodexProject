from __future__ import annotations

import csv
import io
import json
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s17_p1_project_list as runtime


class ProjectListRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server, cls.thread, cls.base_url = runtime.start_server()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, path: str) -> tuple[int, str, bytes, dict[str, str]]:
        request = Request(self.base_url + path, headers={"Accept": "application/json,text/html,text/csv"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read(), dict(response.headers)
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read(), dict(error.headers)

    def api(self, path: str, **values: str) -> tuple[int, str, bytes, dict[str, str]]:
        defaults = {
            "user_id": "demo-owner",
            "role_id": "management",
            "company_id": "demo-north",
            "period": "2026-07",
        }
        defaults.update(values)
        return self.request(path + "?" + urlencode(defaults))

    def test_projects_page_contains_human_ui_and_test_hook(self) -> None:
        status, content_type, body, _ = self.request("/projects")
        text = body.decode("utf-8")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("项目总表", "筛选和排列", "设置显示列", "只读操作", "所选项目对比", "KMFA_PROJECT_LIST_TEST"):
            self.assertIn(token, text)
        self.assertNotIn("KMFA_MetaData", text)

    def test_existing_homepage_and_deep_links_remain_available(self) -> None:
        for path in ("/overview", "/projects/demo-project", "/reports"):
            status, content_type, body, _ = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn("KMFA_HOMEPAGE_TEST", body.decode("utf-8"))

    def test_list_api_binds_filters_sort_page_and_columns(self) -> None:
        status, content_type, body, _ = self.api(
            "/api/projects",
            project_status="attention",
            sort_by="margin",
            group_by="risk",
            page="1",
            page_size="2",
            columns="project,margin,risk,source",
        )
        value = json.loads(body)
        self.assertEqual((status, content_type), (200, "application/json"))
        self.assertEqual(value["selected_columns"], ["project", "margin", "risk", "source"])
        self.assertEqual(value["page_size"], 2)
        self.assertEqual(value["sort_by"], "margin")
        self.assertTrue(all(row["status"] == "ATTENTION" for row in value["rows"]))

    def test_company_scope_is_exact_and_permission_denial_has_no_rows(self) -> None:
        status, _, body, _ = self.api("/api/projects", company_id="demo-west")
        value = json.loads(body)
        self.assertEqual(status, 200)
        self.assertTrue(all(row["company_id"] == "demo-west" for row in value["rows"]))
        denied_status, _, denied_body, _ = self.api(
            "/api/projects", user_id="demo-finance", role_id="finance", company_id="demo-south"
        )
        denied = json.loads(denied_body)
        self.assertEqual(denied_status, 403)
        self.assertFalse(denied["allowed"])
        self.assertNotIn("rows", denied)

    def test_compare_and_export_are_consistent_and_read_only(self) -> None:
        ids = "PUB-PROJ-001,PUB-PROJ-003"
        compare_status, _, compare_body, _ = self.api("/api/projects/compare", project_ids=ids)
        comparison = json.loads(compare_body)
        export_status, content_type, export_body, headers = self.api("/api/projects/export", project_ids=ids)
        exported = list(csv.DictReader(io.StringIO(export_body.decode("utf-8-sig"))))
        self.assertEqual((compare_status, export_status, content_type), (200, 200, "text/csv"))
        self.assertEqual(comparison["project_ids"], [row["项目编号"] for row in exported])
        self.assertEqual(comparison["totals"]["revenue_cents"], sum(int(row["收入(分)"]) for row in exported))
        self.assertTrue(all(row["来源说明"] and row["来源编号"] and row["数据截止日"] for row in exported))
        self.assertEqual(comparison["fact_layer_write_count"], 0)
        self.assertIn("attachment", headers["Content-Disposition"])

    def test_invalid_batch_and_page_fail_closed(self) -> None:
        batch_status, _, batch_body, _ = self.api("/api/projects/compare", project_ids="PUB-PROJ-001")
        page_status, _, page_body, _ = self.api("/api/projects", page_size="99")
        self.assertEqual((batch_status, page_status), (400, 400))
        self.assertFalse(json.loads(batch_body)["allowed"])
        self.assertFalse(json.loads(page_body)["allowed"])


if __name__ == "__main__":
    unittest.main()
