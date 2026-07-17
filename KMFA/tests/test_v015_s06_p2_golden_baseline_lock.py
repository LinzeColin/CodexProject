from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools import v015_s06_p2_golden_baseline_lock as subject


def synthetic_packet() -> dict:
    families = list(subject.FIELD_FAMILIES)
    rows = []
    for index in range(233):
        family = families[index] if index < len(families) else "PROJECT_IDENTITY"
        rows.append({
            "candidate_id": f"S06P2-CAND-{index:024d}",
            "source_ref": f"S06P1-SRC-{(index % 9) + 1:03d}",
            "source_locator": f"PRIVATE_LOCATOR_{index}",
            "field_family": family,
            "raw_text": f"private value {index}",
            "candidate_status": "PENDING_HUMAN_DECISION",
            "expected_canonical_unit": subject.EXPECTED_UNITS[family],
        })
    body = {
        "schema_version": subject.PRIVATE_PACKET_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": subject.RUN_PHASE_ID,
        "candidate_count": len(rows),
        "field_family_counts": dict(sorted(subject.Counter(row["field_family"] for row in rows).items())),
        "candidate_records": rows,
        "raw_mutation_performed": False,
        "human_signoff_required": True,
        "golden_lock_allowed": False,
    }
    return {**body, "packet_digest": subject._sha256(body)}


def valid_signoff(packet: dict) -> dict:
    values = {
        "PROJECT_IDENTITY": ("PROJECT-PRIVATE", "TEXT", "NOT_APPLICABLE"),
        "CONTRACT_AMOUNT": (10000, "CNY_CENT", "TAX_INCLUDED"),
        "TOTAL_EXPENDITURE": (6000, "CNY_CENT", "TAX_INCLUDED"),
        "GROSS_PROFIT": (4000, "CNY_CENT", "TAX_INCLUDED"),
        "GROSS_MARGIN": (4000, "BASIS_POINT", "NOT_APPLICABLE"),
        "COST_CATEGORY": (6000, "CNY_CENT", "TAX_INCLUDED"),
    }
    accepted_families = set()
    decisions = []
    for candidate in packet["candidate_records"]:
        family = candidate["field_family"]
        if family not in accepted_families:
            value, unit, tax_status = values[family]
            decisions.append({
                "candidate_id": candidate["candidate_id"],
                "decision": "ACCEPT",
                "project_ref": "PROJECT-001",
                "canonical_value": value,
                "unit": unit,
                "tax_status": tax_status,
                "business_meaning": f"authoritative {family}",
                "confirmed_source_locator": candidate["source_locator"],
                "category_key": "CATEGORY-001" if family == "COST_CATEGORY" else None,
                "rejection_reason": None,
            })
            accepted_families.add(family)
        else:
            decisions.append({
                "candidate_id": candidate["candidate_id"],
                "decision": "REJECT",
                "project_ref": None,
                "canonical_value": None,
                "unit": None,
                "tax_status": None,
                "business_meaning": None,
                "confirmed_source_locator": None,
                "category_key": None,
                "rejection_reason": "not selected as authoritative field",
            })
    return {
        "schema_version": subject.PRIVATE_SIGNOFF_SCHEMA,
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": subject.RUN_PHASE_ID,
        "packet_digest": packet["packet_digest"],
        "baseline_version": "S06P2-GOLDEN-0001",
        "previous_record_hash": None,
        "correction_reason": None,
        "confirmer": {
            "identity": "owner-private",
            "role": "data-owner",
            "confirmed_at": "2026-07-15T02:00:00+10:00",
            "basis": "source-by-source human review",
        },
        "authorization_statement": subject.AUTHORIZATION_STATEMENT,
        "decision_rows": decisions,
    }


class SignoffGateTests(unittest.TestCase):
    def test_template_and_public_projection_remain_closed(self) -> None:
        packet = synthetic_packet()
        template = subject.build_signoff_template(packet)
        self.assertEqual(len(template["decision_rows"]), 233)
        self.assertTrue(all(row["decision"] == "PENDING" for row in template["decision_rows"]))
        projection = subject.public_projection(packet)
        self.assertEqual(projection["human_signoff_status"], "MISSING")
        self.assertEqual(projection["phase_acceptance_status"], "BLOCKED_BY_MISSING_SIGNOFF")
        self.assertEqual(projection["source_group_count"], 9)
        self.assertTrue(projection["private_review_source_filter_available"])
        self.assertTrue(projection["private_review_stable_source_order"])
        self.assertFalse(projection["private_review_automatic_inference"])
        self.assertFalse(projection["golden_version_locked"])
        self.assertFalse(projection["s06_p3_entry_allowed"])

    def test_candidate_packet_count_is_bound_to_current_p1_output_not_a_hardcode(self) -> None:
        packet = synthetic_packet()
        body = {key: value for key, value in packet.items() if key != "packet_digest"}
        body["candidate_records"] = body["candidate_records"][:6]
        body["candidate_count"] = len(body["candidate_records"])
        body["field_family_counts"] = dict(sorted(subject.Counter(
            row["field_family"] for row in body["candidate_records"]
        ).items()))
        current = {**body, "packet_digest": subject._sha256(body)}
        subject.validate_candidate_packet(current)
        self.assertEqual(len(subject.build_signoff_template(current)["decision_rows"]), 6)

    def test_explicit_packet_bound_signoff_is_required(self) -> None:
        packet = synthetic_packet()
        signoff = valid_signoff(packet)
        signoff["authorization_statement"] = None
        with self.assertRaises(subject.GoldenBaselineError):
            subject.validate_signoff(signoff, packet)
        signoff = valid_signoff(packet)
        signoff["packet_digest"] = "wrong"
        with self.assertRaises(subject.GoldenBaselineError):
            subject.validate_signoff(signoff, packet)

    def test_every_candidate_decision_and_timezone_are_required(self) -> None:
        packet = synthetic_packet()
        signoff = valid_signoff(packet)
        signoff["decision_rows"][7]["decision"] = "PENDING"
        with self.assertRaises(subject.GoldenBaselineError):
            subject.validate_signoff(signoff, packet)
        signoff = valid_signoff(packet)
        signoff["confirmer"]["confirmed_at"] = "2026-07-15T02:00:00"
        with self.assertRaises(subject.GoldenBaselineError):
            subject.validate_signoff(signoff, packet)


class SummaryAndVersionTests(unittest.TestCase):
    def test_exact_integer_cent_summary_passes(self) -> None:
        packet = synthetic_packet()
        accepted = subject.validate_signoff(valid_signoff(packet), packet)
        summaries = subject.build_project_summaries(accepted)
        self.assertEqual(summaries[0]["money_difference_cents"], 0)
        self.assertEqual(summaries[0]["category_total_cents"], 6000)
        self.assertEqual(summaries[0]["gross_margin_basis_points"], 4000)
        self.assertNotIsInstance(summaries[0]["revenue_cents"], float)

    def test_one_cent_difference_fails(self) -> None:
        packet = synthetic_packet()
        signoff = valid_signoff(packet)
        profit = next(
            row for row in signoff["decision_rows"]
            if row["decision"] == "ACCEPT"
            and packet["candidate_records"][int(row["candidate_id"].split("-")[-1])]["field_family"] == "GROSS_PROFIT"
        )
        profit["canonical_value"] = 3999
        accepted = subject.validate_signoff(signoff, packet)
        with self.assertRaises(subject.GoldenBaselineError):
            subject.build_project_summaries(accepted)

    def test_correction_appends_new_hash_chained_version(self) -> None:
        packet = synthetic_packet()
        first_signoff = valid_signoff(packet)
        first = subject.build_version_record(first_signoff, packet, [])
        second_signoff = copy.deepcopy(first_signoff)
        second_signoff["baseline_version"] = "S06P2-GOLDEN-0002"
        second_signoff["previous_record_hash"] = first["record_hash"]
        second_signoff["correction_reason"] = "owner-approved correction"
        second = subject.build_version_record(second_signoff, packet, [first])
        self.assertEqual(second["version_sequence"], 2)
        self.assertEqual(second["previous_record_hash"], first["record_hash"])
        self.assertFalse(second["history_overwrite_allowed"])

    def test_public_projection_drops_private_values_and_identity(self) -> None:
        packet = synthetic_packet()
        signoff = valid_signoff(packet)
        first = subject.build_version_record(signoff, packet, [])
        projection = subject.public_projection(packet, signoff, [first])
        rendered = json.dumps(projection, ensure_ascii=False)
        self.assertNotIn("PROJECT-PRIVATE", rendered)
        self.assertNotIn("owner-private", rendered)
        self.assertNotIn("PRIVATE_LOCATOR", rendered)
        self.assertEqual(projection["public_raw_value_count"], 0)
        self.assertEqual(projection["public_confirmer_identity_count"], 0)
        self.assertEqual(projection["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")


if __name__ == "__main__":
    unittest.main()
