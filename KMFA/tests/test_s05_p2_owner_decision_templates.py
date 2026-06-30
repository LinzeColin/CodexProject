import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "KMFA" / "tools" / "check_s05_p2_owner_decision_templates.py"
TEMPLATES_DIR = (
    ROOT
    / "KMFA"
    / "stage_artifacts"
    / "S05_P2_a0_golden_fixture"
    / "machine"
    / "owner_decision_templates"
)
DECISION_CODES = [
    "provide_private_field_mapping",
    "downgrade_to_cross_source_support",
    "keep_pending",
]


def write_valid_templates(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    base = {
        "record_type": "s05_p2_excel_owner_resolution_decision_template",
        "schema_version": "kmfa.s05_p2_excel_owner_resolution_decision_template.v1",
        "project_id": "KMFA",
        "stage_id": "S05",
        "phase_id": "S05-P2",
        "current_gate": "KMFA-S05-P2-EXCEL-RESOLUTION-GATE",
        "candidate_id": "A0-CAND-70023EFC7305",
        "file_id": "A0-FILE-BAE6D90834C5",
        "not_decision_record": True,
        "output_record_type_after_activation": "s05_p2_excel_owner_resolution_decision",
        "activation_requires": ["owner_or_authorized_actor", "decision_time", "remove_template_marker"],
        "business_plaintext_committed": False,
        "raw_source_committed": False,
        "private_csv_committed": False,
        "q4_confirmation_claimed": False,
        "q5_baseline_claimed": False,
        "source_layer_write_allowed": False,
        "field_keys": ["contract_amount", "total_expense", "gross_profit", "gross_margin", "cost_category"],
    }
    for decision_code in DECISION_CODES:
        payload = dict(base)
        payload["decision_code"] = decision_code
        payload["template_id"] = f"TPL-KMFA-S05P2-{decision_code.upper().replace('_', '-')}"
        payload["required_fill_fields"] = ["actor_role", "actor_ref", "decision_time"]
        if decision_code == "provide_private_field_mapping":
            payload["required_private_hash_ref_fields"] = list(base["field_keys"])
            payload["required_source_anchor_ref_fields"] = list(base["field_keys"])
        else:
            payload["private_hash_refs_allowed"] = False
        (root / f"{decision_code}_template.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )


class S05P2OwnerDecisionTemplateTests(unittest.TestCase):
    def run_checker(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_public_safe_templates_cover_all_allowed_decisions_without_active_records(self) -> None:
        result = self.run_checker()

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PASS: KMFA S05-P2 owner decision templates check passed", result.stdout)
        self.assertIn("template_count=3", result.stdout)
        self.assertIn("active_decision_records=0", result.stdout)

    def test_rejects_template_that_uses_active_decision_record_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_templates = Path(tmp) / "templates"
            write_valid_templates(temp_templates)
            target = temp_templates / "keep_pending_template.json"
            payload = json.loads(target.read_text(encoding="utf-8"))
            payload["record_type"] = "s05_p2_excel_owner_resolution_decision"
            target.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")

            result = self.run_checker("--templates-dir", str(temp_templates))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("templates must not use active decision record_type", result.stdout + result.stderr)

    def test_rejects_template_with_plaintext_value_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_templates = Path(tmp) / "templates"
            write_valid_templates(temp_templates)
            target = temp_templates / "downgrade_to_cross_source_support_template.json"
            payload = json.loads(target.read_text(encoding="utf-8"))
            payload["raw_value"] = "must not appear in a public template"
            target.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")

            result = self.run_checker("--templates-dir", str(temp_templates))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden public metadata key", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
