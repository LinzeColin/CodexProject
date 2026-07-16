from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DATABASE_DIR.parent
SCRIPT = DATABASE_DIR / "scripts/memory_security.py"
POLICY = DATABASE_DIR / "config/memory-security-policy.json"
FIXTURE = DATABASE_DIR / "tests/fixtures/memory_security/adversarial_cases.json"
sys.path.insert(0, str(DATABASE_DIR / "scripts"))


def load_module():
    spec = importlib.util.spec_from_file_location("memory_security_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemorySecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.policy = cls.module.load_policy(DATABASE_DIR)
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_bounded_corpus_meets_zero_obedience_block_and_no_echo_gates(self) -> None:
        result = self.module.evaluate_fixture(DATABASE_DIR, FIXTURE, self.policy)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["case_count"], 10)
        self.assertEqual(result["instruction_obedience_count"], 0)
        self.assertEqual(result["credential_block_rate"], 1.0)
        self.assertEqual(result["suspected_value_echo_count"], 0)
        self.assertEqual(result["failed_case_ids"], [])

    def test_rejections_never_echo_suspected_values(self) -> None:
        for case in self.fixture["cases"]:
            payload = self.module.fixture_payload(case)
            with self.subTest(case=case["id"]):
                result = self.module.scan_untrusted_text(payload, case["boundary"], self.policy)
                serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)
                self.assertNotIn(payload, serialized)
                if case["expected_status"] == "BLOCK":
                    with self.assertRaises(self.module.MemorySecurityError) as caught:
                        self.module.assert_untrusted_text_safe(payload, case["boundary"], self.policy)
                    self.assertNotIn(payload, str(caught.exception))

    def test_entropy_detector_excludes_hashes_and_blocks_unlabelled_tokens(self) -> None:
        safe_hash = "sha256:" + "a1" * 32
        safe = self.module.scan_untrusted_text(safe_hash, "external_document", self.policy)
        self.assertEqual(safe["status"], "PASS")
        entropy_case = next(case for case in self.fixture["cases"] if case["id"] == "CRED-ENTROPY-01")
        blocked = self.module.scan_untrusted_text(
            self.module.fixture_payload(entropy_case), "external_document", self.policy
        )
        self.assertEqual(blocked["status"], "BLOCK")
        self.assertIn("high_entropy_token", blocked["credential_categories"])

    def test_canonical_workflow_audit_proves_supply_chain_and_settlement_boundary(self) -> None:
        result = self.module.audit_supply_chain(REPO_ROOT, self.policy)
        self.assertEqual(result["status"], "PASS")
        self.assertGreater(result["external_action_ref_count"], 0)
        self.assertGreater(result["resolved_action_pin_count"], 0)
        self.assertEqual(result["untraceable_action_pin_count"], 0)
        self.assertEqual(result["settlement_role_count"], 1)
        self.assertEqual(result["settlement_forbidden_fragment_count"], 0)
        self.assertTrue(all(value == 0 for value in result["required_zero_metrics"].values()))


if __name__ == "__main__":
    unittest.main()
