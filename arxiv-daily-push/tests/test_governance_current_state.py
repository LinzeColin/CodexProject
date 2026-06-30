from pathlib import Path
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

    def test_current_state_summary_describes_assignment_live_validation_and_s2plt02_blockers(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_S2PLT02_ARTIFACT_VALIDATION_SUMMARY_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-ARTIFACT-VALIDATION-SUMMARY", current_state)
        self.assertIn("terminal_artifact_validation_status", current_state)
        self.assertIn("084c08ec36f925dedb7ecb3488874a23d82090e124b0a791ecd34a998691e54c", current_state)
        self.assertIn("8b7dc7003c7f60c9065448b2c86d7e1089aedc022b56a84a36487899aa604fa9", current_state)
        self.assertIn("797c920987dcb0f38a1af8c8dc2ed80633c412cf9bb5f91686a7c29bfeaa68f8", current_state)
        self.assertIn("3fbde96111dd78d3ffe4474e012fa5d86de76a24e6fa7640d0310c178003e1db", current_state)
        self.assertIn("terminal_artifact_ref=FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", current_state)
        self.assertIn("terminal_artifact_present=false", current_state)
        self.assertIn("terminal_artifact_ready=false", current_state)
        self.assertIn("terminal_artifact_validation_errors=s2plt02_terminal_delivery_proof_artifact_missing", current_state)
        self.assertIn("terminal_artifact_blocking_reasons=s2plt02_terminal_delivery_proof_artifact_missing;two_consecutive_real_days_not_proven;eight_real_emails_not_proven;real_scheduler_not_proven", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-ARTIFACT-VALIDATION-SUMMARY-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_ARTIFACT_VALIDATION_SUMMARY.md", ledger)
        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_S2PLT03_SUMMARY_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT03-SUMMARY-SYNC", current_state)
        self.assertIn("s2plt03_terminal_resilience_capture_plan_summary", current_state)
        self.assertIn("3b2475e26547816b77885fddb170944fb858a4aa14fc04305de6798c288a8651", current_state)
        self.assertIn("55e5d994d17ceb53cb8e8a1729c52e29d7808dd07527e9ee9a48f52982e129f5", current_state)
        self.assertIn("s2plt03_next_executable_step=WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE", current_state)
        self.assertIn("s2plt03_missing_terminal_inputs=S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT;S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT", current_state)
        self.assertIn("s2plt03_blocking_reasons=s2plt03_terminal_resilience_proof_artifact_missing;s2plt02_not_accepted", current_state)
        self.assertIn("s2plt03_completed_inputs=LOCAL_RESILIENCE_DRILL=true;RESILIENCE_PRECHECK=true;P0_P1_ZERO_PROOF=true;S2PLT02_TERMINAL_DELIVERY_PROOF=false;S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT=false", current_state)
        self.assertIn("s2plt03_artifact_written=false", current_state)
        self.assertIn("s2plt03_accepted=false", current_state)
        self.assertIn("s2plt03_resilience_drill_completed=false", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-S2PLT03-SUMMARY-SYNC-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT03_SUMMARY_SYNC.md", ledger)
        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_S2PLT02_CAPTURE_COMMAND_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-COMMAND-SYNC", current_state)
        self.assertIn("next_executable_command=plan-s2plt02-terminal-delivery-proof-capture", current_state)
        self.assertIn("next_executable_command_dry_run_status=blocked", current_state)
        self.assertIn("next_executable_command_writes_artifact=false", current_state)
        self.assertIn("next_executable_command_satisfies_gate=false", current_state)
        self.assertIn("9621084d1f10a325d6d02284f66db8e78a239aeb16e556bb9de55d455c244f6b", current_state)
        self.assertIn("e7f33cbf0d084cb00c547016d83139b47e62809e2638be3a33effc8dcbe74358", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-COMMAND-SYNC-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_CAPTURE_COMMAND_SYNC.md", ledger)
        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_S2PLT02_RUNTIME_READINESS_SUMMARY_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-RUNTIME-READINESS-SUMMARY", current_state)
        self.assertIn("b70e0ae4ab942c46018d87e28c09b9d8e839f4ab10682cbf4fde8e993a15194e", current_state)
        self.assertIn("final_bundle_prerequisite_plan_state_hash=8878509d00a04899d9b4a647d98146dea5aa88e39f41a07d25f39b9848cb8878", current_state)
        self.assertIn("s2plt02_runtime_readiness_summary_state_hash=48bea5fd4a31cbe6f675b1a2b939d1444b8a148b37d3f6a7b338096071a995f9", current_state)
        self.assertIn("remaining_runtime_actions=capture_second_consecutive_real_m1_m4_smtp_day;capture_real_launchd_scheduler_proof;write_and_validate_s2plt02_terminal_delivery_proof_artifact", current_state)
        self.assertIn("missing_smtp_secret_env_names=ADP_SMTP_HOST;ADP_SMTP_PORT;ADP_SMTP_USERNAME;ADP_SMTP_PASSWORD", current_state)
        self.assertIn("smtp_secret_env_ready=false", current_state)
        self.assertIn("smtp_secret_values_logged=false", current_state)
        self.assertIn("real_smtp_secret_env_missing", current_state)
        self.assertIn("blocked_by_missing_inputs=SECOND_REAL_DELIVERY_DAY;EIGHT_REAL_EMAILS;REAL_SCHEDULER_PROOF;S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", current_state)
        self.assertIn("observed_real_delivery_days=1/2", current_state)
        self.assertIn("observed_real_email_count=4/8", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-RUNTIME-READINESS-SUMMARY-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_RUNTIME_READINESS_SUMMARY.md", ledger)
        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_VALIDATOR_RUNTIME_STEP_SUMMARY_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-VALIDATOR-RUNTIME-STEP-SUMMARY", current_state)
        self.assertIn("303854706b4dee813e8e9d3f970bfce8943db4a162779845835d1682d5dc91ff", current_state)
        self.assertIn("final_bundle_prerequisite_plan_state_hash=bc5c75ce6138842f2b3de247420260b55d3b1a5f7cfb6f10dc44f91efb594af6", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-VALIDATOR-RUNTIME-STEP-SUMMARY-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_VALIDATOR_RUNTIME_STEP_SUMMARY.md", ledger)
        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_PREREQUISITE_S2PLT02_RUNTIME_STEP_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-PREREQUISITE-S2PLT02-RUNTIME-STEP-SYNC", current_state)
        self.assertIn("next_executable_runtime_step=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", current_state)
        self.assertIn("bc5c75ce6138842f2b3de247420260b55d3b1a5f7cfb6f10dc44f91efb594af6", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-PREREQUISITE-S2PLT02-RUNTIME-STEP-SYNC-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_PREREQUISITE_S2PLT02_RUNTIME_STEP_SYNC.md", ledger)
        self.assertIn("next_required_step=S2PLT04_COMPLETION_REPORT", current_state)
        self.assertIn("next_executable_task=S2PLT02_TERMINAL_DELIVERY_PROOF", current_state)
        self.assertIn(
            "S2PLT02_TERMINAL_CAPTURE_PLAN_RUNTIME_AUTH_GATE_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-PLAN-RUNTIME-AUTH-GATE", current_state)
        self.assertIn("runtime_capture_ready=false", current_state)
        self.assertIn("next_executable_step=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", current_state)
        self.assertIn("6fa850a802d93e839146cabf158689af05941a54e895911220cc9c077efde7d2", current_state)
        self.assertIn("01921f133de411eed12662818911e76e67c880d878394c7e39e8fd66f78c1e65", current_state)
        self.assertIn("ADP-S2PLT02-TERMINAL-CAPTURE-PLAN-RUNTIME-AUTH-GATE-20260630.json", current_state)
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_PLAN_RUNTIME_AUTH_GATE.md", ledger)
        self.assertIn("--expected-authorization-readiness-state-hash", current_state)
        self.assertIn("readiness_state_hash does not match current readiness state", current_state)
        self.assertIn("authorization_artifact_status=blocked", current_state)
        self.assertIn("real_proof_capture_authorized=false", current_state)
        self.assertIn("218cfe1712e9020e02cea37b4f1982c4c959bca29462d6b73e8aec7308e8444c", current_state)
        self.assertIn("76b9533077ad56d270a70a12b53af80936875795728d7399a48c6af976e37fa2", current_state)
        self.assertIn("ADP-S2PLT02-AUTHORIZATION-READINESS-HASH-GATE-20260630.json", current_state)
        self.assertIn("PHASE_S2PLT02_AUTHORIZATION_READINESS_HASH_GATE.md", ledger)
        self.assertIn(
            "S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN", current_state)
        self.assertIn("WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE", current_state)
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", current_state)
        self.assertIn("S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT", current_state)
        self.assertIn("s2plt03_terminal_resilience_proof_artifact_missing", current_state)
        self.assertIn("s2plt02_not_accepted", current_state)
        self.assertIn("bd5f74277b41f7e43ec1a907f6d13eee215808e86d04594e03bd4ed71091ddd5", current_state)
        self.assertIn("ADP-S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN-20260630.json", current_state)
        self.assertIn("PHASE_S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN.md", ledger)
        self.assertIn(
            "S2PLT02_TERMINAL_PROOF_EVIDENCE_INVENTORY_INPUT_HARDENING_BLOCKED_NO_PRODUCTION",
            ledger,
        )
        self.assertIn("S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY-INPUT-HARDENING", current_state)
        self.assertIn("launchctl_disabled_file_missing", current_state)
        self.assertIn("launchctl_disabled_file_status=missing", current_state)
        self.assertIn("b43760c8150155bb0f40e627cdec97443451bfad63e1257b08d1fd572dccda39", current_state)
        self.assertIn("d2f12b5f3fbe439fdd0b2d420706700f5a0aa6b3d9ba691da67f2ffe4758d117", current_state)
        self.assertIn("PHASE_S2PLT02_TERMINAL_PROOF_EVIDENCE_INVENTORY_INPUT_HARDENING.md", ledger)
        self.assertIn("no Python traceback", ledger)
        self.assertIn(
            "S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_LIVE_VALIDATION_SYNC_BLOCKED_FINAL_BUNDLE_INCOMPLETE_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-LIVE-VALIDATION-SYNC", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json", current_state)
        self.assertIn("assignment_present=true", current_state)
        self.assertIn("independent_final_reviewer_assigned_by_payload=true", current_state)
        self.assertIn("reviewer `codex-subthread-independent-final-reviewer`", current_state)
        self.assertIn("b5b117307bd61f168ae6a422b24c865227f4824191348b851081af66730ed2c2", current_state)
        self.assertIn("f12f50fe2d474010ab3f93023759872593bdbb3ad65bfbf645287f21a76ef2a3", current_state)
        self.assertIn("ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-LIVE-VALIDATION-SYNC-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_LIVE_VALIDATION_SYNC.md", ledger)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/manifest.json", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json", current_state)
        self.assertIn("HANDOFF/00_下一Agent先读.md", current_state)
        self.assertNotIn("Current task: `S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT`", current_state)
        self.assertNotIn("current agent cannot fabricate it", current_state)
        self.assertIn("S2PLT02-DAILY-RUN-DRY-RUN-TERMINAL-CLASSIFICATION", current_state)
        self.assertIn("daily_run_succeeded_but_smtp_dry_run_not_terminal", current_state)
        self.assertIn("daily_run_succeeded_service_dates=2026-06-29,2026-06-30", current_state)
        self.assertIn("nonterminal_succeeded_dry_run_service_dates=2026-06-29,2026-06-30", current_state)
        self.assertIn("nonterminal_succeeded_dry_run_count=2", current_state)
        self.assertIn("observed_candidate_dry_run_email_count=8", current_state)
        self.assertIn("observed_candidate_real_sent_email_count=0", current_state)
        self.assertIn("ADP-S2PLT02-DAILY-RUN-DRY-RUN-TERMINAL-CLASSIFICATION-20260630.json", current_state)
        self.assertIn("PHASE_S2PLT02_DAILY_RUN_DRY_RUN_TERMINAL_CLASSIFICATION.md", ledger)
        self.assertIn("a9179f2a386c23d6efb0495659f434a3991736ce7a10ec6e234659a4e6a0accf", current_state)
        self.assertIn(
            "S2PMT07_S2PLT04_NONTERMINAL_SUMMARY_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-S2PLT04-NONTERMINAL-SUMMARY-SYNC", current_state)
        self.assertIn("ee3917fedcd96e10a23fbd228367e6837ffca092734d98288502d9702514165f", current_state)
        self.assertIn("s2plt02_nonterminal_ref_count=14", current_state)
        self.assertIn(
            "s2plt02_latest_nonterminal_ref=governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC-20260630.json",
            current_state,
        )
        self.assertIn("s2plt03_nonterminal_ref_count=4", current_state)
        self.assertIn(
            "s2plt03_latest_nonterminal_ref=governance/run_manifests/ADP-S2PLT03-AUDIT-BLOCKER-ZERO-PROOF-SYNC-20260629.json",
            current_state,
        )
        self.assertIn("ADP-S2PMT07-S2PLT04-NONTERMINAL-SUMMARY-SYNC-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_S2PLT04_NONTERMINAL_SUMMARY_SYNC.md", ledger)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-RUNTIME-STATE-SYNC", current_state)
        self.assertIn("audit-s2plt02-terminal-capture-window", current_state)
        self.assertIn("cebee97e51f4cc6231a10b787aa65b17eed10c951330dea4328cd18d73ed912a", current_state)
        self.assertIn("real_sent_candidate_email_count=4", current_state)
        self.assertIn("observed_terminal_email_count_credit=4/8", current_state)
        self.assertIn("launchagents_loaded_but_disabled=true", current_state)
        self.assertIn("scheduler_runtime_evidence_status=launchagents_loaded_but_disabled_not_terminal_scheduler_proof", current_state)
        self.assertIn("ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-RUNTIME-STATE-SYNC-20260630.json", current_state)
        self.assertIn("s2plt02_nonterminal_ref_count=14", current_state)
        self.assertIn("a126940b6692c08c49d870de513555cc89c7374399ed099028fdc7395a94016a", current_state)
        self.assertIn("S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC", current_state)
        self.assertIn("audit-s2plt04-completion-evidence", current_state)
        self.assertIn("0cb047a1ae27d990b3a53c082194ee0e15e45e772244ecd74bbf454fbb6f11be", current_state)
        self.assertIn("s2plt02_nonterminal_ref_count=13", current_state)
        self.assertIn("ADP-S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY-20260630.json", current_state)
        self.assertIn("ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC-20260630.json", current_state)
        self.assertIn("s2plt02_live_2d_terminal_proof_missing", current_state)
        self.assertIn("s2plt03_resilience_terminal_proof_missing", current_state)
        self.assertIn("completion_report_ready=false", current_state)
        self.assertIn("S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC", current_state)
        self.assertIn("authorization_artifact_status=pass", current_state)
        self.assertIn("real_proof_capture_authorized=true", current_state)
        self.assertIn("completed_next_actions=obtain_explicit_owner_authorization_for_real_smtp_scheduler", current_state)
        self.assertIn("safe_to_collect_terminal_proof=false", current_state)
        self.assertIn("7647b32a4ec17c9687e71238ee0ddf2d184ea666d84982dd77e7f2a2d2e427a9", current_state)
        self.assertIn("required_launchagents_disabled", current_state)
        self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION", current_state)
        self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR", current_state)
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN", current_state)
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY", current_state)
        self.assertIn("S2PLT02-REAL-SCHEDULER-PROOF-INPUT-VALIDATOR", current_state)
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF-ARTIFACT-DRAFT-BUILDER", current_state)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT", current_state)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI", current_state)
        self.assertIn("S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY", current_state)
        self.assertIn("audit-s2plt02-terminal-proof-evidence-inventory", current_state)
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF", current_state)
        self.assertIn("usable terminal inputs", current_state)
        self.assertIn("blocked dry-run candidates", current_state)
        self.assertIn("missing terminal inputs", current_state)
        self.assertIn("SECOND_REAL_DELIVERY_DAY", current_state)
        self.assertIn("EIGHT_REAL_EMAILS", current_state)
        self.assertIn("REAL_SCHEDULER_PROOF", current_state)
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", current_state)
        self.assertIn("WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", current_state)
        self.assertIn("delivery_manifest_ready=true", current_state)
        self.assertIn("blocked_missing_explicit_no_production_flags", current_state)
        self.assertIn("ADP-S2PLT02-NORMALIZED-REAL-DELIVERY-MANIFEST-20260628.json", current_state)
        self.assertIn("a795bd90778b5a0bbbd217d286f696936954af47a1a547ed689f907b677d9fa2", current_state)
        self.assertIn("91bf1a4477c621a75fceed90efecdb620341cfc97d5a751c127cc5ffbd6a0d99", current_state)
        self.assertIn("c56a7a1a5e9cb8a81ba0b05aa848c05e1577ce7558bae1700ea4563652c2d93c", current_state)
        self.assertIn("artifact_written=false", current_state)
        self.assertIn("scheduler_install_enabled=false", current_state)
        self.assertIn("daily_operation_enabled=false", current_state)
        self.assertIn("2026-06-29", current_state)
        self.assertIn("2026-06-30", current_state)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", current_state)
        self.assertIn("terminal_delivery_credit=false", current_state)
        self.assertIn("counts_toward_s2plt02_terminal_proof=false", current_state)
        self.assertIn("1f5abf4e3def35129bc6a360722b10087880dfb49f904d6f9b267cb796d7f8f1", current_state)
        self.assertIn("6ad683a0590f9d43c808cf7812edc7c7f93feabec52d365ddb2a8abbbf42b4bf", current_state)
        self.assertIn("dry_run_email_count=8", current_state)
        self.assertIn("real_sent_candidate_email_count=0", current_state)
        self.assertIn("s2plt02_terminal_delivery_proof_artifact_missing", current_state)
        self.assertIn("431949620cef28641fcd606ee5646c006cd5cf9fd412daadc899a534185ac613", current_state)
        self.assertIn("blocked_dry_run_not_real_terminal_input", current_state)
        self.assertIn("safe_to_build_terminal_artifact=false", current_state)
        self.assertIn("no production acceptance", current_state.lower())

    def test_owner_next_action_points_to_s2plt02_terminal_delivery_proof(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        stale_option = "继续 S2PLT02 no-production readiness evidence work under V7.2 boundaries"
        self.assertIn('task_id: "S2PLT02-TERMINAL-DELIVERY-PROOF"', assurance)
        self.assertIn("next_task_id: `S2PLT02-TERMINAL-DELIVERY-PROOF`", owner_status)
        self.assertNotIn('task_id: "S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT`", owner_status)
        for text in (assurance, owner_status):
            text_lower = text.lower()
            self.assertIn("S2PMT07", text)
            self.assertIn("validated independent reviewer assignment", text)
            self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR", text)
            self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION", text)
            self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN", text)
            self.assertIn("S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY", text)
            self.assertIn("S2PLT02-REAL-SCHEDULER-PROOF-INPUT-VALIDATOR", text)
            self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT", text)
            self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI", text)
            self.assertIn("S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY", text)
            self.assertIn("S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC", text)
            self.assertIn("S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN", text)
            self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF", text)
            self.assertIn("ACC-S2PMT07-FINAL-REVIEW", text)
            self.assertIn("real", text_lower)
            self.assertIn("smtp", text_lower)
            self.assertIn("scheduler", text_lower)
            self.assertIn("P0/P1 zero-proof", text)
            self.assertIn("live authorization", text_lower)
            self.assertIn("input inventory", text_lower)
            self.assertIn("capture plan", text_lower)
            self.assertIn("manifest", text_lower)
            self.assertIn("normalized manifest", text_lower)
            self.assertIn("dry-run", text_lower)
            self.assertIn("resilience", text_lower)
            self.assertNotIn(stale_option, text)
        self.assertIn("adp_s2pmt07_blocked_next_task", generator)
        self.assertIn("terminal_delivery_proof_is_next", generator)
        self.assertIn("current_v7_task_id", generator)

    def test_user_center_default_next_step_prioritizes_s2plt02_terminal_proof(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        default_next = decisions.split("## 默认下一步", 1)[1]
        first_action_row = next(
            line for line in default_next.splitlines() if line.startswith("| 1 |")
        )

        self.assertIn("S2PLT02 终态交付 proof", first_action_row)
        self.assertIn("capture plan", first_action_row)
        self.assertIn("audit-s2plt02-terminal-capture-window", first_action_row)
        self.assertIn("validate-s2plt02-real-delivery-manifest", first_action_row)
        self.assertIn("WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", first_action_row)
        self.assertIn("dry-run/scheduler-disabled", first_action_row)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json", default_next)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", default_next)
        self.assertIn("受控真实捕获窗口", default_next)
        self.assertIn("真实 launchd scheduler proof", default_next)
        self.assertIn("独立最终复审人分配已验证", decisions)
        self.assertIn("validate-final-reviewer-assignment", decisions)
        self.assertIn("b5b117307bd61f168ae6a422b24c865227f4824191348b851081af66730ed2c2", decisions)
        self.assertIn("S2PLT02 terminal proof 输入仍不完整", decisions)
        self.assertIn("S2PLT02 terminal proof 捕获计划仍 blocked", decisions)
        self.assertIn("S2PLT02 capture-window CLI 已可复现但仍 blocked", decisions)
        self.assertIn("S2PLT02 real delivery manifest 输入门刚补齐", decisions)
        self.assertIn("S2PLT02 real delivery manifest 规范化输入已补齐", decisions)
        self.assertIn("PHASE_S2PLT02_TERMINAL_DELIVERY_INPUT_INVENTORY.md", decisions)
        self.assertIn("PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN.md", decisions)
        self.assertIn("PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_INPUT_VALIDATOR.md", decisions)
        self.assertIn("PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION.md", decisions)
        self.assertNotIn("候选池", first_action_row)
        self.assertNotIn("评分标准公开", first_action_row)
        self.assertNotIn("独立终审 reviewer assignment artifact 准备", default_next)
        self.assertIn("no-production attestation、independent reviewer assignment validator pass、P0/P1 zero-proof、S2PLT01 terminal acceptance 已是可用输入", decisions)
        self.assertNotIn("| 无冲突的影子数据源证据 | 可以 |", roadmap)
        self.assertIn("S2PMT07 阻断期暂停新增影子数据源", roadmap)

    def test_three_base_model_parameter_summary_matches_governance_counts(self) -> None:
        model_spec = (ADP_ROOT / "docs/governance/MODEL_SPEC.md").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        model_params = (ADP_ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        summary = model_params.split("\n## 2026-", 1)[0]

        model_count = re.search(r"(?m)^- model_count: (\d+)$", model_spec)
        active_formulas = re.search(r"(?m)^- active_formulas: `(\d+)`$", owner_status)
        active_parameters = re.search(r"(?m)^- active_parameters: `(\d+)`$", owner_status)
        if not model_count or not active_formulas or not active_parameters:
            raise AssertionError("governance model/formula/parameter counts are missing")

        self.assertIn(f"- active_model_count: `{model_count.group(1)}`", summary)
        self.assertIn(f"- active_formula_count: `{active_formulas.group(1)}`", summary)
        self.assertIn(f"- active_parameter_count: `{active_parameters.group(1)}`", summary)
        self.assertNotIn("- active_model_count: `120`", summary)
        self.assertNotIn("- active_formula_count: `122`", summary)
        self.assertNotIn("- active_parameter_count: `1073`", summary)


if __name__ == "__main__":
    unittest.main()
