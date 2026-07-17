from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from KMFA.tools import v015_s06_p2_authorized_resolution as subject
from KMFA.tools import v015_s06_p2_golden_baseline_lock as kernel
from KMFA.tests.test_v015_s06_p2_golden_baseline_lock import synthetic_packet, valid_signoff


class ParsingTests(unittest.TestCase):
    def test_spaced_money_and_combined_percentage_are_exact_cents(self) -> None:
        candidate = {
            "field_family": "COST_CATEGORY",
            "raw_text": "（一）原材料 520 00 2 20%",
            "original_display_tokens": ["520 00 2 20%"],
        }
        self.assertEqual(subject.money_cents(candidate), 52000)

    def test_management_percentage_and_missing_insurance_are_not_money(self) -> None:
        management = {
            "field_family": "COST_CATEGORY",
            "raw_text": "分摊的管理费用（合同的2%） 1 200 00 5 08%",
            "original_display_tokens": ["2%", "1 200 00 5 08%"],
        }
        insurance = {
            "field_family": "COST_CATEGORY", "raw_text": "（三）保险费",
            "original_display_tokens": [],
        }
        self.assertEqual(subject.money_cents(management), 120000)
        self.assertEqual(subject.money_cents(insurance), 0)

    def test_spaced_margin_is_integer_basis_points(self) -> None:
        candidate = {"original_display_tokens": ["36 369 50 60 62%"]}
        self.assertEqual(subject.margin_basis_points(candidate), 6062)


class AuthorizationTests(unittest.TestCase):
    def test_authorization_record_is_digest_bound(self) -> None:
        record = subject.build_authorization(
            "全部同意，由你决定", "thread-private", "2026-07-15T06:00:00+10:00",
        )
        self.assertEqual(kernel.validate_authorization_record(record), record["record_digest"])
        tampered = copy.deepcopy(record)
        tampered["decision_authority_granted"] = False
        with self.assertRaises(kernel.GoldenBaselineError):
            kernel.validate_authorization_record(tampered)

    def test_authorized_agent_signoff_requires_private_bound_record(self) -> None:
        packet = synthetic_packet()
        signoff = valid_signoff(packet)
        authorization = subject.build_authorization(
            "全部同意，由你决定", "thread-private", "2026-07-15T06:00:00+10:00",
        )
        signoff["confirmer"] = {
            "identity": kernel.AUTHORIZED_AGENT_IDENTITY,
            "role": kernel.AUTHORIZED_AGENT_ROLE,
            "confirmed_at": "2026-07-15T06:00:00+10:00",
            "basis": (
                f"{subject.POLICY_VERSION};"
                f"AUTHORIZATION_RECORD_DIGEST={authorization['record_digest']}"
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authorization.json"
            path.write_text(json.dumps(authorization, ensure_ascii=False), encoding="utf-8")
            with patch.object(kernel, "PRIVATE_AUTHORIZATION_PATH", path):
                self.assertTrue(kernel.validate_signoff(signoff, packet))
                signoff["confirmer"]["basis"] = subject.POLICY_VERSION
                with self.assertRaises(kernel.GoldenBaselineError):
                    kernel.validate_signoff(signoff, packet)


class RealPacketPolicyTests(unittest.TestCase):
    def test_current_private_packet_resolves_without_guessing_or_cent_difference(self) -> None:
        packet = json.loads(kernel.PRIVATE_PACKET_PATH.read_text(encoding="utf-8"))
        decisions = subject.build_decisions(packet)
        counts = {name: sum(row["decision"] == name for row in decisions) for name in ("ACCEPT", "REJECT")}
        self.assertEqual(counts, {"ACCEPT": 92, "REJECT": 65})
        workbook_ids = {
            row["candidate_id"] for row in packet["candidate_records"]
            if row["source_ref"] == subject.WORKBOOK_SOURCE_REF
        }
        self.assertTrue(all(
            row["decision"] == "REJECT" for row in decisions
            if row["candidate_id"] in workbook_ids
        ))


if __name__ == "__main__":
    unittest.main()
