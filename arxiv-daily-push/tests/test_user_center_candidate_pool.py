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

    def test_traceability_chain_page_exposes_all_matrix_rows_as_clickable_links(self):
        matrix_rows = list(csv.DictReader(TRACEABILITY_MATRIX.read_text(encoding="utf-8").splitlines()))
        page = TRACEABILITY_CHAIN_PAGE.read_text(encoding="utf-8")
        table_rows = re.findall(r"^\| \d+ \|", page, flags=re.MULTILINE)
        readme = (USER_CENTER / "README.md").read_text(encoding="utf-8")

        self.assertGreaterEqual(len(matrix_rows), 245)
        self.assertEqual(len(matrix_rows), 307)
        self.assertEqual(len(table_rows), len(matrix_rows))
        self.assertTrue(page.startswith("# 功能任务测试证据追踪链\n"))
        self.assertRegex(page, r"更新时间：\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Australia/Sydney")
        self.assertIn("[TRACEABILITY_MATRIX.csv](../docs/governance/TRACEABILITY_MATRIX.csv)", page)
        self.assertIn("[C-010 阶段记录](../docs/phase_records/PHASE_S2PAT05_TRACEABILITY_CHAIN_C010.md)", page)
        self.assertIn("[运行清单](../../governance/run_manifests/ADP-S2PAT05-TRACEABILITY-CHAIN-C010-20260627.json)", page)
        self.assertIn("| 序号 | 需求 | 任务 | 验收 | 代码 | 配置 | 测试 | 运行证据 | 状态 |", page)
        self.assertIn("[test_stage2_sources.py](../tests/test_stage2_sources.py)", page)
        self.assertIn("TRACEABILITY_MATRIX 行数 | 307", page)
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
        self.assertIn("S2PLT02/S2PLT03/S2PLT04、最终验收包", page)
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

        self.assertIn("source or board addition, deletion", root_agents)
        self.assertIn("user-center sync gate", root_agents)
        self.assertIn("must not change only", root_agents)
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
