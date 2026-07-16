from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import governance_artifact_policy as artifacts  # noqa: E402


class GovernanceArtifactPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = artifacts.load_policy(ROOT / "governance" / "artifact_policy.json")

    def test_current_repository_policy_and_locked_legacy_baselines_pass(self) -> None:
        summary = artifacts.audit_repository(root=ROOT)
        self.assertEqual(summary["status"], "PASS", summary["errors"])
        self.assertEqual(summary["duplicate_editable_truth_count"], 0)
        self.assertTrue(all(item["matches"] for item in summary["retained_legacy"]))
        openai_database = next(
            item
            for item in summary["retained_legacy"]
            if item["path"] == "OpenAIDatabase/docs/governance"
        )
        self.assertEqual(
            openai_database["current"],
            {
                "count": 14,
                "bytes": 334805,
                "sha256": "c455178e70d2dec8b94ed7cc25fd7a0a73da0b44977aae162bf1f7e6dbf86d01",
            },
        )

    def test_duplicate_editable_canonical_fact_domain_fails(self) -> None:
        policy = copy.deepcopy(self.policy)
        duplicate = copy.deepcopy(policy["canonical_resources"][0])
        duplicate["path"] = "README.md"
        policy["canonical_resources"].append(duplicate)
        errors = artifacts.validate_policy(policy, root=ROOT)
        self.assertTrue(any("duplicate editable canonical fact domain" in error for error in errors), errors)

    def test_retained_legacy_requires_owner_reason_and_read_only(self) -> None:
        policy = copy.deepcopy(self.policy)
        legacy = policy["retained_legacy_collections"][0]
        legacy["owner"] = ""
        legacy["reason"] = ""
        legacy["mutable"] = True
        errors = artifacts.validate_policy(policy, root=ROOT)
        self.assertTrue(any(".owner must be non-empty" in error for error in errors), errors)
        self.assertTrue(any(".reason must be non-empty" in error for error in errors), errors)
        self.assertTrue(any("must be read-only" in error for error in errors), errors)

    def test_compact_receipt_rejects_embedded_stdout(self) -> None:
        contract = self.policy["compact_receipts"]
        payload = {field: "pointer" for field in contract["required_pointer_fields"]}
        payload["acceptance_ids"] = ["ACC.Example.PROG1.0001"]
        payload["changed_files_actual"] = ["example.py"]
        payload["test_commands"] = ["python -m unittest"]
        payload["test_results"] = [{"stdout": "large output"}]
        payload["evidence_refs"] = ["artifact:example"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TSK-EXAMPLE.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            errors = artifacts.validate_compact_receipt(path, contract)
        self.assertTrue(any("embeds full-output keys stdout" in error for error in errors), errors)

    def test_changed_scope_locks_legacy_and_allows_one_new_compact_receipt(self) -> None:
        allowed = artifacts.validate_changed_entries(
            [{"status": "A", "path": "governance/run_manifests/TSK-EXAMPLE.json"}],
            self.policy,
        )
        self.assertEqual(allowed, [])
        legacy = artifacts.validate_changed_entries(
            [{"status": "M", "path": "governance/stage_gates/s4pa/reference_graph.json"}],
            self.policy,
        )
        self.assertTrue(any("retained legacy evidence is read-only" in error for error in legacy), legacy)
        modified_receipt = artifacts.validate_changed_entries(
            [{"status": "M", "path": "governance/run_manifests/TSK-OLD.json"}],
            self.policy,
        )
        self.assertTrue(any("append-only" in error for error in modified_receipt), modified_receipt)

    def test_openai_database_legacy_allowlist_locks_only_registered_views(self) -> None:
        legacy = artifacts.validate_changed_entries(
            [{"status": "M", "path": "OpenAIDatabase/docs/governance/STATUS.md"}],
            self.policy,
        )
        self.assertTrue(any("retained legacy evidence is read-only" in error for error in legacy), legacy)
        canonical = artifacts.validate_changed_entries(
            [{"status": "M", "path": "OpenAIDatabase/docs/governance/project.yaml"}],
            self.policy,
        )
        self.assertFalse(any("retained legacy evidence is read-only" in error for error in canonical), canonical)

    def test_new_tracked_full_log_fails(self) -> None:
        errors = artifacts.validate_changed_entries(
            [{"status": "A", "path": "docs/evidence/full-test.log"}],
            self.policy,
        )
        self.assertTrue(any("must remain an untracked artifact" in error for error in errors), errors)

    def test_renderer_is_deterministic_and_zero_write(self) -> None:
        first = artifacts.render_policy(self.policy)
        second = artifacts.render_policy(self.policy)
        self.assertEqual(first, second)
        summary = artifacts.check_render(root=ROOT)
        self.assertEqual(summary["status"], "PASS", summary)
        self.assertTrue(summary["zero_tracked_write"])

    def test_root_human_entry_is_complete_not_link_only(self) -> None:
        self.assertEqual(artifacts.validate_human_entry(self.policy, root=ROOT), [])


if __name__ == "__main__":
    unittest.main()
