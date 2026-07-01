from pathlib import Path
import json
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
ADP_ROOT = REPO_ROOT / "arxiv-daily-push"


def _quoted_yaml_value(text: str, key: str) -> str:
    match = re.search(rf'(?m)^{re.escape(key)}:\s*"([^"]+)"\s*$', text)
    if not match:
        raise AssertionError(f"{key} is missing from VERSION_MATRIX.yaml")
    return match.group(1)


class GovernanceCurrentStateTests(unittest.TestCase):
    def test_development_ledger_current_state_matches_version_matrix(self) -> None:
        version_matrix = (ADP_ROOT / "docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")

        current_iteration = _quoted_yaml_value(version_matrix, "current_iteration")
        current_phase = _quoted_yaml_value(version_matrix, "current_phase")
        current_gate = _quoted_yaml_value(version_matrix, "current_gate")
        expected_task = re.sub(r"^ITER-\d{8}-ADP-", "", current_iteration)
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(f"- Current phase: {current_phase}", current_state)
        self.assertIn(f"- Current gate: {current_gate}", current_state)
        self.assertIn(f"- Current task: `{expected_task}`", current_state)
        self.assertIn(f"### `{current_iteration}`", ledger)

    def test_current_state_records_daily_operation_preflight_blocked_without_runtime_enablement(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn("DAILY_OPERATION_AUTHORIZATION_PREFLIGHT_BLOCKED_NO_RUNTIME_ENABLEMENT", current_state)
        self.assertIn("S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT", current_state)
        self.assertIn("status=blocked", current_state)
        self.assertIn("preflight_checks_passed=false", current_state)
        self.assertIn("failed_checks=production_preflight_passed", current_state)
        self.assertIn("state_hash=f306ae932dfbbc9f50dd0f465b7d9b125004f81c6dff4a36f7e4062bcb494660", current_state)
        self.assertIn("missing `gh` CLI", current_state)
        self.assertIn("ADP_SMTP_HOST", current_state)
        self.assertIn("OpenAIDatabase/session_history", current_state)
        self.assertIn("integrated_production_accepted=true", current_state)
        self.assertIn("stage2_integrated_production_accepted=true", current_state)
        self.assertIn("production_acceptance_claimed=true", current_state)
        self.assertIn("integrated_production_acceptance_state_hash=4b88b2edd8fe2eae7ee63f8b512eb713501805725f5fcdf3fb6363f0df3b5453", current_state)
        self.assertIn("integrated_production_acceptance.json", current_state)
        self.assertIn("daily_operation_enabled=false", current_state)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", current_state)
        self.assertIn("LaunchAgents disabled", current_state)
        self.assertIn("no background ADP process", current_state)
        self.assertIn("No DAILY_OPERATION, standing SMTP permission, scheduler enable/install, Release, or production restore is claimed", current_state)
        self.assertIn("S2PMT07-DAILY-OPERATION-PREFLIGHT-PREREQUISITE-REPAIR", current_state)

    def test_owner_and_assurance_route_to_daily_operation_preflight_repair_after_block(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        self.assertIn('task_id: "S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT"', assurance)
        self.assertIn("next_task_id: `S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT`", owner_status)
        self.assertIn('release_gate: "DAILY_OPERATION_AUTHORIZATION_PREFLIGHT_BLOCKED_NO_RUNTIME_ENABLEMENT"', assurance)
        self.assertIn("stage2_integrated_production_accepted: true", assurance)
        self.assertIn("current_zero_proof_open_p0_findings: 0", assurance)
        self.assertIn("current_zero_proof_open_p1_findings: 0", assurance)
        self.assertIn("baseline_counts_mutated: false", assurance)
        self.assertIn("open_pr_count=0", assurance)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", assurance)
        self.assertIn("LaunchAgents disabled", assurance)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json", assurance)
        self.assertIn("DAILY_OPERATION 授权预检已运行但阻断", owner_status)
        self.assertIn("missing gh CLI", owner_status)
        self.assertIn("missing SMTP secret env names", owner_status)
        self.assertIn("OpenAIDatabase session-history archive git artifact hygiene violations", owner_status)
        self.assertIn("DAILY_OPERATION 授权预检", owner_status)
        self.assertIn("runtime enablement remains disabled", owner_status)
        self.assertNotIn('task_id: "S2PMT07-S2PLT04-COMPLETION-REPORT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-S2PLT04-COMPLETION-REPORT`", owner_status)
        self.assertNotIn('task_id: "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION"', assurance)
        self.assertNotIn('task_id: "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-EVIDENCE-WRITE"', assurance)
        self.assertIn("owner_decision_recorded_write_gate_allowed", generator)
        self.assertIn("integrated_production_accepted_no_daily_operation", generator)
        self.assertIn("daily_operation_preflight_current", generator)
        self.assertIn("production_boundary_preflight_ready", generator)
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT", generator)
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE", generator)
        self.assertIn("S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT", generator)

    def test_owner_decision_request_attestation_and_current_precommit_binding(self) -> None:
        manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/ADP-S2PMT07-OWNER-DECISION-REQUEST-MAINLINE-ATTESTATION-20260701.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        current = (ADP_ROOT / "docs/pursuing_goal/CURRENT.yaml").read_text(encoding="utf-8")

        result_commit = manifest["result_commit"]
        result_tree_hash = manifest["result_tree_hash"]
        self.assertRegex(result_commit, r"^[0-9a-f]{40}$")
        self.assertRegex(result_tree_hash, r"^[0-9a-f]{40}$")
        self.assertEqual(manifest["binding_status"], "commit_bound")
        self.assertEqual(manifest["task_id"], "S2PMT07-OWNER-DECISION-REQUEST-MAINLINE-ATTESTATION")
        self.assertEqual(manifest["result"], "pass_owner_decision_request_mainline_attested_no_production_enablement")
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.request.json", manifest["evidence_refs"])
        self.assertTrue(manifest["owner_decision_request_ready"])
        self.assertFalse(manifest["owner_production_boundary_decision_recorded"])
        self.assertFalse(manifest["acceptance_write_gate_allowed"])
        self.assertFalse(manifest["runtime_enablement_allowed"])
        self.assertFalse(manifest["stage2_integrated_production_accepted"])
        self.assertFalse(manifest["daily_operation_enabled"])
        self.assertFalse(manifest["real_smtp_send_enabled"])
        self.assertFalse(manifest["scheduler_enabled"])
        self.assertFalse(manifest["release_packaging_enabled"])
        self.assertFalse(manifest["production_restore_enabled"])
        self.assertIn("- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`", owner_status)
        self.assertIn('final_commit_binding: "PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION"', assurance)
        self.assertRegex(owner_status, r"- source_base_commit: `[0-9a-f]{40}`")
        self.assertRegex(owner_status, r"- source_tree_hash: `[0-9a-f]{40}`")
        self.assertRegex(assurance, r'(?m)^source_base_commit: "[0-9a-f]{40}"$')
        self.assertRegex(assurance, r'(?m)^source_tree_hash: "[0-9a-f]{40}"$')
        self.assertNotIn(f"- final_commit_binding: `COMMIT_BOUND:{result_commit}`", owner_status)
        self.assertIn("owner_production_boundary_decision_recorded: true", current)
        self.assertIn("integrated_production_acceptance_write_gate_allowed: true", current)
        self.assertIn("integrated_production_acceptance_owner_decision_request_write_gate_allowed: false", current)
        self.assertIn("integrated_production_acceptance_evidence_written: true", current)
        self.assertIn("stage2_integrated_production_accepted: true", current)
        self.assertIn("daily_operation_enabled: false", current)

    def test_current_pointer_and_user_center_match_owner_packet_and_controlled_run_state(self) -> None:
        current = (ADP_ROOT / "docs/pursuing_goal/CURRENT.yaml").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")

        self.assertIn(
            "current_iteration: ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT",
            current,
        )
        self.assertIn("current_gate: DAILY_OPERATION_AUTHORIZATION_PREFLIGHT_BLOCKED_NO_RUNTIME_ENABLEMENT", current)
        self.assertIn("next_executable_task: S2PMT07-DAILY-OPERATION-PREFLIGHT-PREREQUISITE-REPAIR", current)
        self.assertIn("next_required_step: REPAIR_DAILY_OPERATION_PREFLIGHT_PREREQUISITES_BEFORE_OWNER_AUTHORIZATION", current)
        self.assertIn("daily_operation_authorization_preflight_written: true", current)
        self.assertIn("daily_operation_authorization_preflight_status: blocked", current)
        self.assertIn("daily_operation_authorization_preflight_passed: false", current)
        self.assertIn(
            "daily_operation_authorization_preflight_state_hash: f306ae932dfbbc9f50dd0f465b7d9b125004f81c6dff4a36f7e4062bcb494660",
            current,
        )
        self.assertIn("production_preflight_passed", current)
        self.assertIn("missing_gh_cli", current)
        self.assertIn("missing_smtp_secret_env_names", current)
        self.assertIn("openai_database_large_archive_git_artifact_hygiene_violations", current)
        self.assertIn("daily_operation_authorization_enablement_allowed: false", current)
        self.assertIn("integrated_production_acceptance_preflight_passed: true", current)
        self.assertIn(
            "integrated_production_acceptance_preflight_state_hash: 6fc89cd8b1d83a2501c54aadd3e6ad04dcf209ec3898d7c0e65d8e65ae9ab4e5",
            current,
        )
        self.assertIn("integrated_production_acceptance_owner_decision_packet_ready: true", current)
        self.assertIn(
            "integrated_production_acceptance_owner_decision_packet_state_hash: de807ff8c395bfda9db6edb4aadacb1e1bdb0e076b4025ed3daca7a2402da289",
            current,
        )
        self.assertIn("owner_authorized_controlled_real_run_acceptance_passed: true", current)
        self.assertIn("integrated_production_acceptance_write_gate_precheck_ready: true", current)
        self.assertIn("integrated_production_acceptance_write_gate_allowed: true", current)
        self.assertIn(
            "integrated_production_acceptance_write_gate_state_hash: 565fb28fab914f9dc6a79fa0dd0144556516a5c3b0d22de5dddefc3e0d95c89b",
            current,
        )
        self.assertIn("integrated_production_acceptance_owner_decision_artifact_gate_status: pass_owner_decision_artifact_valid_no_runtime_enablement", current)
        self.assertIn(
            "integrated_production_acceptance_owner_decision_artifact_gate_state_hash: b1ce1cd2749ac3712dae378734b39d1354fff8613c5f875536beed44c2746e6a",
            current,
        )
        self.assertIn(
            "integrated_production_acceptance_owner_decision_artifact: FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.json",
            current,
        )
        self.assertIn("owner_authorized_controlled_real_run_duplicate_send_avoided: true", current)
        self.assertIn("owner_authorized_controlled_real_run_newly_sent_mail_products: []", current)
        self.assertIn("owner_authorized_controlled_real_run_post_smtp_flag: false", current)
        self.assertIn("owner_authorized_controlled_real_run_background_process_count_after: 0", current)
        self.assertIn("integrated_production_acceptance_owner_decision_request_ready: true", current)
        self.assertIn(
            "integrated_production_acceptance_owner_decision_request_state_hash: b406be2981f67b316df5ceba4469cc8fc3b96364a031c179bca9904f008bd9ea",
            current,
        )
        self.assertIn(
            "integrated_production_acceptance_owner_decision_request_artifact: FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.request.json",
            current,
        )
        self.assertIn("integrated_production_acceptance_owner_decision_request_only: true", current)
        self.assertIn("integrated_production_acceptance_owner_decision_request_write_gate_allowed: false", current)
        self.assertIn(
            "integrated_production_acceptance_owner_decision_request_runtime_enablement_allowed: false",
            current,
        )
        self.assertIn("owner_production_boundary_decision_recorded: true", current)
        self.assertIn("integrated_production_acceptance_evidence_written: true", current)
        self.assertIn(
            "integrated_production_acceptance_evidence_status: pass_integrated_production_accepted_evidence_written_no_runtime_enablement",
            current,
        )
        self.assertIn(
            "integrated_production_acceptance_evidence_artifact: FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json",
            current,
        )
        self.assertIn(
            "integrated_production_acceptance_evidence_state_hash: 4b88b2edd8fe2eae7ee63f8b512eb713501805725f5fcdf3fb6363f0df3b5453",
            current,
        )
        self.assertIn("production_acceptance_claimed: true", current)
        self.assertIn("final_bundle_present: true", current)
        self.assertIn("s2plt04_completed: true", current)
        self.assertIn("independent_final_review_passed: true", current)
        self.assertIn("final_commands_executed: true", current)
        self.assertIn("current_zero_proof_open_p0_findings: 0", current)
        self.assertIn("current_zero_proof_open_p1_findings: 0", current)
        self.assertIn("inherited_v7_1_baseline_p0_findings: 8", current)
        self.assertIn("inherited_v7_1_baseline_p1_findings: 37", current)
        self.assertIn("stage2_integrated_production_accepted: true", current)
        self.assertIn("daily_operation_enabled: false", current)
        self.assertIn("DAILY_OPERATION 授权预检已运行但阻断", decisions)
        self.assertIn("production_preflight_passed", decisions)
        self.assertIn("修复 `gh` CLI 可用性", decisions)
        self.assertIn("补齐 SMTP secret env 名称", decisions)
        self.assertIn("OpenAIDatabase/session_history", decisions)
        self.assertIn("integrated_production_acceptance.json", decisions)
        self.assertIn("stage2_integrated_production_accepted=true", decisions)
        self.assertIn("不得请求 persistent DAILY_OPERATION 授权", decisions)
        self.assertIn("不得自动启用 SMTP/scheduler/Release/restore/DAILY_OPERATION", decisions)
        self.assertIn("DAILY_OPERATION 授权预检已运行但阻断", readme)
        self.assertIn("missing `gh` CLI", readme)
        self.assertIn("ADP_SMTP_HOST", readme)
        self.assertIn("OpenAIDatabase/session_history", readme)
        self.assertIn("integrated_production_acceptance.json", readme)
        self.assertIn("DAILY_OPERATION 仍未启用", readme)
        self.assertIn("S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT", readme)
        self.assertIn("DAILY_OPERATION 授权预检已运行但阻断", roadmap)
        self.assertIn("DAILY_OPERATION_AUTHORIZATION_PREFLIGHT_BLOCKED_NO_RUNTIME_ENABLEMENT", roadmap)
        self.assertIn("missing gh CLI", roadmap)
        self.assertIn("missing SMTP secret env names", roadmap)
        self.assertIn("OpenAIDatabase session-history", roadmap)
        self.assertIn("INTEGRATED_PRODUCTION_ACCEPTED", roadmap)

    def test_three_base_model_parameter_summary_matches_governance_counts(self) -> None:
        model_spec = (ADP_ROOT / "docs/governance/MODEL_SPEC.md").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        model_params = (ADP_ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        summary = model_params.split("\n## 2026-", 1)[0]

        model_count = re.search(r"(?m)^- model_count: `?(\d+)`?$", model_spec)
        active_formulas = re.search(r"(?m)^- active_formulas: `(\d+)`$", owner_status)
        active_parameters = re.search(r"(?m)^- active_parameters: `(\d+)`$", owner_status)
        if not model_count or not active_formulas or not active_parameters:
            raise AssertionError("governance model/formula/parameter counts are missing")

        self.assertIn(f"- active_model_count: `{model_count.group(1)}`", summary)
        self.assertIn(f"- active_formula_count: `{active_formulas.group(1)}`", summary)
        self.assertIn(f"- active_parameter_count: `{active_parameters.group(1)}`", summary)
        self.assertIn(
            "- current_task: `S2PMT07-DAILY-OPERATION-AUTHORIZATION-PREFLIGHT`",
            summary,
        )
        self.assertIn("- next_gate: `S2PMT07-DAILY-OPERATION-PREFLIGHT-PREREQUISITE-REPAIR`", summary)
        self.assertIn("DAILY_OPERATION authorization preflight is blocked by production_preflight_passed", summary)
        self.assertIn("missing_gh_cli", summary)
        self.assertIn("DAILY_OPERATION remains disabled", summary)


if __name__ == "__main__":
    unittest.main()
