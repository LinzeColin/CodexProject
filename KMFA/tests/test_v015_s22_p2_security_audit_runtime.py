from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s22_p2_security_audit as runtime


class SecurityAuditRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(); root = Path(self.temporary.name)
        self.auth_value = hashlib.sha256((self.temporary.name + "auth").encode()).hexdigest()
        self.signing_value = hashlib.sha256((self.temporary.name + "sign").encode()).hexdigest()
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data", confirmation_event_path=root / "confirmation.jsonl",
            publication_event_path=root / "publication.jsonl", report_model_event_path=root / "models.jsonl",
            export_event_path=root / "exports.jsonl", export_bundle_root=root / "bundles",
            workflow_event_path=root / "workflows.jsonl", notification_event_path=root / "notifications.jsonl",
            audit_event_path=root / "audit.jsonl",
            secret_values={"KMFA_LOCAL_AUTH_KEY": self.auth_value, "KMFA_SESSION_SIGNING_KEY": self.signing_value},
        )

    def tearDown(self) -> None:
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=3); self.temporary.cleanup()

    def request(self, path, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request_headers = dict(headers or {})
        if data:
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path, data=data, headers=request_headers
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def login(self, username="finance.local", credential=None):
        return self.request("/api/security-audit/login", {"username": username, "credential": credential or self.auth_value})

    def test_page_and_notification_link_are_available(self) -> None:
        text = urllib.request.urlopen(self.base_url + "/security-audit").read().decode("utf-8")
        self.assertIn("安全与审计必须先于生产操作", text)
        predecessor = urllib.request.urlopen(self.base_url + "/notification-delivery").read().decode("utf-8")
        self.assertIn("/security-audit", predecessor)

    def test_options_and_empty_snapshot_hide_secret_values(self) -> None:
        status, options = self.request("/api/security-audit/options")
        _, snapshot = self.request("/api/security-audit")
        encoded = json.dumps(options, ensure_ascii=False)
        self.assertEqual((status, options["role_count"], options["secret_reference_count"], options["attack_category_count"]), (200, 4, 2, 5))
        self.assertNotIn(self.auth_value, encoded); self.assertNotIn(self.signing_value, encoded)
        self.assertEqual((snapshot["audit"]["audit_event_count"], snapshot["high_vulnerability_count"]), (0, 0))

    def test_login_success_and_failure_are_audited_without_credentials(self) -> None:
        status, login = self.login()
        denied_status, denied = self.login(credential=self.signing_value)
        _, snapshot = self.request(
            "/api/security-audit?action_type=LOGIN",
            headers={"X-KMFA-Session": login["session_token"]},
        )
        encoded = json.dumps(snapshot, ensure_ascii=False)
        self.assertEqual((status, login["authenticated"], login["role"]), (201, True, "FINANCE_ADMIN"))
        self.assertEqual((denied_status, denied["code"]), (401, "AUTHENTICATION_FAILED"))
        self.assertEqual(snapshot["query"]["query_result_count"], 2)
        self.assertNotIn(self.auth_value, encoded); self.assertNotIn(self.signing_value, encoded)

    def test_authorized_actions_and_query_filters(self) -> None:
        _, login = self.login(); token = login["session_token"]
        for action in ("SENSITIVE_VIEW", "PROCESSING", "PARAMETER_CHANGE", "PUBLICATION"):
            status, value = self.request("/api/security-audit/action", {
                "session_token": token, "action_type": action,
                "subject_ref": f"SUBJECT::{action}", "company_ref": "COMPANY::SYNTHETIC-A",
            })
            self.assertEqual((status, value["result"]), (201, "SUCCESS"))
        query = urllib.parse.urlencode({"action_type": "PUBLICATION", "result": "SUCCESS"})
        _, snapshot = self.request(
            "/api/security-audit?" + query,
            headers={"X-KMFA-Session": token},
        )
        self.assertEqual(snapshot["query"]["query_result_count"], 1)

    def test_readonly_permission_and_cross_company_scope_are_denied(self) -> None:
        _, readonly = self.login("readonly.local")
        status, denied = self.request("/api/security-audit/action", {
            "session_token": readonly["session_token"], "action_type": "PARAMETER_CHANGE",
            "subject_ref": "PARAMETER::RUNTIME-001", "company_ref": "COMPANY::SYNTHETIC-A",
        })
        _, finance = self.login()
        other_status, other = self.request("/api/security-audit/action", {
            "session_token": finance["session_token"], "action_type": "SENSITIVE_VIEW",
            "subject_ref": "REPORT::RUNTIME-001", "company_ref": "COMPANY::SYNTHETIC-B",
        })
        self.assertEqual((status, denied["code"]), (403, "PERMISSION_DENIED"))
        self.assertEqual((other_status, other["code"]), (403, "COMPANY_SCOPE_DENIED"))

    def test_four_attack_probe_categories_are_rejected(self) -> None:
        for category in ("INJECTION", "PATH_TRAVERSAL", "MALICIOUS_FILE", "FORMULA_INJECTION"):
            status, value = self.request("/api/security-audit/attack-probe", {"category": category})
            self.assertEqual((status, value["category"], value["rejected"]), (200, category, True))
        _, snapshot = self.request("/api/security-audit")
        self.assertEqual(snapshot["rejected_attack_count"], 4)

    def test_direct_input_endpoints_block_dangerous_payloads(self) -> None:
        for body, code in (
            ({"kind": "TEXT", "value": "<script>alert(1)</script>"}, "INJECTION_BLOCKED"),
            ({"kind": "PATH", "value": "../../private"}, "PATH_TRAVERSAL_BLOCKED"),
            ({"kind": "FORMULA", "value": "=1+1"}, "FORMULA_INJECTION_BLOCKED"),
            ({"kind": "FILE", "filename": "report.pdf", "content_base64": base64.b64encode(b"MZ" + b"0" * 32).decode()}, "EXECUTABLE_FILE_BLOCKED"),
        ):
            status, value = self.request("/api/security-audit/input", body)
            self.assertEqual((status, value["code"]), (400, code))

    def test_sensitive_download_requires_authenticated_non_public_delivery(self) -> None:
        _, login = self.login(); token = login["session_token"]
        status, allowed = self.request("/api/security-audit/download", {
            "session_token": token, "artifact_ref": "ARTIFACT::RUNTIME-001",
            "company_ref": "COMPANY::SYNTHETIC-A", "classification": "SENSITIVE", "delivery_mode": "AUTHENTICATED",
        })
        denied_status, denied = self.request("/api/security-audit/download", {
            "session_token": token, "artifact_ref": "ARTIFACT::RUNTIME-002",
            "company_ref": "COMPANY::SYNTHETIC-A", "classification": "SENSITIVE", "delivery_mode": "PUBLIC_LINK",
        })
        self.assertEqual((status, allowed["allowed"], allowed["public_link_created"]), (200, True, False))
        self.assertEqual((denied_status, denied["code"]), (403, "PUBLIC_LINK_BLOCKED"))

    def test_tamper_probe_blocks_continuation_without_corrupting_live_chain(self) -> None:
        self.login()
        status, value = self.request("/api/security-audit/tamper-probe", {})
        _, snapshot = self.request("/api/security-audit")
        self.assertEqual((status, value["tamper_detected"], value["production_continuation_allowed"]), (200, True, False))
        self.assertTrue(snapshot["audit"]["chain_valid"])

    def test_audit_persists_across_new_workbench_instance(self) -> None:
        self.login(); before = self.server.security_workbench.audit.snapshot()
        reloaded = runtime.kernel.SecurityWorkbench(
            self.server.security_workbench.audit.path,
            secret_values={"KMFA_LOCAL_AUTH_KEY": self.auth_value, "KMFA_SESSION_SIGNING_KEY": self.signing_value},
        ).audit.snapshot()
        self.assertEqual((before["audit_event_count"], reloaded["audit_event_count"]), (1, 1))
        self.assertTrue(reloaded["chain_valid"])


if __name__ == "__main__":
    unittest.main()
