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
        self.assertIn("ADP_ALLOW_SMTP_SEND` raw value is `UNSET` or false-like", current_state)
        self.assertIn("LaunchAgents disabled", current_state)
        self.assertIn("no background ADP process", current_state)
        self.assertIn("No DAILY_OPERATION, standing SMTP permission, scheduler enable/install, Release, or production restore is claimed", current_state)
        self.assertIn("S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION", current_state)
        self.assertIn("`ADP_ALLOW_SMTP_SEND` raw value is `UNSET` or false-like", ledger)
        self.assertIn("foreground process `ADP_ALLOW_SMTP_SEND` was false-like", ledger)
        self.assertNotIn(
            "Boundary: `integrated_production_accepted=true` remains recorded, but "
            "`daily_operation_enabled=false`, persistent `ADP_ALLOW_SMTP_SEND=false`",
            ledger,
        )
        self.assertNotIn(
            "Runtime boundary: persistent `ADP_ALLOW_SMTP_SEND=false`, daily/health/watchdog LaunchAgents disabled",
            ledger,
        )
        self.assertNotIn(
            "no background ADP process after closeout, persistent `ADP_ALLOW_SMTP_SEND=false`, "
            "process `ADP_ALLOW_SMTP_SEND=false`",
            ledger,
        )

    def test_owner_decision_page_marks_superseded_daily_operation_blockers_as_historical(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn("persistent_daily_operation_authorization_missing", decisions)
        self.assertIn(
            "历史：gh 等价证据已修复，当时仍有 SMTP 与大文件治理阻断",
            decisions,
        )
        self.assertIn(
            "当时阻断 1（后续已由 secret / artifact repair 消费）：缺 SMTP secret env 名称",
            decisions,
        )
        self.assertIn(
            "当时阻断 2（非当前 ADP 阻断）：既有 `OpenAIDatabase/session_history` archive",
            decisions,
        )
        self.assertIn(
            "历史：DAILY_OPERATION 授权预检已运行但当时阻断",
            decisions,
        )
        self.assertIn(
            "当时阻断 2（后续已由 secret / artifact repair 消费）：缺 SMTP secret env 名称",
            decisions,
        )
        self.assertIn(
            "当时阻断 3（非当前 ADP 阻断）：既有 `OpenAIDatabase/session_history` archive",
            decisions,
        )

        self.assertNotIn("剩余阻断 1：缺 SMTP secret env 名称", decisions)
        self.assertNotIn("剩余阻断 2：既有 `OpenAIDatabase/session_history` archive", decisions)
        self.assertNotIn("| 阻断 2：缺 SMTP secret env 名称", decisions)
        self.assertNotIn("| 阻断 3：既有 `OpenAIDatabase/session_history` archive", decisions)

    def test_owner_decision_page_does_not_reopen_pre_acceptance_final_bundle_gaps(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn("Stage 2 final-bundle live artifacts 已存在并已被 integrated acceptance 消费", decisions)
        self.assertIn(
            "当前只剩 S3/DAILY_OPERATION 持久授权 artifact 缺失",
            decisions,
        )
        self.assertIn("历史当时 final bundle readiness 为 blocked", decisions)
        self.assertIn("历史当时 `live_artifact_write_guard` 为 blocked", decisions)
        self.assertIn("历史当时 live `FINAL_ACCEPTANCE_BUNDLE/manifest.json` 仍缺失", decisions)

        forbidden_phrases = (
            "Final bundle readiness 仍为 blocked，缺 `manifest.json`",
            "保持 `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json`、`FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`、`HANDOFF/00_下一Agent先读.md`、`FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml`、`FINAL_ACCEPTANCE_BUNDLE/manifest.json` 不写入",
            "`FINAL_ACCEPTANCE_BUNDLE/manifest.json`、`s2plt04_completion_report.json`、`independent_review_signoff.yaml`、`final_command_execution.json` 和 `HANDOFF/00_下一Agent先读.md` 仍缺",
            "live `FINAL_ACCEPTANCE_BUNDLE/manifest.json` 仍缺失，final bundle/S2PMT07 不因此通过",
            "validate-final-acceptance-bundle --repo-root . --json` 仍 blocked",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_post_s2plt02_historical_gaps(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 final bundle prerequisite 仍 blocked",
            decisions,
        )
        self.assertIn(
            "历史当时 S2PLT03/S2PLT04/final bundle 继续阻断",
            decisions,
        )
        self.assertIn(
            "`validate-final-acceptance-bundle --json` 历史当时仍 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )
        forbidden_phrases = (
            "| final bundle prerequisite 仍 blocked | 默认下一步",
            "| S2PLT02 terminal delivery proof artifact | 下一步只能构建",
            "| S2PLT03/S2PLT04/final bundle | 继续阻断；不得跳过 S2PLT02 terminal proof | `validate-final-acceptance-bundle --json` 仍 blocked |",
            "`plan-final-bundle-prerequisites --json` 当前只剩 S2PLT03 terminal resilience proof 缺口",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_early_final_bundle_runtime_gaps(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 `plan-final-bundle-prerequisites` 为 blocked，但已给出 `next_executable_command=plan-s2plt02-terminal-delivery-proof-capture`",
            decisions,
        )
        self.assertIn(
            "历史当时 S2PLT02 capture command dry-run 仍 `blocked`",
            decisions,
        )
        self.assertIn(
            "历史当时 `plan-final-bundle-prerequisites` 与 `validate-final-acceptance-bundle` 都 blocked",
            decisions,
        )
        self.assertIn(
            "历史当时 `validate-final-acceptance-bundle` 为 blocked",
            decisions,
        )
        self.assertIn(
            "历史当时 `plan-final-bundle-prerequisites` 为 blocked，`next_required_step=S2PLT04_COMPLETION_REPORT`",
            decisions,
        )
        forbidden_phrases = (
            "| `plan-final-bundle-prerequisites` 当前 blocked",
            "| S2PLT02 capture command dry-run 仍 `blocked`",
            "| `plan-final-bundle-prerequisites` 与 `validate-final-acceptance-bundle` 当前都 blocked",
            "剩余 runtime actions 是 `capture_second_consecutive_real_m1_m4_smtp_day`",
            "；当前只有 `1/2` 真实发送日、`4/8` 真实邮件",
            "| `validate-final-acceptance-bundle` 当前 blocked",
            "| `plan-final-bundle-prerequisites` 当前 blocked，`next_required_step=S2PLT04_COMPLETION_REPORT`",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_top_level_wait_state_rows_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        expected_historical_rows = (
            "历史当时 prerequisite plan `67fd78529ab74d520477820d588053c5796db88322a6affa111f278a203d5232` 与 final readiness `cfcd3d70c0cca7f0a5a8bc3804f599001e585a65dc80fed0cecc75996c6798ee` 均 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 prerequisite plan `d95f0afad934a6692635960d48cda963074840c0615f9bafe1fb023ff9c4f612` 与 final validator `0c032d9c804410f2b4ffe11cb52b00e91500fd7790d1eac533154650625b3c6e` 均 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 prerequisite plan `256aa1a8dfeff4f598fa9fbb172aae3f6e7cde428bde570424a2bc779da7e320` 与 final validator `494538d0e454c51869eca559808316740a422f92b7deeb070d348f65e1277d67` 均 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 prerequisite plan `2ee61c653d48b74f03505221adf6e37039d9cd4339b5554ba145dd02f9ec6198` 与 final validator `3ba4d2fdcc2ea9bfc268f7f579ce8e8e4e3458ee6c69400e157571906ba16b29` 均 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 plan `447072118012325d6b8740d76f37b1838ec788e09e591fbe451fe3a61b0f8d04` 与 final `45669a5d11c178dc6f2eaf23c806fabc420c2e20b2bf4f6b0fbd4f79504d1048` 均 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
        )
        for phrase in expected_historical_rows:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, decisions)

        forbidden_phrases = (
            "| 当前 prerequisite plan `67fd78529ab74d520477820d588053c5796db88322a6affa111f278a203d5232` 与 final readiness `cfcd3d70c0cca7f0a5a8bc3804f599001e585a65dc80fed0cecc75996c6798ee` 均 blocked |",
            "| 当前 prerequisite plan `d95f0afad934a6692635960d48cda963074840c0615f9bafe1fb023ff9c4f612` 与 final validator `0c032d9c804410f2b4ffe11cb52b00e91500fd7790d1eac533154650625b3c6e` 均 blocked |",
            "| 当前 prerequisite plan `256aa1a8dfeff4f598fa9fbb172aae3f6e7cde428bde570424a2bc779da7e320` 与 final validator `494538d0e454c51869eca559808316740a422f92b7deeb070d348f65e1277d67` 均 blocked |",
            "| 当前 prerequisite plan `2ee61c653d48b74f03505221adf6e37039d9cd4339b5554ba145dd02f9ec6198` 与 final validator `3ba4d2fdcc2ea9bfc268f7f579ce8e8e4e3458ee6c69400e157571906ba16b29` 均 blocked |",
            "| 当前 plan `447072118012325d6b8740d76f37b1838ec788e09e591fbe451fe3a61b0f8d04` 与 final `45669a5d11c178dc6f2eaf23c806fabc420c2e20b2bf4f6b0fbd4f79504d1048` 均 blocked |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_terminal_count_split_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 capture-window 新增真实天数 `0`、新增真实邮件 `0`，`8` 封 dry-run 被拒计入 terminal proof",
            decisions,
        )
        self.assertIn(
            "历史当时 terminal proof 数量口径为 `1/2` 天、`4/8` 封；当前这些数量缺口已被 final bundle 和 Stage 2 integrated acceptance 消费",
            decisions,
        )
        self.assertIn(
            "历史当时 S2PLT03、S2PLT04、final bundle 仍依赖 S2PLT02 terminal proof；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )

        forbidden_phrases = (
            "| 当前 capture-window 新增真实天数 `0`、新增真实邮件 `0`，`8` 封 dry-run 被拒计入 terminal proof |",
            "| terminal proof 仍只达到 `1/2` 天、`4/8` 封 |",
            "| S2PLT03、S2PLT04、final bundle 仍依赖 S2PLT02 terminal proof |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_capture_window_summary_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 2026-06-29/2026-06-30 daily run succeeded 但为 dry-run",
            decisions,
        )
        self.assertIn(
            "历史当时 8 封真实邮件未证明；当前这些 capture-window 缺口已被 final bundle 和 Stage 2 integrated acceptance 消费",
            decisions,
        )
        self.assertIn(
            "历史当时真实 scheduler proof 未证明；当前不作为 S3/MVP 默认下一步",
            decisions,
        )
        self.assertIn(
            "历史当时 `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` 缺失；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )

        forbidden_phrases = (
            "| 2026-06-29/2026-06-30 daily run succeeded 但为 dry-run | 不把这两天计入 S2PLT02 terminal proof；继续等待真实第二个连续 M1-M4 SMTP 日 |",
            "| 8 封真实邮件未证明 | 保持 `real_sent_candidate_email_count=0` 与 `dry_run_email_count=8` 的分离口径 |",
            "| 真实 scheduler proof 未证明 | 保持 launchd loaded-but-disabled 为非终态 scheduler proof |",
            "| `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` 缺失 | 不写 S2PLT03/S2PLT04/final bundle；先完成 S2PLT02 terminal proof artifact 验证 |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_artifact_validation_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` 的 artifact validation 为 `terminal_artifact_present=false`",
            decisions,
        )
        self.assertIn(
            "历史当时阻断原因包括 `s2plt02_terminal_delivery_proof_artifact_missing;two_consecutive_real_days_not_proven;eight_real_emails_not_proven;real_scheduler_not_proven`；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )

        forbidden_phrases = (
            "| `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` 当前 `terminal_artifact_present=false`",
            "| 阻断原因仍是 `s2plt02_terminal_delivery_proof_artifact_missing;two_consecutive_real_days_not_proven;eight_real_emails_not_proven;real_scheduler_not_proven` |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_zero_proof_request_consumption_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 request 状态已移除 `p0_p1_zero_proof_artifact_missing`，但 final readiness 仍 blocked",
            decisions,
        )
        self.assertIn(
            "历史当时 final readiness `cf9a46ccbdfd35b01bd579511ed7ae1cdfcac411e00d8f610c80625f596e1094` 仍 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )

        forbidden_phrases = (
            "| request 状态已移除 `p0_p1_zero_proof_artifact_missing`，但 final readiness 仍 blocked |",
            "| 当前 final readiness `cf9a46ccbdfd35b01bd579511ed7ae1cdfcac411e00d8f610c80625f596e1094` 仍 blocked |",
            "| 当前 final readiness `cf9a46ccbdfd35b01bd579511ed7ae1cdfcac411e00d8f610c80625f596e1094` 仍 blocked | 维持 `WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW`；不得声明 Stage2/S3 production accepted |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_inventory_capture_plan_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 capture plan `aafb8d5147d8c7849a2489bfb4991376e978d646b5e149156cbba58ae513aff1` 仍 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )
        self.assertIn(
            "历史当时 capture plan `cba2fb5be5cc1a7dc098b28fe0b0bd137fb43d18e4f077d755571313bcee03e4` 仍 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )

        forbidden_phrases = (
            "| 当前 capture plan `aafb8d5147d8c7849a2489bfb4991376e978d646b5e149156cbba58ae513aff1` 仍 blocked |",
            "| 当前 capture plan `cba2fb5be5cc1a7dc098b28fe0b0bd137fb43d18e4f077d755571313bcee03e4` 仍 blocked |",
            "| 缺失真实 scheduler proof 和 S2PLT02 terminal proof artifact | 等真实捕获窗口满足后，再构建 reviewed terminal proof artifact 并运行 validator | prerequisite `94fbe44f8211dff645ad5939696843122191b5b10ed939a1e04105c5e312c6b9`",
            "| 缺失真实 scheduler proof 和 S2PLT02 terminal proof artifact | 等真实捕获窗口满足后，再构建 reviewed terminal proof artifact 并运行 validator | prerequisite `bcb40505ad7244626589c24991dcf05fe775268ce44b5eab3b68444f38cded6e`",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_runtime_auth_gate_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 `plan-s2plt02-terminal-delivery-proof-capture` 的 `authorization_artifact_status=pass`，但 `runtime_capture_ready=false`；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )
        self.assertIn(
            "历史当时 next executable step 是 `WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW`；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )
        self.assertIn(
            "历史当时 matching authorization 仍不等于 S2PLT02 accepted；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            decisions,
        )

        forbidden_phrases = (
            "| `plan-s2plt02-terminal-delivery-proof-capture` 当前 `authorization_artifact_status=pass`，但 `runtime_capture_ready=false` |",
            "| 当前 next executable step 是 `WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW` |",
            "| matching authorization 仍不等于 S2PLT02 accepted | 继续阻断第二真实日、8 封真实邮件、真实 scheduler proof 和 terminal proof artifact |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_authorization_hash_and_s2plt03_plan_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        expected_historical_rows = (
            "历史当时 live 授权 artifact 只有在 `readiness_state_hash` 匹配 expected hash `79ac4987239ecad8d4eee82de0157901b59259100e6d738bd1b15d17a37dc76e` 时才算当时有效；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 stale/wrong hash 会 `authorization_artifact_status=blocked`，`real_proof_capture_authorized=false`；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 matching hash 仍不等于 S2PLT02 accepted；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 `plan-s2plt03-terminal-resilience-proof-capture` blocked，`next_executable_step=WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE`；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT03 输入只是 `LOCAL_RESILIENCE_DRILL`、`RESILIENCE_PRECHECK`、`P0_P1_ZERO_PROOF`；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
        )
        for phrase in expected_historical_rows:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, decisions)

        forbidden_phrases = (
            "| live 授权 artifact 现在只有在 `readiness_state_hash` 匹配 expected hash `79ac4987239ecad8d4eee82de0157901b59259100e6d738bd1b15d17a37dc76e` 时才算当前有效 |",
            "| stale/wrong hash 会 `authorization_artifact_status=blocked`，`real_proof_capture_authorized=false`，错误为 `readiness_state_hash does not match current readiness state` | 保持 fail-closed；重新生成或复核授权前，不允许把授权 action 标记完成 |",
            "| matching hash 仍不等于 S2PLT02 accepted | 即使授权 pass，也继续阻断第二真实日、8 封真实邮件、真实 scheduler proof 和 terminal proof artifact |",
            "| `plan-s2plt03-terminal-resilience-proof-capture` 当前 blocked，`next_executable_step=WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE`，不得直接写 S2PLT03 terminal proof artifact |",
            "| 当前已完成的 S2PLT03 输入只是 `LOCAL_RESILIENCE_DRILL`、`RESILIENCE_PRECHECK`、`P0_P1_ZERO_PROOF` |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_evidence_inventory_and_dry_run_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        expected_historical_rows = (
            "历史当时 `audit-s2plt02-terminal-proof-evidence-inventory --launchctl-disabled-file` 指向缺失文件时返回 blocked JSON；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时正常 evidence inventory 仍 blocked：当时仅 1 个真实发送日、4 封真实邮件、2 个 nonterminal succeeded dry-run 日；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 2026-06-29/2026-06-30 的 `adp-daily-run.json` 均为 `status=succeeded`，但 M1-M4 SMTP reports 是 dry-run；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 `nonterminal_succeeded_dry_run_count=2`、dry-run 邮件 8 封、真实候选发送 0 封；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
        )
        for phrase in expected_historical_rows:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, decisions)

        forbidden_phrases = (
            "| `audit-s2plt02-terminal-proof-evidence-inventory --launchctl-disabled-file` 指向缺失文件时，现在返回 blocked JSON，不再抛 Python traceback |",
            "| 正常 evidence inventory 仍 blocked：当前仅 1 个真实发送日、4 封真实邮件、2 个 nonterminal succeeded dry-run 日 |",
            "| 2026-06-29/2026-06-30 的 `adp-daily-run.json` 均为 `status=succeeded`，但 M1-M4 SMTP reports 是 dry-run | 将两天都分类为 `daily_run_succeeded_but_smtp_dry_run_not_terminal`；不得写 terminal proof，不得宣称第二真实日、8 封真实邮件或 scheduler proof 已满足 |",
            "| `nonterminal_succeeded_dry_run_count=2`、dry-run 邮件 8 封、真实候选发送 0 封 | 继续按 S2PLT02 capture plan 采集第二真实 M1-M4 SMTP 日、真实 scheduler proof，再写 reviewed terminal proof artifact |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_nonterminal_s2plt04_runtime_readiness_as_current_gap(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        expected_historical_rows = (
            "历史当时 S2PLT04 audit 顶层已公开 S2PLT02/S2PLT03 非终态证据数量，但 completion report 仍未就绪；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 LaunchAgents 已 loaded 且有 calendar triggers，但仍 disabled/not running；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT04 已消费 14 条 S2PLT02 nonterminal refs 但仍 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT04 audit 已同步 13 条 S2PLT02 nonterminal refs，但仍缺 terminal proof；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 live 授权已通过但 readiness 仍 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 terminal proof 仍缺失；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT02 terminal proof missing；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT04 completion report missing；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 final bundle incomplete；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
        )
        for phrase in expected_historical_rows:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, decisions)

        forbidden_phrases = (
            "| S2PLT04 audit 顶层已公开 S2PLT02/S2PLT03 非终态证据数量，但 completion report 仍未就绪 |",
            "| `state_hash=ee3917fedcd96e10a23fbd228367e6837ffca092734d98288502d9702514165f` 仍为 blocked |",
            "| LaunchAgents 已 loaded 且有 calendar triggers，但仍 disabled/not running | 不得把 loaded/calendar trigger 当作真实 scheduler proof；继续按 capture plan 等待第二真实 M1-M4 SMTP 日、8 封真实邮件、真实 scheduler proof 和 reviewed terminal artifact |",
            "| S2PLT04 已消费 14 条 S2PLT02 nonterminal refs 但仍 blocked | 继续阻断 S2PLT04 completion report，直到 S2PLT02/S2PLT03 terminal evidence 均通过 |",
            "| S2PLT04 audit 已同步 13 条 S2PLT02 nonterminal refs，但仍缺 terminal proof | 继续按 capture plan 采集第二真实 M1-M4 SMTP 日、8 封真实邮件、真实 scheduler proof，再补 S2PLT03 terminal proof；未齐前不得写 S2PLT04 completion report |",
            "| live 授权已通过但 readiness 仍 blocked | 把授权视为已完成 next action；继续采集第二真实日、真实 scheduler proof 和 terminal proof artifact |",
            "| terminal proof 仍缺失 | 不得用授权 artifact、dry-run 或 loaded disabled LaunchAgents 替代终态 proof |",
            "| S2PLT02 terminal proof missing | 仅在明确授权和安全门满足后采集第二真实 M1-M4 SMTP 日与真实 scheduler proof |",
            "| S2PLT04 completion report missing | 等 S2PLT02/S2PLT03 terminal evidence 均通过后再生成 |",
            "| final bundle incomplete | 等 S2PLT04、final commands、handoff、signoff、manifest 全部通过 |",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_owner_decision_page_does_not_reopen_historical_default_next_steps_as_current_work(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")

        expected_historical_rows = (
            "历史当时默认下一步 1 是构建、独立复审并验证 S2PLT03 terminal resilience proof；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时默认下一步 2 是补齐 S2PLT04 completion report；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT02 terminal delivery proof artifact draft builder 只输出 stdout，`artifact_written=false`；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT02 scheduler proof 输入验证器只输出 no-write validation state；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT02 terminal delivery input inventory missing inputs 仍为第二真实发送日、8 封真实邮件、真实 scheduler proof 和 live terminal proof artifact；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
            "历史当时 S2PLT02 terminal capture-window audit CLI 为 blocked；当前 final bundle 已被 Stage 2 integrated acceptance 消费",
        )
        for phrase in expected_historical_rows:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, decisions)

        forbidden_phrases = (
            "| 1 | 构建、独立复审并验证 S2PLT03 terminal resilience proof |",
            "| 2 | 补齐 S2PLT04 completion report |",
            "当前仍需真实两日 delivery manifest 和真实 scheduler proof 后才能进入 live proof 复核",
            "当前仍需真实 launchd scheduler proof 后才能进入 live terminal proof 复核",
            "missing inputs 仍为第二真实发送日、8 封真实邮件、真实 scheduler proof 和 live terminal proof artifact；该清单 blocked / exit 2",
            "新增 S2PLT02 terminal capture-window audit CLI，当前仍 blocked",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, decisions)

    def test_mail_status_page_does_not_reopen_consumed_s2plt04_gaps(self) -> None:
        mail_status = (ADP_ROOT / "用户中心/邮件发送与队列状态.md").read_text(encoding="utf-8")

        self.assertIn(
            "S2PLT02 terminal proof 和 S2PLT04 completion report 已进入 final bundle 并被 Stage 2 integrated acceptance 消费",
            mail_status,
        )
        self.assertIn(
            "历史当时不发送 SMTP、不启用 scheduler；当时 S2PLT02 terminal proof 和 S2PLT04 completion report 尚未写入",
            mail_status,
        )
        self.assertNotIn(
            "当前仍不发送 SMTP、不启用 scheduler；S2PLT02 terminal proof 和 S2PLT04 completion report 仍未写入。",
            mail_status,
        )

    def test_user_center_readme_does_not_reopen_consumed_s2plt02_gaps(self) -> None:
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史 S2PLT02 terminal delivery proof 缺口已被 final bundle 和 Stage 2 integrated acceptance 消费",
            readme,
        )
        self.assertIn(
            "历史当时 `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` 仍缺失/未就绪",
            readme,
        )
        self.assertIn(
            "历史当时仍是 `1/2` 真实日、`4/8` 真实邮件",
            readme,
        )
        forbidden_phrases = (
            "- `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` 仍缺失/未就绪",
            "当前仍是 `1/2` 真实日、`4/8` 真实邮件。",
            "仍要先等真实 SMTP/scheduler 捕获窗口，清除第二真实 M1-M4 SMTP 日、8 封真实邮件、真实 scheduler proof 和 terminal proof artifact 缺口。",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, readme)

    def test_user_center_readme_does_not_reopen_superseded_daily_operation_preflight_blockers(self) -> None:
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史：gh 等价证据已修复，当时 DAILY_OPERATION 仍阻断",
            readme,
        )
        self.assertIn(
            "当时剩余失败检查是 `production_preflight_passed`；后续已由 2026-07-01 20:39 secret / artifact repair 消费",
            readme,
        )
        self.assertIn(
            "当前唯一持久运行阻断仍是 `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json` 缺失",
            readme,
        )

        forbidden_phrases = (
            "当前具体阻断：缺 `ADP_SMTP_HOST`、`ADP_SMTP_PORT`、`ADP_SMTP_USERNAME`、`ADP_SMTP_PASSWORD`",
            "既有 `OpenAIDatabase/session_history` archive 文件触发 production git artifact hygiene blocker",
            "默认下一步：补齐 SMTP secret env 名称并通过 OpenAIDatabase owning workflow 处理大文件治理；预检通过前不得请求 persistent DAILY_OPERATION 授权。",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, readme)

    def test_user_center_readme_does_not_reopen_early_final_bundle_runtime_gaps(self) -> None:
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")

        self.assertIn(
            "历史当时 `plan-final-bundle-prerequisites` 已在顶层给出下一条可执行只读命令",
            readme,
        )
        self.assertIn(
            "历史当时 `validate-final-acceptance-bundle` 在顶层直接显示 `next_executable_runtime_step=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW`",
            readme,
        )
        self.assertIn(
            "历史当时 `plan-final-bundle-prerequisites` 已把 S2PLT02 capture plan 的真实 runtime 下一步暴露到顶层",
            readme,
        )
        self.assertIn(
            "当前这些 final-bundle runtime 缺口已被 Stage 2 integrated acceptance 消费",
            readme,
        )

        forbidden_phrases = (
            "`plan-final-bundle-prerequisites` 当前已经在顶层给出下一条可执行只读命令",
            "`validate-final-acceptance-bundle` 当前在顶层直接显示 `next_executable_runtime_step=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW`",
            "这意味着最终验收入口仍 blocked：下一步仍是 S2PLT02 terminal delivery proof 的真实 SMTP/scheduler 捕获窗口",
            "`plan-final-bundle-prerequisites` 当前已经把 S2PLT02 capture plan 的真实 runtime 下一步暴露到顶层",
        )
        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, readme)

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
        self.assertIn("ADP_ALLOW_SMTP_SEND raw value is UNSET or false-like", assurance)
        self.assertNotIn(
            "persistent ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, open_pr_count=0",
            assurance,
        )
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
        self.assertIn("ADP_SMTP_SEND_RAW_VALUE_EVIDENCE", generator)
        self.assertIn("ADP_ALLOW_SMTP_SEND raw value is UNSET or false-like", generator)
        self.assertNotIn(
            "persistent ADP_ALLOW_SMTP_SEND=false, LaunchAgents disabled, open_pr_count=0, and no background ADP process",
            generator,
        )
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
        mail_status = (ADP_ROOT / "用户中心/邮件发送与队列状态.md").read_text(encoding="utf-8")
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
        self.assertIn('ADP_ALLOW_SMTP_SEND_VALUE="${ADP_ALLOW_SMTP_SEND-UNSET}"', handoff)
        self.assertIn("printf 'ADP_ALLOW_SMTP_SEND=%s\\n' \"$ADP_ALLOW_SMTP_SEND_VALUE\"", handoff)
        self.assertIn('blocked: ADP_ALLOW_SMTP_SEND is truthy', handoff)
        for label in ("com.linzezhang.adp.daily", "com.linzezhang.adp.health", "com.linzezhang.adp.watchdog"):
            self.assertIn(label, handoff)
        self.assertIn('for label in com.linzezhang.adp.daily com.linzezhang.adp.health com.linzezhang.adp.watchdog; do', handoff)
        self.assertIn('launchctl print "gui/$(id -u)/$label"', handoff)
        self.assertIn("blocked: %s is loaded", handoff)
        self.assertIn("旧 `com.linze.adp.local.*` 只属于历史记录，不得作为当前 S3 safety check", handoff)
        self.assertNotIn("launchctl print-disabled gui/$(id -u) | rg 'com\\.linze\\.adp\\.local\\.(daily|health|watchdog)'", handoff)
        self.assertIn("`ADP_ALLOW_SMTP_SEND` 原始值只能是 `UNSET` 或 false-like", handoff)
        self.assertIn("`ADP_ALLOW_SMTP_SEND` 为 `UNSET` 或 false-like", handoff)
        self.assertIn("若 `ADP_ALLOW_SMTP_SEND` 为 truthy", handoff)
        self.assertIn(
            "ps aux | rg -i 'arxiv_daily_push|arxiv-daily-push|local_runner|CodexProject.*arxiv-daily-push'",
            handoff,
        )
        self.assertIn("后台进程扫描只匹配 ADP runner/module/path 信号，不使用裸 `adp` 子串", handoff)
        self.assertNotIn("ps aux | rg -i 'arxiv_daily_push|arxiv-daily-push|local_runner|adp'", handoff)
        self.assertIn("安全边界复核主路径：先运行上方最小复核命令中的 copy-safe enablement preflight", handoff)
        self.assertNotIn("安全边界复核主路径：先运行 `python3 tools/verify_daily_operation_enablement_preflight.py`", handoff)
        self.assertIn("open PR 人工 HTML fallback 只允许作为降级审计补充", handoff)
        self.assertIn("不得替代 enablement preflight root gate", handoff)
        self.assertIn("open_pr_count=0", handoff)
        self.assertIn("User-Agent: codex-adp-open-pr-check", handoff)
        self.assertIn("https://github.com/LinzeColin/CodexProject/pulls?q=is%3Apr+is%3Aopen", handoff)
        self.assertIn("fallback_open_pr_count=%s", handoff)
        self.assertIn('test "$FALLBACK_PR_COUNT" = "0"', handoff)
        self.assertNotIn("OPEN_PR_COUNT=$(", handoff)
        self.assertNotIn('test "$OPEN_PR_COUNT" = "0"', handoff)
        self.assertIn("open PR 结果为 `UNKNOWN` / 非 0，停止并回报，不得当作通过", handoff)
        self.assertNotIn("https://api.github.com/repos/LinzeColin/CodexProject/pulls?state=open", handoff)
        self.assertIn("HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md", readme)
        self.assertIn("HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md", decisions)
        self.assertIn("open PR 边界已改为 enablement preflight 自动观察", readme)
        self.assertIn("SMTP 发送开关原始值复核", readme)
        self.assertIn("后台进程扫描停止门已同步到路线图", readme)
        self.assertIn("S3 LaunchAgent 标签停止门已同步", readme)
        self.assertIn("S3 机器预检标签已同步", readme)
        self.assertIn("root verifier 已显示 S3 阻断原因", readme)
        self.assertIn("DAILY_OPERATION 专用 root gate 已补齐", readme)
        self.assertIn("持久授权模板已补齐但默认无效", readme)
        self.assertIn("半改模板仍无效", readme)
        self.assertIn("占位时间和占位授权文本必须替换为当前 owner 明确授权证据", readme)
        self.assertIn("机器 gate 输出同样使用真实 LaunchAgent 标签", handoff)
        self.assertIn("daily_operation_authorization_ready=false", handoff)
        self.assertIn("daily_operation_blocking_reasons", handoff)
        self.assertIn("tools/verify_daily_operation_readiness.py", handoff)
        self.assertIn("daily_operation_persistent_enablement_authorization.template.json", handoff)
        self.assertIn("保留占位 `generated_at` 或 `authorization_text` 仍必须无效", handoff)
        self.assertIn("S3 机器预检标签停止门", roadmap)
        self.assertIn("root verifier S3 阻断字段", roadmap)
        self.assertIn("DAILY_OPERATION fail-closed root gate", roadmap)
        self.assertIn("持久授权模板停止门", roadmap)
        self.assertIn("半改模板", roadmap)
        self.assertIn("短 key 只允许验证历史 artifact", mvp_prep)
        self.assertIn("root verifier PASS 被误读为 S3 可启用", mvp_prep)
        self.assertIn("当前非零退出是正确阻断", mvp_prep)
        self.assertIn("持久授权模板被误当 live artifact", mvp_prep)
        self.assertIn("保留占位时间或占位授权文本", mvp_prep)
        self.assertIn("旧 `com.linze.adp.local.*` 只属于历史记录，不得作为当前 S3 safety check 或通过依据", readme)
        self.assertIn("用户中心历史 SMTP 开关口径已清理", readme)
        self.assertIn("本页历史记录不再把当前安全边界写成必须存在“持久显式 false”环境变量", readme)
        self.assertIn("历史运行条目只说明当时 `ADP_ALLOW_SMTP_SEND` 为 false-like；当前复核仍只接受 `UNSET` 或 false-like", readme)
        self.assertIn("当前治理 SMTP 原始值证据口径已同步", readme)
        self.assertIn("当前 `OWNER_STATUS`、`ASSURANCE_STATUS`、当前状态测试和治理生成器中的 SMTP 边界证据", readme)
        self.assertIn("下方 2026-07-01 历史记录只保留“当时 false-like”的运行证据或环境事实", readme)
        self.assertIn("不是当前要求必须存在一个持久显式 `false` 环境变量", readme)
        self.assertIn("`ADP_ALLOW_SMTP_SEND` 当时为 false-like，当前只接受 `UNSET` 或 false-like", readme)
        self.assertNotIn("持久 `ADP_ALLOW_SMTP_SEND=false`", readme)
        self.assertIn("邮件状态历史 SMTP 开关口径已清理", mail_status)
        self.assertIn("历史运行条目只说明当时 `ADP_ALLOW_SMTP_SEND` 为 false-like；当前复核仍只接受 `UNSET` 或 false-like", mail_status)
        self.assertIn("运行后 `ADP_ALLOW_SMTP_SEND` 当时为 false-like，当前只接受 `UNSET` 或 false-like", mail_status)
        self.assertNotIn("运行后持久 `ADP_ALLOW_SMTP_SEND=false`", mail_status)
        self.assertLess(
            readme.index("当前治理 SMTP 原始值证据口径已同步"),
            readme.index("owner A 决策 mainline 证据已绑定"),
        )
        self.assertIn("只匹配 ADP runner/module/path 信号", readme)
        self.assertIn("禁止使用裸 `adp` 子串作为进程扫描匹配项", readme)
        self.assertIn("不能把未设置的环境变量默认写成显式 `false`", readme)
        self.assertIn("当前允许的安全状态是 `UNSET` 或 false-like", readme)
        self.assertIn("`ADP_ALLOW_SMTP_SEND` 原始值只能是 `UNSET` 或 false-like", readme)
        self.assertIn("`ADP_ALLOW_SMTP_SEND` 原始值只能是 `UNSET` 或 false-like", decisions)
        self.assertIn("历史 SMTP 开关口径已清理", decisions)
        self.assertIn(
            "历史行只说明当时 `ADP_ALLOW_SMTP_SEND` 为 false-like；当前执行入口仍只接受 `UNSET` 或 false-like",
            decisions,
        )
        self.assertIn(
            "继续按原始值复核 `ADP_ALLOW_SMTP_SEND`：只接受 `UNSET` 或 false-like",
            decisions,
        )
        self.assertIn(
            "按当前入口原始值规则复核 `ADP_ALLOW_SMTP_SEND`：只接受 `UNSET` 或 false-like",
            decisions,
        )
        self.assertIn(
            "在受控窗口按授权切换 `ADP_ALLOW_SMTP_SEND`，并在收口后回到 `UNSET` 或 false-like",
            decisions,
        )
        self.assertIn(
            "也不得把这类历史 false-like 状态回写成当前 Stage 2 结论",
            decisions,
        )
        self.assertNotIn("继续保持持久 `ADP_ALLOW_SMTP_SEND=false`", decisions)
        self.assertNotIn("保持 `ADP_ALLOW_SMTP_SEND=false`，三个 ADP LaunchAgent disabled", decisions)
        self.assertNotIn("当时保持 `ADP_ALLOW_SMTP_SEND=false`", decisions)
        self.assertNotIn("当时维持 `ADP_ALLOW_SMTP_SEND=false`", decisions)
        self.assertNotIn("先清除 `ADP_ALLOW_SMTP_SEND=false`", decisions)
        self.assertIn("只有明确得到 `open_pr_count=0` 才能通过", readme)
        self.assertIn("`UNKNOWN`、非 0、命令失败或无法解析都必须停止并回报", readme)
        self.assertIn("open PR 自动观察停止门", roadmap)
        self.assertIn("GitHub API 自动观察", roadmap)
        self.assertIn("HTML fallback 只允许作为降级审计补充", roadmap)
        self.assertIn("SMTP 发送开关原始值停止门", roadmap)
        self.assertIn("后台进程扫描停止门", roadmap)
        self.assertIn("LaunchAgent 标签停止门", roadmap)
        for label in ("com.linzezhang.adp.daily", "com.linzezhang.adp.health", "com.linzezhang.adp.watchdog"):
            self.assertIn(label, roadmap)
            self.assertIn(label, mvp_prep)
        self.assertIn("S3/MVP 安全边界复核必须检查后台进程，但只能匹配 ADP runner/module/path 信号", roadmap)
        self.assertIn("旧 `com.linze.adp.local.*` 只属于历史运行记录，不得作为当前 S3 safety check 或通过依据", roadmap)
        self.assertIn("不得使用裸 `adp` 子串作为进程扫描匹配项", roadmap)
        self.assertIn("命中真实 `arxiv_daily_push`、`arxiv-daily-push`、`local_runner` 或 `CodexProject.*arxiv-daily-push` 运行进程时必须停止并回报", roadmap)
        self.assertIn("S3/MVP 安全边界复核必须显示 `ADP_ALLOW_SMTP_SEND` 原始值", roadmap)
        self.assertIn("只接受 `UNSET` 或 false-like", roadmap)
        self.assertIn("`1`、`true`、`yes`、`on` 等 truthy 必须停止并回报", roadmap)
        self.assertIn("只接受明确 `open_pr_count=0`", roadmap)
        self.assertIn("`UNKNOWN`、非 0、命令失败或无法解析都必须停止并回报，不得当作通过", roadmap)
        self.assertIn("该复核只证明 open PR 边界，不授权 S3/DAILY_OPERATION", roadmap)
        self.assertRegex(
            one_look,
            r"^# 一看三查\n\n更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney\n",
        )
        self.assertEqual(one_look.count("更新时间："), 1)
        self.assertRegex(
            roadmap,
            r"^# 路线图与停止门\n\n更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney\n\n本页说明 ADP 当前在哪个阶段",
        )
        self.assertEqual(roadmap.count("更新时间："), 1)
        self.assertTrue(mvp_prep.startswith("# MVP 准备与复审修补\n"))
        self.assertIn("不进入 S3/DAILY_OPERATION", mvp_prep)
        self.assertIn("只做复审、修补、用户向可读性、证据同步、测试补强和低风险局部修复", mvp_prep)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json", mvp_prep)
        self.assertIn("daily_operation_enabled=false", mvp_prep)
        self.assertIn("`ADP_ALLOW_SMTP_SEND` 为 `UNSET` 或 false-like", mvp_prep)
        self.assertIn("旧 `com.linze.adp.local.*` 不得作为当前通过依据", mvp_prep)
        self.assertIn("后台进程扫描只匹配 ADP runner/module/path，不使用裸 `adp` 子串", mvp_prep)
        self.assertIn("GitHub `origin/main` 的干净隔离工作树", mvp_prep)
        self.assertIn("本机脏工作树、detached HEAD 或临时 worktree 结果不能单独当作交付基线", mvp_prep)
        self.assertIn(
            '默认通过 `python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2` 自动观察 GitHub open PR count',
            mvp_prep,
        )
        self.assertIn("open_pr_observation_mode=auto_observed", mvp_prep)
        self.assertIn("open PR 由 enablement preflight 自动观察为 0", mvp_prep)
        self.assertIn("## 09 推荐下一轮 Run Contract 模板", mvp_prep)
        self.assertNotIn("## 09 推荐第一轮 Run Contract", mvp_prep)
        self.assertIn(
            '目标测试、project governance、governance sync、`python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1`、`python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2`',
            mvp_prep,
        )
        self.assertNotIn("`verify_acceptance_bundle --require-zero P0 P1`", mvp_prep)
        self.assertIn("MVP 准备与复审修补](./MVP准备与复审修补.md)", readme)
        self.assertRegex(
            readme,
            r"^# ADP 用户中心\n\n更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney\n\n这里是 ADP 在 GitHub 上的唯一中文用户入口",
        )
        self.assertEqual(readme.count("更新时间："), 1)
        self.assertLess(readme.index("## 总览"), readme.index("## 最近治理与历史记录"))
        self.assertLess(readme.index("## 一看三查"), readme.index("## 最近治理与历史记录"))
        self.assertIn("MVP Run Contract README 入口同步", readme)
        self.assertIn("看后续复审修补的范围、停止条件、验收标准和下一轮 Run Contract 模板", readme)
        self.assertNotIn("看后续复审修补的范围、停止条件、验收标准和第一轮 Run Contract", readme)
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

    def test_daily_operation_enablement_preflight_root_gate_is_owner_readable(self) -> None:
        handoff = (REPO_ROOT / "HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md").read_text(encoding="utf-8")
        readme = (ADP_ROOT / "用户中心/README.md").read_text(encoding="utf-8")
        one_look = (ADP_ROOT / "用户中心/一看三查.md").read_text(encoding="utf-8")
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        mvp_prep = (ADP_ROOT / "用户中心/MVP准备与复审修补.md").read_text(encoding="utf-8")
        final_bundle_status = (ADP_ROOT / "用户中心/最终验收包与S3阻断.md").read_text(encoding="utf-8")
        feature_list = (ADP_ROOT / "功能清单.md").read_text(encoding="utf-8")
        dev_record = (ADP_ROOT / "开发记录.md").read_text(encoding="utf-8")
        model_params = (ADP_ROOT / "模型参数文件.md").read_text(encoding="utf-8")
        root_tool = "tools/verify_daily_operation_enablement_preflight.py"
        expected_task = "S2PMT07-DAILY-OPERATION-ENABLEMENT-PREFLIGHT"

        self.assertTrue((REPO_ROOT / root_tool).exists(), "enablement preflight root tool must exist")
        for text in (handoff, mvp_prep, feature_list, dev_record, model_params):
            self.assertIn(root_tool, text)
            self.assertIn(expected_task, text)
            self.assertIn("persistent_daily_operation_authorization_missing", text)
        self.assertIn("status=FAIL / exit 2", handoff)
        self.assertIn(
            "以下命令必须从 CodexProject 仓库根目录运行；`tools/`、`scripts/` 和 `FINAL_ACCEPTANCE_BUNDLE/` 均为仓库根路径",
            handoff,
        )
        self.assertIn("不要给这些 root tools 追加 `--json`", handoff)
        self.assertIn("python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1", handoff)
        self.assertIn(
            'python3 -B tools/verify_daily_operation_readiness.py --root .; ec=$?; echo "EXPECTED_READINESS_EXIT=$ec"; test "$ec" -eq 2',
            handoff,
        )
        self.assertIn(
            'python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2',
            handoff,
        )
        self.assertNotIn(
            "python3 tools/verify_daily_operation_readiness.py\npython3 tools/verify_daily_operation_enablement_preflight.py",
            handoff,
        )
        self.assertNotIn("tools/verify_acceptance_bundle.py --root . --require-zero P0 P1 --json", handoff)
        self.assertNotIn("tools/verify_daily_operation_readiness.py --root . --json", handoff)
        self.assertNotIn("tools/verify_daily_operation_enablement_preflight.py --root . --json", handoff)
        self.assertIn("open_pr_observation_mode=auto_observed", handoff)
        self.assertNotIn("--open-pr-count 0", handoff)
        self.assertNotIn("--adp-allow-smtp-send UNSET", handoff)
        self.assertIn("adp_allow_smtp_send_environment_raw", handoff)
        self.assertIn("runtime_observation_mode=auto_observed", handoff)
        self.assertNotIn("--launchagent-daily-disabled true", handoff)
        self.assertNotIn("--background-adp-process-count 0", handoff)
        self.assertIn("readiness + open PR + SMTP flag + LaunchAgent + background process", mvp_prep)
        self.assertIn("默认自动观察 open PR count、ADP_ALLOW_SMTP_SEND 环境值、LaunchAgent 和后台进程", mvp_prep)
        self.assertIn("enablement_preflight_ready=false", model_params)
        self.assertIn("runtime_observation_mode=auto_observed", model_params)
        self.assertIn("open_pr_observation_mode=auto_observed", model_params)
        self.assertIn("adp_allow_smtp_send_environment_raw", model_params)
        self.assertIn("open_pr_observation_errors", mvp_prep)
        self.assertIn("runtime_observation_errors", mvp_prep)
        self.assertIn("具体错误", mvp_prep)
        self.assertIn("## 10 下一轮最小验证命令", mvp_prep)
        self.assertIn("以下命令必须从 CodexProject 仓库根目录运行", mvp_prep)
        self.assertIn("不要给这些 root tools 追加 `--json`", mvp_prep)
        acceptance_bundle_command = "python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1"
        readiness_command = (
            'python3 -B tools/verify_daily_operation_readiness.py --root .; ec=$?; '
            'echo "EXPECTED_READINESS_EXIT=$ec"; test "$ec" -eq 2'
        )
        preflight_command = (
            'python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; '
            'echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2'
        )
        self.assertIn(acceptance_bundle_command, mvp_prep)
        self.assertIn(
            readiness_command,
            mvp_prep,
        )
        self.assertIn(
            preflight_command,
            mvp_prep,
        )
        self.assertNotIn("tools/verify_acceptance_bundle.py --root . --require-zero P0 P1 --json", mvp_prep)
        self.assertNotIn("tools/verify_daily_operation_readiness.py --root . --json", mvp_prep)
        self.assertNotIn("tools/verify_daily_operation_enablement_preflight.py --root . --json", mvp_prep)
        for line_label, required_command in (
            ("Enablement preflight", preflight_command),
            ("Root 执行根", readiness_command),
            ("Root 执行根", preflight_command),
            ("生产边界", preflight_command),
            ("S3 readiness", readiness_command),
            ("S3 enablement preflight", preflight_command),
        ):
            matching_rows = [line for line in mvp_prep.splitlines() if line.startswith(f"| {line_label} |")]
            self.assertTrue(matching_rows, f"missing MVP row for {line_label}")
            self.assertTrue(
                any(f"`{required_command}`" in row for row in matching_rows),
                f"MVP row {line_label} must expose copy-safe command {required_command}",
            )
        self.assertNotIn("| `tools/verify_daily_operation_readiness.py` |", mvp_prep)
        self.assertNotIn("| `tools/verify_daily_operation_enablement_preflight.py` |", mvp_prep)
        self.assertNotIn(
            "| `tools/verify_daily_operation_readiness.py` / `tools/verify_daily_operation_enablement_preflight.py` |",
            mvp_prep,
        )
        self.assertNotIn("S3 handoff 安全边界复核", mvp_prep)
        self.assertNotIn("、生产边界复核；", mvp_prep)
        self.assertIn(f"、`{preflight_command}`；", mvp_prep)
        self.assertIn(f"| 覆盖命令 | `{readiness_command}` / `{preflight_command}` |", roadmap)
        self.assertIn(f"| 覆盖命令 | `{readiness_command}` |", roadmap)
        self.assertIn(f"| 覆盖命令 | `{preflight_command}` |", roadmap)
        self.assertNotIn("| 覆盖命令 | `tools/verify_daily_operation_readiness.py`", roadmap)
        self.assertNotIn("| 覆盖命令 | `tools/verify_daily_operation_enablement_preflight.py`", roadmap)
        self.assertIn(f"| S3 root 执行根 | 正确 root 必须显示 `repo_root_valid=true`", one_look)
        self.assertIn(f"`{readiness_command}` / `{preflight_command}`", one_look)
        self.assertIn(f"| Root 执行根 | 正确 CodexProject 仓库根必须", final_bundle_status)
        self.assertIn(f"`{readiness_command}` / `{preflight_command}`", final_bundle_status)
        self.assertIn(f"| Root 执行根校验 | 正确 CodexProject 仓库根必须输出", handoff)
        self.assertIn(f"`{readiness_command}` / `{preflight_command}`", handoff)
        for owner_copy_guidance_text in (readme, one_look, final_bundle_status, handoff):
            self.assertNotIn(
                "复制 `tools/verify_daily_operation_readiness.py` 或 `tools/verify_daily_operation_enablement_preflight.py`",
                owner_copy_guidance_text,
            )
            self.assertNotIn(
                "| `tools/verify_daily_operation_readiness.py` / `tools/verify_daily_operation_enablement_preflight.py` |",
                owner_copy_guidance_text,
            )
        for current_guidance_text in (handoff, mvp_prep, decisions, roadmap):
            self.assertIn(
                acceptance_bundle_command,
                current_guidance_text,
            )
            self.assertNotIn("`tools/verify_acceptance_bundle.py --require-zero P0 P1`", current_guidance_text)
        self.assertIn("open_pr_observation_errors_promoted_to_blocking_reasons=true", model_params)
        self.assertIn("runtime_observation_errors_promoted_to_blocking_reasons=true", model_params)
        for command_owner_text in (readme, final_bundle_status):
            self.assertIn("不要给这些 root tools 追加 `--json`", command_owner_text)
            self.assertIn("python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1", command_owner_text)
            self.assertIn(
                'python3 -B tools/verify_daily_operation_readiness.py --root .; ec=$?; echo "EXPECTED_READINESS_EXIT=$ec"; test "$ec" -eq 2',
                command_owner_text,
            )
            self.assertIn(
                'python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2',
                command_owner_text,
            )
            self.assertNotIn("tools/verify_acceptance_bundle.py --root . --require-zero P0 P1 --json", command_owner_text)
            self.assertNotIn("tools/verify_daily_operation_readiness.py --root . --json", command_owner_text)
            self.assertNotIn("tools/verify_daily_operation_enablement_preflight.py --root . --json", command_owner_text)
        for owner_text in (handoff, final_bundle_status, readme, one_look, decisions, roadmap):
            self.assertIn("repo_root_valid=true", owner_text)
            self.assertIn("root_validation_errors=[]", owner_text)
            self.assertIn("required_paths_missing=[]", owner_text)
            self.assertIn("codexproject_repo_root_invalid", owner_text)


if __name__ == "__main__":
    unittest.main()
