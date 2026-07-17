from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from KMFA.tools import v015_s22_p2_security_audit as security


class SecurityAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.auth_value = hashlib.sha256((self.temporary.name + "auth").encode()).hexdigest()
        self.signing_value = hashlib.sha256((self.temporary.name + "sign").encode()).hexdigest()
        self.workbench = security.SecurityWorkbench(
            self.root / "audit.jsonl",
            secret_values={
                "KMFA_LOCAL_AUTH_KEY": self.auth_value,
                "KMFA_SESSION_SIGNING_KEY": self.signing_value,
            },
        )
        self.now = datetime(2026, 7, 17, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def login(self, username: str = "finance.local", session_id: str = "A1" * 12):
        return self.workbench.sessions.authenticate(
            username, self.auth_value, occurred_at=self.now, session_id=session_id,
        )

    def test_production_cannot_disable_audit(self) -> None:
        with self.assertRaisesRegex(security.SecurityError, "生产运行不能关闭审计"):
            security.AuditJournal(self.root / "disabled.jsonl", enabled=False, environment="PRODUCTION")

    def test_audit_chain_covers_required_actions_and_is_queryable(self) -> None:
        login = self.login(); token = login["session_token"]
        for index, action in enumerate(security.REQUIRED_AUDIT_ACTION_TYPES[1:], start=1):
            self.workbench.sessions.perform(
                token, action_type=action, subject_ref=f"SUBJECT::{action}",
                company_ref="COMPANY::SYNTHETIC-A", occurred_at=self.now + timedelta(minutes=index),
            )
        snapshot = self.workbench.audit.snapshot()
        self.assertEqual(snapshot["required_action_type_coverage_count"], 5)
        self.assertTrue(snapshot["chain_valid"] and snapshot["append_only"])
        self.assertEqual(self.workbench.audit.query(action_type="LOGIN")["query_result_count"], 1)

    def test_audit_tamper_and_in_place_replace_fail_closed(self) -> None:
        self.login()
        with self.assertRaises(security.SecurityError):
            self.workbench.audit.replace_event("AUDIT-S22P2-000001", {})
        rows = self.workbench.audit.events(); rows[0]["reason_code"] = "CHANGED"
        self.workbench.audit.path.write_text(json.dumps(rows[0]) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(security.SecurityError, "已被修改"):
            self.workbench.audit.events()

    def test_secret_provider_accepts_only_environment_references_without_exposure(self) -> None:
        inventory = self.workbench.secrets.inventory()
        self.assertEqual(len(inventory), 2)
        self.assertTrue(all(row["source"] == "ENVIRONMENT" and row["value_exposed"] is False for row in inventory))
        self.assertNotIn(self.auth_value, json.dumps(inventory))
        with self.assertRaises(security.SecurityError):
            self.workbench.secrets.resolve("UNTRACKED_REFERENCE")

    def test_missing_and_placeholder_runtime_values_fail_closed(self) -> None:
        missing = security.SecretProvider({})
        with self.assertRaisesRegex(security.SecurityError, "未配置"):
            missing.resolve("KMFA_LOCAL_AUTH_KEY")
        weak = security.SecretProvider({"KMFA_LOCAL_AUTH_KEY": "placeholder-" * 4})
        with self.assertRaisesRegex(security.SecurityError, "占位值"):
            weak.resolve("KMFA_LOCAL_AUTH_KEY")

    def test_login_failure_is_audited_without_username_or_credential(self) -> None:
        with self.assertRaises(security.SecurityError):
            self.workbench.sessions.authenticate("finance.local", self.signing_value, occurred_at=self.now)
        encoded = json.dumps(self.workbench.audit.events(), ensure_ascii=False)
        self.assertNotIn("finance.local", encoded)
        self.assertNotIn(self.signing_value, encoded)
        self.assertEqual(self.workbench.audit.events()[0]["result"], "DENIED")

    def test_signed_session_rejects_tamper_and_expiry(self) -> None:
        login = self.login(); token = login["session_token"]
        self.assertEqual(self.workbench.sessions.decode(token, occurred_at=self.now)["role"], "FINANCE_ADMIN")
        with self.assertRaisesRegex(security.SecurityError, "会话无效"):
            self.workbench.sessions.decode(token[:-1] + ("A" if token[-1] != "A" else "B"), occurred_at=self.now)
        with self.assertRaisesRegex(security.SecurityError, "会话已过期"):
            self.workbench.sessions.decode(token, occurred_at=self.now + timedelta(minutes=31))

    def test_role_and_company_permissions_are_fail_closed_and_audited(self) -> None:
        readonly = self.login("readonly.local", "B2" * 12)
        with self.assertRaisesRegex(security.SecurityError, "没有此操作权限"):
            self.workbench.sessions.perform(
                readonly["session_token"], action_type="PARAMETER_CHANGE",
                subject_ref="PARAMETER::SYNTHETIC-001", company_ref="COMPANY::SYNTHETIC-A",
                occurred_at=self.now + timedelta(minutes=1),
            )
        finance = self.login("finance.local", "C3" * 12)
        with self.assertRaisesRegex(security.SecurityError, "其他主体"):
            self.workbench.sessions.perform(
                finance["session_token"], action_type="SENSITIVE_VIEW",
                subject_ref="REPORT::SYNTHETIC-001", company_ref="COMPANY::SYNTHETIC-B",
                occurred_at=self.now + timedelta(minutes=2),
            )
        denied = [row for row in self.workbench.audit.events() if row["result"] == "DENIED"]
        self.assertEqual(len(denied), 2)

    def test_injection_and_path_traversal_are_rejected(self) -> None:
        for value in ("<script>alert(1)</script>", "' OR 1=1 --", "; rm -rf /"):
            with self.assertRaisesRegex(security.SecurityError, "危险"):
                self.workbench.guard.validate_text(value)
        for value in ("../private", "/absolute/file", "folder\\..\\file"):
            with self.assertRaises(security.SecurityError):
                self.workbench.guard.validate_relative_path(value)
        self.assertTrue(self.workbench.guard.validate_relative_path("exports/report.pdf")["allowed"])

    def test_malicious_file_and_formula_injection_are_rejected(self) -> None:
        with self.assertRaisesRegex(security.SecurityError, "可执行文件"):
            self.workbench.guard.validate_file("report.pdf", b"MZ" + b"0" * 32)
        with self.assertRaisesRegex(security.SecurityError, "文件类型"):
            self.workbench.guard.validate_file("payload.sh", b"safe-looking")
        for cell in ("=1+1", "+cmd", "@SUM(A1)"):
            with self.assertRaisesRegex(security.SecurityError, "可执行公式"):
                self.workbench.guard.validate_csv_cell(cell)
        self.assertTrue(self.workbench.guard.validate_file("report.csv", b"name,status\nitem,ok")["allowed"])

    def test_sensitive_download_requires_auth_scope_and_no_public_link(self) -> None:
        login = self.login(); token = login["session_token"]
        allowed = self.workbench.guard.authorize_download(
            token, artifact_ref="ARTIFACT::SYNTHETIC-001", company_ref="COMPANY::SYNTHETIC-A",
            classification="SENSITIVE", delivery_mode="AUTHENTICATED", occurred_at=self.now + timedelta(minutes=1),
        )
        self.assertTrue(allowed["allowed"]); self.assertFalse(allowed["public_link_created"])
        with self.assertRaisesRegex(security.SecurityError, "公开链接"):
            self.workbench.guard.authorize_download(
                token, artifact_ref="ARTIFACT::SYNTHETIC-002", company_ref="COMPANY::SYNTHETIC-A",
                classification="SENSITIVE", delivery_mode="PUBLIC_LINK", occurred_at=self.now + timedelta(minutes=2),
            )

    def test_tamper_probe_detects_copy_without_mutating_live_audit(self) -> None:
        self.login(); before = copy.deepcopy(self.workbench.audit.events())
        result = self.workbench.tamper_probe()
        self.assertTrue(result["tamper_detected"])
        self.assertFalse(result["production_continuation_allowed"])
        self.assertEqual(before, self.workbench.audit.events())

    def test_public_verification_is_complete_and_boundary_safe(self) -> None:
        result = security.public_verification()
        self.assertEqual((result["public_check_count"], result["public_check_pass_count"], result["public_check_failed_count"]), (60, 60, 0))
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("/Users/", encoded)
        self.assertNotIn("KMFA_MetaData", encoded)


if __name__ == "__main__":
    unittest.main()
