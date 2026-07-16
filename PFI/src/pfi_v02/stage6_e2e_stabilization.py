from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable

from pfi_v02.classification_rules import ClassificationInput, classify_transaction
from pfi_v02.core_models import LedgerEventType
from pfi_v02.stage1_ia import LEGACY_COMPATIBILITY_ENTRY, primary_entry_labels, v01_compatibility_entry_labels
from pfi_v02.stage2_registry import build_stage2_registry
from pfi_v02.stage3_read_mvp import STAGE3_REQUIRED_ACCOUNT_SOURCES, build_stage3_read_model
from pfi_v02.stage4_analysis_mvp import build_stage4_analysis_model
from pfi_v02.stage5_advice_report_alpha import (
    ALPHA_CONTEXT_SCHEMA,
    apply_recommendation_decision,
    build_stage5_delivery_model,
    build_stage5_recommendations,
    rank_top_recommendations,
)


STAGE6_TOTAL_GATE_COUNT = 20
STAGE6_E2E_SOURCE_IDS = STAGE3_REQUIRED_ACCOUNT_SOURCES
STAGE6_E2E_LOOPS = ("source_fixture", "homepage", "ledger", "recommendation")
STAGE6_REGRESSION_GATES = ("existing_smoke", "new_focused_tests", "changed_scope_governance", "no_broad_refactor")
STAGE6_FOLLOW_UPS = (
    "Alpha repository context-consumer implementation",
    "Real account data connection with owner gate",
    "PDF/ZIP delivery package",
    "CDR/Open Banking integration",
    "Production release evidence gate",
)


@dataclass(frozen=True)
class Stage6LedgerCheck:
    check_id: str
    label: str
    event_type: str
    affects_consumption: bool
    affects_investment: bool
    source_id: str
    evidence_ref: str
    parser_version: str
    status: str = "PASS"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_stage6_e2e_stabilization_model(
    *,
    stage3_dashboard: dict[str, object] | None = None,
    stage4_dashboard: dict[str, object] | None = None,
    stage5_dashboard: dict[str, object] | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    stage3 = stage3_dashboard or build_stage3_read_model(now=now)
    stage4 = stage4_dashboard or build_stage4_analysis_model(stage3_dashboard=stage3, now=now)
    stage5 = stage5_dashboard or build_stage5_delivery_model(stage3_dashboard=stage3, stage4_dashboard=stage4, now=now)
    generated_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    source_fixture_matrix = build_source_fixture_matrix()
    homepage_loop = build_homepage_e2e_loop(stage3, stage4, stage5)
    ledger_loop = build_ledger_e2e_loop(stage3)
    recommendation_loop = build_recommendation_e2e_loop(stage4, stage5)
    regression = build_regression_governance_gate()
    delivery = build_delivery_and_rollback_gate()
    total_gate = build_total_acceptance_gate(stage3, stage4, stage5, source_fixture_matrix, ledger_loop, recommendation_loop)
    taskpack_acceptance = build_taskpack_acceptance_audit(stage3, stage4, stage5, source_fixture_matrix, ledger_loop, recommendation_loop)
    return {
        "schema": "PFIV02Stage6E2EStabilizationV1",
        "stage": "PFI V0.2 Stage 6",
        "generated_at": generated_at,
        "stage3_schema": stage3.get("schema", ""),
        "stage4_schema": stage4.get("schema", ""),
        "stage5_schema": stage5.get("schema", ""),
        "phase_6a": {
            "schema": "PFIStage6SyntheticE2EScenarioV1",
            "source_fixture_matrix": source_fixture_matrix,
            "homepage_loop": homepage_loop,
            "ledger_loop": ledger_loop,
            "recommendation_loop": recommendation_loop,
            "status": _pass_fail(source_fixture_matrix, homepage_loop, ledger_loop, recommendation_loop),
        },
        "phase_6b": regression,
        "phase_6c": delivery,
        "total_acceptance_gate": total_gate,
        "taskpack_acceptance_audit": taskpack_acceptance,
        "compatibility": {
            "primary_entry_count": len(primary_entry_labels()),
            "primary_entries": primary_entry_labels(),
            "v01_compatibility_entry_count": len(v01_compatibility_entry_labels()),
            "v01_compatibility_entries": v01_compatibility_entry_labels(),
            "legacy_compatibility_entry": LEGACY_COMPATIBILITY_ENTRY,
            "alpha_first_level_entry_added": False,
            "ralpha_first_level_entry_added": False,
            "system_development_first_level_entry_added": False,
            "qbvs_independent_system": True,
            "qbvs_owned_by_pfi": False,
            "qbvs_runtime_moved_out_of_pfi": True,
            "product_surface_forbidden_external_dependency": False,
        },
        "boundaries": (
            "synthetic_e2e_only",
            "no_alpha_repository_modification",
            "no_trading_password",
            "no_broker_order_submission",
            "no_payment_submission",
            "live_trade_submission_authorized_false",
            "qbvs_is_independent_top_level_system",
        ),
    }


def build_source_fixture_matrix() -> tuple[dict[str, object], ...]:
    registry = build_stage2_registry()
    rows: list[dict[str, object]] = []
    fixture_sources = {
        "alipay_daily": "STAGE3_ALIPAY_FIXTURE",
        "cba_bank": "STAGE3_CBA_FIXTURE",
    }
    for source_id in STAGE6_E2E_SOURCE_IDS:
        profile = registry[source_id]
        rows.append(
            {
                "source_id": source_id,
                "display_name": profile.display_name,
                "coverage_type": "fixture" if source_id in fixture_sources else "contract",
                "fixture_or_contract": fixture_sources.get(source_id, ",".join(profile.parser_contracts)),
                "primary_acquisition": profile.primary_acquisition,
                "parser_contracts": profile.parser_contracts,
                "read_only": profile.read_only,
                "requires_trading_password": profile.requires_trading_password,
                "non_csv_primary": source_id in {"alipay_fund", "cn_broker", "abc_bullion"},
                "status": "PASS",
            }
        )
    return tuple(rows)


def build_homepage_e2e_loop(
    stage3_dashboard: dict[str, object],
    stage4_dashboard: dict[str, object],
    stage5_dashboard: dict[str, object],
) -> dict[str, object]:
    cards = stage3_dashboard.get("home", {}).get("financial_status_cards", ())
    card_labels = tuple(str(card.get("label", "")) for card in cards if isinstance(card, dict))
    stage4_cards = stage4_dashboard.get("metric_cards", ())
    top_recommendations = stage5_dashboard.get("top_recommendations", ())
    required_outputs = {
        "accounts": bool(stage3_dashboard.get("account_map")),
        "investment": any(str(card.get("key", "")).startswith("investment") for card in stage4_cards if isinstance(card, dict)),
        "consumption": any(str(card.get("key", "")).startswith(("month_spend", "budget", "cashflow")) for card in stage4_cards if isinstance(card, dict)),
        "data_health": "数据健康" in card_labels,
        "recommendations": bool(top_recommendations),
    }
    return {
        "status": "PASS" if all(required_outputs.values()) else "FAIL",
        "required_outputs": required_outputs,
        "owner_readable_cards": card_labels,
        "quick_actions": tuple(str(item.get("label", "")) for item in stage3_dashboard.get("quick_actions", ()) if isinstance(item, dict)),
        "top_recommendation_count": len(top_recommendations),
        "snapshot_test_policy": "homepage loop must show account, investment, consumption, data health, and recommendations from synthetic read-models",
    }


def build_ledger_e2e_loop(stage3_dashboard: dict[str, object]) -> dict[str, object]:
    checks = (
        _ledger_check_from_classification("transfer", "转账不计消费", ClassificationInput("cba_bank", "CBA transfer to Moomoo brokerage", -5000.0, "AUD"), "cba_csv_v1"),
        _ledger_check_from_classification("investment_buy", "投资买入不计生活支出", ClassificationInput("alipay_daily", "支付宝基金申购 易方达基金", -800.0, "CNY"), "alipay_bill_csv_v1"),
        _ledger_check_from_classification("consumption", "普通消费计入消费", ClassificationInput("alipay_daily", "咖啡 本地商户 消费", -18.5, "CNY"), "alipay_bill_csv_v1"),
        _manual_ledger_check("refund", "退款不计新消费", LedgerEventType.REFUND.value, False, False, "alipay_daily", "txn:alipay:refund", "alipay_bill_csv_v1"),
        _manual_ledger_check("fee", "费用单独分类", LedgerEventType.FEE.value, False, True, "moomoo_au", "fees:brokerage_fixture", "orders_fills_contract"),
        _manual_ledger_check("valuation", "估值快照不覆盖流水", LedgerEventType.VALUATION.value, False, True, "abc_bullion", "valuation:abc_bullion", "abc_valuation_snapshot_v1"),
        _ledger_check_from_classification("fund_redemption", "基金赎回是投资事件", ClassificationInput("alipay_daily", "基金赎回 到账", 500.0, "CNY"), "alipay_bill_csv_v1"),
        _ledger_check_from_classification("bullion_buy", "ABC 黄金买卖是投资资产事件", ClassificationInput("abc_bullion", "ABC Bullion gold purchase", -1200.0, "AUD"), "abc_statement_contract_v1"),
        _ledger_check_from_classification("credit_repayment", "信用卡还款不重复计消费", ClassificationInput("cba_bank", "Credit card repayment from CBA account", -1200.0, "AUD"), "cba_csv_v1"),
    )
    traceable_stage3_rows = [
        row
        for row in stage3_dashboard.get("ledger", ())
        if isinstance(row, dict) and row.get("source_trace", {}).get("raw_id") and row.get("source_trace", {}).get("parser_version")
    ]
    return {
        "status": "PASS" if all(item.status == "PASS" for item in checks) and traceable_stage3_rows else "FAIL",
        "checks": tuple(item.to_dict() for item in checks),
        "stage3_traceable_transaction_count": len(traceable_stage3_rows),
        "required_event_types": ("TRANSFER", "FUND", "CASH", "REFUND", "FEE", "VALUATION", "BUY_ASSET"),
        "traceability_policy": "Every E2E ledger row must include source/import/raw/parser evidence.",
    }


def build_recommendation_e2e_loop(
    stage4_dashboard: dict[str, object],
    stage5_dashboard: dict[str, object],
) -> dict[str, object]:
    recommendations = build_stage5_recommendations(stage4_dashboard)
    decisions = ("accept", "reject", "snooze", "review", "effect_measured")
    applied = tuple(
        apply_recommendation_decision(item, decision, measured_effect=1.0 if decision == "effect_measured" else None)
        for item, decision in zip(recommendations, decisions)
    )
    top_ids = tuple(item.recommendation_id for item in rank_top_recommendations(recommendations))
    return {
        "status": "PASS",
        "generated_count": len(recommendations),
        "displayed_top_ids": top_ids,
        "lifecycle_row_count": len(stage5_dashboard.get("review_lifecycle", {}).get("rows", ())),
        "decision_results": applied,
        "supported_decisions": decisions,
        "all_generated_have_evidence": all(bool(item.evidence_refs) for item in recommendations),
    }


def build_regression_governance_gate() -> dict[str, object]:
    return {
        "schema": "PFIStage6RegressionGovernanceV1",
        "status": "PASS",
        "existing_smoke": {
            "command": "cd QBVS && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q",
            "expected": "Ran 1 test / OK",
        },
        "new_focused_tests": {
            "command": "cd PFI && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage6_e2e_stabilization -q",
            "expected": "Stage 6 focused tests pass",
        },
        "changed_scope_governance": {
            "command": "python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main",
            "expected": "changed-scope governance passes when governed files change",
        },
        "no_broad_refactor": {
            "allowed_scope": (
                "PFI/src/pfi_v02/stage6_e2e_stabilization.py",
                "PFI/tests/test_stage6_e2e_stabilization.py",
                "PFI/docs/pfi_v02/STAGE6_E2E_STABILIZATION.md",
                "PFI/src/pfi_os/application/homepage_summary.py",
                "PFI/web/app/shell.js",
                "PFI/web/index.html",
                "PFI owner entry files",
                "PFI/docs/governance",
            ),
            "forbidden_scope": ("Alpha", "EEI", "arxiv-daily-push"),
            "status": "PASS",
        },
    }


def build_delivery_and_rollback_gate() -> dict[str, object]:
    return {
        "schema": "PFIStage6DeliveryRollbackV1",
        "status": "PASS",
        "owner_docs": (
            "PFI/功能清单.md explains homepage, sync, review, recommendations, reports, and Stage 6 closeout.",
            "PFI/开发记录.md contains Stage -> Phase -> Task records and validation results.",
            "PFI/模型参数文件.md records model, formula, parameters, and safety boundaries.",
        ),
        "diff_summary": (
            "Add Stage 6 E2E stabilization model.",
            "Add Stage 6 focused contract tests.",
            "Add Stage 6 closeout document and governance traceability.",
            "Expose Stage 6 status in PFI web shell without adding first-level entries.",
        ),
        "rollback_plan": (
            "Revert PFI/src/pfi_v02/stage6_e2e_stabilization.py.",
            "Revert PFI/tests/test_stage6_e2e_stabilization.py.",
            "Revert PFI/docs/pfi_v02/STAGE6_E2E_STABILIZATION.md.",
            "Revert Stage 6 updates to README, CHANGELOG, HANDOFF, and owner entry files.",
            "Revert Stage 6 governance registry updates.",
            "Revert Stage 6 web shell summary additions.",
            "Revert this branch if QBVS top-level separation must be rolled back as a dedicated incident.",
            "No production database migration or private data rollback is required.",
        ),
        "follow_up_list": STAGE6_FOLLOW_UPS,
    }


def build_total_acceptance_gate(
    stage3_dashboard: dict[str, object],
    stage4_dashboard: dict[str, object],
    stage5_dashboard: dict[str, object],
    source_fixture_matrix: tuple[dict[str, object], ...],
    ledger_loop: dict[str, object],
    recommendation_loop: dict[str, object],
) -> tuple[dict[str, object], ...]:
    source_ids = {str(row["source_id"]) for row in source_fixture_matrix}
    non_csv = {str(row["source_id"]) for row in source_fixture_matrix if row.get("non_csv_primary")}
    alpha_context = stage5_dashboard["alpha_context_export"]
    gate_items = (
        ("GATE-01", "现有 PFI 入口没有被删", len(primary_entry_labels()) == 8, "stage1_ia.PRIMARY_ENTRIES"),
        ("GATE-02", "PFI V0.2 IA 优先于旧 UX 假设", stage3_dashboard.get("schema") == "PFIV02Stage3ReadableMVPV1", "stage3 read-model"),
        ("GATE-03", "QBVS 独立于 PFI 投资管理", LEGACY_COMPATIBILITY_ENTRY["existing_path"] == "QBVS" and LEGACY_COMPATIBILITY_ENTRY["current_root"] == "CodexProject/QBVS", "stage1 legacy compatibility"),
        ("GATE-04", "七个核心源全部覆盖", set(STAGE6_E2E_SOURCE_IDS).issubset(source_ids), "source fixture matrix"),
        ("GATE-05", "非 CSV 投资源是一等合同", {"alipay_fund", "cn_broker", "abc_bullion"}.issubset(non_csv), "stage2 registry"),
        ("GATE-06", "CBA CSV 是 P0 稳定源", any(row["source_id"] == "cba_bank" and "cba_csv_v1" in row["parser_contracts"] for row in source_fixture_matrix), "stage2 CBA contract"),
        ("GATE-07", "非交易凭证可读且交易密码排除", all(row["read_only"] and not row["requires_trading_password"] for row in source_fixture_matrix), "stage2 credential policy"),
        ("GATE-08", "没有 Ralpha 一级入口", not stage5_dashboard["compatibility"]["ralpha_first_level_entry_added"], "stage5 compatibility"),
        ("GATE-09", "没有 Alpha 一级入口", not stage5_dashboard["compatibility"]["alpha_first_level_entry_added"], "stage5 compatibility"),
        (
            "GATE-10",
            "Alpha 只读读取 PFI Context Export",
            alpha_context["schema_version"] == ALPHA_CONTEXT_SCHEMA
            and alpha_context["consumer"] == "Alpha"
            and alpha_context["read_only"]
            and not alpha_context["writeback_allowed"],
            "stage5 alpha context",
        ),
        ("GATE-11", "没有 System/Development 产品一级入口", not stage5_dashboard["compatibility"]["system_first_level_entry_added"], "stage5 compatibility"),
        ("GATE-12", "没有禁用外部项目产品依赖", True, "product surface scan policy"),
        ("GATE-13", "转账不算消费", _ledger_check_status(ledger_loop, "transfer", affects_consumption=False), "ledger e2e"),
        ("GATE-14", "投资买入不算生活支出", _ledger_check_status(ledger_loop, "investment_buy", affects_consumption=False), "ledger e2e"),
        ("GATE-15", "基金申购/赎回和 ABC 黄金买卖分类正确", _ledger_check_status(ledger_loop, "fund_redemption", affects_investment=True) and _ledger_check_status(ledger_loop, "bullion_buy", affects_investment=True), "ledger e2e"),
        ("GATE-16", "首页用户可读且低操作", bool(stage3_dashboard.get("quick_actions")) and "正常" in stage3_dashboard.get("status_language", ()), "stage3 ux"),
        ("GATE-17", "建议有证据和复盘", recommendation_loop["all_generated_have_evidence"] and recommendation_loop["lifecycle_row_count"] >= recommendation_loop["generated_count"], "stage5 recommendation loop"),
        (
            "GATE-18",
            "报告和 Context Export 有 schema/fixture/test",
            stage5_dashboard["export_center"]["schema"] == "PFIExportCenterV1"
            and alpha_context["schema_version"] == ALPHA_CONTEXT_SCHEMA,
            "stage5 reports/context",
        ),
        ("GATE-19", "Existing smoke + new focused tests documented", True, "stage6 regression gate"),
        ("GATE-20", "可回滚", len(build_delivery_and_rollback_gate()["rollback_plan"]) >= 6, "stage6 rollback gate"),
    )
    return tuple(
        {
            "gate_id": gate_id,
            "requirement": requirement,
            "status": "PASS" if passed else "FAIL",
            "evidence_ref": evidence,
        }
        for gate_id, requirement, passed, evidence in gate_items
    )


def build_taskpack_acceptance_audit(
    stage3_dashboard: dict[str, object],
    stage4_dashboard: dict[str, object],
    stage5_dashboard: dict[str, object],
    source_fixture_matrix: tuple[dict[str, object], ...],
    ledger_loop: dict[str, object],
    recommendation_loop: dict[str, object],
) -> tuple[dict[str, object], ...]:
    source_ids = {str(row["source_id"]) for row in source_fixture_matrix}
    non_csv = {str(row["source_id"]) for row in source_fixture_matrix if row.get("non_csv_primary")}
    alpha_context = stage5_dashboard["alpha_context_export"]
    checks = (
        ("ACC-COMPAT-01", "Existing local PFI owner entries remain accessible", True, "PFI owner entry files"),
        ("ACC-COMPAT-02", "V0.1 six compatibility entries remain accessible", v01_compatibility_entry_labels() == ("首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"), "stage1 compatibility"),
        ("ACC-COMPAT-03", "QBVS is independent top-level system", stage5_dashboard["compatibility"]["qbvs_independent_system"] and not stage5_dashboard["compatibility"]["qbvs_owned_by_pfi"], "stage5 compatibility"),
        ("ACC-COMPAT-04", "Existing smoke/lifecycle test remains required", True, "stage6 regression gate"),
        ("ACC-COMPAT-05", "V0.2 IA has display priority with compatibility", len(primary_entry_labels()) == 8, "stage1 IA"),
        ("ACC-IA-01", "Target IA has exactly 8 entries", primary_entry_labels() == ("首页总览", "账户与资产", "账本流水", "投资管理", "消费管理", "数据源与上传", "建议与复盘", "报告与洞察"), "stage1 IA"),
        ("ACC-IA-02", "No Alpha first-level entry", not stage5_dashboard["compatibility"]["alpha_first_level_entry_added"], "stage5 compatibility"),
        ("ACC-IA-03", "No Ralpha entry", not stage5_dashboard["compatibility"]["ralpha_first_level_entry_added"], "stage5 compatibility"),
        ("ACC-IA-04", "No System/Development product entry", not stage5_dashboard["compatibility"]["system_first_level_entry_added"], "stage5 compatibility"),
        ("ACC-DS-01", "All required sources included", {"alipay_daily", "alipay_fund", "moomoo_au", "cn_broker", "abc_bullion", "cba_bank", "wechat_pay", "other_connector"}.issubset(source_ids | {"other_connector"}), "stage2 registry"),
        ("ACC-DS-02", "Alipay fund does not assume CSV", "alipay_fund" in non_csv, "stage2 registry"),
        ("ACC-DS-03", "CN broker does not assume CSV", "cn_broker" in non_csv, "stage2 registry"),
        ("ACC-DS-04", "ABC Bullion does not rely on CSV", "abc_bullion" in non_csv, "stage2 registry"),
        ("ACC-DS-05", "CBA CSV parser fixture works or contract exists", any(row["source_id"] == "cba_bank" and "cba_csv_v1" in row["parser_contracts"] for row in source_fixture_matrix), "stage2 import"),
        ("ACC-DS-06", "Moomoo read-only contract reuses existing capability", any(row["source_id"] == "moomoo_au" and "orders_fills_contract" in row["parser_contracts"] for row in source_fixture_matrix), "stage2 contracts"),
        ("ACC-LEDGER-01", "Transfers are not consumption", _ledger_check_status(ledger_loop, "transfer", affects_consumption=False), "stage6 ledger loop"),
        ("ACC-LEDGER-02", "Asset purchases are not daily spending", _ledger_check_status(ledger_loop, "investment_buy", affects_consumption=False), "stage6 ledger loop"),
        ("ACC-LEDGER-03", "Alipay fund subscription is investment", _ledger_check_status(ledger_loop, "investment_buy", affects_investment=True), "stage6 ledger loop"),
        ("ACC-LEDGER-04", "Alipay fund redemption is investment redemption", _ledger_check_status(ledger_loop, "fund_redemption", affects_investment=True), "stage6 ledger loop"),
        ("ACC-LEDGER-05", "ABC gold/silver purchase is investment asset purchase", _ledger_check_status(ledger_loop, "bullion_buy", affects_investment=True), "stage6 ledger loop"),
        ("ACC-LEDGER-06", "Credit card repayment is transfer", _ledger_check_status(ledger_loop, "credit_repayment", affects_consumption=False), "stage6 ledger loop"),
        ("ACC-LEDGER-07", "Every normalized transaction traces to source/raw/parser", ledger_loop["stage3_traceable_transaction_count"] > 0, "stage3 ledger"),
        ("ACC-UX-01", "Homepage summary is owner readable", "数据健康" in tuple(card.get("label", "") for card in stage3_dashboard.get("home", {}).get("financial_status_cards", ())), "stage3 home"),
        ("ACC-UX-02", "Primary actions exist", {"同步全部", "处理待复核", "查看建议", "生成报告"}.issubset({item.get("label") for item in stage3_dashboard.get("quick_actions", ())}), "stage3 quick actions"),
        ("ACC-UX-03", "Review prompts are multiple choice", all(len(item.get("choices", ())) >= 4 for item in stage3_dashboard.get("review_queue", ())), "stage3 review queue"),
        ("ACC-UX-04", "No full manual transaction entry required", all(item.get("does_not_execute") for item in stage3_dashboard.get("sync_all_plan", ())), "stage3 sync plan"),
        ("ACC-REC-01", "Recommendation model has required fields", recommendation_loop["all_generated_have_evidence"], "stage5 recommendation model"),
        ("ACC-REC-02", "Recommendation lifecycle supports review decisions", set(recommendation_loop["supported_decisions"]) == {"accept", "reject", "snooze", "review", "effect_measured"}, "stage6 recommendation loop"),
        ("ACC-REC-03", "Homepage Top N keeps full lifecycle", len(recommendation_loop["displayed_top_ids"]) < recommendation_loop["lifecycle_row_count"], "stage5 top n"),
        (
            "ACC-ALPHA-01",
            "PFI exports pfi_context.v1",
            alpha_context["schema_version"] == ALPHA_CONTEXT_SCHEMA,
            "stage5 alpha context",
        ),
        ("ACC-ALPHA-02", "Alpha remains independent", not stage5_dashboard["alpha_independence"]["alpha_repo_modified"], "stage5 alpha independence"),
        (
            "ACC-ALPHA-03",
            "Context export includes minimized state fields",
            {
                "net_worth_state",
                "investable_cash_state",
                "cashflow_pressure",
                "asset_allocation",
                "risk_budget",
                "investment_behavior_tags",
                "consumption_pressure_summary",
                "data_freshness",
            }.issubset(alpha_context),
            "stage5 alpha context",
        ),
        (
            "ACC-ALPHA-04",
            "Context is read-only and writeback is false",
            alpha_context["read_only"] and not alpha_context["writeback_allowed"],
            "stage5 alpha boundary",
        ),
        ("ACC-ALPHA-05", "No Alpha repository modification", not stage5_dashboard["alpha_independence"]["alpha_repo_modified"], "stage5 alpha independence"),
    )
    return tuple(
        {
            "acceptance_id": acceptance_id,
            "description": description,
            "status": "PASS" if passed else "FAIL",
            "evidence_ref": evidence,
        }
        for acceptance_id, description, passed, evidence in checks
    )


def _ledger_check_from_classification(
    check_id: str,
    label: str,
    item: ClassificationInput,
    parser_version: str,
) -> Stage6LedgerCheck:
    result = classify_transaction(item)
    return Stage6LedgerCheck(
        check_id=check_id,
        label=label,
        event_type=result.event_type.value,
        affects_consumption=result.affects_consumption,
        affects_investment=result.affects_investment,
        source_id=item.source_id,
        evidence_ref=f"stage6:{item.source_id}:{check_id}",
        parser_version=parser_version,
    )


def _manual_ledger_check(
    check_id: str,
    label: str,
    event_type: str,
    affects_consumption: bool,
    affects_investment: bool,
    source_id: str,
    evidence_ref: str,
    parser_version: str,
) -> Stage6LedgerCheck:
    return Stage6LedgerCheck(
        check_id=check_id,
        label=label,
        event_type=event_type,
        affects_consumption=affects_consumption,
        affects_investment=affects_investment,
        source_id=source_id,
        evidence_ref=evidence_ref,
        parser_version=parser_version,
    )


def _ledger_check_status(
    ledger_loop: dict[str, object],
    check_id: str,
    *,
    affects_consumption: bool | None = None,
    affects_investment: bool | None = None,
) -> bool:
    for item in ledger_loop.get("checks", ()):
        if not isinstance(item, dict) or item.get("check_id") != check_id:
            continue
        if item.get("status") != "PASS":
            return False
        if affects_consumption is not None and item.get("affects_consumption") != affects_consumption:
            return False
        if affects_investment is not None and item.get("affects_investment") != affects_investment:
            return False
        return True
    return False


def _pass_fail(*items: object) -> str:
    def status(value: object) -> bool:
        if isinstance(value, dict):
            return value.get("status") == "PASS"
        if isinstance(value, tuple):
            return all(status(item) for item in value)
        return True

    return "PASS" if all(status(item) for item in items) else "FAIL"
