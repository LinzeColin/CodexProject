from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s17_p2_project_detail as runtime


class ProjectDetailRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server, cls.thread, cls.base_url = runtime.start_server()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, path: str) -> tuple[int, str, bytes]:
        request = Request(self.base_url + path, headers={"Accept": "application/json,text/html"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read()
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read()

    def api(self, **values: str) -> tuple[int, str, bytes]:
        defaults = {
            "user_id": "demo-owner",
            "role_id": "management",
            "company_id": "demo-north",
            "period": "2026-07",
            "project_id": "PUB-PROJ-001",
        }
        defaults.update(values)
        return self.request("/api/projects/detail?" + urlencode(defaults))

    def test_detail_page_contains_human_ui_tabs_and_test_hook(self) -> None:
        status, content_type, body = self.request("/projects/PUB-PROJ-001")
        text = body.decode("utf-8")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in (
            "返回项目列表",
            "项目详情栏目",
            "项目概况",
            "收入与回款",
            "KMFA_PROJECT_DETAIL_TEST",
        ):
            self.assertIn(token, text)
        self.assertNotIn("KMFA_MetaData", text)

    def test_existing_list_homepage_and_reports_remain_available(self) -> None:
        for path in ("/projects", "/overview", "/reports"):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn("KMFA_PROJECT_LIST_TEST", body.decode("utf-8"))

    def test_detail_api_returns_five_distinct_sections_and_zero_difference_cost(self) -> None:
        status, content_type, body = self.api(active_tab="cost", risk="HIGH", page="2")
        value = json.loads(body)
        self.assertEqual((status, content_type), (200, "application/json"))
        self.assertEqual(value["active_tab"], "cost")
        self.assertEqual(value["section_ids"], ["overview", "cost", "revenue_collection", "variance", "documents"])
        self.assertEqual(value["section_overlap_count"], 0)
        self.assertTrue(value["cost"]["zero_difference_pass"])
        self.assertEqual(value["cost"]["chart_table_difference_cents"], 0)
        self.assertIn("risk=HIGH", value["navigation"]["return_url"])
        self.assertIn("page=2", value["navigation"]["return_url"])

    def test_company_scope_is_exact_and_permission_denial_has_no_detail(self) -> None:
        status, _, body = self.api(company_id="demo-west")
        value = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(value["project"]["company_id"], "demo-west")
        denied_status, _, denied_body = self.api(
            user_id="demo-finance", role_id="finance", company_id="demo-south"
        )
        denied = json.loads(denied_body)
        self.assertEqual(denied_status, 403)
        self.assertFalse(denied["allowed"])
        self.assertNotIn("project", denied)

    def test_invalid_project_and_tab_fail_closed(self) -> None:
        project_status, _, project_body = self.api(project_id="NOT-IN-SCOPE")
        tab_status, _, tab_body = self.api(active_tab="all-at-once")
        self.assertEqual((project_status, tab_status), (400, 400))
        self.assertFalse(json.loads(project_body)["allowed"])
        self.assertFalse(json.loads(tab_body)["allowed"])

    def test_previous_project_list_api_still_works(self) -> None:
        status, content_type, body = self.request(
            "/api/projects?user_id=demo-owner&role_id=management&company_id=demo-north&period=2026-07"
        )
        value = json.loads(body)
        self.assertEqual((status, content_type), (200, "application/json"))
        self.assertEqual(len(value["rows"]), 4)
        self.assertTrue(all(row["route"] == f"/projects/{row['project_id']}" for row in value["rows"]))


if __name__ == "__main__":
    unittest.main()
