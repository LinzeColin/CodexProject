import json
import unittest

from KMFA.tools.project_composite_key import (
    MATCHING_WEIGHTS_BPS,
    REQUIRED_COMPONENTS,
    build_default_project_composite_key,
    build_identity_profile,
    score_project_match,
    validate_project_composite_key_artifacts,
)


EVIDENCE_REF = "KMFA/stage_artifacts/S08_P1_project_composite_key/human/test_results.md"
SOURCE_HASH_A = "sha256:" + "a" * 64
SOURCE_HASH_B = "sha256:" + "b" * 64


def full_components(source_hash: str = SOURCE_HASH_A) -> dict[str, str]:
    return {
        "contract_number": "KMFA-HT-2026-001",
        "project_name": "SYNTHETIC_PROJECT_ALPHA",
        "counterparty": "SYNTHETIC_COUNTERPARTY_ALPHA",
        "company_entity": "SYNTHETIC_ENTITY_ALPHA",
        "occurrence_or_project_date": "2026-06-30",
        "amount_signature": "amount-cents:12345600",
        "responsible_person": "SYNTHETIC_OWNER_ALPHA",
        "source_hash": source_hash,
    }


class ProjectCompositeKeyTests(unittest.TestCase):
    def test_full_component_match_is_strong_and_public_safe(self) -> None:
        authority = build_identity_profile(
            profile_id="IDP-SYN-AUTH-001",
            source_ref="SRC-SYN-AUTH-001",
            components=full_components(),
            private_ref_prefix="private://KMFA/S08-P1/auth",
        )
        candidate = build_identity_profile(
            profile_id="IDP-SYN-CAND-001",
            source_ref="SRC-SYN-CAND-001",
            components=full_components(),
            private_ref_prefix="private://KMFA/S08-P1/candidate",
        )

        result = score_project_match(authority, candidate, evidence_ref=EVIDENCE_REF)

        self.assertEqual(result["score_bps"], 10000)
        self.assertEqual(result["match_decision"], "strong_auto_match")
        self.assertFalse(result["manual_review_required"])
        self.assertEqual(result["matched_weight_bps"], sum(MATCHING_WEIGHTS_BPS.values()))
        self.assertEqual(set(result["matched_components"]), set(REQUIRED_COMPONENTS))
        public_payload = json.dumps([authority, candidate, result], ensure_ascii=False, sort_keys=True)
        for forbidden_value in full_components().values():
            if forbidden_value.startswith("sha256:"):
                continue
            self.assertNotIn(forbidden_value, public_payload)
        for forbidden_key in (
            "raw_value",
            "normalized_value",
            "contract_number_plaintext",
            "project_name_plaintext",
            "counterparty_plaintext",
            "source_header_text",
        ):
            self.assertNotIn(forbidden_key, public_payload)

    def test_missing_single_component_does_not_block_matching(self) -> None:
        authority = build_identity_profile(
            profile_id="IDP-SYN-AUTH-001",
            source_ref="SRC-SYN-AUTH-001",
            components=full_components(),
            private_ref_prefix="private://KMFA/S08-P1/auth",
        )
        missing_contract = full_components()
        del missing_contract["contract_number"]
        candidate = build_identity_profile(
            profile_id="IDP-SYN-CAND-002",
            source_ref="SRC-SYN-CAND-002",
            components=missing_contract,
            private_ref_prefix="private://KMFA/S08-P1/candidate",
        )

        result = score_project_match(authority, candidate, evidence_ref=EVIDENCE_REF)

        self.assertEqual(result["score_bps"], 8000)
        self.assertEqual(result["missing_components"], ["contract_number"])
        self.assertFalse(result["blocked_by_missing_single_field"])
        self.assertEqual(result["match_decision"], "human_review_required")
        self.assertTrue(result["manual_review_required"])

    def test_below_strong_threshold_enters_manual_review_queue(self) -> None:
        authority = build_identity_profile(
            profile_id="IDP-SYN-AUTH-001",
            source_ref="SRC-SYN-AUTH-001",
            components=full_components(),
            private_ref_prefix="private://KMFA/S08-P1/auth",
        )
        weak_candidate_components = {
            "project_name": "SYNTHETIC_PROJECT_ALPHA",
            "counterparty": "SYNTHETIC_COUNTERPARTY_ALPHA",
            "company_entity": "SYNTHETIC_ENTITY_ALPHA",
            "occurrence_or_project_date": "2026-06-30",
        }
        candidate = build_identity_profile(
            profile_id="IDP-SYN-CAND-003",
            source_ref="SRC-SYN-CAND-003",
            components=weak_candidate_components,
            private_ref_prefix="private://KMFA/S08-P1/candidate",
        )

        result = score_project_match(authority, candidate, evidence_ref=EVIDENCE_REF)

        self.assertEqual(result["score_bps"], 5500)
        self.assertEqual(result["match_decision"], "human_review_required")
        self.assertTrue(result["manual_review_required"])
        self.assertEqual(result["review_reason"], "score_below_strong_threshold")
        self.assertEqual(result["manual_review_queue_record"]["queue_type"], "project_identity_manual_review")
        self.assertFalse(result["manual_review_queue_record"]["auto_merge_allowed"])

    def test_default_s08p1_artifacts_cover_required_components_thresholds_and_review(self) -> None:
        manifest, profiles, match_results, review_queue = build_default_project_composite_key(
            generated_at="2026-06-30T20:00:00+10:00"
        )
        validate_project_composite_key_artifacts(manifest, profiles, match_results, review_queue)

        self.assertEqual(set(REQUIRED_COMPONENTS), set(manifest["required_components"]))
        self.assertEqual(sum(manifest["matching_weights_bps"].values()), 10000)
        self.assertEqual(manifest["thresholds_bps"]["strong_auto_match"], 8500)
        self.assertEqual(manifest["thresholds_bps"]["human_review"], 7000)
        self.assertFalse(manifest["stage_scope"]["fact_layer_scope_included"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertTrue(any(item["match_decision"] == "strong_auto_match" for item in match_results))
        self.assertTrue(any(item["match_decision"] == "human_review_required" for item in match_results))
        self.assertEqual(len(review_queue), 2)


if __name__ == "__main__":
    unittest.main()
