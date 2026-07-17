from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s15_p3_app_experience as runtime


class AppExperienceRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server, cls.thread, cls.base_url = runtime.start_server()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, path: str, value=None) -> tuple[int, str, str]:
        data = None if value is None else json.dumps(value, ensure_ascii=False).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=data,
            headers={"Accept": "application/json,text/html", "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read().decode("utf-8")
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read().decode("utf-8")

    def query(self, path: str, **values: str) -> tuple[int, str, str]:
        return self.request(path + "?" + urlencode(values))

    def test_deep_links_return_search_notification_and_preference_runtime(self) -> None:
        for path in ("/overview", "/projects/demo-project", "/settings"):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn("搜索项目、客户、报告或待办", body)
            self.assertIn("通知与待办", body)
            self.assertIn("偏好设置", body)
            self.assertIn("KMFA_EXPERIENCE_TEST", body)
            self.assertIn("KMFA_ROLE_TEST", body)

    def test_search_api_returns_sources_and_filters_sensitive_result(self) -> None:
        management_status, _, management_body = self.query(
            "/api/search",
            user_id="demo-owner",
            role_id="management",
            company_id="demo-north",
            query="敏感来源",
            kind="ALL",
        )
        finance_status, _, finance_body = self.query(
            "/api/search",
            user_id="demo-owner",
            role_id="finance",
            company_id="demo-north",
            query="敏感来源",
            kind="ALL",
        )
        self.assertEqual((management_status, finance_status), (200, 200))
        self.assertEqual(json.loads(management_body)["results"], [])
        finance = json.loads(finance_body)
        self.assertEqual(finance["result_count"], 1)
        self.assertEqual(finance["results"][0]["source_zh"], "受限来源检查")

    def test_cross_company_search_fails_closed_without_results(self) -> None:
        status, _, body = self.query(
            "/api/search",
            user_id="demo-finance",
            role_id="finance",
            company_id="demo-south",
            query="项目",
            kind="ALL",
        )
        payload = json.loads(body)
        self.assertEqual(status, 403)
        self.assertFalse(payload["allowed"])
        self.assertEqual(payload["results"], [])
        self.assertEqual(payload["reason_code"], "COMPANY_NOT_GRANTED")

    def test_recent_access_is_user_scoped_and_permission_rechecked(self) -> None:
        status, _, body = self.request(
            "/api/recent",
            {
                "user_id": "demo-owner",
                "role_id": "finance",
                "company_id": "demo-north",
                "item_id": "SEARCH-TODO-SENSITIVE",
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["event"]["allowed"])
        finance_status, _, finance_body = self.query(
            "/api/recent", user_id="demo-owner", role_id="finance", company_id="demo-north"
        )
        management_status, _, management_body = self.query(
            "/api/recent", user_id="demo-owner", role_id="management", company_id="demo-north"
        )
        other_status, _, other_body = self.query(
            "/api/recent", user_id="demo-finance", role_id="finance", company_id="demo-north"
        )
        self.assertEqual((finance_status, management_status, other_status), (200, 200, 200))
        self.assertEqual(json.loads(finance_body)["recent_count"], 1)
        self.assertEqual(json.loads(management_body)["recent_count"], 0)
        self.assertEqual(json.loads(other_body)["recent_count"], 0)

    def test_notification_api_has_four_categories_and_action_for_every_item(self) -> None:
        status, _, body = self.query(
            "/api/notifications", user_id="demo-owner", role_id="finance", company_id="demo-north"
        )
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual({item["category"] for item in payload["items"]}, {"DATA_UPDATE", "DIFFERENCE", "REPORT", "RISK"})
        self.assertTrue(payload["all_items_have_action"])
        self.assertTrue(all(item["route"] and item["action_zh"] for item in payload["items"]))

    def test_preferences_persist_for_current_user_and_other_user_is_isolated(self) -> None:
        value = {
            "actor_user_id": "demo-owner",
            "target_user_id": "demo-owner",
            "role_id": "management",
            "current_company_id": "demo-north",
            "preferences": {
                "company": "demo-west",
                "period": "2026-H1",
                "table_columns": ["source", "status"],
                "density": "comfortable",
            },
        }
        status, _, body = self.request("/api/preferences", value)
        saved = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(saved["preferences"], value["preferences"])
        read_status, _, read_body = self.query(
            "/api/preferences",
            actor_user_id="demo-owner",
            target_user_id="demo-owner",
            role_id="management",
            current_company_id="demo-north",
        )
        self.assertEqual(read_status, 200)
        self.assertEqual(json.loads(read_body)["preferences"], value["preferences"])
        denied_status, _, denied_body = self.query(
            "/api/preferences",
            actor_user_id="demo-owner",
            target_user_id="demo-finance",
            role_id="management",
            current_company_id="demo-north",
        )
        self.assertEqual(denied_status, 403)
        self.assertEqual(json.loads(denied_body)["reason_code"], "OTHER_USER_PREFERENCE_DENIED")

    def test_preference_save_does_not_change_fact_payload(self) -> None:
        before_status, _, before_body = self.query(
            "/api/context",
            company="demo-north",
            period="2026-07",
            project_status="all",
            report_version="latest",
        )
        status, _, body = self.request(
            "/api/preferences",
            {
                "actor_user_id": "demo-owner",
                "target_user_id": "demo-owner",
                "role_id": "management",
                "current_company_id": "demo-north",
                "preferences": {
                    "company": "demo-south",
                    "period": "2026-Q2",
                    "table_columns": [],
                    "density": "compact",
                },
            },
        )
        after_status, _, after_body = self.query(
            "/api/context",
            company="demo-north",
            period="2026-07",
            project_status="all",
            report_version="latest",
        )
        self.assertEqual((before_status, status, after_status), (200, 200, 200))
        self.assertEqual(json.loads(before_body), json.loads(after_body))
        event = json.loads(body)
        self.assertEqual(event["fact_layer_write_count"], 0)
        self.assertEqual(event["raw_write_count"], 0)

    def test_invalid_preference_and_recent_payload_fail_closed(self) -> None:
        preference_status, _, preference_body = self.request(
            "/api/preferences",
            {
                "actor_user_id": "demo-finance",
                "target_user_id": "demo-finance",
                "role_id": "finance",
                "current_company_id": "demo-north",
                "preferences": {
                    "company": "demo-south",
                    "period": "2026-07",
                    "table_columns": ["source"],
                    "density": "compact",
                },
            },
        )
        recent_status, _, recent_body = self.request(
            "/api/recent",
            {
                "user_id": "demo-owner",
                "role_id": "management",
                "company_id": "demo-north",
                "item_id": "SEARCH-TODO-SENSITIVE",
            },
        )
        self.assertEqual(preference_status, 403)
        self.assertEqual(json.loads(preference_body)["reason_code"], "PREFERRED_COMPANY_NOT_GRANTED")
        self.assertEqual(recent_status, 403)
        self.assertEqual(json.loads(recent_body)["event"]["reason_code"], "RECENT_ITEM_NOT_VISIBLE")


if __name__ == "__main__":
    unittest.main()
