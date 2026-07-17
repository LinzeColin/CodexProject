from __future__ import annotations

import copy
import http.client
import json
import stat
import tempfile
import threading
import unittest
from pathlib import Path

from KMFA.tests.test_v015_s06_p2_golden_baseline_lock import synthetic_packet, valid_signoff
from KMFA.tools import v015_s06_p2_golden_baseline_lock as kernel
from KMFA.tools import v015_s06_p2_signoff_review as review


TOKEN = "test-review-token-000000000000000000000000"


class ReviewServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.packet = synthetic_packet()
        self.template = kernel.build_signoff_template(self.packet)
        self.packet_path = self.root / "private_candidate_reconciliation.json"
        self.template_path = self.root / "private_human_signoff_template.json"
        self.draft_path = self.root / "private_human_signoff_draft.json"
        self.signoff_path = self.root / "private_human_signoff.json"
        self.ledger_before = (
            kernel.PRIVATE_VERSION_LEDGER_PATH.read_bytes()
            if kernel.PRIVATE_VERSION_LEDGER_PATH.exists()
            else None
        )
        self.packet_path.write_text(json.dumps(self.packet), encoding="utf-8")
        self.template_path.write_text(json.dumps(self.template), encoding="utf-8")
        self.server = review.build_server(
            self.packet_path,
            self.template_path,
            self.draft_path,
            self.signoff_path,
            port=0,
            token=TOKEN,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(
        self,
        method: str,
        path: str,
        value: dict | None = None,
        *,
        token: bool = False,
        origin: str | None = None,
    ) -> tuple[int, dict | str, dict[str, str]]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers: dict[str, str] = {}
        body = None
        if token:
            headers["X-KMFA-Review-Token"] = TOKEN
        if origin is not None:
            headers["Origin"] = origin
        if value is not None:
            body = json.dumps(value)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read().decode("utf-8")
        response_headers = {key: item for key, item in response.getheaders()}
        connection.close()
        if response_headers.get("Content-Type", "").startswith("application/json"):
            return response.status, json.loads(payload), response_headers
        return response.status, payload, response_headers

    def test_review_page_is_token_gated_local_and_private_data_is_not_in_html(self) -> None:
        status, _, _ = self.request("GET", "/review/wrong-token")
        self.assertEqual(status, 404)
        status, _, _ = self.request("GET", "/api/state")
        self.assertEqual(status, 404)
        status, page, headers = self.request("GET", f"/review/{TOKEN}")
        self.assertEqual(status, 200)
        self.assertIn("KMFA v1.5", page)
        self.assertIn('id="source"', page)
        self.assertIn("先按来源逐组处理", page)
        self.assertNotIn("PRIVATE_VALUE", page)
        self.assertEqual(headers["Cache-Control"], "no-store, max-age=0")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertIn("default-src 'none'", headers["Content-Security-Policy"])

        status, state, _ = self.request("GET", "/api/state", token=True)
        self.assertEqual(status, 200)
        self.assertEqual(state["packet"]["candidate_count"], 233)
        self.assertEqual(state["decision_counts"], {"PENDING": 233, "ACCEPT": 0, "REJECT": 0})

    def test_draft_requires_exact_origin_and_is_written_mode_0600(self) -> None:
        request = {"draft": copy.deepcopy(self.template)}
        status, _, _ = self.request(
            "PUT", "/api/draft", request, token=True, origin="http://malicious.invalid",
        )
        self.assertEqual(status, 403)
        self.assertFalse(self.draft_path.exists())

        request["draft"]["decision_rows"][0]["decision"] = "REJECT"
        request["draft"]["decision_rows"][0]["rejection_reason"] = "not authoritative"
        status, body, _ = self.request(
            "PUT", "/api/draft", request, token=True, origin=f"http://127.0.0.1:{self.port}",
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["saved"])
        self.assertEqual(body["decision_counts"], {"PENDING": 232, "ACCEPT": 0, "REJECT": 1})
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self.draft_path.stat().st_mode), 0o600)

    def test_incomplete_finalization_fails_closed_without_creating_signoff(self) -> None:
        draft = copy.deepcopy(self.template)
        draft["confirmer"] = {
            "identity": "owner-private",
            "role": "data-owner",
            "confirmed_at": "2026-07-15T02:00:00+10:00",
            "basis": "source-by-source human review",
        }
        draft["authorization_statement"] = kernel.AUTHORIZATION_STATEMENT
        status, body, _ = self.request(
            "POST",
            "/api/finalize",
            {"signoff": draft, "confirmation": kernel.AUTHORIZATION_STATEMENT},
            token=True,
            origin=f"http://127.0.0.1:{self.port}",
        )
        self.assertEqual(status, 400)
        self.assertIn("PENDING", body["error"])
        self.assertFalse(self.signoff_path.exists())

    def test_valid_signoff_is_created_once_but_golden_ledger_is_not_appended(self) -> None:
        signoff = valid_signoff(self.packet)
        candidates = {row["candidate_id"]: row for row in self.packet["candidate_records"]}
        for decision in signoff["decision_rows"]:
            family = candidates[decision["candidate_id"]]["field_family"]
            if decision["canonical_value"] is not None and family != "PROJECT_IDENTITY":
                decision["canonical_value"] = str(decision["canonical_value"])
        request = {"signoff": signoff, "confirmation": kernel.AUTHORIZATION_STATEMENT}
        status, body, _ = self.request(
            "POST", "/api/finalize", request, token=True,
            origin=f"http://127.0.0.1:{self.port}",
        )
        self.assertEqual(status, 201)
        self.assertTrue(body["finalized"])
        self.assertFalse(body["golden_version_appended"])
        self.assertEqual(body["resolved_candidate_count"], 233)
        self.assertEqual(stat.S_IMODE(self.signoff_path.stat().st_mode), 0o600)
        saved = json.loads(self.signoff_path.read_text(encoding="utf-8"))
        money = next(
            row for row in saved["decision_rows"]
            if row["decision"] == "ACCEPT"
            and candidates[row["candidate_id"]]["field_family"] == "CONTRACT_AMOUNT"
        )
        self.assertIsInstance(money["canonical_value"], int)
        ledger_after = (
            kernel.PRIVATE_VERSION_LEDGER_PATH.read_bytes()
            if kernel.PRIVATE_VERSION_LEDGER_PATH.exists()
            else None
        )
        self.assertEqual(ledger_after, self.ledger_before)

        original = self.signoff_path.read_bytes()
        status, body, _ = self.request(
            "POST", "/api/finalize", request, token=True,
            origin=f"http://127.0.0.1:{self.port}",
        )
        self.assertEqual(status, 409)
        self.assertIn("cannot be overwritten", body["error"])
        self.assertEqual(self.signoff_path.read_bytes(), original)

    def test_non_loopback_binding_is_rejected_before_server_creation(self) -> None:
        with self.assertRaises(review.ReviewError):
            review.build_server(
                self.packet_path,
                self.template_path,
                self.draft_path,
                self.signoff_path,
                host="0.0.0.0",
                token=TOKEN,
            )


if __name__ == "__main__":
    unittest.main()
