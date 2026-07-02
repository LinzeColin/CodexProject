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

    def test_current_state_records_daily_operation_persistent_authorization_missing_without_runtime_enablement(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(
            "DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT",
            current_state,
        )
        self.assertIn("S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST", current_state)
        self.assertIn("ready_owner_persistent_daily_operation_authorization_request_no_runtime_enablement", current_state)
        self.assertIn("request_only=true", current_state)
        self.assertIn("daily_operation_persistent_enablement_authorization.request.json", current_state)
        self.assertIn("state_hash=be561b7e01250e75d471bbdbd2a4df2e048d8b287bb310d202c8549b2aefb3ee", current_state)
        self.assertIn("DAILY_OPERATION_PERSISTENT_AUTHORIZATION_MISSING_NO_RUNTIME_ENABLEMENT", current_state)
        self.assertIn("S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION", current_state)
        self.assertIn("blocked_persistent_daily_operation_authorization_missing", current_state)
        self.assertIn("persistent_daily_operation_authorization_missing", current_state)
        self.assertIn("daily_operation_persistent_enablement_authorization_gate.json", current_state)
        self.assertIn("daily_operation_persistent_enablement_authorization.json", current_state)
        self.assertIn("state_hash=f9ef81e7a07bca57e11876e2a53d3d18e9148d6da7c8919002ce6cfb55f8ef61", current_state)
        self.assertIn("S2PMT07-DAILY-OPERATION-OWNER-AUTHORIZATION-DECISION", current_state)
        self.assertIn("pass_daily_operation_owner_decision_recorded_keep_disabled", current_state)
        self.assertIn("keep_daily_operation_disabled_no_persistent_authorization", current_state)
        self.assertIn("owner_daily_operation_decision_recorded=true", current_state)
        self.assertIn("owner_daily_operation_authorization_recorded=false", current_state)
        self.assertIn("persistent_daily_operation_authorized=false", current_state)
        self.assertIn("state_hash=803dc436b9c27b99fa82109604184fd8bc028c32eac9a40545e0824ce7f3972b", current_state)
        self.assertIn("daily_operation_owner_authorization_decision.json", current_state)
        self.assertIn("ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-KEEP-DISABLED-20260701.json", current_state)
        self.assertIn("S2PMT07-DAILY-OPERATION-SECRET-AND-ARTIFACT-REPAIR", current_state)
        self.assertIn("status=blocked_owner_daily_operation_authorization_required", current_state)
        self.assertIn("preflight_checks_passed=true", current_state)
        self.assertIn("failed_checks=[]", current_state)
        self.assertIn("production_preflight_status=pass", current_state)
        self.assertIn("state_hash=a856ee3d1532d8973e11bb502f76f7320f9816904b52aab64975112c764de55e", current_state)
        self.assertIn("github_open_pr_count_zero_api_v1", current_state)
        self.assertIn("adp_local_runner_env_file_secret_presence_v1", current_state)
        self.assertIn("secret_env_values_logged=false", current_state)
        self.assertIn("git_artifact_scope_roots=arxiv-daily-push", current_state)
        self.assertIn("OpenAIDatabase/session_history", current_state)
        self.assertIn("do not block this ADP preflight", current_state)
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
        self.assertIn("S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION", current_state)

    def test_persistent_daily_operation_gate_is_bound_to_mainline_without_runtime_enablement(self) -> None:
        manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/"
            / "ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE-MAINLINE-ATTESTATION-20260701.json"
        )
        self.assertTrue(manifest_path.exists(), "persistent authorization gate mainline attestation must exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current = (ADP_ROOT / "docs/pursuing_goal/CURRENT.yaml").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")

        self.assertEqual(
            manifest["task_id"],
            "S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE-MAINLINE-ATTESTATION",
        )
        self.assertEqual(
            manifest["result"],
            "pass_persistent_daily_operation_authorization_gate_mainline_attested_no_runtime_enablement",
        )
        self.assertEqual(manifest["binding_status"], "commit_bound")
        self.assertRegex(manifest["result_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(manifest["result_tree_hash"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            manifest["attested_gate_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization_gate.json",
        )
        self.assertEqual(manifest["attested_gate_status"], "blocked_persistent_daily_operation_authorization_missing")
        self.assertEqual(
            manifest["attested_gate_state_hash"],
            "f9ef81e7a07bca57e11876e2a53d3d18e9148d6da7c8919002ce6cfb55f8ef61",
        )
        self.assertTrue(manifest["persistent_daily_operation_authorization_missing"])
        self.assertFalse(manifest["persistent_daily_operation_authorized"])
        self.assertFalse(manifest["daily_operation_enabled"])
        self.assertFalse(manifest["real_smtp_send_enabled"])
        self.assertFalse(manifest["scheduler_enabled"])
        self.assertFalse(manifest["scheduler_install_enabled"])
        self.assertFalse(manifest["release_packaging_enabled"])
        self.assertFalse(manifest["production_restore_enabled"])
        self.assertFalse(manifest["new_smtp_run_executed_by_this_attestation"])
        self.assertIn(
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json",
            manifest["evidence_refs"],
        )

        self.assertIn(
            "current_iteration: ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION",
            current,
        )
        self.assertIn(
            "current_gate: DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT",
            current,
        )
        self.assertIn("daily_operation_persistent_authorization_request_ready: true", current)
        self.assertIn("daily_operation_persistent_authorization_request_only: true", current)
        self.assertIn(
            "daily_operation_persistent_authorization_request_artifact: FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.request.json",
            current,
        )
        self.assertIn(
            "daily_operation_persistent_authorization_request_state_hash: be561b7e01250e75d471bbdbd2a4df2e048d8b287bb310d202c8549b2aefb3ee",
            current,
        )
        self.assertIn("daily_operation_persistent_authorization_gate_mainline_attested: true", current)
        self.assertIn(
            "daily_operation_persistent_authorization_gate_mainline_attestation_manifest: governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE-MAINLINE-ATTESTATION-20260701.json",
            current,
        )
        self.assertIn("daily_operation_persistent_authorization_gate_mainline_attestation_commit:", current)
        self.assertIn("daily_operation_enabled: false", current)
        self.assertIn("persistent_daily_operation_authorization_missing", current)

        self.assertIn("持久 DAILY_OPERATION 授权请求包已准备好", readme)
        self.assertIn("daily_operation_persistent_enablement_authorization.request.json", readme)
        self.assertIn("持久 DAILY_OPERATION 授权门 mainline 证据已绑定", readme)
        self.assertIn("ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE-MAINLINE-ATTESTATION-20260701.json", readme)
        self.assertIn("持久 DAILY_OPERATION 授权请求包已准备好", decisions)
        self.assertIn("request_only=true", decisions)
        self.assertIn("持久 DAILY_OPERATION 授权门 mainline 证据已绑定", decisions)
        self.assertIn("daily_operation_enabled=false", decisions)
        self.assertIn(
            "ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST",
            ledger,
        )
        self.assertIn(
            "ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE-MAINLINE-ATTESTATION",
            ledger,
        )

    def test_persistent_daily_operation_request_is_bound_to_mainline_without_runtime_enablement(self) -> None:
        manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/"
            / "ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-MAINLINE-ATTESTATION-20260701.json"
        )
        self.assertTrue(manifest_path.exists(), "persistent authorization request mainline attestation must exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current = (ADP_ROOT / "docs/pursuing_goal/CURRENT.yaml").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")

        self.assertEqual(
            manifest["task_id"],
            "S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-MAINLINE-ATTESTATION",
        )
        self.assertEqual(
            manifest["result"],
            "pass_persistent_daily_operation_authorization_request_mainline_attested_no_runtime_enablement",
        )
        self.assertEqual(manifest["binding_status"], "commit_bound")
        self.assertEqual(manifest["result_commit"], "4f72c42ea62275fdd18285cf189070c6aa76bd71")
        self.assertEqual(manifest["result_tree_hash"], "0f0772e4250330372d58456a355e205327dff933")
        self.assertEqual(
            manifest["attested_request_artifact"],
            "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.request.json",
        )
        self.assertEqual(manifest["attested_request_artifact_sha256"], "af14bad7742b776399aa7adbb0b500a04ea3193d8b8be5c6e6a284147e65572e")
        self.assertEqual(manifest["attested_request_state_hash"], "be561b7e01250e75d471bbdbd2a4df2e048d8b287bb310d202c8549b2aefb3ee")
        self.assertTrue(manifest["request_only"])
        self.assertTrue(manifest["persistent_daily_operation_authorization_missing"])
        self.assertFalse(manifest["persistent_daily_operation_authorized"])
        self.assertFalse(manifest["daily_operation_enabled"])
        self.assertFalse(manifest["new_smtp_run_executed_by_this_attestation"])

        self.assertIn(
            "current_iteration: ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION",
            current,
        )
        self.assertIn(
            "current_gate: DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT",
            current,
        )
        self.assertIn("daily_operation_persistent_authorization_request_mainline_attested: true", current)
        self.assertIn("daily_operation_persistent_authorization_request_mainline_attestation_commit: 4f72c42ea62275fdd18285cf189070c6aa76bd71", current)
        self.assertIn("daily_operation_persistent_authorization_request_mainline_attestation_tree_hash: 0f0772e4250330372d58456a355e205327dff933", current)
        self.assertIn("daily_operation_persistent_authorization_request_enablement_allowed: false", current)

        self.assertIn("持久 DAILY_OPERATION 授权请求包 mainline 证据已绑定", readme)
        self.assertIn("daily_operation_persistent_enablement_authorization.request.json", readme)
        self.assertIn("持久 DAILY_OPERATION 授权请求包 mainline 证据已绑定", decisions)
        self.assertIn("request_only=true", decisions)
        self.assertIn("DAILY_OPERATION_PERSISTENT_AUTHORIZATION_REQUEST_MAINLINE_ATTESTED_NO_RUNTIME_ENABLEMENT", roadmap)
        self.assertIn("- source_base_commit: `90b297a55451b691c3e0270cfaa64e5d58c5a519`", owner_status)
        self.assertIn("- source_tree_hash: `d92ec4a0cd884641263c7979f7a5c625229ae83c`", owner_status)
        self.assertIn("- final_commit_binding: `COMMIT_BOUND:90b297a55451b691c3e0270cfaa64e5d58c5a519`", owner_status)
        self.assertIn('source_base_commit: "90b297a55451b691c3e0270cfaa64e5d58c5a519"', assurance)
        self.assertIn('source_tree_hash: "d92ec4a0cd884641263c7979f7a5c625229ae83c"', assurance)
        self.assertIn('final_commit_binding: "COMMIT_BOUND:90b297a55451b691c3e0270cfaa64e5d58c5a519"', assurance)
        self.assertIn(
            "ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-MAINLINE-ATTESTATION",
            ledger,
        )

    def test_owner_option_a_after_persistent_request_keeps_daily_operation_disabled(self) -> None:
        manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/"
            / "ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-KEEP-DISABLED-20260701.json"
        )
        self.assertTrue(manifest_path.exists(), "owner option A decision after request must be recorded")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current = (ADP_ROOT / "docs/pursuing_goal/CURRENT.yaml").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        auth_artifact = REPO_ROOT / "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json"

        self.assertEqual(
            manifest["task_id"],
            "S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-KEEP-DISABLED",
        )
        self.assertEqual(
            manifest["result"],
            "pass_owner_selected_option_a_keep_daily_operation_disabled_after_request_no_runtime_enablement",
        )
        self.assertEqual(manifest["owner_selected_option"], "A")
        self.assertEqual(manifest["decision"], "keep_daily_operation_disabled_no_persistent_authorization")
        self.assertEqual(
            manifest["decision_state_hash"],
            "d793c63910fa3b1e467e0b6b1c78deb63e87a44f02e8507ec363d174b9813fb4",
        )
        self.assertTrue(manifest["request_mainline_attested"])
        self.assertTrue(manifest["persistent_authorization_artifact_absent"])
        self.assertFalse(manifest["persistent_daily_operation_authorized"])
        self.assertFalse(manifest["daily_operation_enabled"])
        self.assertFalse(manifest["real_smtp_send_enabled"])
        self.assertFalse(manifest["scheduler_install_enabled"])
        self.assertFalse(manifest["release_packaging_enabled"])
        self.assertFalse(manifest["production_restore_enabled"])
        self.assertFalse(auth_artifact.exists(), "option A must not create persistent DAILY_OPERATION authorization")

        self.assertIn(
            "current_iteration: ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION",
            current,
        )
        self.assertIn(
            "current_gate: DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT",
            current,
        )
        self.assertIn("next_required_step: DAILY_OPERATION_REMAINS_DISABLED_UNTIL_EXPLICIT_OWNER_AUTHORIZATION", current)
        self.assertIn("daily_operation_owner_option_a_after_request_recorded: true", current)
        self.assertIn("daily_operation_persistent_authorization_request_owner_response: A_KEEP_DISABLED", current)
        self.assertIn("daily_operation_persistent_authorization_owner_decision_after_request_state_hash: d793c63910fa3b1e467e0b6b1c78deb63e87a44f02e8507ec363d174b9813fb4", current)
        self.assertIn("daily_operation_enabled: false", current)

        self.assertIn("owner 已选择 A：继续禁用 DAILY_OPERATION", readme)
        self.assertIn("owner 已选择 A：继续禁用 DAILY_OPERATION", decisions)
        self.assertIn("DAILY_OPERATION_OWNER_DECISION_RECORDED_KEEP_DISABLED_AFTER_REQUEST_NO_RUNTIME_ENABLEMENT", roadmap)
        self.assertIn("DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT", roadmap)
        self.assertIn(
            "ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-KEEP-DISABLED",
            ledger,
        )

    def test_owner_option_a_mainline_attestation_keeps_daily_operation_disabled(self) -> None:
        manifest_path = (
            REPO_ROOT
            / "governance/run_manifests/"
            / "ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION-20260701.json"
        )
        self.assertTrue(manifest_path.exists(), "owner option A mainline attestation must exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        current = (ADP_ROOT / "docs/pursuing_goal/CURRENT.yaml").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        auth_artifact = REPO_ROOT / "FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json"

        self.assertEqual(
            manifest["task_id"],
            "S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION",
        )
        self.assertEqual(
            manifest["result"],
            "pass_owner_option_a_after_request_mainline_attested_keep_disabled_no_runtime_enablement",
        )
        self.assertEqual(manifest["binding_status"], "commit_bound")
        self.assertEqual(manifest["result_commit"], "90b297a55451b691c3e0270cfaa64e5d58c5a519")
        self.assertEqual(manifest["result_tree_hash"], "d92ec4a0cd884641263c7979f7a5c625229ae83c")
        self.assertEqual(manifest["owner_selected_option"], "A")
        self.assertEqual(manifest["decision"], "keep_daily_operation_disabled_no_persistent_authorization")
        self.assertEqual(
            manifest["attested_decision_manifest_sha256"],
            "ce1545e7d9f9c3fd8af016f802a830bc2d2370e92843c14bdf47dc7d32c0e82d",
        )
        self.assertEqual(
            manifest["decision_state_hash"],
            "d793c63910fa3b1e467e0b6b1c78deb63e87a44f02e8507ec363d174b9813fb4",
        )
        self.assertTrue(manifest["persistent_authorization_artifact_absent"])
        self.assertFalse(manifest["persistent_daily_operation_authorized"])
        self.assertFalse(manifest["daily_operation_enabled"])
        self.assertFalse(manifest["real_smtp_send_enabled"])
        self.assertFalse(manifest["scheduler_enabled"])
        self.assertFalse(manifest["scheduler_install_enabled"])
        self.assertFalse(manifest["release_packaging_enabled"])
        self.assertFalse(manifest["production_restore_enabled"])
        self.assertFalse(auth_artifact.exists(), "mainline attestation must not create persistent authorization")

        self.assertIn(
            "current_iteration: ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION",
            current,
        )
        self.assertIn(
            "current_gate: DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT",
            current,
        )
        self.assertIn("daily_operation_owner_option_a_after_request_mainline_attested: true", current)
        self.assertIn("daily_operation_persistent_authorization_owner_decision_after_request_mainline_attestation_commit: 90b297a55451b691c3e0270cfaa64e5d58c5a519", current)
        self.assertIn("daily_operation_persistent_authorization_owner_decision_after_request_mainline_attestation_tree_hash: d92ec4a0cd884641263c7979f7a5c625229ae83c", current)
        self.assertIn("daily_operation_enabled: false", current)

        self.assertIn("owner A 决策 mainline 证据已绑定", readme)
        self.assertIn("owner A 决策 mainline 证据已绑定", decisions)
        self.assertIn("DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT", roadmap)
        self.assertIn("- source_base_commit: `90b297a55451b691c3e0270cfaa64e5d58c5a519`", owner_status)
        self.assertIn("- source_tree_hash: `d92ec4a0cd884641263c7979f7a5c625229ae83c`", owner_status)
        self.assertIn('source_base_commit: "90b297a55451b691c3e0270cfaa64e5d58c5a519"', assurance)
        self.assertIn('source_tree_hash: "d92ec4a0cd884641263c7979f7a5c625229ae83c"', assurance)
        self.assertIn(
            "ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION",
            ledger,
        )

    def test_owner_and_assurance_route_to_persistent_authorization_missing_gate(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        self.assertIn('task_id: "S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION"', assurance)
        self.assertIn("next_task_id: `S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION`", owner_status)
        self.assertIn(
            'release_gate: "DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT"',
            assurance,
        )
        self.assertIn("stage2_integrated_production_accepted: true", assurance)
        self.assertIn("current_zero_proof_open_p0_findings: 0", assurance)
        self.assertIn("current_zero_proof_open_p1_findings: 0", assurance)
        self.assertIn("baseline_counts_mutated: false", assurance)
        self.assertIn("open_pr_count=0", assurance)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", assurance)
        self.assertIn("LaunchAgents disabled", assurance)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/daily_operation_owner_authorization_decision.json", assurance)
        self.assertIn("DAILY_OPERATION owner decision is recorded as keep-disabled", assurance)
        self.assertIn("keep-disabled", owner_status)
        self.assertIn("daily_operation_owner_authorization_decision.json", owner_status)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json if owner authorizes", assurance)
        self.assertIn("daily_operation_persistent_enablement_authorization.json if owner authorizes", owner_status)
        self.assertIn("runtime remains disabled", owner_status)
        self.assertIn("separate enablement preflight", owner_status)
        self.assertNotIn('task_id: "S2PMT07-S2PLT04-COMPLETION-REPORT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-S2PLT04-COMPLETION-REPORT`", owner_status)
        self.assertNotIn('task_id: "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION"', assurance)
        self.assertNotIn('task_id: "S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-EVIDENCE-WRITE"', assurance)
        self.assertIn("owner_decision_recorded_write_gate_allowed", generator)
        self.assertIn("integrated_production_accepted_no_daily_operation", generator)
        self.assertIn("daily_operation_preflight_current", generator)
        self.assertIn("daily_operation_owner_decision_keep_disabled", generator)
        self.assertIn("daily_operation_persistent_authorization_request_ready", generator)
        self.assertIn("daily_operation_persistent_authorization_missing", generator)
        self.assertIn("production_boundary_preflight_ready", generator)
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-PREFLIGHT", generator)
        self.assertIn("S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE", generator)
        self.assertIn("S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION", generator)

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
        self.assertIn("- final_commit_binding: `COMMIT_BOUND:90b297a55451b691c3e0270cfaa64e5d58c5a519`", owner_status)
        self.assertIn('final_commit_binding: "COMMIT_BOUND:90b297a55451b691c3e0270cfaa64e5d58c5a519"', assurance)
        self.assertRegex(owner_status, r"- source_base_commit: `[0-9a-f]{40}`")
        self.assertRegex(owner_status, r"- source_tree_hash: `[0-9a-f]{40}`")
        self.assertRegex(assurance, r'(?m)^source_base_commit: "[0-9a-f]{40}"$')
        self.assertRegex(assurance, r'(?m)^source_tree_hash: "[0-9a-f]{40}"$')
        self.assertNotIn(f"- final_commit_binding: `COMMIT_BOUND:{result_commit}`", owner_status)
        self.assertIn("- final_commit_binding: `COMMIT_BOUND:90b297a55451b691c3e0270cfaa64e5d58c5a519`", owner_status)
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
            "current_iteration: ITER-20260701-ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION",
            current,
        )
        self.assertIn(
            "current_gate: DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT",
            current,
        )
        self.assertIn("next_executable_task: S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION", current)
        self.assertIn("next_required_step: DAILY_OPERATION_REMAINS_DISABLED_UNTIL_EXPLICIT_OWNER_AUTHORIZATION", current)
        self.assertIn("daily_operation_owner_option_a_after_request_recorded: true", current)
        self.assertIn("daily_operation_persistent_authorization_request_owner_response: A_KEEP_DISABLED", current)
        self.assertIn(
            "daily_operation_persistent_authorization_owner_decision_after_request_state_hash: d793c63910fa3b1e467e0b6b1c78deb63e87a44f02e8507ec363d174b9813fb4",
            current,
        )
        self.assertIn("daily_operation_persistent_authorization_request_ready: true", current)
        self.assertIn("daily_operation_persistent_authorization_request_only: true", current)
        self.assertIn("daily_operation_persistent_authorization_request_status: ready_owner_persistent_daily_operation_authorization_request_no_runtime_enablement", current)
        self.assertIn("daily_operation_persistent_authorization_request_artifact: FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.request.json", current)
        self.assertIn("daily_operation_persistent_authorization_request_manifest: governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-20260701.json", current)
        self.assertIn("daily_operation_persistent_authorization_request_state_hash: be561b7e01250e75d471bbdbd2a4df2e048d8b287bb310d202c8549b2aefb3ee", current)
        self.assertIn("daily_operation_persistent_authorization_request_enablement_allowed: false", current)
        self.assertIn("daily_operation_persistent_authorization_gate_written: true", current)
        self.assertIn("daily_operation_persistent_authorization_gate_status: blocked_persistent_daily_operation_authorization_missing", current)
        self.assertIn("daily_operation_persistent_authorization_gate_artifact: FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization_gate.json", current)
        self.assertIn("daily_operation_persistent_authorization_gate_manifest: governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-GATE-20260701.json", current)
        self.assertIn("daily_operation_persistent_authorization_gate_state_hash: f9ef81e7a07bca57e11876e2a53d3d18e9148d6da7c8919002ce6cfb55f8ef61", current)
        self.assertIn("daily_operation_persistent_authorization_artifact: FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json", current)
        self.assertIn("persistent_daily_operation_authorization_missing", current)
        self.assertIn("daily_operation_persistent_authorization_enablement_allowed: false", current)
        self.assertIn("daily_operation_owner_decision_recorded: true", current)
        self.assertIn("daily_operation_owner_decision_status: pass_daily_operation_owner_decision_recorded_keep_disabled", current)
        self.assertIn("daily_operation_owner_decision_artifact: FINAL_ACCEPTANCE_BUNDLE/daily_operation_owner_authorization_decision.json", current)
        self.assertIn("daily_operation_owner_decision_manifest: governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-KEEP-DISABLED-20260701.json", current)
        self.assertIn("daily_operation_owner_decision_state_hash: 803dc436b9c27b99fa82109604184fd8bc028c32eac9a40545e0824ce7f3972b", current)
        self.assertIn("daily_operation_owner_decision: keep_daily_operation_disabled_no_persistent_authorization", current)
        self.assertIn("daily_operation_owner_authorization_recorded: false", current)
        self.assertIn("daily_operation_persistent_authorized: false", current)
        self.assertIn("daily_operation_owner_decision_enablement_allowed: false", current)
        self.assertIn("daily_operation_authorization_preflight_written: true", current)
        self.assertIn("daily_operation_authorization_preflight_status: blocked_owner_daily_operation_authorization_required", current)
        self.assertIn("daily_operation_authorization_preflight_passed: true", current)
        self.assertIn(
            "daily_operation_authorization_preflight_state_hash: a856ee3d1532d8973e11bb502f76f7320f9816904b52aab64975112c764de55e",
            current,
        )
        self.assertIn("daily_operation_authorization_preflight_github_cli_equivalent_id: github_open_pr_count_zero_api_v1", current)
        self.assertIn("daily_operation_authorization_preflight_github_cli_equivalent_accepted: true", current)
        self.assertIn("daily_operation_authorization_preflight_secret_env_evidence_id: adp_local_runner_env_file_secret_presence_v1", current)
        self.assertIn("daily_operation_authorization_preflight_secret_env_values_logged: false", current)
        self.assertIn("daily_operation_authorization_preflight_git_artifact_scope_roots:", current)
        self.assertIn("    - arxiv-daily-push", current)
        self.assertIn("daily_operation_authorization_preflight_failed_checks: []", current)
        self.assertIn("owner_daily_operation_authorization_missing", current)
        self.assertIn("daily_operation_not_enabled", current)
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
        self.assertIn("持久 DAILY_OPERATION 授权请求包已准备好", decisions)
        self.assertIn("daily_operation_persistent_enablement_authorization.request.json", decisions)
        self.assertIn("request_only=true", decisions)
        self.assertIn("持久 DAILY_OPERATION 授权门已运行但阻断", decisions)
        self.assertIn("daily_operation_persistent_enablement_authorization_gate.json", decisions)
        self.assertIn("daily_operation_persistent_enablement_authorization.json", decisions)
        self.assertIn("persistent_daily_operation_authorization_missing", decisions)
        self.assertIn("DAILY_OPERATION owner 决策已记录为保持禁用", decisions)
        self.assertIn("keep_daily_operation_disabled_no_persistent_authorization", decisions)
        self.assertIn("persistent_daily_operation_authorized=false", decisions)
        self.assertIn("preflight_checks_passed=true", decisions)
        self.assertIn("production_preflight_status=pass", decisions)
        self.assertIn("github_open_pr_count_zero_api_v1", decisions)
        self.assertIn("adp_local_runner_env_file_secret_presence_v1", decisions)
        self.assertIn("values_logged=false", decisions)
        self.assertIn("git_artifact_scope_roots=arxiv-daily-push", decisions)
        self.assertIn("integrated_production_acceptance.json", decisions)
        self.assertIn("stage2_integrated_production_accepted=true", decisions)
        self.assertIn("保持 DAILY_OPERATION 禁用", decisions)
        self.assertIn("不得自动启用 SMTP/scheduler/Release/restore/DAILY_OPERATION", decisions)
        self.assertIn("持久 DAILY_OPERATION 授权请求包已准备好", readme)
        self.assertIn("daily_operation_persistent_enablement_authorization.request.json", readme)
        self.assertIn("持久 DAILY_OPERATION 授权门已阻断", readme)
        self.assertIn("daily_operation_persistent_enablement_authorization_gate.json", readme)
        self.assertIn("daily_operation_persistent_enablement_authorization.json", readme)
        self.assertIn("persistent_daily_operation_authorization_missing", readme)
        self.assertIn("DAILY_OPERATION owner 决策已记录为保持禁用", readme)
        self.assertIn("daily_operation_owner_authorization_decision.json", readme)
        self.assertIn("persistent_daily_operation_authorized=false", readme)
        self.assertIn("github_open_pr_count_zero_api_v1", readme)
        self.assertIn("adp_local_runner_env_file_secret_presence_v1", readme)
        self.assertIn("secret value", readme)
        self.assertIn("ADP scoped git artifact hygiene", readme)
        self.assertIn("integrated_production_acceptance.json", readme)
        self.assertIn("DAILY_OPERATION 仍未启用", readme)
        self.assertIn("S2PMT07-DAILY-OPERATION-SECRET-AND-ARTIFACT-REPAIR", readme)
        self.assertIn("DAILY_OPERATION_PERSISTENT_AUTHORIZATION_REQUEST_MAINLINE_ATTESTED_NO_RUNTIME_ENABLEMENT", roadmap)
        self.assertIn("daily_operation_persistent_enablement_authorization.request.json", roadmap)
        self.assertIn("DAILY_OPERATION_PERSISTENT_AUTHORIZATION_MISSING_NO_RUNTIME_ENABLEMENT", roadmap)
        self.assertIn("persistent_daily_operation_authorization_missing", roadmap)
        self.assertIn("daily_operation_persistent_enablement_authorization.json", roadmap)
        self.assertIn("github_open_pr_count_zero_api_v1", roadmap)
        self.assertIn("SMTP secret key-presence metadata", roadmap)
        self.assertIn("persistent_daily_operation_authorized=false", roadmap)
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
            "- current_task: `S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION`",
            summary,
        )
        self.assertIn(
            "- next_gate: `DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTED_KEEP_DISABLED_NO_RUNTIME_ENABLEMENT`",
            summary,
        )
        self.assertIn("owner A keep-disabled decision mainline-bound", summary)
        self.assertIn("persistent_daily_operation_authorized=false", summary)
        self.assertIn("daily_operation_enabled=false", summary)

    def test_s3_daily_operation_handoff_records_post_acceptance_blocker(self) -> None:
        handoff = (REPO_ROOT / "HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        one_look = (ADP_ROOT / "用户中心/一看三查.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        mvp_prep = (ADP_ROOT / "用户中心/MVP准备与复审修补.md").read_text(encoding="utf-8")

        self.assertIn("S3 DAILY_OPERATION 下一 Agent 先读", handoff)
        self.assertIn("交接内容生成基线", handoff)
        self.assertIn("bccc600959e6bf478c8fc71f8c2e90c13c455d1f", handoff)
        self.assertIn("交接页首次落库提交", handoff)
        self.assertIn("91f22b876b05f373229ef4bf5de2e67bdb927c0b", handoff)
        self.assertNotIn("| current main |", handoff)
        self.assertIn("stage2_integrated_production_accepted=true", handoff)
        self.assertIn("production_acceptance_claimed=true", handoff)
        self.assertIn("daily_operation_enabled=false", handoff)
        self.assertIn("persistent_daily_operation_authorized=false", handoff)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json", handoff)
        self.assertIn("不要把它当成当前 S3/DAILY_OPERATION 状态页", handoff)
        self.assertIn(
            "`FINAL_ACCEPTANCE_BUNDLE/manifest.json`、`no_production_side_effects.json`、`owner_production_boundary_decision.json`、`p0_p1_zero_proof.json`",
            handoff,
        )
        self.assertIn(
            "`closure_state` / `no_production_side_effects` false 字段，只说明该 artifact 写入时的 no-production / closure-state 语境",
            handoff,
        )
        self.assertIn(
            "不得回退当前 Stage 2 accepted 事实，也不得诱导修改这些历史 final bundle artifact",
            handoff,
        )
        self.assertIn(
            "当前 Stage 2 accepted 事实以 `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml` 和 `FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json` 为准",
            handoff,
        )
        self.assertIn("不要为了追逐当前提交号重复改写本页", handoff)
        self.assertIn("不要启用 SMTP", handoff)
        self.assertIn("不要启用、安装或 kickstart scheduler/LaunchAgents", handoff)
        self.assertIn("open_pr_count=0", handoff)
        self.assertIn("User-Agent: codex-adp-open-pr-check", handoff)
        self.assertIn("https://github.com/LinzeColin/CodexProject/pulls?q=is%3Apr+is%3Aopen", handoff)
        self.assertIn('test "$OPEN_PR_COUNT" = "0"', handoff)
        self.assertIn("若 open PR 结果为 `UNKNOWN` 或非 0，停止并回报，不得当作通过", handoff)
        self.assertNotIn("https://api.github.com/repos/LinzeColin/CodexProject/pulls?state=open", handoff)
        self.assertIn("HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md", readme)
        self.assertIn("HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md", decisions)
        self.assertIn("open PR 边界复核 fallback 已同步到停止门", readme)
        self.assertIn("只有明确得到 `open_pr_count=0` 才能通过", readme)
        self.assertIn("`UNKNOWN`、非 0、命令失败或无法解析都必须停止并回报", readme)
        self.assertIn("open PR 边界复核 fallback", roadmap)
        self.assertIn("只接受明确 `open_pr_count=0`", roadmap)
        self.assertIn("`UNKNOWN`、非 0、命令失败或无法解析都必须停止并回报，不得当作通过", roadmap)
        self.assertIn("该复核只证明 open PR 边界，不授权 S3/DAILY_OPERATION", roadmap)
        self.assertTrue(mvp_prep.startswith("# MVP 准备与复审修补\n"))
        self.assertIn("不进入 S3/DAILY_OPERATION", mvp_prep)
        self.assertIn("只做复审、修补、用户向可读性、证据同步、测试补强和低风险局部修复", mvp_prep)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json", mvp_prep)
        self.assertIn("daily_operation_enabled=false", mvp_prep)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", mvp_prep)
        self.assertIn("GitHub `origin/main` 的干净隔离工作树", mvp_prep)
        self.assertIn("本机脏工作树、detached HEAD 或临时 worktree 结果不能单独当作交付基线", mvp_prep)
        self.assertIn("## 09 推荐第一轮 Run Contract", mvp_prep)
        self.assertIn("MVP 准备与复审修补](./MVP准备与复审修补.md)", readme)
        self.assertIn("MVP 准备与复审修补](./MVP准备与复审修补.md)", decisions)
        self.assertIn("MVP 准备与复审修补](./MVP准备与复审修补.md)", one_look)
        self.assertIn("MVP 准备与复审修补](./MVP准备与复审修补.md)", roadmap)
        self.assertIn("Stage 2 accepted 后的 MVP 复审修补", roadmap)
        self.assertIn("当前工作不是继续实现多来源，而是修补 owner-facing 证据、用户中心和测试", roadmap)
        self.assertIn("不是正式生产前预检查，也不是 S3/DAILY_OPERATION 启用", roadmap)
        self.assertIn("维护复习行动收益展示", roadmap)
        self.assertNotIn("多来源、多邮件、多复习行动收益链路仍在推进", roadmap)
        self.assertNotIn("这是正式生产前的最终预检查", roadmap)
        self.assertNotIn("补齐复习行动收益每日快照", roadmap)
        self.assertNotIn("没有用户中心数量快照就说体验完整", roadmap)
        self.assertIn("Stage 2 最终门 | 已通过 Stage 2 integrated acceptance", one_look)
        self.assertIn("S3 / DAILY_OPERATION | 不进入；保持禁用", one_look)
        self.assertIn("Stage 2 integrated acceptance | 已记录并保持 `true`", decisions)
        self.assertIn("是否现在宣称 Stage 2 integrated acceptance 已记录 | 接受", decisions)
        self.assertIn("是否现在宣称 S3/DAILY_OPERATION 已进入 | 不接受", decisions)
        self.assertIn("运行基线 | 本机和 launchd 只作为历史/受控运行证据来源", decisions)
        self.assertNotIn("本机加本地 Codex 运行器是当前生产策略", decisions)
        self.assertNotIn("Stage 2 最终门 | 未通过", one_look)
        self.assertNotIn("| Stage 2 | 尚未正式生产通过 |", decisions)
        self.assertNotIn("是否现在宣称 Stage 2 生产通过 | 不接受", decisions)
        self.assertNotIn("Final bundle 已公开 S2PLT03 capture plan summary，但它仍 blocked", decisions)
        model_params = (ADP_ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        self.assertIn("handoff_source_baseline=bccc600959e6bf478c8fc71f8c2e90c13c455d1f", model_params)
        self.assertIn("handoff_first_main_commit=91f22b876b05f373229ef4bf5de2e67bdb927c0b", model_params)
        self.assertNotIn("current_main=bccc600959e6bf478c8fc71f8c2e90c13c455d1f", model_params)


if __name__ == "__main__":
    unittest.main()
