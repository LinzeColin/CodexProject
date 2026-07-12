from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from OpenAIDatabase.tests.test_s07p1_economic_proxy import ATLASCTL_SCRIPT, REPO_ROOT, SCRIPTS_ROOT, run_json
from OpenAIDatabase.tests.test_s08p1_agent_collaboration import write_agent_collaboration_fixtures


AGENT_AUTHORIZATION_SCRIPT = REPO_ROOT / "scripts" / "build_memory_atlas_agent_authorization.py"
AUTHORIZATION_CONFIG = REPO_ROOT / "机器治理" / "行为智能模型" / "agent_authorization_boundary.v1_2_s08_p2.json"
RAW_PUBLIC_POLICY = REPO_ROOT / "机器治理" / "同步与备份" / "raw_public_archive_policy.v1_2_s03_p1.json"
RAW_LEDGER_POLICY = REPO_ROOT / "机器治理" / "同步与备份" / "raw_manifest_ledger_policy.v1_2_s03_p3.json"
FORMULA_WHAT_IF_CONFIG = REPO_ROOT / "机器治理" / "参数与公式" / "formula_what_if_defaults.v1_2_s07_p3.json"


def load_agent_authorization_module():
    sys.path.insert(0, str(SCRIPTS_ROOT))
    spec = importlib.util.spec_from_file_location("build_memory_atlas_agent_authorization", AGENT_AUTHORIZATION_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_authorization_fixtures(root: Path) -> None:
    write_agent_collaboration_fixtures(root)
    for source, target in [
        (AUTHORIZATION_CONFIG, root / "机器治理" / "行为智能模型" / "agent_authorization_boundary.v1_2_s08_p2.json"),
        (RAW_PUBLIC_POLICY, root / "机器治理" / "同步与备份" / "raw_public_archive_policy.v1_2_s03_p1.json"),
        (RAW_LEDGER_POLICY, root / "机器治理" / "同步与备份" / "raw_manifest_ledger_policy.v1_2_s03_p3.json"),
        (FORMULA_WHAT_IF_CONFIG, root / "机器治理" / "参数与公式" / "formula_what_if_defaults.v1_2_s07_p3.json"),
    ]:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    run_json([
        sys.executable,
        str(ATLASCTL_SCRIPT),
        "analyze",
        "--stage",
        "agent-collaboration",
        "--database-dir",
        str(root),
    ])


class S08P2AgentAuthorizationTest(unittest.TestCase):
    def test_builds_authorization_boundary_report_without_apply_or_raw_mutation(self) -> None:
        module = load_agent_authorization_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_authorization_fixtures(root)
            output = root / "data/derived/agent_collaboration/agent_authorization_boundary_report.json"
            result = module.build_authorization_boundary_report(root, dry_run=True, generated_at="2026-07-08T00:00:00Z")
            self.assertEqual(result["task_id"], "MA-V12-S08P2")
            self.assertEqual(result["acceptance_id"], "ACC-MA-V12-S08P2")
            self.assertEqual(result["status"], "phase_s08_p2_authorization_boundary_completed_pending_s08_p3")
            self.assertFalse(output.exists())
            self.assertTrue(result["phase_boundary"]["authorization_boundary_defined_as_machine_checks"])
            self.assertTrue(result["phase_boundary"]["does_not_modify_raw"])
            self.assertTrue(result["phase_boundary"]["does_not_apply_proposals"])
            self.assertTrue(result["phase_boundary"]["requires_human_approval_before_apply"])
            self.assertTrue(result["phase_boundary"]["raw_is_never_apply_target"])
            self.assertTrue(result["phase_boundary"]["does_not_implement_complex_delegation_contract_ui"])
            self.assertTrue(result["phase_boundary"]["does_not_generate_stage_flight_recorder"])
            self.assertEqual(result["phase_boundary"]["next_phase"], "S08 P3")
            self.assertEqual(result["machine_output_check_summary"]["check_count"], 4)
            self.assertFalse(result["machine_output_check_summary"]["current_phase_executes_apply"])
            self.assertFalse(result["machine_output_check_summary"]["raw_apply_target_allowed"])
            self.assertTrue(result["machine_output_check_summary"]["human_approval_required"])
            for check in result["machine_output_checks"]:
                self.assertEqual(check["status"], "PASS")
                self.assertTrue(check["explanation_zh"])
                self.assertTrue(check["evidence_refs"])
            contract = result["proposal_contract"]
            self.assertIn("approval", contract["required_fields"])
            self.assertIn("validation_commands", contract["required_fields"])
            self.assertIn("rollback_plan", contract["required_fields"])
            self.assertIn("public_raw", contract["apply_forbidden_targets"])
            self.assertIn("data/public_raw/", contract["forbidden_path_prefixes"])

    def test_atlasctl_agent_authorization_apply_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_authorization_fixtures(root)
            output = root / "data/derived/agent_collaboration/agent_authorization_boundary_report.json"
            dry_run = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "agent-authorization",
                "--database-dir",
                str(root),
                "--dry-run",
            ])
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["writes_files"])
            self.assertFalse(output.exists())

            applied = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "analyze",
                "--stage",
                "agent-authorization",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(applied["task_id"], "MA-V12-S08P2")
            self.assertTrue(output.exists())

            audit = run_json([
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "audit",
                "--check",
                "agent-authorization",
                "--database-dir",
                str(root),
            ])
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(audit["bad_items"], [])
            self.assertEqual(audit["machine_output_check_count"], 4)
            self.assertTrue(audit["human_approval_required"])
            self.assertFalse(audit["raw_apply_target_allowed"])
            self.assertFalse(audit["proposal_apply_execution"])
            self.assertFalse(audit["complex_delegation_contract_ui"])
            self.assertEqual(audit["stage_flight_recorder"], "deferred_to_s08_p3")


if __name__ == "__main__":
    unittest.main()
