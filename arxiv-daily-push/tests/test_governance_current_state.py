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

    def test_current_state_summary_describes_s2plt02_controlled_launchd_timeout_and_blockers(self) -> None:
        ledger = (ADP_ROOT / "docs/governance/DEVELOPMENT_LEDGER.md").read_text(encoding="utf-8")
        current_state = ledger.split("\n### `", 1)[0]

        self.assertIn(
            "S2PLT02_REAL_SCHEDULER_PROOF_CAPTURE_PASS_BLOCKED_TERMINAL_ARTIFACT",
            current_state,
        )
        self.assertIn("S2PLT02-REAL-SCHEDULER-PROOF-CAPTURE-PASS", current_state)
        self.assertIn("real_scheduler_proven=true", current_state)
        self.assertIn("scheduler_evidence_present=true", current_state)
        self.assertIn("scheduler_proof_ready=true", current_state)
        self.assertIn("real_smtp_sent_by_scheduler_proof_run=false", current_state)
        self.assertIn("production_evidence_ready_by_scheduler_proof_run=false", current_state)
        self.assertIn("live_arxiv_fetch_attempted_by_scheduler_proof_run=false", current_state)
        self.assertIn("020904b1b96c87cccdec3a64c77607373789ee0dbd275bf015f0cd5a79b22811", current_state)
        self.assertIn("62f065d518d31c67d38a3c004ce48f9acc5f7e97867387eb5584dbf84c07aa21", current_state)
        self.assertIn("ADP-S2PLT02-REAL-SCHEDULER-PROOF-20260701.json", current_state)
        self.assertIn("ADP-S2PLT02-REAL-SCHEDULER-PROOF-VALIDATION-20260701.json", current_state)
        self.assertIn("ADP-S2PLT02-REAL-SCHEDULER-PROOF-CAPTURE-PASS-20260701.json", current_state)
        self.assertIn("PHASE_S2PLT02_REAL_SCHEDULER_PROOF_CAPTURE_PASS.md", ledger)
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_READY_NO_PRODUCTION_ACCEPTANCE", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", current_state)
        self.assertIn("artifact_validation_state_hash=fa02f1ea5f652b90c84381f97538edf25c8fdd3574fc1eb6ed00e3b09f75d756", current_state)
        self.assertIn("acceptance_hash=2c784298d2b3a42792d400f590afe3688da91f0f2c4c519c4f8890a81c06c2ef", current_state)
        self.assertIn("next executable task is `S2PLT03_TERMINAL_RESILIENCE_PROOF`", current_state)
        self.assertIn("Previous controlled launchd timeout remains visible", current_state)

        self.assertIn(
            "S2PLT02_CONTROLLED_LAUNCHD_KICKSTART_TIMEOUT_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PLT02-CONTROLLED-LAUNCHD-KICKSTART-TIMEOUT", current_state)
        self.assertIn("kickstart` returned `0`", current_state)
        self.assertIn("did not exit within the bounded 180 second window", current_state)
        self.assertIn("counts_toward_s2plt02_terminal_proof=false", current_state)
        self.assertIn("final ADP process count is `0`", current_state)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", current_state)
        self.assertIn("launchagents_disabled_not_terminal_scheduler_proof", current_state)
        self.assertIn("scheduler_run_manifest_missing", current_state)
        self.assertIn("86c26aed6038f185f993fc7e7bb3f3eb5a849fd9d6438a2fb6bcf2ddedcbdaa9", current_state)
        self.assertIn(
            "ADP-S2PLT02-CONTROLLED-LAUNCHD-KICKSTART-TIMEOUT-20260701.json",
            current_state,
        )
        self.assertIn("PHASE_S2PLT02_CONTROLLED_LAUNCHD_KICKSTART_TIMEOUT.md", ledger)
        self.assertIn("No SMTP was sent", current_state)
        self.assertIn("no terminal proof artifact was written", current_state)
        self.assertIn("no Stage2/S3/integrated production acceptance is claimed", current_state)
        self.assertIn("Previous canonical checkout alignment remains visible", current_state)
        self.assertIn("S2PLT02-CANONICAL-LAUNCHAGENT-CHECKOUT-ALIGNMENT", current_state)
        self.assertIn("root/project/current-main checks all `true`", current_state)
        self.assertIn("1ce7c3dc8bf1a20c6aed90182a4c43f056f4f01b504c159781c15c0afbc332df", current_state)
        self.assertIn("Previous LaunchAgent root/current-main guard remains visible", current_state)
        self.assertIn("S2PLT02-LAUNCHAGENT-ROOT-CURRENT-MAIN-GUARD", current_state)
        self.assertIn("89b033448ce4ef8de096f847658c0a0beb3b02f5115965b10b30c3f5661ae878", current_state)
        self.assertIn("Previous controlled real 20260701 run remains visible", current_state)
        self.assertIn("S2PLT02-CONTROLLED-REAL-RUN-20260701-SCHEDULER-ONLY-BLOCKER-SYNC", current_state)
        self.assertIn("real_smtp_sent=true", current_state)
        self.assertIn("sent_mail_count=4", current_state)
        self.assertIn("observed_real_delivery_days=2/2", current_state)
        self.assertIn("observed_real_email_count=8/8", current_state)
        self.assertIn("REAL_SCHEDULER_PROOF", current_state)
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", current_state)
        self.assertIn("Previous terminal scheduler blocker sync remains visible", current_state)
        self.assertIn("S2PLT02-TERMINAL-SCHEDULER-BLOCKER-SYNC", current_state)
        self.assertIn("Previous controlled real second-day capture remains visible", current_state)
        self.assertIn("S2PLT02-CONTROLLED-REAL-SECOND-DAY-CAPTURE", current_state)

        self.assertIn(
            "S2PLT02_TERMINAL_CAPTURE_READONLY_COMMAND_EXECUTABILITY_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-READONLY-COMMAND-EXECUTABILITY-SYNC", current_state)
        self.assertIn("allowed_readonly_commands", current_state)
        self.assertIn(
            "adp audit-s2plt02-terminal-proof-evidence-inventory --repo-root . --generated-at 2026-07-01T05:42:34+10:00 --json",
            current_state,
        )
        self.assertIn("aafb8d5147d8c7849a2489bfb4991376e978d646b5e149156cbba58ae513aff1", current_state)
        self.assertIn("502a892c3a207233c0d9ea985685c5064e2aaa279ca9010a490b30190aefecfe", current_state)
        self.assertIn("30235e5dd5cd5afabda6de1fdedbfeab5faeb93f61dd076f46a41b2a56bb25a1", current_state)
        self.assertIn("26207ef1ba63b2fe56d7904e141cf20dbd49268d98407a45a73dbf2fcfd0ed4c", current_state)
        self.assertIn("94fbe44f8211dff645ad5939696843122191b5b10ed939a1e04105c5e312c6b9", current_state)
        self.assertIn("bb901dfd9fdb65683c0d76ca413ba1d9df853169bc63e7c9d37ef1ebc343a723", current_state)
        self.assertIn("a6f7e782a8e62a223087ee08ffebbf444c46909ef096e878849af079400abc47", current_state)
        self.assertIn("6ae337c9dd434e0f43909cf2ddc13f3d0de3a1bb5beb919ac2323ee61b8ef48f", current_state)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-CAPTURE-READONLY-COMMAND-EXECUTABILITY-SYNC-20260701.json",
            current_state,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_READONLY_COMMAND_EXECUTABILITY_SYNC.md", ledger)
        self.assertIn("Previous inventory summary sync remains visible", current_state)
        self.assertIn(
            "S2PLT02_TERMINAL_CAPTURE_INVENTORY_SUMMARY_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-INVENTORY-SUMMARY-SYNC", current_state)
        self.assertIn("terminal_delivery_input_inventory_summary", current_state)
        self.assertIn("terminal_delivery_artifact_validation_summary", current_state)
        self.assertIn("cba2fb5be5cc1a7dc098b28fe0b0bd137fb43d18e4f077d755571313bcee03e4", current_state)
        self.assertIn("4df922bd5dc56541cbd76380adc6897fb779c929afa1c37e7f1d2eab236e8e5b", current_state)
        self.assertIn("3fbde96111dd78d3ffe4474e012fa5d86de76a24e6fa7640d0310c178003e1db", current_state)
        self.assertIn("323015614b4a846a44ecd12e1a3f698237ff0987085f46f8d9cc2f098ddabb52", current_state)
        self.assertIn("3285063a1708b45cc881f1868d91282293b89bdb8cc9b3a2a2d87d07d5dd439b", current_state)
        self.assertIn("bcb40505ad7244626589c24991dcf05fe775268ce44b5eab3b68444f38cded6e", current_state)
        self.assertIn("23c5a2f6beed34c440ee8f3de870ca71a2c2deb1d44cbd67623a3c7aa7fc510c", current_state)
        self.assertIn("SECOND_REAL_DELIVERY_DAY;EIGHT_REAL_EMAILS;REAL_SCHEDULER_PROOF;S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", current_state)
        self.assertIn("write_terminal_artifact_allowed=false", current_state)
        self.assertIn("scheduler_enable_allowed_by_this_plan=false", current_state)
        self.assertIn("production_acceptance_allowed=false", current_state)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-CAPTURE-INVENTORY-SUMMARY-SYNC-20260701.json",
            current_state,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_INVENTORY_SUMMARY_SYNC.md", ledger)
        self.assertIn("Previous zero-proof request consumption sync remains visible", current_state)
        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_ZERO_PROOF_REQUEST_CONSUMPTION_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-ZERO-PROOF-REQUEST-CONSUMPTION-SYNC", current_state)
        self.assertIn("zero_proof_artifact_validation_state_hash=bf966c244f9f7c52b75ae7d56ff8f8c0fbda498cd678f4003ee3ed2c40961786", current_state)
        self.assertIn("assignment_request_state_hash=8a4596dbb16f55932e36b256fc22852e1f8ca52da22bdd85d6d1c79d23b61c1b", current_state)
        self.assertIn("closure_decision_request_state_hash=afc1155fafad8c460db5e09eb9890e7408a1e28dd0bf155121bf1a0308529e34", current_state)
        self.assertIn("bf966c244f9f7c52b75ae7d56ff8f8c0fbda498cd678f4003ee3ed2c40961786", current_state)
        self.assertIn("8a4596dbb16f55932e36b256fc22852e1f8ca52da22bdd85d6d1c79d23b61c1b", current_state)
        self.assertIn("afc1155fafad8c460db5e09eb9890e7408a1e28dd0bf155121bf1a0308529e34", current_state)
        self.assertIn("cf9a46ccbdfd35b01bd579511ed7ae1cdfcac411e00d8f610c80625f596e1094", current_state)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-ZERO-PROOF-REQUEST-CONSUMPTION-SYNC-20260701.json",
            current_state,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_ZERO_PROOF_REQUEST_CONSUMPTION_SYNC.md", ledger)
        self.assertIn("Previous reviewer assignment consumption sync remains visible", current_state)
        self.assertIn("S2PMT07-FINAL-BUNDLE-REVIEWER-ASSIGNMENT-CONSUMPTION-SYNC", current_state)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_LIVE_WRITE_READY_TOP_LEVEL_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-LIVE-WRITE-READY-TOP-LEVEL-SYNC", current_state)
        self.assertIn("ready_to_write_live_artifacts=false", current_state)
        self.assertIn("current_wait_state=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", current_state)
        self.assertIn("c9216c53cedf0cb5fcc12fd15ffb021b83586906f233a4f78ed96ecfe84f9b13", current_state)
        self.assertIn("256aa1a8dfeff4f598fa9fbb172aae3f6e7cde428bde570424a2bc779da7e320", current_state)
        self.assertIn("494538d0e454c51869eca559808316740a422f92b7deeb070d348f65e1277d67", current_state)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-LIVE-WRITE-READY-TOP-LEVEL-SYNC-20260701.json",
            current_state,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_LIVE_WRITE_READY_TOP_LEVEL_SYNC.md", ledger)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_TOP_LEVEL_WAIT_STATE_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-TOP-LEVEL-WAIT-STATE-SYNC", current_state)
        self.assertIn("current_wait_state=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", current_state)
        self.assertIn("c9216c53cedf0cb5fcc12fd15ffb021b83586906f233a4f78ed96ecfe84f9b13", current_state)
        self.assertIn("2ee61c653d48b74f03505221adf6e37039d9cd4339b5554ba145dd02f9ec6198", current_state)
        self.assertIn("3ba4d2fdcc2ea9bfc268f7f579ce8e8e4e3458ee6c69400e157571906ba16b29", current_state)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-TOP-LEVEL-WAIT-STATE-SYNC-20260701.json",
            current_state,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_TOP_LEVEL_WAIT_STATE_SYNC.md", ledger)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_S2PLT02_CURRENT_WAIT_STATE_SUMMARY_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-CURRENT-WAIT-STATE-SUMMARY", current_state)
        self.assertIn("current_wait_state=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", current_state)
        self.assertIn("c9216c53cedf0cb5fcc12fd15ffb021b83586906f233a4f78ed96ecfe84f9b13", current_state)
        self.assertIn("0b6753d007633aaeca00368eb29ebe54cc677846085051988a60854713c93b42", current_state)
        self.assertIn("4f1e0e311ea68a5cc320e1c0a5d11985b2a256acbeb06217a57e86d6fa217d65", current_state)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-CURRENT-WAIT-STATE-SUMMARY-20260701.json",
            current_state,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_CURRENT_WAIT_STATE_SUMMARY.md", ledger)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_PREREQUISITE_MISSING_INVENTORY_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-READONLY-COMMAND-CONTRACT", current_state)
        self.assertIn("capture_wait_state_guard", current_state)
        self.assertIn("5b344929d8d00c9cf881accbbd9abd68963b5f40cbd975a805fa4da62a8a8a25", current_state)
        self.assertIn("581fe9f53d82db88959196f874d312e50b1739a839158f7bf2d38cc186c03506", current_state)
        self.assertIn("8409313fd39c4627122aca97cc80d28480f65b5230f6982ae7e720b6e0134b73", current_state)
        self.assertIn("eef4f33e08feb99de67c24c9339ae204658f6b0ac4d0e5cd810092b5a3246aff", current_state)
        self.assertIn(
            "adp plan-s2plt02-terminal-delivery-proof-capture --repo-root . --generated-at 2026-06-30T18:03:24+10:00 --json",
            current_state,
        )
        self.assertIn("ADP-S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-READONLY-COMMAND-CONTRACT-20260701.json", current_state)
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_WAIT_STATE_READONLY_COMMAND_CONTRACT.md", ledger)
        self.assertIn("ADP-S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-GUARD-20260701.json", current_state)
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_WAIT_STATE_GUARD.md", ledger)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_PREREQUISITE_MISSING_INVENTORY_SYNC_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-PREREQUISITE-MISSING-INVENTORY-SYNC", current_state)
        self.assertIn("final_bundle_missing_artifact_inventory", current_state)
        self.assertIn("447072118012325d6b8740d76f37b1838ec788e09e591fbe451fe3a61b0f8d04", current_state)
        self.assertIn("45669a5d11c178dc6f2eaf23c806fabc420c2e20b2bf4f6b0fbd4f79504d1048", current_state)
        self.assertIn("51d89042f47937b6ef65862d30dff1d8398caf21f5d8f875709ac6e6ff255cf0", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-PREREQUISITE-MISSING-INVENTORY-SYNC-20260701.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_PREREQUISITE_MISSING_INVENTORY_SYNC.md", ledger)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_MISSING_ARTIFACT_INVENTORY_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-MISSING-ARTIFACT-INVENTORY", current_state)
        self.assertIn("final_bundle_missing_artifact_inventory", current_state)
        self.assertIn("missing_item_count=5", current_state)
        self.assertIn("2e80e00465c90d27c821981c2f2a7190050ea7c3e390a38a526ff6d7bbb539ae", current_state)
        self.assertIn("51d89042f47937b6ef65862d30dff1d8398caf21f5d8f875709ac6e6ff255cf0", current_state)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-MISSING-ARTIFACT-INVENTORY-20260701.json",
            current_state,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_MISSING_ARTIFACT_INVENTORY.md", ledger)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_LIVE_ARTIFACT_WRITE_GUARD_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-LIVE-ARTIFACT-WRITE-GUARD", current_state)
        self.assertIn("live_artifact_write_guard", current_state)
        self.assertIn("9454e47e36d6cc04e20918f50d8f7d6be6e5c12fadfc4a6f5f86144562199eb9", current_state)
        self.assertIn("1146133f14fe04dba14e0313409fad828bfe2d6439adefc68a640d5500568b85", current_state)
        self.assertIn("HANDOFF/00_下一Agent先读.md", current_state)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/manifest.json", current_state)
        self.assertIn("write_live_next_agent_handoff", current_state)
        self.assertIn("write_final_acceptance_bundle_manifest", current_state)
        self.assertIn("claim_stage2_or_s3_production_acceptance", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-LIVE-ARTIFACT-WRITE-GUARD-20260701.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_LIVE_ARTIFACT_WRITE_GUARD.md", ledger)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_S2PLT02_TERMINAL_COUNT_SPLIT_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-TERMINAL-COUNT-SPLIT", current_state)
        self.assertIn("S2PLT02 terminal count split", current_state)
        self.assertIn("fb04c0b2582c24bdecf9d6d33658f25139ab8cf656cd6e22c69f01e5a3e1c419", current_state)
        self.assertIn("7527930ba22a849c42ff55a0e65ea3c4b242e6c629f51db671468b63a1925a2b", current_state)
        self.assertIn("e7c9834eca19f665f1b57566f47cbd03ecaaf95fa9eb538187af3c3f7e1aa7f1", current_state)
        self.assertIn("e2471c2bdba40251132ae5d4374a5642db547f0fa82af54b4641b67a6f21b74c", current_state)
        self.assertIn("ab1ef6efbca6e019569e65849cd66dbb4cca336fca4bd95314252603db65a151", current_state)
        self.assertIn("observed_real_counts_source=terminal_delivery_input_inventory_existing_real_smtp_evidence", current_state)
        self.assertIn("observed_real_delivery_days=1", current_state)
        self.assertIn("observed_real_email_count=4", current_state)
        self.assertIn("current_capture_window_real_delivery_days_added=0", current_state)
        self.assertIn("current_capture_window_real_email_count_added=0", current_state)
        self.assertIn("current_capture_window_dry_run_email_count_rejected=8", current_state)
        self.assertIn("terminal_proof_real_delivery_days_after_current_capture_window=1", current_state)
        self.assertIn("terminal_proof_real_email_count_after_current_capture_window=4", current_state)
        self.assertIn("remaining_real_delivery_days_for_terminal_proof=1", current_state)
        self.assertIn("remaining_real_email_count_for_terminal_proof=4", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-TERMINAL-COUNT-SPLIT-20260701.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_TERMINAL_COUNT_SPLIT.md", ledger)

        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_S2PLT02_CAPTURE_WINDOW_SUMMARY_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-WINDOW-SUMMARY", current_state)
        self.assertIn("terminal_capture_window_audit_summary", current_state)
        self.assertIn("9f564e7fab8d69c12102143f2aed4a015b5ecff5eb8b9862f3ebc9d37f909144", current_state)
        self.assertIn("1ab9fa8e6fc25ea35fb5405a26917bbf2d5993b1911704b2d3acb654fdb5c5c5", current_state)
        self.assertIn("e2471c2bdba40251132ae5d4374a5642db547f0fa82af54b4641b67a6f21b74c", current_state)
        self.assertIn("ab1ef6efbca6e019569e65849cd66dbb4cca336fca4bd95314252603db65a151", current_state)
        self.assertIn("dry_run_service_dates=2026-06-29;2026-06-30", current_state)
        self.assertIn("nonterminal_succeeded_dry_run_service_dates=2026-06-29;2026-06-30", current_state)
        self.assertIn("dry_run_email_count=8", current_state)
        self.assertIn("real_sent_candidate_email_count=0", current_state)
        self.assertIn("observed_terminal_email_count_credit=4", current_state)
        self.assertIn("terminal_delivery_credit=false", current_state)
        self.assertIn("counts_toward_s2plt02_terminal_proof=false", current_state)
        self.assertIn("scheduler_runtime_evidence_status=launchagent_runtime_state_unknown", current_state)
        self.assertIn("capture_window_cli_scheduler_runtime_evidence_status=launchagents_loaded_but_disabled_not_terminal_scheduler_proof", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-WINDOW-SUMMARY-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_CAPTURE_WINDOW_SUMMARY.md", ledger)
        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_S2PLT04_COMPLETION_EVIDENCE_SUMMARY_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT04-COMPLETION-EVIDENCE-SUMMARY", current_state)
        self.assertIn("s2plt04_completion_evidence_audit_summary", current_state)
        self.assertIn("b9d7ce5a9011f44fa66250d174da9731238f1914a008ba5d61e81c85192eb8a4", current_state)
        self.assertIn("5e0d1a81d1f8f8de49721844d8b96f376a74a11ee69170e30685c915032ed8e2", current_state)
        self.assertIn("ee3917fedcd96e10a23fbd228367e6837ffca092734d98288502d9702514165f", current_state)
        self.assertIn("s2plt04_completion_report_written=false", current_state)
        self.assertIn("completion_report_ready=false", current_state)
        self.assertIn("s2plt02_live_2d_terminal_proof_missing;s2plt03_resilience_terminal_proof_missing", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-S2PLT04-COMPLETION-EVIDENCE-SUMMARY-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT04_COMPLETION_EVIDENCE_SUMMARY.md", ledger)
        self.assertIn(
            "S2PMT07_FINAL_BUNDLE_P0P1_ZERO_PROOF_STATUS_SUMMARY_BLOCKED_NO_PRODUCTION",
            current_state,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-P0P1-ZERO-PROOF-STATUS-SUMMARY", current_state)
        self.assertIn("p0_p1_zero_proof_status_summary", current_state)
        self.assertIn("6036321e310edadb57834353b45c08a632100caab1f61dfd00fa7c108a57b05f", current_state)
        self.assertIn("b0fc0aefd87ee9ed3c412024d534ec23a6fdf5d32316b6089fee769a3d24d758", current_state)
        self.assertIn("bf966c244f9f7c52b75ae7d56ff8f8c0fbda498cd678f4003ee3ed2c40961786", current_state)
        self.assertIn("current_zero_proof_counts=P0=0;P1=0", current_state)
        self.assertIn("inherited_v7_1_baseline_counts=P0=8;P1=37", current_state)
        self.assertIn("baseline_counts_mutated=false", current_state)
        self.assertIn("production_acceptance_claimed=false", current_state)
        self.assertIn("integrated_production_accepted=false", current_state)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-P0P1-ZERO-PROOF-STATUS-SUMMARY-20260630.json", current_state)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_P0P1_ZERO_PROOF_STATUS_SUMMARY.md", ledger)
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

    def test_owner_next_action_points_to_s2plt03_terminal_resilience_proof(self) -> None:
        assurance = (ADP_ROOT / "docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        owner_status = (ADP_ROOT / "docs/governance/OWNER_STATUS.md").read_text(encoding="utf-8")
        generator = (REPO_ROOT / "scripts/generate_governance_dashboard.py").read_text(encoding="utf-8")

        stale_option = "继续 S2PLT02 no-production readiness evidence work under V7.2 boundaries"
        self.assertIn('task_id: "S2PLT03-TERMINAL-RESILIENCE-PROOF"', assurance)
        self.assertIn("next_task_id: `S2PLT03-TERMINAL-RESILIENCE-PROOF`", owner_status)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", assurance)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", owner_status)
        self.assertIn("do not re-run S2PLT02 SMTP or scheduler capture", assurance)
        self.assertIn("do not re-run S2PLT02 SMTP or scheduler capture", owner_status)
        self.assertNotIn("next collect S2PLT02 terminal delivery proof", assurance)
        self.assertNotIn("next collect S2PLT02 terminal delivery proof", owner_status)
        self.assertNotIn('task_id: "S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT"', assurance)
        self.assertNotIn("next_task_id: `S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT`", owner_status)
        for text in (assurance, owner_status):
            text_lower = text.lower()
            self.assertIn("S2PMT07", text)
            self.assertIn("validated independent reviewer assignment", text)
            self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", text)
            self.assertIn("S2PLT03-TERMINAL-RESILIENCE-PROOF", text)
            self.assertIn("ACC-S2PMT07-FINAL-REVIEW", text)
            self.assertTrue("real" in text_lower or "真实" in text)
            self.assertIn("smtp", text_lower)
            self.assertIn("scheduler", text_lower)
            self.assertIn("P0/P1 zero-proof", text)
            self.assertIn("resilience", text_lower)
            self.assertNotIn(stale_option, text)
        for no_write_ref in (
            "S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR",
            "S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION",
            "S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN",
            "S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY",
            "S2PLT02-REAL-SCHEDULER-PROOF-INPUT-VALIDATOR",
            "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT",
            "S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI",
            "S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY",
            "S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC",
            "S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN",
        ):
            self.assertIn(no_write_ref, assurance)
        assurance_lower = assurance.lower()
        self.assertIn("live authorization", assurance_lower)
        self.assertIn("input inventory", assurance_lower)
        self.assertIn("capture plan", assurance_lower)
        self.assertIn("manifest", assurance_lower)
        self.assertIn("normalized manifest", assurance_lower)
        self.assertIn("dry-run", assurance_lower)
        self.assertIn("adp_s2pmt07_blocked_next_task", generator)
        self.assertIn("terminal_delivery_proof_is_next", generator)
        self.assertIn("terminal_resilience_proof_is_next", generator)
        self.assertIn("s2plt02_terminal_delivery_accepted", generator)
        self.assertIn("current_v7_task_id", generator)

    def test_user_center_default_next_step_prioritizes_s2plt03_terminal_resilience_proof(self) -> None:
        decisions = (ADP_ROOT / "用户中心/关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (ADP_ROOT / "用户中心/路线图与停止门.md").read_text(encoding="utf-8")
        default_next = decisions.split("## 默认下一步", 1)[1]
        first_action_row = next(
            line for line in default_next.splitlines() if line.startswith("| 1 |")
        )

        self.assertIn("S2PLT03 terminal resilience proof", first_action_row)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt03_terminal_resilience_proof.json", first_action_row)
        self.assertIn("validate-s2plt03-terminal-resilience-proof", first_action_row)
        self.assertIn("不得重复触发 S2PLT02 SMTP/scheduler 捕获", first_action_row)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", default_next)
        self.assertIn("S2PLT04 completion report", default_next)
        self.assertIn("S2PLT02 terminal delivery proof 已通过", decisions)
        self.assertIn("默认下一步 `S2PLT03_TERMINAL_RESILIENCE_PROOF`", decisions)
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
