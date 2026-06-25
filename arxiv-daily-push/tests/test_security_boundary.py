from __future__ import annotations

import unittest

from arxiv_daily_push.security_boundary import (
    build_supply_chain_baseline,
    build_trust_boundary_receipt,
    sanitize_public_url,
    typed_fact,
    typed_inference,
    validate_supply_chain_baseline,
    validate_trust_boundary_receipt,
    validate_typed_frontstage,
)


class SecurityBoundaryTests(unittest.TestCase):
    def test_sanitize_public_url_blocks_unsafe_schemes_credentials_and_hosts(self) -> None:
        self.assertEqual(sanitize_public_url("javascript:alert(1)"), "")
        self.assertEqual(sanitize_public_url("data:text/html,boom"), "")
        self.assertEqual(sanitize_public_url("file:///etc/passwd"), "")
        self.assertEqual(sanitize_public_url("https://user:pass@arxiv.org/abs/2401.00001"), "")
        self.assertEqual(sanitize_public_url("https://evil.test/abs/2401.00001"), "")
        self.assertEqual(sanitize_public_url("http://arxiv.org/abs/2401.00001"), "https://arxiv.org/abs/2401.00001")

    def test_trust_boundary_receipt_marks_source_content_untrusted_and_disables_tools(self) -> None:
        receipt = build_trust_boundary_receipt(
            {
                "canonical_url": "https://arxiv.org/abs/2401.00001",
                "content_refs": [{"ref_type": "abstract", "uri": "https://arxiv.org/abs/2401.00001"}],
            }
        )

        self.assertEqual(receipt["source_content_trust"], "UNTRUSTED_DATA")
        self.assertFalse(receipt["tool_policy"]["source_content_can_request_tools"])
        self.assertFalse(receipt["tool_policy"]["model_can_read_secrets"])
        self.assertFalse(validate_trust_boundary_receipt(receipt))

    def test_typed_frontstage_requires_fact_and_inference_bindings(self) -> None:
        frontstage = {
            "typed_statements": [
                typed_fact("Fact text", claim_ids=["claim:1"], evidence_ids=["stable_url:https://arxiv.org/abs/1"]),
                typed_inference(
                    "Inference text",
                    premise_claim_ids=["claim:1"],
                    reasoning_version="test-v1",
                    confidence=0.7,
                ),
                {
                    "statement_type": "action",
                    "text": "Review only",
                    "premise_claim_ids": ["claim:1"],
                    "action_scope": "local_review",
                },
            ]
        }

        self.assertFalse(validate_typed_frontstage(frontstage, allowed_claim_ids=["claim:1"]))
        frontstage["typed_statements"][0]["claim_ids"] = ["claim:missing"]
        self.assertIn("unknown claim ids", " ".join(validate_typed_frontstage(frontstage, allowed_claim_ids=["claim:1"])))

    def test_supply_chain_baseline_declares_local_controls_without_side_effects(self) -> None:
        baseline = build_supply_chain_baseline(
            workflow_files=[".github/workflows/project-governance.yml"],
            dependency_files=["arxiv-daily-push/pyproject.toml"],
        )

        self.assertFalse(baseline["production_side_effects"])
        self.assertFalse(validate_supply_chain_baseline(baseline))


if __name__ == "__main__":
    unittest.main()
