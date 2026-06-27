from __future__ import annotations

import unittest
from pathlib import Path

from arxiv_daily_push.security_boundary import (
    audit_supply_chain_ci_enforcement,
    audit_workflow_supply_chain,
    build_dependency_sbom,
    build_frontstage_evidence_a004_report,
    build_trust_boundary_a005_report,
    build_supply_chain_baseline,
    build_dependency_vulnerability_gate,
    build_trust_boundary_receipt,
    sanitize_public_url,
    typed_fact,
    typed_inference,
    validate_frontstage_evidence_a004_report,
    validate_supply_chain_baseline,
    validate_trust_boundary_a005_report,
    validate_trust_boundary_receipt,
    validate_typed_frontstage,
)


ROOT = Path(__file__).resolve().parents[2]
ADP_WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("arxiv-daily-push-*.yml")) + [
    ROOT / ".github" / "workflows" / "project-governance.yml"
]


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

    def test_frontstage_evidence_a004_report_passes_with_required_blocks(self) -> None:
        report = build_frontstage_evidence_a004_report(generated_at="2026-06-27T10:30:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_id"], "A-004")
        self.assertEqual(report["task_id"], "S2PMT01-FRONTSTAGE-EVIDENCE-A004")
        self.assertTrue(report["gates"]["typed_statement_schema_enforced"])
        self.assertTrue(report["gates"]["evidence_binding_enforced"])
        self.assertTrue(report["gates"]["unknown_claims_blocked"])
        self.assertTrue(report["gates"]["unsupported_foreground_claims_blocked"])
        self.assertFalse(report["p0_closure_claimed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(validate_frontstage_evidence_a004_report(report))

    def test_frontstage_evidence_a004_report_blocks_tampered_gate_or_closure(self) -> None:
        report = build_frontstage_evidence_a004_report(generated_at="2026-06-27T10:30:00+10:00")

        tampered = {**report, "p0_closure_claimed": True}
        self.assertIn(
            "p0_closure_claimed must be false for A-004 frontstage evidence",
            validate_frontstage_evidence_a004_report(tampered),
        )
        tampered = {**report, "probes": {**report["probes"], "unknown_claim_reference_blocks": False}}
        self.assertIn("unknown_claim_reference_blocks probe must pass", validate_frontstage_evidence_a004_report(tampered))
        tampered_invalid = {
            **report,
            "invalid_case_results": {
                **report["invalid_case_results"],
                "unsupported_foreground_claim": {"status": "pass", "errors": []},
            },
        }
        self.assertIn("unsupported_foreground_claim must be blocked", validate_frontstage_evidence_a004_report(tampered_invalid))

    def test_trust_boundary_a005_report_passes_with_required_blocks(self) -> None:
        report = build_trust_boundary_a005_report(generated_at="2026-06-27T11:30:00+10:00")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_id"], "A-005")
        self.assertEqual(report["task_id"], "S2PMT01-TRUST-BOUNDARY-A005")
        self.assertTrue(report["probes"]["source_content_labeled_untrusted"])
        self.assertTrue(report["probes"]["unsafe_url_schemes_blocked"])
        self.assertTrue(report["probes"]["source_content_tool_requests_blocked"])
        self.assertTrue(report["probes"]["secret_access_blocked"])
        self.assertTrue(report["gates"]["tool_and_secret_boundary_enforced"])
        self.assertFalse(report["p0_closure_claimed"])
        self.assertFalse(report["real_smtp_sent"])
        self.assertFalse(validate_trust_boundary_a005_report(report))

    def test_trust_boundary_a005_report_blocks_tampered_boundary_or_closure(self) -> None:
        report = build_trust_boundary_a005_report(generated_at="2026-06-27T11:30:00+10:00")

        tampered = {**report, "p0_closure_claimed": True}
        self.assertIn(
            "p0_closure_claimed must be false for A-005 trust-boundary evidence",
            validate_trust_boundary_a005_report(tampered),
        )
        tampered = {**report, "probes": {**report["probes"], "secret_access_blocked": False}}
        self.assertIn("secret_access_blocked probe must pass", validate_trust_boundary_a005_report(tampered))
        tampered_invalid = {
            **report,
            "invalid_case_results": {
                **report["invalid_case_results"],
                "model_can_read_secrets": {"status": "pass", "errors": []},
            },
        }
        self.assertIn("model_can_read_secrets must be blocked", validate_trust_boundary_a005_report(tampered_invalid))

    def test_supply_chain_baseline_declares_local_controls_without_side_effects(self) -> None:
        workflow_contents = {str(path.relative_to(ROOT)): path.read_text(encoding="utf-8") for path in ADP_WORKFLOWS}
        dependency_contents = {
            "arxiv-daily-push/pyproject.toml": (ROOT / "arxiv-daily-push" / "pyproject.toml").read_text(
                encoding="utf-8"
            )
        }
        baseline = build_supply_chain_baseline(
            workflow_files=sorted(workflow_contents),
            dependency_files=["arxiv-daily-push/pyproject.toml"],
            workflow_contents=workflow_contents,
            dependency_contents=dependency_contents,
            vulnerability_findings=[],
            approved_vulnerability_exceptions=[],
        )

        self.assertFalse(baseline["production_side_effects"])
        self.assertEqual(baseline["controls"]["workflow_audit"]["status"], "pass")
        self.assertEqual(baseline["controls"]["dependency_sbom"]["status"], "pass")
        self.assertEqual(baseline["controls"]["dependency_sbom"]["runtime_dependency_count"], 0)
        self.assertGreaterEqual(baseline["controls"]["dependency_sbom"]["build_dependency_count"], 1)
        self.assertEqual(baseline["controls"]["ci_enforcement_gate"]["status"], "pass")
        self.assertGreaterEqual(baseline["controls"]["workflow_audit"]["workflow_count"], 9)
        self.assertFalse(validate_supply_chain_baseline(baseline))

    def test_dependency_sbom_extracts_pyproject_runtime_and_build_dependencies(self) -> None:
        sbom = build_dependency_sbom(
            {
                "arxiv-daily-push/pyproject.toml": """
[project]
dependencies = ["requests>=2"]

[build-system]
requires = ["setuptools>=61", "wheel"]
"""
            }
        )

        self.assertEqual(sbom["status"], "pass")
        self.assertEqual(sbom["component_count"], 3)
        self.assertEqual(sbom["runtime_dependency_count"], 1)
        self.assertEqual(sbom["build_dependency_count"], 2)
        self.assertIn(
            {
                "name": "requests",
                "version_spec": ">=2",
                "scope": "runtime",
                "source_file": "arxiv-daily-push/pyproject.toml",
            },
            sbom["components"],
        )
        self.assertTrue(sbom["sbom_hash"])

    def test_supply_chain_baseline_blocks_missing_sbom_and_ci_enforcement(self) -> None:
        baseline = build_supply_chain_baseline(
            workflow_files=[".github/workflows/project-governance.yml"],
            dependency_files=["arxiv-daily-push/pyproject.toml"],
            workflow_contents={
                ".github/workflows/project-governance.yml": """
permissions:
  contents: read
jobs:
  governance:
    steps:
      - uses: actions/checkout@v5
"""
            },
            dependency_contents={},
            vulnerability_findings=[],
            approved_vulnerability_exceptions=[],
        )

        errors = "\n".join(validate_supply_chain_baseline(baseline))
        self.assertIn("dependency_sbom", errors)
        self.assertIn("ci_enforcement_gate", errors)

    def test_supply_chain_ci_enforcement_requires_security_boundary_test(self) -> None:
        blocked = audit_supply_chain_ci_enforcement(
            {
                ".github/workflows/project-governance.yml": """
steps:
  - run: python3 -m unittest arxiv-daily-push/tests/test_stage2_final_gate.py -q
"""
            }
        )
        passed = audit_supply_chain_ci_enforcement(
            {
                ".github/workflows/project-governance.yml": """
steps:
  - run: PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_security_boundary.py -q
"""
            }
        )

        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(passed["status"], "pass")
        self.assertEqual(passed["matches"][0]["path"], ".github/workflows/project-governance.yml")

    def test_supply_chain_audit_blocks_write_permissions_and_unknown_mutable_actions(self) -> None:
        audit = audit_workflow_supply_chain(
            {
                ".github/workflows/bad.yml": """
name: bad
permissions:
  contents: write
jobs:
  test:
    steps:
      - uses: third-party/example-action@v1
"""
            }
        )

        self.assertEqual(audit["status"], "blocked")
        self.assertIn("contents: write", " ".join(audit["issues"]))
        self.assertIn("not SHA-pinned or approved", " ".join(audit["issues"]))

    def test_dependency_vulnerability_gate_blocks_unapproved_high_findings(self) -> None:
        gate = build_dependency_vulnerability_gate(
            [{"finding_id": "PYSEC-TEST-001", "severity": "high", "package": "example"}],
            approved_exceptions=[],
        )

        self.assertEqual(gate["status"], "blocked")
        self.assertIn("has no approved exception", " ".join(gate["issues"]))
        baseline = build_supply_chain_baseline(
            workflow_files=[".github/workflows/project-governance.yml"],
            dependency_files=["arxiv-daily-push/pyproject.toml"],
            workflow_contents={".github/workflows/project-governance.yml": "permissions:\n  contents: read\nsteps:\n  - uses: actions/checkout@v5\n"},
            dependency_contents={
                "arxiv-daily-push/pyproject.toml": "[build-system]\nrequires = ['setuptools>=61']\n"
            },
            vulnerability_findings=[{"finding_id": "PYSEC-TEST-001", "severity": "high", "package": "example"}],
            approved_vulnerability_exceptions=[],
        )
        self.assertIn("dependency_vulnerability_gate", " ".join(validate_supply_chain_baseline(baseline)))

    def test_dependency_vulnerability_gate_accepts_complete_exception(self) -> None:
        gate = build_dependency_vulnerability_gate(
            [{"finding_id": "PYSEC-TEST-001", "severity": "critical", "package": "example"}],
            approved_exceptions=[
                {
                    "finding_id": "PYSEC-TEST-001",
                    "approved_by": "security-reviewer",
                    "expires_at": "2026-07-01",
                    "rationale": "test-only fixture exception",
                }
            ],
        )

        self.assertEqual(gate["status"], "pass")
        self.assertEqual(gate["issues"], [])


if __name__ == "__main__":
    unittest.main()
