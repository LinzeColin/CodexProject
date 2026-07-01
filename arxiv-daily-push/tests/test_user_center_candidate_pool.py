import csv
import re
import unittest
from pathlib import Path

from arxiv_daily_push.owner_controls import load_owner_controls


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
LEDGER = ROOT / "docs" / "owner" / "CONTENT_LEDGER.csv"
CONTROLS = ROOT / "config" / "owner_controls.yaml"
SOURCE_CATALOG = ROOT / "docs" / "owner" / "SOURCE_CATALOG.md"
USER_CENTER = ROOT / "用户中心"
ROOT_AGENTS = REPO_ROOT / "AGENTS.md"
PROJECT_AGENTS = ROOT / "AGENTS.md"
PROJECT_README = ROOT / "README.md"
CANDIDATE_POOL_PAGE = USER_CENTER / "截至今日候选池.md"
DATA_SOURCE_PAGE = USER_CENTER / "数据源与板块健康.md"
REPORT_PREVIEW_INDEX_PAGE = USER_CENTER / "已生成报告与邮件预览.md"
TRACEABILITY_CHAIN_PAGE = USER_CENTER / "功能任务测试证据追踪链.md"
RESTORE_PATH_SAFETY_PAGE = USER_CENTER / "恢复路径安全扫描.md"
RESTORE_ATOMIC_REPLACEMENT_PAGE = USER_CENTER / "恢复原子替换扫描.md"
OUTBOX_DELIVERY_PAGE = USER_CENTER / "事务发件箱与消息ID扫描.md"
FRONTSTAGE_EVIDENCE_PAGE = USER_CENTER / "前台陈述证据绑定扫描.md"
TRUST_BOUNDARY_PAGE = USER_CENTER / "来源信任边界扫描.md"
B001_INSTALL_LIFECYCLE_PAGE = USER_CENTER / "自动唤醒安装生命周期扫描.md"
LEGACY_MAIL_SCAN_PAGE = USER_CENTER / "旧邮件标识兼容扫描.md"
TRACEABILITY_MATRIX = ROOT / "docs" / "governance" / "TRACEABILITY_MATRIX.csv"
MODEL_PARAMS_PAGE = ROOT / "模型参数文件.md"
SUMMARY_PAGES = (
    USER_CENTER / "README.md",
    USER_CENTER / "邮件发送与队列状态.md",
    USER_CENTER / "一看三查.md",
    USER_CENTER / "关键结论与用户决策.md",
)


def _section(text: str, start_heading: str, end_heading: str) -> str:
    start = text.index(start_heading)
    end = text.index(end_heading, start)
    return text[start:end]


class UserCenterCandidatePoolTests(unittest.TestCase):
    def test_total_candidate_pool_page_matches_content_ledger_row_count(self):
        ledger_rows = list(csv.DictReader(LEDGER.read_text(encoding="utf-8").splitlines()))
        page = CANDIDATE_POOL_PAGE.read_text(encoding="utf-8")
        total_pool_section = _section(page, "## 总候选池记录", "## 禁止误读")
        table_rows = re.findall(r"^\| \d+ \|", total_pool_section, flags=re.MULTILINE)

        self.assertEqual(len(ledger_rows), 299)
        self.assertEqual(len(table_rows), len(ledger_rows))
        self.assertTrue(page.startswith("# 截至今日总候选池\n"))
        self.assertIn("截至今日总候选池 | 299 条", page)
        self.assertIn("[CONTENT_LEDGER.csv](../docs/owner/CONTENT_LEDGER.csv)", page)
        self.assertIn("[报告/邮件预览索引](./已生成报告与邮件预览.md#", page)
        self.assertNotIn("../docs/owner/reports.md#", page)
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")

    def test_candidate_pool_page_exposes_top_20_scored_selection_and_inventory_rules(self):
        page = CANDIDATE_POOL_PAGE.read_text(encoding="utf-8")
        top20_section = _section(page, "## 候选队列前20精选", "## 候选队列前20评分明细")
        top20_rows = re.findall(r"^\| \d+ \|", top20_section, flags=re.MULTILINE)

        self.assertEqual(len(top20_rows), 20)
        self.assertIn("| 1 | cs.AI | [arXiv:2606.22716]", top20_section)
        self.assertIn("| 65.51 |", top20_section)
        self.assertIn("同一篇文章按论文标识去重", top20_section)
        self.assertIn("| 序号 | 领域代码 | 标题 / 条目 | 分数 | 状态 | 候选日期 | 证据 |", top20_section)
        self.assertNotIn("| Rank |", top20_section)
        self.assertIn("截至今日总候选池 = 已处理候选 + 待处理候选", page)
        self.assertIn("每日期末总候选池 = 昨日期末总候选池 + 今日新增候选 - 今日剔除候选", page)
        self.assertIn("今日待处理候选 = 昨日待处理候选 + 今日新增候选 - 今日完成处理 - 今日剔除候选", page)
        self.assertIn("当前仓库尚未接入日级库存流转账本", page)
        self.assertIn("板块期末候选数", page)
        self.assertIn("ending_pool = yesterday_pool + today_added - today_completed - today_removed", page)
        self.assertNotIn("Stage 2 生产验收通过", page)

    def test_candidate_pool_top_20_exposes_per_article_score_breakdown(self):
        page = CANDIDATE_POOL_PAGE.read_text(encoding="utf-8")
        detail_section = _section(page, "## 候选队列前20评分明细", "## 每日库存流转规则")
        detail_rows = re.findall(r"^\| \d+ \|", detail_section, flags=re.MULTILINE)

        self.assertEqual(len(detail_rows), 20)
        self.assertIn("adp-roi-semantic-rubric-v2", detail_section)
        self.assertIn("单元格只展示归一化信号百分比", detail_section)
        self.assertIn("每个证据命中统一增加 7%", detail_section)
        self.assertIn("公开语义评分 rubric", detail_section)
        self.assertIn("[global_scan.py](../src/arxiv_daily_push/global_scan.py)", detail_section)
        self.assertIn("| 序号 | 领域代码 | 论文 | V2 总分 | 相关性 15% | 学习价值 20% | 经济转化率 25% | ROI 20% | 跨学科价值 10% | 可解释性 10% | 核对 | 证据 |", detail_section)
        self.assertIn("| 1 | cs.AI | [arXiv:2606.22716](https://arxiv.org/abs/2606.22716) | 61.55 | 70% | 88% | 39% | 59.50% | 43% | 75% | V2 重算 |", detail_section)
        self.assertIn("| 20 | cs.CR | [arXiv:2606.08372](https://arxiv.org/abs/2606.08372) | 55.15 |", detail_section)
        self.assertEqual(detail_section.count("V2 重算 | [arXiv 元数据]"), 20)

    def test_report_preview_index_exists_for_generated_records(self):
        ledger_rows = list(csv.DictReader(LEDGER.read_text(encoding="utf-8").splitlines()))
        generated_rows = [
            row
            for row in ledger_rows
            if row["report_file_state"] == "generated" or row["email_state"] == "preview_generated"
        ]
        page = REPORT_PREVIEW_INDEX_PAGE.read_text(encoding="utf-8")
        table_rows = re.findall(r"^\| \d+ \|", page, flags=re.MULTILINE)

        self.assertEqual(len(generated_rows), 30)
        self.assertEqual(len(table_rows), len(generated_rows))
        self.assertIn("本页是 GitHub 浅层用户中心里的报告/邮件预览索引", page)
        self.assertIn("不是完整报告正文", page)
        self.assertIn("| 序号 | 锚点 | 领域代码 | 标题 / 条目 | 状态 | 候选日期 | 证据 |", page)
        self.assertNotIn("| 原始定位 |", page)
        self.assertEqual(page.count("[CONTENT_LEDGER.csv](../docs/owner/CONTENT_LEDGER.csv)"), len(generated_rows) + 1)

    def test_learning_snapshot_summary_pages_do_not_revert_to_pending_after_daily_snapshot(self):
        snapshot_page = (USER_CENTER / "复习行动与收益.md").read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")
        one_check_three = (USER_CENTER / "一看三查.md").read_text(encoding="utf-8")

        self.assertIn("本表已由 2026-06-28 本地恢复补发运行写入", snapshot_page)
        self.assertIn("| 今日到期复习 | 0 项 |", snapshot_page)
        self.assertIn("| 今日 15 分钟行动 | 1 项 |", snapshot_page)
        self.assertIn("| 新增能力资产 | 1 项 |", snapshot_page)
        self.assertIn("复习行动与收益](./复习行动与收益.md) 已显示字段、证据链和 2026-06-28 今日快照数字", readme)
        self.assertIn("复习行动与收益](./复习行动与收益.md) 已有 GitHub 展示位、证据链和 2026-06-28 今日快照数字", one_check_three)
        self.assertNotIn("今日快照待写入", readme)
        self.assertNotIn("今日快照待写入", one_check_three)
        self.assertNotIn("仍需真实运行写入的数字", one_check_three)
        self.assertNotIn("当前仓库没有可作为今日真实数字的持久化日报", one_check_three)

    def test_traceability_chain_page_exposes_all_matrix_rows_as_clickable_links(self):
        matrix_rows = list(csv.DictReader(TRACEABILITY_MATRIX.read_text(encoding="utf-8").splitlines()))
        page = TRACEABILITY_CHAIN_PAGE.read_text(encoding="utf-8")
        table_rows = re.findall(r"^\| \d+ \|", page, flags=re.MULTILINE)
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertGreaterEqual(len(matrix_rows), 406)
        self.assertEqual(len(table_rows), len(matrix_rows))
        self.assertTrue(page.startswith("# 功能任务测试证据追踪链\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertEqual(page.count("更新时间："), 1)
        self.assertIn("## 当前阅读规则", page)
        self.assertIn("Stage 2 integrated acceptance 已记录", page)
        self.assertIn("不进入；`daily_operation_enabled=false`", page)
        self.assertIn("2026-07-01 19:04 以前的 S2PLT02、S2PLT03、S2PLT04、final bundle", page)
        self.assertIn("不得用来回退 Stage 2 integrated acceptance", page)
        self.assertIn("只能做 MVP 复审修补、证据链可读性、用户中心同步和测试补强", page)
        self.assertIn("[final bundle manifest](../../FINAL_ACCEPTANCE_BUNDLE/manifest.json)", page)
        self.assertIn("[TRACEABILITY_MATRIX.csv](../docs/governance/TRACEABILITY_MATRIX.csv)", page)
        self.assertIn("[C-010 阶段记录](../docs/phase_records/PHASE_S2PAT05_TRACEABILITY_CHAIN_C010.md)", page)
        self.assertIn("[运行清单](../../governance/run_manifests/ADP-S2PAT05-TRACEABILITY-CHAIN-C010-20260627.json)", page)
        self.assertIn("| 序号 | 需求 | 任务 | 验收 | 代码 | 配置 | 测试 | 运行证据 | 状态 |", page)
        self.assertIn("[test_stage2_sources.py](../tests/test_stage2_sources.py)", page)
        self.assertIn(f"TRACEABILITY_MATRIX 行数 | {len(matrix_rows)}", page)
        self.assertIn(f"{len(matrix_rows)} 条可点击链路", readme)

        self.assertIn("REQ-ADP-V7-072-S2PLT02-CONTROLLED-REAL-SECOND-DAY-CAPTURE", page)
        self.assertIn("S2PLT02-CONTROLLED-REAL-SECOND-DAY-CAPTURE", page)
        self.assertIn("ADP-S2PLT02-CONTROLLED-REAL-SECOND-DAY-CAPTURE-20260630.json", page)
        self.assertIn("PHASE_LOCAL_DAILY_M1_M4_CONTROLLED_REAL_CATCHUP_20260629.md", page)
        self.assertIn("blocked_after_evidence_capture_no_production", page)
        self.assertIn("observed_real_delivery_days=2/2", page)
        self.assertIn("observed_real_email_count=8/8", page)

        self.assertIn("REQ-ADP-V7-071-S2PLT02-TERMINAL-CAPTURE-READONLY-COMMAND-EXECUTABILITY-SYNC", page)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-READONLY-COMMAND-EXECUTABILITY-SYNC", page)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-CAPTURE-READONLY-COMMAND-EXECUTABILITY-SYNC-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_READONLY_COMMAND_EXECUTABILITY_SYNC.md", page)
        self.assertIn("blocked_s2plt02_terminal_capture_readonly_commands_executable_no_production", page)
        self.assertIn("allowed_readonly_commands", page)
        self.assertIn(
            "adp audit-s2plt02-terminal-proof-evidence-inventory --repo-root . --generated-at 2026-07-01T05:42:34+10:00 --json",
            page,
        )
        self.assertIn("aafb8d5147d8c7849a2489bfb4991376e978d646b5e149156cbba58ae513aff1", page)
        self.assertIn("502a892c3a207233c0d9ea985685c5064e2aaa279ca9010a490b30190aefecfe", page)
        self.assertIn("26207ef1ba63b2fe56d7904e141cf20dbd49268d98407a45a73dbf2fcfd0ed4c", page)
        self.assertIn("REQ-ADP-V7-082-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST", page)
        self.assertIn("S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST", page)
        self.assertIn("daily_operation_persistent_enablement_authorization.request.json", page)
        self.assertIn("ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-20260701.json", page)
        self.assertIn("ready_owner_persistent_daily_operation_authorization_request_no_runtime_enablement", page)
        self.assertIn("request_only=true", page)
        self.assertIn(
            "REQ-ADP-V7-083-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-MAINLINE-ATTESTATION",
            page,
        )
        self.assertIn("S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-MAINLINE-ATTESTATION", page)
        self.assertIn("PHASE_S2PMT07_DAILY_OPERATION_PERSISTENT_AUTHORIZATION_REQUEST_MAINLINE_ATTESTATION.md", page)
        self.assertIn("ADP-S2PMT07-DAILY-OPERATION-PERSISTENT-AUTHORIZATION-REQUEST-MAINLINE-ATTESTATION-20260701.json", page)
        self.assertIn("pass_persistent_daily_operation_authorization_request_mainline_attested_no_runtime_enablement", page)
        self.assertIn("4f72c42ea62275fdd18285cf189070c6aa76bd71", page)
        self.assertIn("0f0772e4250330372d58456a355e205327dff933", page)
        self.assertIn("94fbe44f8211dff645ad5939696843122191b5b10ed939a1e04105c5e312c6b9", page)
        self.assertIn("6ae337c9dd434e0f43909cf2ddc13f3d0de3a1bb5beb919ac2323ee61b8ef48f", page)
        self.assertIn(
            "REQ-ADP-V7-084-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-KEEP-DISABLED",
            page,
        )
        self.assertIn("S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-KEEP-DISABLED", page)
        self.assertIn("ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-KEEP-DISABLED-20260701.json", page)
        self.assertIn("PHASE_S2PMT07_DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_KEEP_DISABLED.md", page)
        self.assertIn("pass_owner_selected_option_a_keep_daily_operation_disabled_after_request_no_runtime_enablement", page)
        self.assertIn("d793c63910fa3b1e467e0b6b1c78deb63e87a44f02e8507ec363d174b9813fb4", page)
        self.assertIn("owner_selected_option=A", page)
        self.assertIn(
            "REQ-ADP-V7-085-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION",
            page,
        )
        self.assertIn("S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION", page)
        self.assertIn("ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION-20260701.json", page)
        self.assertIn("PHASE_S2PMT07_DAILY_OPERATION_OWNER_DECISION_AFTER_REQUEST_MAINLINE_ATTESTATION.md", page)
        self.assertIn("pass_owner_option_a_after_request_mainline_attested_keep_disabled_no_runtime_enablement", page)
        self.assertIn("90b297a55451b691c3e0270cfaa64e5d58c5a519", page)
        self.assertIn("d92ec4a0cd884641263c7979f7a5c625229ae83c", page)
        self.assertIn("ce1545e7d9f9c3fd8af016f802a830bc2d2370e92843c14bdf47dc7d32c0e82d", page)

        self.assertIn("REQ-ADP-V7-070-S2PLT02-TERMINAL-CAPTURE-INVENTORY-SUMMARY-SYNC", page)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-INVENTORY-SUMMARY-SYNC", page)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-CAPTURE-INVENTORY-SUMMARY-SYNC-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_INVENTORY_SUMMARY_SYNC.md", page)
        self.assertIn("blocked_s2plt02_terminal_capture_inventory_summary_synced_no_production", page)
        self.assertIn("terminal_delivery_input_inventory_summary.state_hash=4df922bd5dc56541cbd76380adc6897fb779c929afa1c37e7f1d2eab236e8e5b", page)
        self.assertIn("terminal_delivery_artifact_validation_summary.state_hash=3fbde96111dd78d3ffe4474e012fa5d86de76a24e6fa7640d0310c178003e1db", page)
        self.assertIn("cba2fb5be5cc1a7dc098b28fe0b0bd137fb43d18e4f077d755571313bcee03e4", page)
        self.assertIn("bcb40505ad7244626589c24991dcf05fe775268ce44b5eab3b68444f38cded6e", page)
        self.assertIn("23c5a2f6beed34c440ee8f3de870ca71a2c2deb1d44cbd67623a3c7aa7fc510c", page)

        self.assertIn("REQ-ADP-V7-069-S2PMT07-FINAL-BUNDLE-ZERO-PROOF-REQUEST-CONSUMPTION-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-ZERO-PROOF-REQUEST-CONSUMPTION-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-ZERO-PROOF-REQUEST-CONSUMPTION-SYNC-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_ZERO_PROOF_REQUEST_CONSUMPTION_SYNC.md", page)
        self.assertIn("blocked_final_bundle_zero_proof_request_consumed_no_production", page)
        self.assertIn("zero_proof_artifact_validation_state_hash=bf966c244f9f7c52b75ae7d56ff8f8c0fbda498cd678f4003ee3ed2c40961786", page)
        self.assertIn("assignment_request_state_hash=8a4596dbb16f55932e36b256fc22852e1f8ca52da22bdd85d6d1c79d23b61c1b", page)
        self.assertIn("closure_decision_request_state_hash=afc1155fafad8c460db5e09eb9890e7408a1e28dd0bf155121bf1a0308529e34", page)
        self.assertIn("cf9a46ccbdfd35b01bd579511ed7ae1cdfcac411e00d8f610c80625f596e1094", page)

        self.assertIn("REQ-ADP-V7-068-S2PMT07-FINAL-BUNDLE-REVIEWER-ASSIGNMENT-CONSUMPTION-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-REVIEWER-ASSIGNMENT-CONSUMPTION-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-REVIEWER-ASSIGNMENT-CONSUMPTION-SYNC-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_REVIEWER_ASSIGNMENT_CONSUMPTION_SYNC.md", page)
        self.assertIn("blocked_final_bundle_reviewer_assignment_consumed_no_production", page)
        self.assertIn("assignment_validation_state_hash=b5b117307bd61f168ae6a422b24c865227f4824191348b851081af66730ed2c2", page)
        self.assertIn("assignment_request_state_hash=7f59ff864ad3a43f24e3b105f13a5aed8802729e8c18482483db8ed78c2921ad", page)
        self.assertIn("closure_decision_request_state_hash=246a736255b77c3a40f74fbdc4431f52367e3d474d4d13156a19ec9b6e7feddf", page)
        self.assertIn("be9cd3bb14da9d57dcaee0168bae396ed95049bf6c261515a5d39959cf3ad461", page)

        self.assertIn("REQ-ADP-V7-066-S2PLT02-TERMINAL-CAPTURE-NO-WRITE-FLAGS-TOP-LEVEL-SYNC", page)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-NO-WRITE-FLAGS-TOP-LEVEL-SYNC", page)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-CAPTURE-NO-WRITE-FLAGS-TOP-LEVEL-SYNC-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_NO_WRITE_FLAGS_TOP_LEVEL_SYNC.md", page)
        self.assertIn("blocked_s2plt02_terminal_capture_no_write_flags_top_level_synced_no_production", page)
        self.assertIn("write_terminal_artifact_allowed=false", page)
        self.assertIn("scheduler_enable_allowed_by_this_plan=false", page)
        self.assertIn("production_acceptance_allowed=false", page)
        self.assertIn("12b564610114a7278b9566255085d5308984c28e433965581bcbde630e9bf9aa", page)
        self.assertIn("d95f0afad934a6692635960d48cda963074840c0615f9bafe1fb023ff9c4f612", page)
        self.assertIn("0c032d9c804410f2b4ffe11cb52b00e91500fd7790d1eac533154650625b3c6e", page)

        self.assertIn("REQ-ADP-V7-065-S2PMT07-FINAL-BUNDLE-LIVE-WRITE-READY-TOP-LEVEL-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-LIVE-WRITE-READY-TOP-LEVEL-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-LIVE-WRITE-READY-TOP-LEVEL-SYNC-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_LIVE_WRITE_READY_TOP_LEVEL_SYNC.md", page)
        self.assertIn("blocked_final_bundle_live_write_ready_top_level_synced_no_production", page)
        self.assertIn("ready_to_write_live_artifacts=false", page)
        self.assertIn("current_wait_state=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", page)
        self.assertIn("c9216c53cedf0cb5fcc12fd15ffb021b83586906f233a4f78ed96ecfe84f9b13", page)
        self.assertIn("256aa1a8dfeff4f598fa9fbb172aae3f6e7cde428bde570424a2bc779da7e320", page)
        self.assertIn("494538d0e454c51869eca559808316740a422f92b7deeb070d348f65e1277d67", page)

        self.assertIn("REQ-ADP-V7-064-S2PMT07-FINAL-BUNDLE-TOP-LEVEL-WAIT-STATE-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-TOP-LEVEL-WAIT-STATE-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-TOP-LEVEL-WAIT-STATE-SYNC-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_TOP_LEVEL_WAIT_STATE_SYNC.md", page)
        self.assertIn("blocked_final_bundle_top_level_wait_state_synced_no_production", page)
        self.assertIn("current_wait_state=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", page)
        self.assertIn("c9216c53cedf0cb5fcc12fd15ffb021b83586906f233a4f78ed96ecfe84f9b13", page)
        self.assertIn("2ee61c653d48b74f03505221adf6e37039d9cd4339b5554ba145dd02f9ec6198", page)
        self.assertIn("3ba4d2fdcc2ea9bfc268f7f579ce8e8e4e3458ee6c69400e157571906ba16b29", page)

        self.assertIn("REQ-ADP-V7-063-S2PMT07-FINAL-BUNDLE-S2PLT02-CURRENT-WAIT-STATE-SUMMARY", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-CURRENT-WAIT-STATE-SUMMARY", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-CURRENT-WAIT-STATE-SUMMARY-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_CURRENT_WAIT_STATE_SUMMARY.md", page)
        self.assertIn("blocked_final_bundle_s2plt02_current_wait_state_summary_synced_no_production", page)
        self.assertIn("current_wait_state=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", page)
        self.assertIn("c9216c53cedf0cb5fcc12fd15ffb021b83586906f233a4f78ed96ecfe84f9b13", page)
        self.assertIn("0b6753d007633aaeca00368eb29ebe54cc677846085051988a60854713c93b42", page)
        self.assertIn("4f1e0e311ea68a5cc320e1c0a5d11985b2a256acbeb06217a57e86d6fa217d65", page)

        self.assertIn("REQ-ADP-V7-061-S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-READONLY-COMMAND-CONTRACT", page)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-READONLY-COMMAND-CONTRACT", page)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-READONLY-COMMAND-CONTRACT-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_WAIT_STATE_READONLY_COMMAND_CONTRACT.md", page)
        self.assertIn("blocked_s2plt02_terminal_capture_wait_state_readonly_command_contract_synced_no_production", page)
        self.assertIn(
            "adp plan-s2plt02-terminal-delivery-proof-capture --repo-root . --generated-at 2026-06-30T18:03:24+10:00 --json",
            page,
        )
        self.assertIn("5b344929d8d00c9cf881accbbd9abd68963b5f40cbd975a805fa4da62a8a8a25", page)
        self.assertIn("581fe9f53d82db88959196f874d312e50b1739a839158f7bf2d38cc186c03506", page)
        self.assertIn("8409313fd39c4627122aca97cc80d28480f65b5230f6982ae7e720b6e0134b73", page)
        self.assertIn("eef4f33e08feb99de67c24c9339ae204658f6b0ac4d0e5cd810092b5a3246aff", page)

        self.assertIn("REQ-ADP-V7-062-S2PMT07-FINAL-BUNDLE-PREREQUISITE-MISSING-INVENTORY-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-PREREQUISITE-MISSING-INVENTORY-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-PREREQUISITE-MISSING-INVENTORY-SYNC-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_PREREQUISITE_MISSING_INVENTORY_SYNC.md", page)
        self.assertIn("blocked_final_bundle_prerequisite_missing_inventory_synced_no_production", page)
        self.assertIn("447072118012325d6b8740d76f37b1838ec788e09e591fbe451fe3a61b0f8d04", page)
        self.assertIn("45669a5d11c178dc6f2eaf23c806fabc420c2e20b2bf4f6b0fbd4f79504d1048", page)
        self.assertIn("51d89042f47937b6ef65862d30dff1d8398caf21f5d8f875709ac6e6ff255cf0", page)

        self.assertIn("REQ-ADP-V7-060-S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-GUARD", page)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-GUARD", page)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-CAPTURE-WAIT-STATE-GUARD-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_WAIT_STATE_GUARD.md", page)
        self.assertIn("blocked_s2plt02_terminal_capture_wait_state_guard_synced_no_production", page)
        self.assertIn("capture_wait_state_guard", page)

        self.assertIn("REQ-ADP-V7-059-S2PMT07-FINAL-BUNDLE-MISSING-ARTIFACT-INVENTORY", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-MISSING-ARTIFACT-INVENTORY", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-MISSING-ARTIFACT-INVENTORY-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_MISSING_ARTIFACT_INVENTORY.md", page)
        self.assertIn("blocked_final_bundle_missing_artifact_inventory_synced_no_production", page)
        self.assertIn("final_bundle_missing_artifact_inventory", page)
        self.assertIn("missing_item_count=5", page)
        self.assertIn("2e80e00465c90d27c821981c2f2a7190050ea7c3e390a38a526ff6d7bbb539ae", page)
        self.assertIn("51d89042f47937b6ef65862d30dff1d8398caf21f5d8f875709ac6e6ff255cf0", page)

        self.assertIn("REQ-ADP-V7-057-S2PMT07-FINAL-BUNDLE-S2PLT02-TERMINAL-COUNT-SPLIT", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-TERMINAL-COUNT-SPLIT", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-TERMINAL-COUNT-SPLIT-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_TERMINAL_COUNT_SPLIT.md", page)
        self.assertIn("blocked_final_bundle_s2plt02_terminal_count_split_synced_no_production", page)
        self.assertIn("fb04c0b2582c24bdecf9d6d33658f25139ab8cf656cd6e22c69f01e5a3e1c419", page)
        self.assertIn("7527930ba22a849c42ff55a0e65ea3c4b242e6c629f51db671468b63a1925a2b", page)
        self.assertIn("e7c9834eca19f665f1b57566f47cbd03ecaaf95fa9eb538187af3c3f7e1aa7f1", page)
        self.assertIn("e2471c2bdba40251132ae5d4374a5642db547f0fa82af54b4641b67a6f21b74c", page)
        self.assertIn("ab1ef6efbca6e019569e65849cd66dbb4cca336fca4bd95314252603db65a151", page)
        self.assertIn("observed_real_counts_source=terminal_delivery_input_inventory_existing_real_smtp_evidence", page)
        self.assertIn("observed_real_delivery_days=1", page)
        self.assertIn("observed_real_email_count=4", page)
        self.assertIn("current_capture_window_real_delivery_days_added=0", page)
        self.assertIn("current_capture_window_real_email_count_added=0", page)
        self.assertIn("current_capture_window_dry_run_email_count_rejected=8", page)
        self.assertIn("terminal_proof_real_delivery_days_after_current_capture_window=1", page)
        self.assertIn("terminal_proof_real_email_count_after_current_capture_window=4", page)
        self.assertIn("remaining_real_delivery_days_for_terminal_proof=1", page)
        self.assertIn("remaining_real_email_count_for_terminal_proof=4", page)

        self.assertIn("REQ-ADP-V7-058-S2PMT07-FINAL-BUNDLE-LIVE-ARTIFACT-WRITE-GUARD", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-LIVE-ARTIFACT-WRITE-GUARD", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-LIVE-ARTIFACT-WRITE-GUARD-20260701.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_LIVE_ARTIFACT_WRITE_GUARD.md", page)
        self.assertIn("blocked_final_bundle_live_artifact_write_guard_synced_no_production", page)
        self.assertIn("live_artifact_write_guard", page)
        self.assertIn("9454e47e36d6cc04e20918f50d8f7d6be6e5c12fadfc4a6f5f86144562199eb9", page)
        self.assertIn("1146133f14fe04dba14e0313409fad828bfe2d6439adefc68a640d5500568b85", page)
        self.assertIn("HANDOFF/00_下一Agent先读.md", page)
        self.assertIn("FINAL_ACCEPTANCE_BUNDLE/manifest.json", page)

        self.assertIn("REQ-ADP-V7-056-S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-WINDOW-SUMMARY", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-WINDOW-SUMMARY", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-WINDOW-SUMMARY-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_CAPTURE_WINDOW_SUMMARY.md", page)
        self.assertIn("blocked_final_bundle_s2plt02_capture_window_summary_synced_no_production", page)
        self.assertIn("9f564e7fab8d69c12102143f2aed4a015b5ecff5eb8b9862f3ebc9d37f909144", page)
        self.assertIn("1ab9fa8e6fc25ea35fb5405a26917bbf2d5993b1911704b2d3acb654fdb5c5c5", page)
        self.assertIn("3abd9c06b9490e0023eb4d1db2a2d19a7679041f9f887179304bee0d025f0429", page)
        self.assertIn("e2471c2bdba40251132ae5d4374a5642db547f0fa82af54b4641b67a6f21b74c", page)
        self.assertIn("ab1ef6efbca6e019569e65849cd66dbb4cca336fca4bd95314252603db65a151", page)
        self.assertIn("dry_run_service_dates=2026-06-29;2026-06-30", page)
        self.assertIn("nonterminal_succeeded_dry_run_service_dates=2026-06-29;2026-06-30", page)
        self.assertIn("dry_run_email_count=8", page)
        self.assertIn("real_sent_candidate_email_count=0", page)
        self.assertIn("observed_terminal_email_count_credit=4", page)
        self.assertIn("terminal_delivery_credit=false", page)
        self.assertIn("counts_toward_s2plt02_terminal_proof=false", page)
        self.assertIn("launchagent_runtime_state_unknown", page)
        self.assertIn("launchagents_loaded_but_disabled_not_terminal_scheduler_proof", page)
        self.assertIn("REQ-ADP-V7-055-S2PMT07-FINAL-BUNDLE-S2PLT04-COMPLETION-EVIDENCE-SUMMARY", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT04-COMPLETION-EVIDENCE-SUMMARY", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT04-COMPLETION-EVIDENCE-SUMMARY-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT04_COMPLETION_EVIDENCE_SUMMARY.md", page)
        self.assertIn("blocked_final_bundle_s2plt04_completion_evidence_summary_synced_no_production", page)
        self.assertIn("b9d7ce5a9011f44fa66250d174da9731238f1914a008ba5d61e81c85192eb8a4", page)
        self.assertIn("5e0d1a81d1f8f8de49721844d8b96f376a74a11ee69170e30685c915032ed8e2", page)
        self.assertIn("ee3917fedcd96e10a23fbd228367e6837ffca092734d98288502d9702514165f", page)
        self.assertIn("s2plt04_completion_report_written=false", page)
        self.assertIn("completion_report_ready=false", page)
        self.assertIn("s2plt02_live_2d_terminal_proof_missing;s2plt03_resilience_terminal_proof_missing", page)
        self.assertIn("REQ-ADP-V7-054-S2PMT07-FINAL-BUNDLE-P0P1-ZERO-PROOF-STATUS-SUMMARY", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-P0P1-ZERO-PROOF-STATUS-SUMMARY", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-P0P1-ZERO-PROOF-STATUS-SUMMARY-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_P0P1_ZERO_PROOF_STATUS_SUMMARY.md", page)
        self.assertIn("blocked_final_bundle_p0p1_zero_proof_status_summary_synced_no_production", page)
        self.assertIn("6036321e310edadb57834353b45c08a632100caab1f61dfd00fa7c108a57b05f", page)
        self.assertIn("b0fc0aefd87ee9ed3c412024d534ec23a6fdf5d32316b6089fee769a3d24d758", page)
        self.assertIn("bf966c244f9f7c52b75ae7d56ff8f8c0fbda498cd678f4003ee3ed2c40961786", page)
        self.assertIn("current_zero_proof_counts=P0=0;P1=0", page)
        self.assertIn("inherited_v7_1_baseline_counts=P0=8;P1=37", page)
        self.assertIn("baseline_counts_mutated=false", page)
        self.assertIn("production_acceptance_claimed=false", page)
        self.assertIn("integrated_production_accepted=false", page)
        self.assertIn("REQ-ADP-V7-053-S2PMT07-FINAL-BUNDLE-S2PLT02-ARTIFACT-VALIDATION-SUMMARY", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-ARTIFACT-VALIDATION-SUMMARY", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-ARTIFACT-VALIDATION-SUMMARY-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_ARTIFACT_VALIDATION_SUMMARY.md", page)
        self.assertIn("blocked_final_bundle_s2plt02_artifact_validation_summary_synced_no_production", page)
        self.assertIn("084c08ec36f925dedb7ecb3488874a23d82090e124b0a791ecd34a998691e54c", page)
        self.assertIn("8b7dc7003c7f60c9065448b2c86d7e1089aedc022b56a84a36487899aa604fa9", page)
        self.assertIn("797c920987dcb0f38a1af8c8dc2ed80633c412cf9bb5f91686a7c29bfeaa68f8", page)
        self.assertIn("3fbde96111dd78d3ffe4474e012fa5d86de76a24e6fa7640d0310c178003e1db", page)
        self.assertIn("terminal_artifact_validation_status=blocked", page)
        self.assertIn("terminal_artifact_ref=FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json", page)
        self.assertIn("terminal_artifact_present=false", page)
        self.assertIn("terminal_artifact_ready=false", page)
        self.assertIn("terminal_artifact_validation_errors=s2plt02_terminal_delivery_proof_artifact_missing", page)
        self.assertIn("terminal_artifact_blocking_reasons=s2plt02_terminal_delivery_proof_artifact_missing;two_consecutive_real_days_not_proven;eight_real_emails_not_proven;real_scheduler_not_proven", page)
        self.assertIn("REQ-ADP-V7-052-S2PMT07-FINAL-BUNDLE-S2PLT03-SUMMARY-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT03-SUMMARY-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT03-SUMMARY-SYNC-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT03_SUMMARY_SYNC.md", page)
        self.assertIn("blocked_final_bundle_s2plt03_summary_synced_no_production", page)
        self.assertIn("3b2475e26547816b77885fddb170944fb858a4aa14fc04305de6798c288a8651", page)
        self.assertIn("55e5d994d17ceb53cb8e8a1729c52e29d7808dd07527e9ee9a48f52982e129f5", page)
        self.assertIn("s2plt03_terminal_resilience_capture_plan_summary", page)
        self.assertIn("next_executable_step=WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE", page)
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT;S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT", page)
        self.assertIn("s2plt03_terminal_resilience_proof_artifact_missing;s2plt02_not_accepted", page)
        self.assertIn("artifact_written=false", page)
        self.assertIn("s2plt03_accepted=false", page)
        self.assertIn("s2plt03_resilience_drill_completed=false", page)
        self.assertIn("REQ-ADP-V7-051-S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-COMMAND-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-COMMAND-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-CAPTURE-COMMAND-SYNC-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_CAPTURE_COMMAND_SYNC.md", page)
        self.assertIn("blocked_final_bundle_s2plt02_capture_command_synced_no_production", page)
        self.assertIn("9621084d1f10a325d6d02284f66db8e78a239aeb16e556bb9de55d455c244f6b", page)
        self.assertIn("e7f33cbf0d084cb00c547016d83139b47e62809e2638be3a33effc8dcbe74358", page)
        self.assertIn("next_executable_command=plan-s2plt02-terminal-delivery-proof-capture", page)
        self.assertIn("next_executable_command_dry_run_status=blocked", page)
        self.assertIn("next_executable_command_writes_artifact=false", page)
        self.assertIn("next_executable_command_satisfies_gate=false", page)
        self.assertIn("REQ-ADP-V7-049-S2PMT07-FINAL-BUNDLE-VALIDATOR-RUNTIME-STEP-SUMMARY", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-VALIDATOR-RUNTIME-STEP-SUMMARY", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-VALIDATOR-RUNTIME-STEP-SUMMARY-20260630.json", page)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_VALIDATOR_RUNTIME_STEP_SUMMARY.md", page)
        self.assertIn("blocked_final_bundle_validator_runtime_step_summary_synced_no_production", page)
        self.assertIn("303854706b4dee813e8e9d3f970bfce8943db4a162779845835d1682d5dc91ff", page)
        self.assertIn(
            "final_bundle_prerequisite_plan_state_hash=bc5c75ce6138842f2b3de247420260b55d3b1a5f7cfb6f10dc44f91efb594af6",
            page,
        )
        self.assertIn("REQ-ADP-V7-050-S2PMT07-FINAL-BUNDLE-S2PLT02-RUNTIME-READINESS-SUMMARY", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-S2PLT02-RUNTIME-READINESS-SUMMARY", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-S2PLT02-RUNTIME-READINESS-SUMMARY-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_S2PLT02_RUNTIME_READINESS_SUMMARY.md", page)
        self.assertIn("blocked_final_bundle_s2plt02_runtime_readiness_summary_synced_no_production", page)
        self.assertIn("b70e0ae4ab942c46018d87e28c09b9d8e839f4ab10682cbf4fde8e993a15194e", page)
        self.assertIn("8878509d00a04899d9b4a647d98146dea5aa88e39f41a07d25f39b9848cb8878", page)
        self.assertIn("48bea5fd4a31cbe6f675b1a2b939d1444b8a148b37d3f6a7b338096071a995f9", page)
        self.assertIn("capture_second_consecutive_real_m1_m4_smtp_day", page)
        self.assertIn("capture_real_launchd_scheduler_proof", page)
        self.assertIn("write_and_validate_s2plt02_terminal_delivery_proof_artifact", page)
        self.assertIn("real_smtp_secret_env_missing", page)
        self.assertIn("missing_smtp_secret_env_names=ADP_SMTP_HOST;ADP_SMTP_PORT;ADP_SMTP_USERNAME;ADP_SMTP_PASSWORD", page)
        self.assertIn("smtp_secret_env_ready=false", page)
        self.assertIn("smtp_secret_values_logged=false", page)
        self.assertIn("REQ-ADP-V7-048-S2PMT07-FINAL-BUNDLE-PREREQUISITE-S2PLT02-RUNTIME-STEP-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-PREREQUISITE-S2PLT02-RUNTIME-STEP-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-PREREQUISITE-S2PLT02-RUNTIME-STEP-SYNC-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_PREREQUISITE_S2PLT02_RUNTIME_STEP_SYNC.md", page)
        self.assertIn("blocked_final_bundle_prerequisite_s2plt02_runtime_step_synced_no_production", page)
        self.assertIn("next_executable_runtime_step=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", page)
        self.assertIn("bc5c75ce6138842f2b3de247420260b55d3b1a5f7cfb6f10dc44f91efb594af6", page)
        self.assertIn("next_executable_task=S2PLT02_TERMINAL_DELIVERY_PROOF", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC", page)
        self.assertIn("S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC", page)
        self.assertIn("ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC-20260630.json", page)
        self.assertIn("PHASE_S2PLT02_REAL_PROOF_CAPTURE_READINESS_LIVE_AUTH_SYNC.md", page)
        self.assertIn(
            "blocked_s2plt02_real_proof_capture_readiness_live_authorization_pass_terminal_gaps_visible_no_production",
            page,
        )
        self.assertIn("REQ-ADP-V7-043-S2PLT02-TERMINAL-CAPTURE-PLAN-RUNTIME-AUTH-GATE", page)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-PLAN-RUNTIME-AUTH-GATE", page)
        self.assertIn("ADP-S2PLT02-TERMINAL-CAPTURE-PLAN-RUNTIME-AUTH-GATE-20260630.json", page)
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_PLAN_RUNTIME_AUTH_GATE.md", page)
        self.assertIn("blocked_s2plt02_capture_plan_runtime_auth_gate_no_production", page)
        self.assertIn("runtime_capture_ready=false", page)
        self.assertIn("next_executable_step=WAIT_FOR_REAL_SMTP_SCHEDULER_CAPTURE_WINDOW", page)
        self.assertIn("6fa850a802d93e839146cabf158689af05941a54e895911220cc9c077efde7d2", page)
        self.assertIn("01921f133de411eed12662818911e76e67c880d878394c7e39e8fd66f78c1e65", page)
        self.assertIn("adp_allow_smtp_send_false", page)
        self.assertIn("REQ-ADP-V7-043-S2PLT02-AUTHORIZATION-READINESS-HASH-GATE", page)
        self.assertIn("S2PLT02-AUTHORIZATION-READINESS-HASH-GATE", page)
        self.assertIn("ADP-S2PLT02-AUTHORIZATION-READINESS-HASH-GATE-20260630.json", page)
        self.assertIn("PHASE_S2PLT02_AUTHORIZATION_READINESS_HASH_GATE.md", page)
        self.assertIn("blocked_s2plt02_authorization_stale_readiness_hash_fail_closed_no_production", page)
        self.assertIn("readiness_state_hash does not match current readiness state", page)
        self.assertIn("authorization_artifact_status=blocked", page)
        self.assertIn("real_proof_capture_authorized=false", page)
        self.assertIn("218cfe1712e9020e02cea37b4f1982c4c959bca29462d6b73e8aec7308e8444c", page)
        self.assertIn("76b9533077ad56d270a70a12b53af80936875795728d7399a48c6af976e37fa2", page)
        self.assertIn("authorization_artifact_status=pass", page)
        self.assertIn("authorization_validation_errors=[]", page)
        self.assertIn("real_proof_capture_authorized=true", page)
        self.assertIn("completed_next_actions=obtain_explicit_owner_authorization_for_real_smtp_scheduler", page)
        self.assertIn("7647b32a4ec17c9687e71238ee0ddf2d184ea666d84982dd77e7f2a2d2e427a9", page)
        self.assertIn(
            "REQ-ADP-V7-041-S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC",
            page,
        )
        self.assertIn("S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-S2PLT04-S2PLT02-LATEST-NONTERMINAL-EVIDENCE-SYNC-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_S2PLT04_S2PLT02_LATEST_NONTERMINAL_EVIDENCE_SYNC.md", page)
        self.assertIn(
            "blocked_s2plt04_s2plt02_latest_nonterminal_evidence_synced_inventory_and_live_auth_no_production",
            page,
        )
        self.assertIn("s2plt02_nonterminal_ref_count=13", page)
        self.assertIn("0cb047a1ae27d990b3a53c082194ee0e15e45e772244ecd74bbf454fbb6f11be", page)
        self.assertIn(
            "REQ-ADP-V7-041-S2PMT07-S2PLT04-NONTERMINAL-SUMMARY-SYNC",
            page,
        )
        self.assertIn("S2PMT07-S2PLT04-NONTERMINAL-SUMMARY-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-S2PLT04-NONTERMINAL-SUMMARY-SYNC-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PMT07_S2PLT04_NONTERMINAL_SUMMARY_SYNC.md", page)
        self.assertIn(
            "blocked_s2plt04_nonterminal_summary_machine_fields_synced_no_production",
            page,
        )
        self.assertIn("s2plt02_nonterminal_ref_count=14", page)
        self.assertIn(
            "s2plt02_latest_nonterminal_ref=governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-LIVE-AUTH-SYNC-20260630.json",
            page,
        )
        self.assertIn("s2plt03_nonterminal_ref_count=4", page)
        self.assertIn(
            "s2plt03_latest_nonterminal_ref=governance/run_manifests/ADP-S2PLT03-AUDIT-BLOCKER-ZERO-PROOF-SYNC-20260629.json",
            page,
        )
        self.assertIn("ee3917fedcd96e10a23fbd228367e6837ffca092734d98288502d9702514165f", page)
        self.assertIn(
            "REQ-ADP-V7-041-S2PLT02-DAILY-RUN-DRY-RUN-TERMINAL-CLASSIFICATION",
            page,
        )
        self.assertIn("S2PLT02-DAILY-RUN-DRY-RUN-TERMINAL-CLASSIFICATION", page)
        self.assertIn(
            "ADP-S2PLT02-DAILY-RUN-DRY-RUN-TERMINAL-CLASSIFICATION-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PLT02_DAILY_RUN_DRY_RUN_TERMINAL_CLASSIFICATION.md", page)
        self.assertIn("daily_run_succeeded_but_smtp_dry_run_not_terminal", page)
        self.assertIn("nonterminal_succeeded_dry_run_service_dates=2026-06-29,2026-06-30", page)
        self.assertIn("nonterminal_succeeded_dry_run_count=2", page)
        self.assertIn("a9179f2a386c23d6efb0495659f434a3991736ce7a10ec6e234659a4e6a0accf", page)
        self.assertIn(
            "REQ-ADP-V7-041-S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY-INPUT-HARDENING",
            page,
        )
        self.assertIn("S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY-INPUT-HARDENING", page)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-PROOF-EVIDENCE-INVENTORY-INPUT-HARDENING-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_PROOF_EVIDENCE_INVENTORY_INPUT_HARDENING.md", page)
        self.assertIn("launchctl_disabled_file_missing", page)
        self.assertIn("launchctl_disabled_file_status=missing", page)
        self.assertIn("b43760c8150155bb0f40e627cdec97443451bfad63e1257b08d1fd572dccda39", page)
        self.assertIn("d2f12b5f3fbe439fdd0b2d420706700f5a0aa6b3d9ba691da67f2ffe4758d117", page)
        self.assertIn(
            "REQ-ADP-V7-042-S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN",
            page,
        )
        self.assertIn("S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN", page)
        self.assertIn(
            "ADP-S2PLT03-TERMINAL-RESILIENCE-PROOF-CAPTURE-PLAN-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PLT03_TERMINAL_RESILIENCE_PROOF_CAPTURE_PLAN.md", page)
        self.assertIn("WAIT_FOR_S2PLT02_TERMINAL_ACCEPTANCE", page)
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT", page)
        self.assertIn("S2PLT03_TERMINAL_RESILIENCE_PROOF_ARTIFACT", page)
        self.assertIn("bd5f74277b41f7e43ec1a907f6d13eee215808e86d04594e03bd4ed71091ddd5", page)
        self.assertIn(
            "blocked_s2plt03_capture_plan_waiting_for_s2plt02_terminal_acceptance_no_production",
            page,
        )
        self.assertIn(
            "REQ-ADP-V7-041-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-LIVE-VALIDATION-SYNC",
            page,
        )
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-LIVE-VALIDATION-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-LIVE-VALIDATION-SYNC-20260630.json",
            page,
        )
        self.assertIn(
            "PHASE_S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_LIVE_VALIDATION_SYNC.md",
            page,
        )
        self.assertIn("assignment_present=true", page)
        self.assertIn("independent_final_reviewer_assigned_by_payload=true", page)
        self.assertIn("codex-subthread-independent-final-reviewer", page)
        self.assertIn("b5b117307bd61f168ae6a422b24c865227f4824191348b851081af66730ed2c2", page)
        self.assertIn("f12f50fe2d474010ab3f93023759872593bdbb3ad65bfbf645287f21a76ef2a3", page)
        self.assertIn("REQ-ADP-V7-041-S2PMT07-FINAL-COMMAND-ROOT-TOOLS", page)
        self.assertIn("S2PMT07-FINAL-COMMAND-ROOT-TOOLS", page)
        self.assertIn("ADP-S2PMT07-FINAL-COMMAND-ROOT-TOOLS-20260629.json", page)
        self.assertIn("blocked_final_command_root_tools_ready_bundle_still_incomplete_no_production", page)
        self.assertIn("[validate_task_pack.py](../../tools/validate_task_pack.py)", page)
        self.assertIn("[verify_acceptance_bundle.py](../../tools/verify_acceptance_bundle.py)", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION", page)
        self.assertIn("S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION", page)
        self.assertIn("ADP-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-20260629.json", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-DRAFT-CLI", page)
        self.assertIn("S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-DRAFT-CLI", page)
        self.assertIn("ADP-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-DRAFT-CLI-RUNTIME-SYNC-20260629.json", page)
        self.assertIn("draft_s2plt02_real_proof_capture_authorization_artifact_cli_runtime_hash_synced_no_write_no_production", page)
        self.assertIn("authorization_artifact_written=false", page)
        self.assertIn("PHASE_S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DRAFT_CLI_RUNTIME_SYNC.md", page)
        runtime_sync_rows = [
            row
            for row in matrix_rows
            if row["task_id"] == "S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-DRAFT-CLI"
        ]
        self.assertEqual(len(runtime_sync_rows), 1)
        self.assertIn(
            "ADP-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-DRAFT-CLI-RUNTIME-SYNC-20260629.json",
            runtime_sync_rows[0]["evidence_ref"],
        )
        self.assertIn(
            "arxiv-daily-push/docs/phase_records/PHASE_S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DRAFT_CLI_RUNTIME_SYNC.md",
            runtime_sync_rows[0]["code_ref"],
        )
        self.assertIn("REQ-ADP-V7-041-S2PLT02-REAL-PROOF-CAPTURE-READINESS-RUNTIME-STATE-SYNC", page)
        self.assertIn("S2PLT02-REAL-PROOF-CAPTURE-READINESS-RUNTIME-STATE-SYNC", page)
        self.assertIn("ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-RUNTIME-STATE-SYNC-20260629.json", page)
        self.assertIn("launchagents_loaded_but_disabled=true", page)
        self.assertIn("launchagents_loaded_but_disabled_not_terminal_scheduler_proof", page)
        self.assertIn("79ac4987239ecad8d4eee82de0157901b59259100e6d738bd1b15d17a37dc76e", page)
        self.assertIn("REQ-ADP-V7-041-S2PMT07-FINAL-BUNDLE-NEXT-EXECUTABLE-COMMAND-SYNC", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-NEXT-EXECUTABLE-COMMAND-SYNC", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-NEXT-EXECUTABLE-COMMAND-SYNC-20260629.json", page)
        self.assertIn("blocked_final_bundle_next_executable_command_synced_no_authorization_no_production", page)
        self.assertIn("next_executable_command=build-s2plt02-real-proof-capture-authorization-artifact-draft", page)
        self.assertIn("next_executable_command_writes_artifact=false", page)
        self.assertIn("next_executable_command_satisfies_gate=false", page)
        self.assertIn("f05b64685d487f28c9ddabb1216e5c67c5c4391ba86e5d5d5341aa398fa9a3a4", page)
        self.assertIn("REQ-ADP-V7-041-S2PMT07-FINAL-BUNDLE-AUTH-DRAFT-LIVE-GUARD", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-AUTH-DRAFT-LIVE-GUARD", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-AUTH-DRAFT-LIVE-GUARD-20260629.json", page)
        self.assertIn("blocked_final_bundle_auth_draft_live_guard_no_authorization_no_production", page)
        self.assertIn("next_executable_command_dry_run_status=pass", page)
        self.assertIn("live_authorization_artifact_status=pass", page)
        self.assertIn("S2PLT02_TERMINAL_DELIVERY_PROOF", page)
        self.assertIn("f05b64685d487f28c9ddabb1216e5c67c5c4391ba86e5d5d5341aa398fa9a3a4", page)
        self.assertIn("REQ-ADP-V7-041-S2PMT07-ZERO-PROOF-READINESS-CONSUMPTION", page)
        self.assertIn("S2PMT07-ZERO-PROOF-READINESS-CONSUMPTION", page)
        self.assertIn("ADP-S2PMT07-ZERO-PROOF-READINESS-CONSUMPTION-20260629.json", page)
        self.assertIn(
            "REQ-ADP-V7-041-S2PMT07-FINAL-BUNDLE-PREREQUISITE-ZERO-PROOF-BLOCKER-SYNC",
            page,
        )
        self.assertIn("S2PMT07-FINAL-BUNDLE-PREREQUISITE-ZERO-PROOF-BLOCKER-SYNC", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-PREREQUISITE-ZERO-PROOF-BLOCKER-SYNC-20260629.json",
            page,
        )
        self.assertIn("blocked_final_bundle_prerequisite_zero_proof_blockers_synced_no_production", page)
        self.assertIn("prerequisite plan 不再重复显示", page)
        self.assertIn("s2plt02_real_proof_capture_authorization_live_ready_terminal_proof_blocked_no_production", page)
        self.assertIn("authorization_artifact_present=true", page)
        self.assertIn("live_authorization_validation_errors=[]", page)
        self.assertIn("sha256:d98242a6c95c6ba62e7e926bf3613e36339d398f70bf9e44b1af1d95794c6c79", page)
        self.assertIn("历史字段：`authorization_artifact_present=false`", page)
        self.assertIn("real_proof_capture_authorized=false", page)
        self.assertIn("real_proof_capture_authorized_by_payload=false", page)
        self.assertIn("real_smtp_send_enabled_by_this_packet=false", page)
        self.assertIn("scheduler_install_enabled_by_this_packet=false", page)
        self.assertIn("terminal_delivery_proof_artifact_written_by_this_packet=false", page)
        self.assertIn("S2PLT02 live authorization", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT", page)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT", page)
        self.assertIn("ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-20260630.json", page)
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT.md", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI", page)
        self.assertIn("S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI", page)
        self.assertIn("ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI-20260630.json", page)
        self.assertIn("PHASE_S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_CLI.md", page)
        self.assertIn("blocked_s2plt02_terminal_capture_window_audit_cli_reproducible_dry_run_scheduler_disabled_no_production", page)
        self.assertIn("6ad683a0590f9d43c808cf7812edc7c7f93feabec52d365ddb2a8abbbf42b4bf", page)
        self.assertIn("dry_run_email_count=8", page)
        self.assertIn("real_sent_candidate_email_count=0", page)
        self.assertIn("terminal_delivery_credit=false", page)
        self.assertIn("counts_toward_s2plt02_terminal_proof=false", page)
        self.assertIn("ADP_ALLOW_SMTP_SEND=false", page)
        self.assertIn("all_required_launchagents_disabled=true", page)
        self.assertIn("1f5abf4e3def35129bc6a360722b10087880dfb49f904d6f9b267cb796d7f8f1", page)
        self.assertIn(
            "REQ-ADP-V7-041-S2PLT02-TERMINAL-DELIVERY-PROOF-ARTIFACT-DRAFT-BUILDER",
            page,
        )
        self.assertIn("S2PLT02-TERMINAL-DELIVERY-PROOF-ARTIFACT-DRAFT-BUILDER", page)
        self.assertIn(
            "ADP-S2PLT02-TERMINAL-DELIVERY-PROOF-ARTIFACT-DRAFT-BUILDER-20260630.json",
            page,
        )
        self.assertIn("PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_DRAFT_BUILDER.md", page)
        self.assertIn("s2plt02_terminal_delivery_proof_artifact_draft_builder_ready_no_write_no_production", page)
        self.assertIn("artifact_written=false", page)
        self.assertIn("artifact_validation_errors=[]", page)
        self.assertIn("beb8f19417b694428749bef5eb01de375ce2321f209c9086dfe4862bf48c2a8b", page)
        self.assertIn("5aa91771f2900db713fb865a12cb69f5c09bd6b03761083337c2d58af13a3b96", page)
        self.assertIn("005e2294441b6aa6e827b0acb8f30916c59cc994768f0562a248a49c9dd6dae7", page)
        self.assertIn("2d9892b750815a0e9540d49dbd2ac65d13dbd8c866651720d1cbf96dd49ffe94", page)
        self.assertIn("PHASE_S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_LIVE.md", page)
        self.assertIn("当前 live 授权状态以上方", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION", page)
        self.assertIn("S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION", page)
        self.assertIn("ADP-S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION-20260630.json", page)
        self.assertIn("ADP-S2PLT02-NORMALIZED-REAL-DELIVERY-MANIFEST-20260628.json", page)
        self.assertIn("PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION.md", page)
        self.assertIn("s2plt02_real_delivery_manifest_normalized_no_write_no_production", page)
        self.assertIn("normalized_manifest_ready=true", page)
        self.assertIn("a795bd90778b5a0bbbd217d286f696936954af47a1a547ed689f907b677d9fa2", page)
        self.assertIn("91bf1a4477c621a75fceed90efecdb620341cfc97d5a751c127cc5ffbd6a0d99", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-REAL-PROOF-CAPTURE-READINESS", page)
        self.assertIn("S2PLT02-REAL-PROOF-CAPTURE-READINESS", page)
        self.assertIn("ADP-S2PLT02-REAL-PROOF-CAPTURE-READINESS-20260629.json", page)
        self.assertIn("blocked_real_proof_capture_readiness_no_authorization_no_production", page)
        self.assertIn("safe_to_collect_terminal_proof=false", page)
        self.assertIn("real_proof_capture_authorized=false", page)
        self.assertIn("all_required_launchagents_disabled=true", page)
        self.assertIn("second_real_delivery_day_present=false", page)
        self.assertIn("terminal_delivery_proof_artifact_present=false", page)
        self.assertIn("real_scheduler_proven=false", page)
        self.assertIn("79ac4987239ecad8d4eee82de0157901b59259100e6d738bd1b15d17a37dc76e", page)
        self.assertIn("PHASE_S2PLT02_REAL_PROOF_CAPTURE_READINESS.md", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-DRY-RUN-SECOND-DAY-AUDIT", page)
        self.assertIn("S2PLT02-DRY-RUN-SECOND-DAY-AUDIT", page)
        self.assertIn("ADP-S2PLT02-DRY-RUN-SECOND-DAY-AUDIT-20260629.json", page)
        self.assertIn("blocked_s2plt02_second_day_dry_run_not_terminal_no_production", page)
        self.assertIn("dry_run_mail_count=4", page)
        self.assertIn("real_sent_mail_count=0", page)
        self.assertIn("observed_natural_days_credit=0", page)
        self.assertIn("observed_email_count_credit=0", page)
        self.assertIn("counts_toward_s2plt02_terminal_proof=false", page)
        self.assertIn("terminal_delivery_credit=false", page)
        self.assertIn("real_smtp_proven=false", page)
        self.assertIn("real_scheduler_proven=false", page)
        self.assertIn("s2plt02_accepted=false", page)
        self.assertIn("9fbd118380da579c2cd47a92e6fe3e54fc89ffd9b76dddb8d3a7199e5821e965", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-TERMINAL-DELIVERY-PROOF-VALIDATOR", page)
        self.assertIn("S2PMT07-S2PLT02-TERMINAL-DELIVERY-PROOF-VALIDATOR", page)
        self.assertIn("ADP-S2PMT07-S2PLT02-TERMINAL-DELIVERY-PROOF-VALIDATOR-20260629.json", page)
        self.assertIn("blocked_s2plt02_terminal_delivery_proof_validator_ready_artifact_missing_no_production", page)
        self.assertIn("artifact_present=false", page)
        self.assertIn("terminal_delivery_proof_ready=false", page)
        self.assertIn("s2plt02_accepted_by_artifact=false", page)
        self.assertIn("s2plt02_terminal_delivery_proof_artifact_missing", page)
        self.assertIn("3fbde96111dd78d3ffe4474e012fa5d86de76a24e6fa7640d0310c178003e1db", page)
        self.assertIn("94bd3841adf70c44e10963ad94da2dd3b57b68152882639ca2637997bdbf1ca1", page)
        self.assertIn("observed_natural_days=1/2", page)
        self.assertIn("observed_email_count=4/8", page)
        self.assertIn("REQ-ADP-V7-040-S2PLT01-TERMINAL-ACCEPTANCE-CONSUMPTION", page)
        self.assertIn("S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-CONSUMPTION", page)
        self.assertIn("ADP-S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-CONSUMPTION-20260629.json", page)
        self.assertIn("s2plt01_terminal_accepted_s2plt04_consumed_still_blocked_s2plt02_s2plt03_no_production", page)
        self.assertIn("artifact_present=true", page)
        self.assertIn("s2plt01_accepted_by_artifact=true", page)
        self.assertIn("510ffaf0c3b9de5cb2398cc9cb2c1ffa652ffe6f7a4026abe3c0484275b5d615", page)
        self.assertIn("47fceec1911e8d2f3b8b43356058d58d22b48eaabf3be174e18292e0c816e7e6", page)
        self.assertIn("49f4ca23db902dcffc554b6dd50204944b9b1d5d86c0eb8dc3e9b8040c17fa35", page)
        self.assertIn("f2307d2d12c3c847ec782802621c0547c8362c56e5e2cfa57b2c9a12253c9e78", page)
        self.assertIn("REQ-ADP-V7-040-S2PLT01-TERMINAL-ACCEPTANCE-ARTIFACT-VALIDATOR", page)
        self.assertIn("S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-ARTIFACT-VALIDATOR", page)
        self.assertIn("ADP-S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-ARTIFACT-VALIDATOR-20260629.json", page)
        self.assertIn("blocked_s2plt01_terminal_acceptance_artifact_validator_missing_artifact_no_production", page)
        self.assertIn("artifact_present=false", page)
        self.assertIn("s2plt01_accepted_by_artifact=false", page)
        self.assertIn("s2plt01_terminal_acceptance_artifact_missing", page)
        self.assertIn("fcd71fb7e6c8f9956edd7fc3e33deadeeb4349183daf0f3950f10df6d8d03431", page)
        self.assertIn("6461557654b36bb383b91eb98bc610c1cf497de8563f7f0aa897db08fc26d315", page)
        self.assertIn("REQ-ADP-V7-039-S2PLT04-COMPLETION-EVIDENCE-LATEST-SYNC", page)
        self.assertIn("S2PMT07-S2PLT04-COMPLETION-EVIDENCE-LATEST-SYNC", page)
        self.assertIn("ADP-S2PMT07-S2PLT04-COMPLETION-EVIDENCE-LATEST-SYNC-20260629.json", page)
        self.assertIn("blocked_s2plt04_completion_evidence_latest_nonterminal_refs_synced_no_report_no_production", page)
        self.assertIn("completion_report_ready=false", page)
        self.assertIn("717822760035bbebe20c429cd2db4e11501e9ebecc2bbc633a04f72de9914c58", page)
        self.assertIn("faedeea7dcc41d0122044cbdd07c1901f01fa6a7ca39f0d580f9f6844fc3f9b2", page)
        self.assertIn("REQ-ADP-V7-042-S2PLT03-AUDIT-BLOCKER-ZERO-PROOF-SYNC", page)
        self.assertIn("S2PLT03-AUDIT-BLOCKER-ZERO-PROOF-SYNC", page)
        self.assertIn("ADP-S2PLT03-AUDIT-BLOCKER-ZERO-PROOF-SYNC-20260629.json", page)
        self.assertIn("blocked_s2plt03_audit_blocker_zero_proof_consistent_s2plt02_not_accepted_no_production", page)
        self.assertIn("audit_blockers.status=pass", page)
        self.assertIn("audit_blockers.checks.P0_zero=true", page)
        self.assertIn("audit_blockers.checks.P1_zero=true", page)
        self.assertIn("3483d4a8c4248d3a41cfae5db4febbe7c9d42368ae6ae9311d0c5a9819d13466", page)
        self.assertIn("d8cdd55b7848c6b7745a0707522f0277c7b7ef2f82e2ca2a0152e5c520211333", page)
        self.assertIn("REQ-ADP-V7-040-S2PLT01-ENTRY-PRECHECK-ZERO-PROOF-SYNC", page)
        self.assertIn("S2PMT07-S2PLT01-ENTRY-PRECHECK-ZERO-PROOF-SYNC", page)
        self.assertIn("ADP-S2PMT07-S2PLT01-ENTRY-PRECHECK-ZERO-PROOF-SYNC-20260629.json", page)
        self.assertIn("blocked_s2plt01_entry_precheck_zero_proof_ready_acceptance_still_missing_no_production", page)
        self.assertIn("current_entry_precheck_zero_proof_readiness.status=pass", page)
        self.assertIn("entry_precheck_passed=true", page)
        self.assertIn("entry_precheck_report_hash=b7c0b96f4cdc570a935680f52dd3804b262ef4898630df8cfadc9ce2796eb55b", page)
        self.assertIn("current_entry_precheck_zero_proof_ready=true", page)
        self.assertIn("REQ-ADP-V7-040-S2PLT01-REPLAY-PAYLOAD-READINESS-SYNC", page)
        self.assertIn("S2PMT07-S2PLT01-REPLAY-PAYLOAD-READINESS-SYNC", page)
        self.assertIn("ADP-S2PMT07-S2PLT01-REPLAY-PAYLOAD-READINESS-SYNC-20260629.json", page)
        self.assertIn("blocked_s2plt01_replay_payload_package_verified_acceptance_still_missing_no_production", page)
        self.assertIn("replay_payload_execution_package_validation.status=pass", page)
        self.assertIn("observed_replay_days=30", page)
        self.assertIn("observed_mail_previews=120", page)
        self.assertIn("source_terminal_states_proven=true", page)
        self.assertIn("future_leakage_count=0", page)
        self.assertIn("p0_p1_blocker_count=0", page)
        self.assertIn("47394faede126c943dc46b3ca2ae0c8680d5ef32f1f26f4618e3064fcbc28171", page)
        self.assertIn("review_receipt_is_nonterminal", page)
        self.assertIn("s2plt01_not_accepted", page)
        self.assertIn("REQ-ADP-V7-040-S2PLT01-ZERO-PROOF-READINESS-SYNC", page)
        self.assertIn("S2PMT07-S2PLT01-ZERO-PROOF-READINESS-SYNC", page)
        self.assertIn("blocked_s2plt01_zero_proof_consumed_terminal_evidence_still_missing_no_production", page)
        self.assertIn("inherited_p0_zero=true", page)
        self.assertIn("inherited_p1_zero=true", page)
        self.assertIn("REQ-ADP-V7-040-S2PLT01-TERMINAL-ACCEPTANCE-DEPENDENCY-ORDER", page)
        self.assertIn("S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-DEPENDENCY-ORDER", page)
        self.assertIn("ADP-S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-DEPENDENCY-ORDER-20260629.json", page)
        self.assertIn("blocked_s2plt01_terminal_acceptance_dependency_order_fixed_no_acceptance_no_production", page)
        self.assertIn("s2plt04_not_completed", page)
        self.assertIn("s2pmt07_not_completed", page)
        self.assertIn("不再是 S2PLT01 terminal readiness blockers", page)
        self.assertIn("REQ-ADP-V7-042-S2PLT03-ZERO-PROOF-RESILIENCE-SYNC", page)
        self.assertIn("S2PLT03-ZERO-PROOF-RESILIENCE-SYNC", page)
        self.assertIn("ADP-S2PLT03-ZERO-PROOF-RESILIENCE-SYNC-20260629.json", page)
        self.assertIn("blocked_s2plt03_zero_proof_consumed_s2plt02_still_not_accepted_no_production", page)
        self.assertIn("audit-s2plt03-resilience-readiness", page)
        self.assertIn("p0_zero=true", page)
        self.assertIn("p1_zero=true", page)
        self.assertIn("s2plt02_not_accepted", page)
        self.assertIn("S2PLT03_ACCEPTED=false", page)
        self.assertIn("S2PLT02-ZERO-PROOF-READINESS-SYNC", page)
        self.assertIn("ADP-S2PLT02-ZERO-PROOF-READINESS-SYNC-20260629.json", page)
        self.assertIn("blocked_s2plt02_zero_proof_consumed_terminal_evidence_still_missing_no_production", page)
        self.assertIn("P0_ZERO=true", page)
        self.assertIn("P1_ZERO=true", page)
        self.assertIn("S2PLT02-TERMINAL-READINESS-AUDIT", page)
        self.assertIn("ADP-S2PLT02-TERMINAL-READINESS-AUDIT-20260629.json", page)
        self.assertIn("blocked_s2plt02_terminal_readiness_audit_m4_ready_no_acceptance", page)
        self.assertIn("m4_watermark_correct=true", page)
        self.assertIn("observed_natural_days=1/2", page)
        self.assertIn("observed_email_count=4/8", page)
        self.assertIn("real_scheduler_not_proven", page)
        self.assertIn("S2PLT02_ACCEPTED=false", page)
        self.assertIn("S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-AUDIT", page)
        self.assertIn("ADP-S2PMT07-S2PLT01-TERMINAL-ACCEPTANCE-AUDIT-20260629.json", page)
        self.assertIn("blocked_terminal_acceptance_audit_s2plt01_nonterminal_no_production", page)
        self.assertIn("terminal_acceptance_ready=false", page)
        self.assertIn("S2PMT07-S2PLT04-COMPLETION-EVIDENCE-AUDIT", page)
        self.assertIn("ADP-S2PMT07-S2PLT04-COMPLETION-EVIDENCE-AUDIT-20260629.json", page)
        self.assertIn("REQ-ADP-LOCAL-DAILY-M1-M4-SEND-ORCHESTRATION", page)
        self.assertIn("LOCAL-DAILY-M1-M4-SEND-ORCHESTRATION", page)
        self.assertIn("PHASE_LOCAL_DAILY_M1_M4_SEND_ORCHESTRATION_20260628.md", page)
        self.assertIn("REQ-ADP-V7-039-GOVERNANCE-CURRENT-STATE-SYNC", page)
        self.assertIn("S2PMT07-GOVERNANCE-CURRENT-STATE-SYNC", page)
        self.assertIn("ADP-S2PMT07-GOVERNANCE-CURRENT-STATE-SYNC-20260628.json", page)
        self.assertIn("REQ-ADP-LOCAL-DAILY-RESEND-REUSE-INPUT", page)
        self.assertIn("LOCAL-DAILY-RESEND-REUSE-INPUT", page)
        self.assertIn("ADP-LOCAL-DAILY-RESEND-REUSE-INPUT-20260628.json", page)
        self.assertIn("REQ-ADP-LOCAL-DAILY-M1-M4-RESEND-EXECUTION", page)
        self.assertIn("LOCAL-DAILY-M1-M4-RESEND-EXECUTION", page)
        self.assertIn("ADP-LOCAL-DAILY-M1-M4-RESEND-EXECUTION-20260628.json", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-ARTIFACT-VALIDATION", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-ARTIFACT-VALIDATION", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-ARTIFACT-VALIDATION-20260628.json", page)
        self.assertIn("blocked_final_bundle_artifact_validation_ready_bundle_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-PARTIAL-REAL-DELIVERY", page)
        self.assertIn("S2PLT02-PARTIAL-REAL-DELIVERY-EVIDENCE", page)
        self.assertIn("ADP-S2PLT02-PARTIAL-REAL-DELIVERY-EVIDENCE-20260628.json", page)
        self.assertIn("blocked_partial_real_delivery_evidence_no_s2plt02_acceptance", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-DELIVERY-LEDGER", page)
        self.assertIn("S2PLT02-DELIVERY-EVIDENCE-LEDGER", page)
        self.assertIn("ADP-S2PLT02-DELIVERY-EVIDENCE-LEDGER-20260628.json", page)
        self.assertIn("blocked_delivery_ledger_partial_no_s2plt02_acceptance", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-M4-WATERMARK-PROOF", page)
        self.assertIn("S2PLT02-M4-WATERMARK-PROOF", page)
        self.assertIn("ADP-S2PLT02-M4-WATERMARK-PROOF-20260628.json", page)
        self.assertIn("blocked_m4_watermark_proof_missing_no_s2plt02_acceptance", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT02-M4-WATERMARK-PROOF-RECORD", page)
        self.assertIn("S2PLT02-M4-WATERMARK-PROOF-RECORD", page)
        self.assertIn("ADP-S2PLT02-M4-WATERMARK-PROOF-RECORD-20260628.json", page)
        self.assertIn("ready_m4_watermark_proof_s2plt02_blocked_no_acceptance", page)
        self.assertIn("REQ-ADP-V7-039-REMAINING-BLOCKER-MATRIX", page)
        self.assertIn("S2PMT07-REMAINING-BLOCKER-MATRIX", page)
        self.assertIn("ADP-S2PMT07-REMAINING-BLOCKER-MATRIX-20260628.json", page)
        self.assertIn("REQ-ADP-V7-039-CLI-MODULE-ENTRYPOINT", page)
        self.assertIn("S2PMT07-CLI-MODULE-ENTRYPOINT", page)
        self.assertIn("ADP-S2PMT07-CLI-MODULE-ENTRYPOINT-20260629.json", page)
        self.assertIn("cli_module_entrypoint_verified_s2plt04_blocked_no_production", page)
        self.assertIn("REQ-ADP-V7-039-S2PLT04-COMPLETION-REPORT-DEPENDENCY-ORDER", page)
        self.assertIn("S2PMT07-S2PLT04-COMPLETION-REPORT-DEPENDENCY-ORDER", page)
        self.assertIn("ADP-S2PMT07-S2PLT04-COMPLETION-REPORT-DEPENDENCY-ORDER-20260629.json", page)
        self.assertIn("completion_report_dependency_order_fixed_s2plt04_still_blocked_no_production", page)
        self.assertIn("blocked_matrix_ready_no_closure", page)
        self.assertIn("REQ-ADP-V7-039-OWNER-NEXT-ACTION-SYNC", page)
        self.assertIn("S2PMT07-OWNER-NEXT-ACTION-SYNC", page)
        self.assertIn("ADP-S2PMT07-OWNER-NEXT-ACTION-SYNC-20260628.json", page)
        self.assertIn("owner_next_action_synced_no_production_no_acceptance", page)
        self.assertIn("REQ-ADP-V7-039-A005-PARAMETER-SELECTOR-ASSURANCE", page)
        self.assertIn("S2PMT07-A005-PARAMETER-SELECTOR-ASSURANCE", page)
        self.assertIn("ADP-S2PMT07-A005-PARAMETER-SELECTOR-ASSURANCE-20260628.json", page)
        self.assertIn("verified_parameter_selector_count_no_production", page)
        self.assertIn("REQ-ADP-V7-039-LOCAL-RUNTIME-NO-PRODUCTION-GATE", page)
        self.assertIn("S2PMT07-LOCAL-RUNTIME-NO-PRODUCTION-GATE", page)
        self.assertIn("ADP-S2PMT07-LOCAL-RUNTIME-NO-PRODUCTION-GATE-20260628.json", page)
        self.assertIn("local_runtime_no_production_gate_verified_no_scheduler_no_smtp_no_acceptance", page)
        self.assertIn("REQ-ADP-V7-039-NO-PRODUCTION-ATTESTATION-ARTIFACT", page)
        self.assertIn("S2PMT07-NO-PRODUCTION-ATTESTATION-ARTIFACT", page)
        self.assertIn("no_production_side_effects.json", page)
        self.assertIn("ADP-S2PMT07-NO-PRODUCTION-ATTESTATION-ARTIFACT-20260628.json", page)
        self.assertIn("no_production_attestation_artifact_validated_final_bundle_still_blocked", page)
        self.assertIn("REQ-ADP-V7-039-NO-PRODUCTION-ATTESTATION-READINESS-SYNC", page)
        self.assertIn("S2PMT07-NO-PRODUCTION-ATTESTATION-READINESS-SYNC", page)
        self.assertIn("PHASE_S2PMT07_NO_PRODUCTION_ATTESTATION_READINESS_SYNC.md", page)
        self.assertIn("ADP-S2PMT07-NO-PRODUCTION-ATTESTATION-READINESS-SYNC-20260628.json", page)
        self.assertIn("no_production_attestation_readiness_sync_final_bundle_still_blocked", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-COMMITTED-ARTIFACT-CONSUMPTION", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-COMMITTED-ARTIFACT-CONSUMPTION", page)
        self.assertIn("PHASE_S2PMT07_FINAL_BUNDLE_COMMITTED_ARTIFACT_CONSUMPTION.md", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-COMMITTED-ARTIFACT-CONSUMPTION-20260628.json", page)
        self.assertIn("committed_artifact_consumption_ready_final_bundle_still_blocked", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-TEMPLATES", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-TEMPLATES", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-TEMPLATES-20260628.json", page)
        self.assertIn("templates_ready_final_bundle_still_blocked_no_production", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-INTAKE", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-INTAKE", page)
        self.assertIn(
            "ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-INTAKE-20260628.json",
            page,
        )
        self.assertIn("assignment_artifact_intake_ready_artifact_missing_final_bundle_still_blocked", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-ASSIGNMENT-REQUIRED-ITEM", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-ASSIGNMENT-REQUIRED-ITEM", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-ASSIGNMENT-REQUIRED-ITEM-20260628.json", page)
        self.assertIn("assignment_required_item_blocks_directory_validation_without_artifact", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-CLI-VALIDATOR", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-CLI-VALIDATOR", page)
        self.assertIn(
            "ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-CLI-VALIDATOR-20260628.json",
            page,
        )
        self.assertIn("blocked_reviewer_assignment_cli_validator_ready_artifact_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-OWNER-PACKET-CLI", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-OWNER-PACKET-CLI", page)
        self.assertIn(
            "ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-OWNER-PACKET-CLI-20260628.json",
            page,
        )
        self.assertIn("blocked_owner_packet_cli_ready_no_assignment_no_production", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-PLACEHOLDER-GATE", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-PLACEHOLDER-GATE", page)
        self.assertIn(
            "ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-PLACEHOLDER-GATE-20260628.json",
            page,
        )
        self.assertIn("assignment_placeholder_gate_ready_artifact_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-TEMPLATE-PLACEHOLDER-GATE", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-TEMPLATE-PLACEHOLDER-GATE", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-BUNDLE-TEMPLATE-PLACEHOLDER-GATE-20260628.json",
            page,
        )
        self.assertIn("final_bundle_template_placeholder_gate_ready_artifacts_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-READINESS-CLI", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-READINESS-CLI", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-READINESS-CLI-20260628.json", page)
        self.assertIn("blocked_final_bundle_readiness_cli_ready_artifacts_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-CLOSURE-DECISION-OWNER-PACKET-CLI", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-CLOSURE-DECISION-OWNER-PACKET-CLI", page)
        self.assertIn(
            "ADP-S2PMT07-INDEPENDENT-FINAL-CLOSURE-DECISION-OWNER-PACKET-CLI-20260628.json",
            page,
        )
        self.assertIn("blocked_closure_decision_owner_packet_cli_ready_no_closure_no_production", page)
        self.assertIn("REQ-ADP-V7-039-P0-P1-ZERO-PROOF-CLI-VALIDATOR", page)
        self.assertIn("S2PMT07-P0-P1-ZERO-PROOF-CLI-VALIDATOR", page)
        self.assertIn(
            "ADP-S2PMT07-P0-P1-ZERO-PROOF-CLI-VALIDATOR-20260628.json",
            page,
        )
        self.assertIn("blocked_zero_proof_cli_validator_ready_artifact_missing_no_production", page)
        self.assertIn("validate-p0-p1-zero-proof", page)
        self.assertIn("artifact_present=true", page)
        self.assertIn("p0_zero_proven_by_payload=true", page)
        self.assertIn("p1_zero_proven_by_payload=true", page)
        self.assertNotIn('validation_errors=["p0_p1_zero_proof_artifact_missing"]', page)
        self.assertIn("REQ-ADP-V7-039-REMAINING-FINAL-BUNDLE-ARTIFACT-CLI-VALIDATORS", page)
        self.assertIn("S2PMT07-REMAINING-FINAL-BUNDLE-ARTIFACT-CLI-VALIDATORS", page)
        self.assertIn("validate-final-bundle-manifest", page)
        self.assertIn("validate-s2plt04-completion-report", page)
        self.assertIn("validate-no-production-attestation", page)
        self.assertIn("validate-next-agent-handoff", page)
        self.assertIn("ADP-S2PMT07-REMAINING-FINAL-BUNDLE-ARTIFACT-CLI-VALIDATORS-20260628.json", page)
        self.assertIn("blocked_remaining_final_bundle_artifact_cli_validators_ready_artifacts_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-PREREQUISITE-PLAN-CLI", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-PREREQUISITE-PLAN-CLI", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-PREREQUISITE-PLAN-CLI-20260629.json", page)
        self.assertIn("blocked_final_bundle_prerequisite_plan_cli_ready_no_artifacts_no_production", page)
        self.assertIn("plan-final-bundle-prerequisites", page)
        self.assertIn("INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION", page)
        self.assertIn("NO_PRODUCTION_SIDE_EFFECT_ATTESTATION=pass", page)
        self.assertIn("ready_for_final_bundle_manifest=false", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-DRAFT-CLI", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-DRAFT-CLI", page)
        self.assertIn(
            "ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-DRAFT-CLI-20260629.json",
            page,
        )
        self.assertIn("blocked_assignment_artifact_draft_cli_ready_no_assignment_no_production", page)
        self.assertIn("build-final-reviewer-assignment-artifact-draft", page)
        self.assertIn("assignment_artifact_written=false", page)
        self.assertIn("assignment_gate_satisfied_by_this_command=false", page)
        self.assertIn("independent_final_reviewer_assigned_by_this_command=false", page)
        self.assertIn("validation_errors=[]", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-COMMAND-EXECUTION-CLI-VALIDATOR", page)
        self.assertIn("S2PMT07-FINAL-COMMAND-EXECUTION-CLI-VALIDATOR", page)
        self.assertIn(
            "ADP-S2PMT07-FINAL-COMMAND-EXECUTION-CLI-VALIDATOR-20260628.json",
            page,
        )
        self.assertIn("blocked_final_command_execution_cli_validator_ready_artifact_missing_no_production", page)
        self.assertIn("validate-final-command-execution", page)
        self.assertIn("final_command_execution_missing", page)
        self.assertIn("build-final-closure-decision-owner-packet", page)
        self.assertIn("independent_final_closure_decision_present=false", page)
        self.assertIn("REPLACE_WITH", page)
        self.assertIn("RECOMPUTE_WITH", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-HARD-GATE", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-HARD-GATE", page)
        self.assertIn("ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-HARD-GATE-20260628.json", page)
        self.assertIn("assignment_hard_gate_blocks_final_bundle_without_artifact", page)
        self.assertIn("REQ-ADP-V7-041-S2PJT02-S2PJT03-OWNER-SNAPSHOT-SUMMARY-SYNC", page)
        self.assertIn("S2PJT02-S2PJT03-OWNER-SNAPSHOT-SUMMARY-SYNC", page)
        self.assertIn("ADP-S2PJT02-S2PJT03-OWNER-SNAPSHOT-SUMMARY-SYNC-20260628.json", page)
        self.assertIn("owner_snapshot_summary_synced_no_production_no_acceptance", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-OWNER-PACKET", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-OWNER-PACKET", page)
        self.assertIn("ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-OWNER-PACKET-20260628.json", page)
        self.assertIn("blocked_owner_action_packet_ready_no_assignment_no_production", page)
        self.assertIn("当前 7 个 S2PMT07 blocker 已映射到所需证据", page)
        self.assertIn("REQ-ADP-V7-039-P1-A006-A009-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-A006-A009-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-A006-A009-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P1-A010-A016-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-A010-A016-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-A010-A016-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-P1-ZERO-PROOF-READINESS", page)
        self.assertIn("S2PMT07-P0-P1-ZERO-PROOF-READINESS", page)
        self.assertIn("ADP-S2PMT07-P0-P1-ZERO-PROOF-READINESS-20260628.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-P1-ZERO-PROOF-VALIDATOR", page)
        self.assertIn("S2PMT07-P0-P1-ZERO-PROOF-VALIDATOR", page)
        self.assertIn("ADP-S2PMT07-P0-P1-ZERO-PROOF-VALIDATOR-20260628.json", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-MANIFEST-VALIDATOR", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-MANIFEST-VALIDATOR", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-MANIFEST-VALIDATOR-20260628.json", page)
        self.assertIn("blocked_manifest_validator_ready_manifest_missing_no_closure_no_production", page)
        self.assertIn("REQ-ADP-V7-039-S2PLT04-COMPLETION-REPORT-VALIDATOR", page)
        self.assertIn("S2PMT07-S2PLT04-COMPLETION-REPORT-VALIDATOR", page)
        self.assertIn("ADP-S2PMT07-S2PLT04-COMPLETION-REPORT-VALIDATOR-20260628.json", page)
        self.assertIn("blocked_s2plt04_completion_report_validator_ready_report_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-P1-A017-A019-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-A017-A019-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-A017-A019-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P1-A018-A021-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-A018-A021-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-A018-A021-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-040-P1-B002-B004-B005-B015-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-B002-B004-B005-B015-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-B002-B004-B005-B015-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-040-P1-B003-B011-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-B003-B011-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-B003-B011-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-040-P1-B006-B009-B010-B012-B013-B014-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-B006-B009-B010-B012-B013-B014-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-B006-B009-B010-B012-B013-B014-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P1-A020-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-A020-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-A020-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-040-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-C001-C003-C005-C006-C007-C010-C011-C012-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-040-P1-C002-TECH-REVIEW", page)
        self.assertIn("S2PMT07-P1-C002-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-P1-C002-TECHNICAL-REVIEW-20260628.json", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-READINESS", page)
        self.assertIn("S2PMT07-FINAL-ACCEPTANCE-BUNDLE-READINESS", page)
        self.assertIn("PHASE_S2PMT07_FINAL_ACCEPTANCE_BUNDLE_READINESS.md", page)
        self.assertIn("ADP-S2PMT07-FINAL-ACCEPTANCE-BUNDLE-READINESS-20260628.json", page)
        self.assertIn("REQ-ADP-V7-039-NO-PRODUCTION-ATTESTATION-VALIDATOR", page)
        self.assertIn("S2PMT07-NO-PRODUCTION-SIDE-EFFECT-ATTESTATION-VALIDATOR", page)
        self.assertIn("ADP-S2PMT07-NO-PRODUCTION-SIDE-EFFECT-ATTESTATION-VALIDATOR-20260628.json", page)
        self.assertIn("blocked_no_production_attestation_validator_ready_artifact_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-NEXT-AGENT-HANDOFF-VALIDATOR", page)
        self.assertIn("S2PMT07-NEXT-AGENT-HANDOFF-VALIDATOR", page)
        self.assertIn("ADP-S2PMT07-NEXT-AGENT-HANDOFF-VALIDATOR-20260628.json", page)
        self.assertIn("blocked_next_agent_handoff_validator_ready_artifact_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-FINAL-BUNDLE-PREREQUISITE-PLAN", page)
        self.assertIn("S2PMT07-FINAL-BUNDLE-PREREQUISITE-PLAN", page)
        self.assertIn("ADP-S2PMT07-FINAL-BUNDLE-PREREQUISITE-PLAN-20260628.json", page)
        self.assertIn("blocked_prerequisite_plan_ready_no_production", page)
        self.assertIn("REQ-ADP-V7-039-P0-P1-ZERO-PROOF-ASSEMBLY", page)
        self.assertIn("S2PMT07-P0-P1-ZERO-PROOF-ASSEMBLY", page)
        self.assertIn("ADP-S2PMT07-P0-P1-ZERO-PROOF-ASSEMBLY-20260628.json", page)
        self.assertIn("blocked_zero_proof_assembly_ready_no_closure_no_production", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-CLOSURE-DECISION-REQUEST", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-CLOSURE-DECISION-REQUEST", page)
        self.assertIn("ADP-S2PMT07-INDEPENDENT-FINAL-CLOSURE-DECISION-REQUEST-20260628.json", page)
        self.assertIn("blocked_decision_request_ready_no_closure_no_production", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-REQUEST", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-REQUEST", page)
        self.assertIn("ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-REQUEST-20260628.json", page)
        self.assertIn("blocked_reviewer_assignment_request_ready_no_assignment_no_production", page)
        self.assertIn("REQ-ADP-V7-039-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-VALIDATOR", page)
        self.assertIn("S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-VALIDATOR", page)
        self.assertIn("ADP-S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-VALIDATOR-20260628.json", page)
        self.assertIn("blocked_reviewer_assignment_artifact_validator_ready_artifact_missing_no_production", page)
        self.assertIn("REQ-ADP-V7-039-MAINLINE-ATTESTATION", page)
        self.assertIn("S2PMT07-MAINLINE-ATTESTATION", page)
        self.assertIn("ADP-S2PMT07-MAINLINE-ATTESTATION-20260628.json", page)
        self.assertIn("mainline_attested_no_production_no_acceptance", page)
        self.assertIn("REQ-ADP-V7-040-S2PLT01-REVIEW-SYNC", page)
        self.assertIn("S2PLT01-REPLAY-REVIEW-STATUS-SYNC", page)
        self.assertIn("PHASE_S2PLT01_REPLAY_REVIEW_STATUS_SYNC.md", page)
        self.assertIn("ADP-S2PLT01-REPLAY-REVIEW-STATUS-SYNC-20260628.json", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT03-PRECHECK", page)
        self.assertIn("S2PLT03", page)
        self.assertIn("ACC-S2PLT03-RESILIENCE", page)
        self.assertIn("PHASE_S2PLT03_RESILIENCE_PRECHECK.md", page)
        self.assertIn("REQ-ADP-V7-041-S2PLT03-LOCAL-DRILL", page)
        self.assertIn("S2PLT03-LOCAL-RESILIENCE-DRILL", page)
        self.assertIn("PHASE_S2PLT03_LOCAL_RESILIENCE_DRILL.md", page)
        self.assertIn("local_drill_passed_no_production_precheck_blocked", page)
        self.assertIn("REQ-ADP-V7-043-S2PLT04-S2PLT02-PRECHECK-SYNC", page)
        self.assertIn("S2PLT04-S2PLT02-PRECHECK-EVIDENCE-SYNC", page)
        self.assertIn("PHASE_S2PLT04_S2PLT02_PRECHECK_EVIDENCE_SYNC.md", page)
        self.assertIn("blocked_precheck_nonterminal_s2plt02_readiness_evidence_consumed_no_production", page)
        self.assertIn("REQ-ADP-V7-043-S2PLT04-S2PLT01-REVIEW-SYNC", page)
        self.assertIn("S2PLT04-S2PLT01-REPLAY-REVIEW-EVIDENCE-SYNC", page)
        self.assertIn("S2PLT04-STATE-CONTENT-EVIDENCE-BUNDLE-SYNC", page)
        self.assertIn("REQ-ADP-V7-043-S2PLT04-FINAL-BUNDLE-READINESS-SYNC", page)
        self.assertIn("S2PLT04-FINAL-BUNDLE-READINESS-SYNC", page)
        self.assertIn("PHASE_S2PLT04_FINAL_BUNDLE_READINESS_SYNC.md", page)
        self.assertIn("blocked_precheck_final_bundle_readiness_detail_bound_no_production", page)
        self.assertIn("REQ-ADP-V7-039-P0-P1-CANDIDATE-READINESS", page)
        self.assertIn("S2PMT07-P0-P1-TECHNICAL-CANDIDATE-READINESS", page)
        self.assertIn("ADP-S2PMT07-P0-P1-TECHNICAL-CANDIDATE-READINESS-20260628.json", page)
        self.assertIn("blocked_candidate_ready_no_closure_no_production", page)
        self.assertIn("PHASE_S2PLT04_S2PLT01_REPLAY_REVIEW_EVIDENCE_SYNC.md", page)
        self.assertIn("blocked_precheck_nonterminal_s2plt01_replay_review_evidence_consumed_no_production", page)
        self.assertIn("S2PLT02 现在记录 1 天 / 4 封 ledger evidence", page)
        self.assertIn("2026-06-28 显式 M4 水印 proof record 已就绪", page)
        self.assertIn("第二天真实 SMTP、8 封总数、scheduler proof", page)
        self.assertIn("integrated production acceptance 仍未通过", page)
        self.assertIn("REQ-ADP-V7-039-P0-CLOSURE-PACKAGE", page)
        self.assertIn("S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE", page)
        self.assertIn("ADP-S2PMT07-P0-TECHNICAL-CLOSURE-CANDIDATE-PACKAGE-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-B008-REVIEW", page)
        self.assertIn("S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-B008-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-B007-REVIEW", page)
        self.assertIn("S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-B007-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-A005-REVIEW", page)
        self.assertIn("S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-A005-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-A004-REVIEW", page)
        self.assertIn("S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-A004-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-A003-REVIEW", page)
        self.assertIn("S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-A002-REVIEW", page)
        self.assertIn("S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW", page)
        self.assertIn("ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-B007-MULTIPROCESS", page)
        self.assertIn("S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE", page)
        self.assertIn("ADP-S2PMT07-B007-MULTIPROCESS-RACE-EVIDENCE-20260627.json", page)
        self.assertIn("REQ-ADP-V7-039-P0-B008-FAKE-SMTP", page)
        self.assertIn("S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE", page)
        self.assertIn("ADP-S2PMT07-B008-FAKE-SMTP-CRASH-WINDOW-EVIDENCE-20260627.json", page)
        self.assertNotIn("/Users/", page)
        self.assertNotIn("file://", page)
        self.assertIn("[功能任务测试证据追踪链](./功能任务测试证据追踪链.md)", readme)

    def test_legacy_mail_scan_page_exposes_c011_current_evidence(self):
        page = LEGACY_MAIL_SCAN_PAGE.read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertTrue(page.startswith("# 旧邮件标识兼容扫描\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertIn("C-011", page)
        self.assertIn("活跃旧邮件运行命中 | 0", page)
        self.assertIn("活跃旧用户页面命中 | 0", page)
        self.assertIn("未分类命中 | 0", page)
        self.assertIn("`EMAIL_LEARNING_V1`", page)
        self.assertIn("`M1, M2, M3, M4`", page)
        self.assertIn("[C-011 运行清单](../../governance/run_manifests/ADP-S2PAT05-LEGACY-MAIL-SCAN-C011-20260627.json)", page)
        self.assertIn("[C-011 阶段记录](../docs/phase_records/PHASE_S2PAT05_LEGACY_MAIL_SCAN_C011.md)", page)
        self.assertIn("[P1 复审 receipt](../docs/phase_records/PHASE_S2PMT07_P1_INDEPENDENT_REVIEW_RECEIPT.md)", page)
        self.assertIn("[Focused tests](../tests/test_stage2_sources.py)", page)
        self.assertNotIn("/Users/", page)
        self.assertNotIn("file://", page)
        self.assertIn("[旧邮件标识兼容扫描](./旧邮件标识兼容扫描.md)", readme)

    def test_restore_path_safety_page_exposes_a001_current_evidence(self):
        page = RESTORE_PATH_SAFETY_PAGE.read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertTrue(page.startswith("# 恢复路径安全扫描\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertIn("P0 `A-001`", page)
        self.assertIn("相对路径穿越 | 已阻断", page)
        self.assertIn("绝对路径逃逸 | 已阻断", page)
        self.assertIn("符号链接逃逸 | 已阻断", page)
        self.assertIn("阻断时保留原目标库 | 已验证", page)
        self.assertIn("独立技术复审 | `PASS_WITH_NO_PRODUCTION_ACCEPTANCE` / 技术关闭候选", page)
        self.assertIn("[A-001 运行清单](../../governance/run_manifests/ADP-S2PMT02-RESTORE-PATH-SAFETY-A001-20260627.json)", page)
        self.assertIn(
            "[A-001 独立技术复审 receipt](../../governance/run_manifests/ADP-S2PMT07-A001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json)",
            page,
        )
        self.assertIn("[A-001 阶段记录](../docs/phase_records/PHASE_S2PMT02_RESTORE_PATH_SAFETY_A001.md)", page)
        self.assertIn("[P0 复审 receipt](../docs/phase_records/PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md)", page)
        self.assertNotIn("/Users/", page)
        self.assertNotIn("file://", page)
        self.assertIn("[恢复路径安全扫描](./恢复路径安全扫描.md)", readme)

    def test_restore_atomic_replacement_page_exposes_a002_current_evidence(self):
        page = RESTORE_ATOMIC_REPLACEMENT_PAGE.read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertTrue(page.startswith("# 恢复原子替换扫描\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertIn("P0 `A-002`", page)
        self.assertIn("新目标有效恢复 | 已验证", page)
        self.assertIn("覆盖恢复保留旧目标备份 | 已验证", page)
        self.assertIn("无效覆盖恢复保留原目标 | 已验证", page)
        self.assertIn("临时恢复文件残留 | 0", page)
        self.assertIn("独立技术复审 | `PASS_WITH_NO_PRODUCTION_ACCEPTANCE` / 技术关闭候选", page)
        self.assertIn(
            "[A-002 独立技术复审 receipt](../../governance/run_manifests/ADP-S2PMT07-A002-INDEPENDENT-TECHNICAL-REVIEW-20260627.json)",
            page,
        )
        self.assertIn(
            "[A-002 运行清单](../../governance/run_manifests/ADP-S2PMT02-RESTORE-ATOMIC-REPLACEMENT-A002-20260627.json)",
            page,
        )
        self.assertIn("[A-002 阶段记录](../docs/phase_records/PHASE_S2PMT02_RESTORE_ATOMIC_REPLACEMENT_A002.md)", page)
        self.assertIn("[P0 复审 receipt](../docs/phase_records/PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md)", page)
        self.assertNotIn("/Users/", page)
        self.assertNotIn("file://", page)
        self.assertIn("[恢复原子替换扫描](./恢复原子替换扫描.md)", readme)

    def test_outbox_delivery_page_exposes_a003_current_evidence(self):
        page = OUTBOX_DELIVERY_PAGE.read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertTrue(page.startswith("# 事务发件箱与消息ID扫描\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertIn("P0 `A-003`", page)
        self.assertIn("同 revision 消息 ID 稳定 | 已验证", page)
        self.assertIn("内容修订后消息 ID 变化 | 已验证", page)
        self.assertIn("同一发件箱记录 100 次 claim | 1 成功 / 99 阻断", page)
        self.assertIn("SMTP accepted-before-commit 无 provider ref | fail-closed", page)
        self.assertIn("fail-closed 后不可重 claim | 已验证", page)
        self.assertIn("Provider accept ref 后本地 finalize | 已验证", page)
        self.assertIn("finalize 后不可重 claim | 已验证", page)
        self.assertIn("独立技术复审 | `PASS_WITH_NO_PRODUCTION_ACCEPTANCE` / 技术关闭候选", page)
        self.assertIn("`at_least_once_with_idempotent_message_id`", page)
        self.assertIn("exactly-once 声明 | `false`", page)
        self.assertIn("真实 SMTP 发送 | `false`", page)
        self.assertIn("`fail_closed_not_retry_safe_not_reclaimed`", page)
        self.assertIn("`provider_finalized_not_reclaimed`", page)
        self.assertIn(
            "[A-003 运行清单](../../governance/run_manifests/ADP-S2PMT03-OUTBOX-DELIVERY-A003-20260627.json)",
            page,
        )
        self.assertIn(
            "[A-003 独立技术复审 receipt](../../governance/run_manifests/ADP-S2PMT07-A003-INDEPENDENT-TECHNICAL-REVIEW-20260627.json)",
            page,
        )
        self.assertIn("[A-003 阶段记录](../docs/phase_records/PHASE_S2PMT03_OUTBOX_DELIVERY_A003.md)", page)
        self.assertIn("[P0 复审 receipt](../docs/phase_records/PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md)", page)
        self.assertIn("[聚焦测试](../tests/test_stage2_lease_fencing.py)", page)
        self.assertNotIn("/Users/", page)
        self.assertNotIn("file://", page)
        self.assertIn("[事务发件箱与消息ID扫描](./事务发件箱与消息ID扫描.md)", readme)

    def test_frontstage_evidence_page_exposes_a004_current_evidence(self):
        page = FRONTSTAGE_EVIDENCE_PAGE.read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertTrue(page.startswith("# 前台陈述证据绑定扫描\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertIn("P0 `A-004`", page)
        self.assertIn("fact 必须绑定 claim 与 evidence", page)
        self.assertIn("inference 必须绑定 premise、reasoning version、confidence", page)
        self.assertIn("action 必须绑定 premise 与 action scope", page)
        self.assertIn("unknown claim reference | fail-closed", page)
        self.assertIn("unsupported foreground claim | fail-closed", page)
        self.assertIn("真实 SMTP 发送 | `false`", page)
        self.assertIn("P0 关闭声明 | `false`", page)
        self.assertIn(
            "[A-004 运行清单](../../governance/run_manifests/ADP-S2PMT01-FRONTSTAGE-EVIDENCE-A004-20260627.json)",
            page,
        )
        self.assertIn("[A-004 阶段记录](../docs/phase_records/PHASE_S2PMT01_FRONTSTAGE_EVIDENCE_A004.md)", page)
        self.assertIn("[聚焦测试](../tests/test_security_boundary.py)", page)
        self.assertNotIn("/Users/", page)
        self.assertNotIn("file://", page)
        self.assertIn("[前台陈述证据绑定扫描](./前台陈述证据绑定扫描.md)", readme)

    def test_trust_boundary_page_exposes_a005_current_evidence(self):
        page = TRUST_BOUNDARY_PAGE.read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertTrue(page.startswith("# 来源信任边界扫描\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertIn("P0 `A-005`", page)
        self.assertIn("来源内容标签 | `UNTRUSTED_DATA`", page)
        self.assertIn("unsafe URL scheme | fail-closed", page)
        self.assertIn("unapproved host | fail-closed", page)
        self.assertIn("来源内容请求工具 | fail-closed", page)
        self.assertIn("密钥读取 | fail-closed", page)
        self.assertIn("仓库写入 | fail-closed", page)
        self.assertIn("邮件发送 | fail-closed", page)
        self.assertIn("真实 SMTP 发送 | `false`", page)
        self.assertIn("P0 关闭声明 | `false`", page)
        self.assertIn(
            "[A-005 运行清单](../../governance/run_manifests/ADP-S2PMT01-TRUST-BOUNDARY-A005-20260627.json)",
            page,
        )
        self.assertIn("[A-005 阶段记录](../docs/phase_records/PHASE_S2PMT01_TRUST_BOUNDARY_A005.md)", page)
        self.assertIn("[聚焦测试](../tests/test_security_boundary.py)", page)
        self.assertNotIn("/Users/", page)
        self.assertNotIn("file://", page)
        self.assertIn("[来源信任边界扫描](./来源信任边界扫描.md)", readme)

    def test_install_lifecycle_page_exposes_b001_current_evidence(self):
        page = B001_INSTALL_LIFECYCLE_PAGE.read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertTrue(page.startswith("# 自动唤醒安装生命周期扫描\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertIn("P0 `B-001`", page)
        self.assertIn("安装 / 状态 / 触发探针 / 卸载", page)
        self.assertIn("真实隔离触发证明 | 已记录外部 proof / 待独立复审", page)
        self.assertIn("独立技术复审 | `PASS_WITH_NO_PRODUCTION_ACCEPTANCE` / 技术关闭候选", page)
        self.assertIn("launchd bootstrap | 已在 isolated label 执行 / 生产 label 未触碰", page)
        self.assertIn("scheduler 启用 | `false`", page)
        self.assertIn("真实 SMTP 发送 | `false`", page)
        self.assertIn("P0 关闭声明 | `false`", page)
        self.assertIn(
            "[B-001 运行清单](../../governance/run_manifests/ADP-S2PMT04-INSTALL-LIFECYCLE-B001-20260627.json)",
            page,
        )
        self.assertIn(
            "[B-001 isolated proof reconciliation](../../governance/run_manifests/ADP-S2PMT07-B001-ISOLATED-PROOF-RECONCILIATION-20260627.json)",
            page,
        )
        self.assertIn(
            "[B-001 独立技术复审 receipt](../../governance/run_manifests/ADP-S2PMT07-B001-INDEPENDENT-TECHNICAL-REVIEW-20260627.json)",
            page,
        )
        self.assertIn("[B-001 阶段记录](../docs/phase_records/PHASE_S2PMT04_INSTALL_LIFECYCLE_B001.md)", page)
        self.assertIn("[P0 复审 receipt](../docs/phase_records/PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md)", page)
        self.assertIn("[聚焦测试](../tests/test_stage2_lifecycle_cache.py)", page)
        self.assertNotIn("/Users/", page)
        self.assertNotIn("file://", page)
        self.assertIn("[自动唤醒安装生命周期扫描](./自动唤醒安装生命周期扫描.md)", readme)

    def test_user_center_pages_keep_chinese_facing_labels(self):
        forbidden = (
            "| Rank |",
            "Code/category",
            "UI/UX",
            "owner 快速浏览",
            "owner 页面",
            "解释=report_generated",
            "解释=not_generated",
            "rank 和证据",
            "rank 和 score",
        )
        for path in sorted(USER_CENTER.glob("*.md")):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)
        candidate_page = CANDIDATE_POOL_PAGE.read_text(encoding="utf-8")
        self.assertIn("| 序号 | 领域代码 | 标题 / 条目 | 状态 | 分数 | 候选日期 / 截至时间 | 证据 |", candidate_page)
        self.assertNotIn("| 序号 | 领域代码 | 标题 / 条目 | 状态 | 分数 | Rank |", candidate_page)

    def test_summary_pages_do_not_treat_11_item_queue_as_total_pool(self):
        forbidden = (
            "当前展示候选",
            "当前展示 11 条",
            "11 条高价值候选",
            "页面展示 11 条",
            "下表只列当前展示的 11 条",
            "全量内容记录",
            "内容记录全量",
            "当前运行队列",
        )
        for path in SUMMARY_PAGES:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)
                self.assertIn("[截至今日候选池](./截至今日候选池.md)", text)
                self.assertIn("候选队列前20精选", text)

    def test_mvp_prep_entry_is_visible_from_owner_first_paths_without_s3_enablement(self):
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")
        one_look = (USER_CENTER / "一看三查.md").read_text(encoding="utf-8")
        decisions = (USER_CENTER / "关键结论与用户决策.md").read_text(encoding="utf-8")
        roadmap = (USER_CENTER / "路线图与停止门.md").read_text(encoding="utf-8")
        mvp = (USER_CENTER / "MVP准备与复审修补.md").read_text(encoding="utf-8")
        mail_status = (USER_CENTER / "邮件发送与队列状态.md").read_text(encoding="utf-8")
        candidate_pool = CANDIDATE_POOL_PAGE.read_text(encoding="utf-8")

        for text in (readme, one_look, decisions, roadmap):
            self.assertIn("[MVP 准备与复审修补](./MVP准备与复审修补.md)", text)
        self.assertIn("Stage 2 最终门 | 已通过 Stage 2 integrated acceptance", one_look)
        self.assertIn("S3 / DAILY_OPERATION | 不进入；保持禁用", one_look)
        self.assertIn("宣称 S3/DAILY_OPERATION 已进入 | 不可以", one_look)
        self.assertIn("Stage 2 integrated acceptance | 已记录并保持 `true`", decisions)
        self.assertIn("是否现在宣称 Stage 2 integrated acceptance 已记录 | 接受", decisions)
        self.assertIn("是否现在宣称 S3/DAILY_OPERATION 已进入 | 不接受", decisions)
        self.assertIn("Stage 2 integrated acceptance | `stage2_integrated_production_accepted=true`", roadmap)
        self.assertIn("DAILY_OPERATION | `daily_operation_enabled=false`", roadmap)
        self.assertIn("Stage 2 integrated acceptance | 已记录并保持 `true`", readme)
        self.assertIn("这不代表 S3/DAILY_OPERATION 已进入", readme)
        self.assertIn("当前不进入 S3/DAILY_OPERATION", one_look)
        self.assertIn("不进入 S3/DAILY_OPERATION", mvp)
        self.assertNotIn("Stage 2 最终门 | 未通过", one_look)
        self.assertNotIn("不能宣称正式生产验收完成", one_look)
        self.assertNotIn("Stage 2 是否正式生产通过 | 没有", readme)
        for text in (readme, one_look, decisions, mail_status, candidate_pool):
            self.assertNotIn("这不是 Stage 2 生产验收通过声明", text)
            self.assertNotIn("Stage 2 生产验收通过", text)
            self.assertNotIn("| Stage 2 | 尚未正式生产通过 |", text)
            self.assertNotIn("是否现在宣称 Stage 2 生产通过 | 不接受", text)
            self.assertNotIn("Final bundle 已公开 S2PLT03 capture plan summary，但它仍 blocked", text)

    def test_user_center_exposes_board_data_source_catalog(self):
        controls = load_owner_controls(CONTROLS)
        page = DATA_SOURCE_PAGE.read_text(encoding="utf-8")
        source_catalog = SOURCE_CATALOG.read_text(encoding="utf-8")
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")
        one_look = (USER_CENTER / "一看三查.md").read_text(encoding="utf-8")
        key_decisions = (USER_CENTER / "关键结论与用户决策.md").read_text(encoding="utf-8")
        model_params = MODEL_PARAMS_PAGE.read_text(encoding="utf-8")

        self.assertTrue(DATA_SOURCE_PAGE.is_file())
        self.assertIn("[config/owner_controls.yaml](../config/owner_controls.yaml)", page)
        self.assertIn("[SOURCE_CATALOG.md](../docs/owner/SOURCE_CATALOG.md)", page)
        self.assertIn("5 个板块", page)
        self.assertIn("6 个数据源", page)
        self.assertIn("生产启用来源 | 1 个：`SRC-ARXIV`", page)
        self.assertIn("跨板块总览不直接采集独立来源", page)
        self.assertIn("不能把影子测试或规划来源写成已生产启用", page)
        for board in controls["boards"]:
            self.assertIn(str(board["board_id"]), page)
            self.assertIn(str(board["name"]), page)
            self.assertIn(str(board["board_id"]), source_catalog)
        for source in controls["sources"]:
            self.assertIn(str(source["source_id"]), page)
            self.assertIn(str(source["name"]), page)
            self.assertIn(str(source["access_method"]), page)
            self.assertIn(str(source["source_id"]), source_catalog)
        self.assertIn("SRC-BIORXIV", source_catalog)
        self.assertIn("SRC-MEDRXIV", source_catalog)
        self.assertNotIn("| Board ID |", source_catalog)
        self.assertNotIn("| Source ID |", source_catalog)
        self.assertIn("[数据源与板块健康](./数据源与板块健康.md)", readme)
        self.assertIn("[数据源与板块健康](./数据源与板块健康.md)", one_look)
        self.assertIn("[数据源与板块健康](./数据源与板块健康.md)", key_decisions)
        self.assertIn("[数据源与板块健康](用户中心/数据源与板块健康.md)", model_params)

    def test_future_source_changes_are_bound_to_user_center_sync_gate(self):
        root_agents = ROOT_AGENTS.read_text(encoding="utf-8")
        agents = PROJECT_AGENTS.read_text(encoding="utf-8")
        readme = PROJECT_README.read_text(encoding="utf-8")

        self.assertIn("source or board", root_agents)
        self.assertIn("add/delete/rename/enable/disable", root_agents)
        self.assertIn("user-center sync gate", root_agents)
        self.assertIn("config/code-only changes", root_agents)
        self.assertIn("are not complete", root_agents)
        self.assertIn("新增、删除、重命名、启用或停用任何板块或数据源", agents)
        required_paths = (
            "用户中心/数据源与板块健康.md",
            "用户中心/README.md",
            "用户中心/一看三查.md",
            "用户中心/关键结论与用户决策.md",
            "docs/owner/SOURCE_CATALOG.md",
            "模型参数文件.md",
            "功能清单.md",
            "开发记录.md",
            "arxiv-daily-push/tests/test_user_center_candidate_pool.py",
            "arxiv-daily-push/tests/test_owner_controls.py",
        )
        for required_path in required_paths:
            with self.subTest(required_path=required_path):
                self.assertIn(required_path, agents)
        self.assertIn("不得关闭任务、合并主线或宣称来源变更完成", agents)
        self.assertIn("[数据源与板块健康](./用户中心/数据源与板块健康.md)", readme)

    def test_model_params_disclose_current_roi_score_formula(self):
        text = MODEL_PARAMS_PAGE.read_text(encoding="utf-8")

        self.assertIn("当前用户中心分数来源", text)
        self.assertIn("adp-roi-semantic-rubric-v2", text)
        self.assertIn("ROI 候选排序", text)
        self.assertIn("相关性 15%；学习价值 20%；经济转化率 25%；ROI 20%；跨学科价值 10%；可解释性 10%；总和 100%", text)
        self.assertIn("每命中一个公开证据项统一增加 7%", text)
        self.assertIn("公开语义评分 rubric", text)
        self.assertIn("每个分项贡献 = 归一化信号 x 该因子权重", text)
        self.assertIn("不能用比例拆分总分来伪造分项", text)
        self.assertIn("旧八因子口径", text)


if __name__ == "__main__":
    unittest.main()
