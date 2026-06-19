from __future__ import annotations

import json
import re
import sqlite3
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .model_compare import MODEL_COMPARISON_JSON
from .report_store import connect_report_db
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


RECOMMENDATION_OPERATIONS_JSON_LATEST = "recommendation_operations_latest.json"
RECOMMENDATION_OPERATIONS_MD_LATEST = "recommendation_operations_latest.md"
RECOMMENDATION_OPERATIONS_PDF_LATEST = "recommendation_operations_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")
DEFAULT_BANKROLL_REFERENCE_AUD = 4000.0
KELLY_DISCOUNT = 0.5
MAIN_MARKET_EDGE_THRESHOLD = 0.025
SMALL_MARKET_EDGE_THRESHOLD = 0.05
SINGLE_BET_CAP_FRACTION = 0.02
ROR_REVIEW_THRESHOLD = 0.05
EXCEL_TEMPLATE_FILENAME = "football_betting_analysis_ABC_template.xlsx"
USER_BUDGET_FLOOR_AUD = 3000.0
USER_BUDGET_MID_AUD = 4000.0
USER_BUDGET_CEILING_AUD = 5000.0
USER_DECLARED_COMMITTED_REFERENCE_AUD = 2000.0
PROBABILITY_ENGINE_SEED = 20260613


def write_recommendation_operations_bundle(output_dir: Path, db_path: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    db_path = Path(db_path or output_dir / "tab_fifa_reports.sqlite3")
    payload = build_recommendation_operations(output_dir, db_path)
    json_path = output_dir / RECOMMENDATION_OPERATIONS_JSON_LATEST
    md_path = output_dir / RECOMMENDATION_OPERATIONS_MD_LATEST
    pdf_path = output_dir / RECOMMENDATION_OPERATIONS_PDF_LATEST

    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_recommendation_operations_markdown(payload))
    pdf_summary = write_recommendation_operations_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    payload["storage"] = persist_recommendation_operations(db_path, payload)
    atomic_write_json(json_path, payload)
    return payload


def build_recommendation_operations(output_dir: Path, db_path: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    generated_at = datetime.now(REPORT_TZ).isoformat()
    latest_commit = load_json(output_dir / "latest_commit.json")
    readiness = load_json(output_dir / "automation_readiness_latest.json")
    raw_health = load_json(output_dir / "raw_refresh_health_latest.json")
    active_timeline = load_json(output_dir / "active_timeline_report_latest.json") or load_json(output_dir / "active_timeline_latest.json")
    available_strategy = load_json(output_dir / "available_board_strategy_latest.json")
    source_registry = load_json(output_dir / "source_model_registry_latest.json")
    excel_reference = excel_reference_profile()

    execution_allowed = recommendation_execution_allowed(readiness, raw_health)
    gate_message = execution_gate_message(readiness, raw_health)
    bankroll_reference = bankroll_reference_aud(output_dir, latest_commit)
    all_research_rows = recommendation_rows(output_dir, db_path, latest_commit, limit=12, bankroll_reference=bankroll_reference)
    research_rows, excluded_unavailable_rows, all_scoped_rows = partition_rows_by_board_scope(all_research_rows, available_strategy)
    research_rows = research_rows[:12]
    excluded_unavailable_rows = apply_board_scope_gate(excluded_unavailable_rows)
    rows = apply_execution_gate(research_rows, execution_allowed=execution_allowed, gate_message=gate_message)
    summary = summarize_rows(
        rows,
        research_rows,
        latest_commit,
        readiness,
        raw_health,
        active_timeline,
        available_strategy,
        execution_allowed,
        all_research_rows=all_scoped_rows,
        excluded_unavailable_rows=excluded_unavailable_rows,
    )
    probability_engine = probability_engine_framework(
        summary=summary,
        source_registry=source_registry,
        excel_reference=excel_reference,
    )
    summary.update(probability_engine_summary(probability_engine))
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "snapshot_id": snapshot_id(generated_at),
        "mode": "recommendation_operations_dashboard",
        "purpose": "把首页推荐下注板块沉淀为正式操作研究报告：每个候选盘口的时间、板块、下注、赔率、金额、Edge、套利率、Risk of ruin、EV、概率、置信度、门禁状态和新旧变化。",
        "executive_status": {
            "status": "actionable" if execution_allowed and summary["executable_new_stake_aud"] > 0 else "research_only_blocked",
            "execution_allowed": execution_allowed,
            "current_action": "按行复核 TAB 实时赔率后执行" if execution_allowed else "暂不新增下注",
            "current_executable_new_stake_aud": summary["executable_new_stake_aud"],
            "research_candidate_stake_aud": summary["research_candidate_stake_aud"],
            "primary_user_action": "先恢复 TAB Live discovery 和 raw refresh；门禁通过前只看研究候选，不投入新增金额。"
            if not execution_allowed
            else "从 Top 1 开始逐项核对实时赔率，赔率未低于报告价再按金额执行。",
            "gate_message": gate_message,
        },
        "summary": summary,
        "recommendation_rows": rows,
        "research_rows_before_gate": research_rows,
        "all_research_rows_before_scope": all_scoped_rows,
        "excluded_unavailable_rows": excluded_unavailable_rows,
        "market_funding_analysis": {
            "summary": summary.get("market_funding", {}),
            "rows": [
                {
                    "time": row.get("time"),
                    "board": row.get("board"),
                    "event": row.get("event"),
                    "market": row.get("market"),
                    "selection": row.get("selection"),
                    **(row.get("market_funding") or {}),
                }
                for row in research_rows
            ],
        },
        "probability_engine": probability_engine,
        "old_new_compare": old_new_compare(db_path, rows),
        "source_alignment": {
            "model_registry_status": (source_registry.get("executive_status") or {}).get("status", ""),
            "reference_count": (source_registry.get("summary") or {}).get("reference_count", 0),
            "implemented_reference_count": (source_registry.get("summary") or {}).get("implemented_reference_count", 0),
            "design_reference_count": (source_registry.get("summary") or {}).get("design_reference_count", 0),
            "license_control_required": (source_registry.get("executive_status") or {}).get("license_control_required", False),
            "primary_references": [
                str(item.get("display_name") or item.get("source") or "")
                for item in (source_registry.get("rows") or [])[:6]
            ],
        },
        "calculation_policy": {
            "template_reference": EXCEL_TEMPLATE_FILENAME,
            "template_read_status": excel_reference.get("template_read_status", "static_profile"),
            "template_sheet_count": excel_reference.get("sheet_count") or len(excel_reference["sheet_names"]),
            "excel_reference_profile": excel_reference,
            "template_evidence_digest": excel_reference_digest(excel_reference),
            "template_formula_count": int(excel_reference.get("formula_count_total") or 0),
            "template_evidence_terms": excel_reference.get("template_evidence_terms") or [],
            "template_decision_rules": excel_reference.get("template_decision_rules") or [],
            "template_analysis_materials": excel_template_analysis_materials(excel_reference),
            "edge_formula": "Edge = 模型概率 - 赔率盈亏平衡概率",
            "arbitrage_rate_formula": "套利率 = max(0, 模型概率 × 十进制赔率 - 1)，这是价值套利率，不是跨平台无风险套利证明。",
            "kelly_formula": "满Kelly = max(0, p - (1-p)/(odds-1))；风险参考使用半Kelly。",
            "risk_of_ruin_formula": "Risk of ruin 为基于中位资金池、单注比例、半Kelly偏离和盘口风险标记的保守启发式估计，并输出低/中/偏高/高等级。",
            "minimum_acceptable_odds_formula": "最低可接受赔率 = 1 / (模型概率 - Edge门槛)；若 TAB 实时赔率低于该值，则即使 EV 为正也不建议执行。",
            "expected_profit_formula": "预计收益 = 建议研究金额 × EV；每 AUD100 预期收益 = 100 × EV，用于跨盘口快速比较。",
            "ror_review_rule": f"Risk of ruin 达到 {ROR_REVIEW_THRESHOLD:.0%} 或以上时进入复核/降仓队列，不能只因 EV 为正直接买入。",
            "price_drift_tolerance_formula": "价格容忍度 = (当前赔率 - 最低可接受赔率) / 当前赔率；为负表示价格已经走差。",
            "stake_cap_usage_formula": "仓位上限占用 = 单注资金比例 / 2%单注上限；超过100%时必须降仓或放弃。",
            "risk_adjusted_value_formula": "风险调整价值分 = EV + max(0, Edge门槛差) - Risk of ruin；用于同一报告内排序，不等于真实收益保证。",
            "portfolio_risk_formula": "组合RoR = 注额加权行级RoR + 集中度惩罚 + 偏高RoR行惩罚 + 预算压力惩罚；用于研究候选组合压力测试，不等于真实破产概率。",
            "market_funding_tendency_formula": "市场资金倾向分 = 50 + EV/Edge/套利率/价格容忍度价值压力 + 流动性/盘口深度压力 - RoR/盘口浮动/风险事件压力；0-100分，属于盘口资金代理指标。",
            "market_funding_proxy_formula": "总资金/净资金/成交量/流动性/盘口深度/日均盘口变动浮动率均由市场类型、赔率区间、价值信号、价格容忍度、仓位比例和风险标记估算；TAB公开页未披露真实成交资金。",
            "probability_engine_framework": probability_engine,
            "probability_engine_formula": "概率工程 = 赛制规则引擎 + 球队强度评级 + 进球模型 + 事件/阵容特征 + 市场基准 + Monte Carlo 路径模拟 + 概率校准；未实装模块只进入规划/复核队列。",
            "data_leakage_control_rule": "每条预测必须记录 timestamp、run_id、固定 random seed、数据源版本；opening/closing 赔率、confirmed/rumor 新闻、赛前/赛中/赛后特征必须隔离。",
            "bankroll_reference_aud": bankroll_reference,
            "budget_reference": {
                "budget_floor_aud": USER_BUDGET_FLOOR_AUD,
                "budget_mid_aud": USER_BUDGET_MID_AUD,
                "budget_ceiling_aud": USER_BUDGET_CEILING_AUD,
                "declared_committed_reference_aud": USER_DECLARED_COMMITTED_REFERENCE_AUD,
                "declared_reference_status": "用户声明参考值，待持仓快照同步确认；未同步前不作为已验证事实。",
            },
            "extracted_template_controls": excel_template_control_matrix(excel_reference),
            "risk_discipline": {
                "base_stake_range": "0.5%-1.0% bankroll",
                "single_bet_cap": "2.0% bankroll",
                "main_market_edge_threshold": "2%-3%",
                "small_market_edge_threshold": "4%-6%",
                "preferred_market_order": "亚洲让球 / 大小球 > 1X2 > 角球/牌数 > 正确比分",
                "late_check_window": "赛前10分钟复核价格、去水、首发、伤停、动机、赛程疲劳、战术匹配和大小球节奏。",
                "forbidden_behaviors": ["追损", "加倍", "情绪下注", "无首发重仓", "无记录下注"],
                "world_cup_adjustments": ["中立场", "小组赛动机", "淘汰赛保守性", "国家队样本小", "旅行与休息时间"],
                "review_priority": "先看 CLV，再看 ROI；样本不足时不因短期输赢推翻模型。",
            },
            "judgment_basis": [
                excel_reference_digest(excel_reference),
                "ChatGPT Excel 模板已吸收为：赛前10分钟清单、赔率去水、EV、Edge、Kelly、Poisson/xG、下注日志、CLV/ROI 复盘口径。",
                "价格执行层：从 Excel 的“价格走差就放弃”规则转化为最低可接受赔率、赔率缓冲和价格容忍度，避免报告价过期后继续下注。",
                "风控执行层：从 Excel 的单注上限和半Kelly规则转化为仓位上限占用、Kelly安全垫和 Risk of ruin 复核队列。",
                "下注纪律层：基础单注 0.5%-1.0% bankroll，单注上限 2.0% bankroll；主流市场 Edge 至少 2%-3%，小市场至少 4%-6%。",
                "推荐过滤层：模型概率必须高于盈亏平衡概率，Edge 需要达到对应盘口门槛；未达门槛或 RoR 偏高时只进入观察/复核队列。",
                "组合风险层：按用户预算区间 AUD 3,000-5,000 和用户声明已投入参考 AUD 2,000 做压力测试，输出候选组合占用、预计收益、全输亏损和组合RoR。",
                "市场资金层：新增市场资金倾向分、总资金代理、净资金代理、成交量代理、流动性、盘口深度和日均盘口变动浮动率；该层只作为资金面代理分析，不伪装为 TAB 官方成交数据。",
                "概率工程层：把赛制规则、Dixon-Coles/Bayesian Poisson、Elo/Bradley-Terry/FIFA/SPI 类强度、xG/xT/VAEP、市场赔率基准、Monte Carlo、校准指标和防泄漏规则纳入覆盖矩阵；未上线项标为 planned/partial，不伪装成已实现。",
                "板块范围层：当前 TAB live nav 未列出或 route mismatch 的板块只进入排除审计队列，不计入当前推荐池、Top pick、Edge/套利率/RoR 汇总。",
                "本地概率层：TAB 市场反推 xG、Poisson/Dixon-Coles、Elo/DC、goalmodel proxy 和质量 overlay。",
                "赛事情境层：世界杯需要额外修正中立场、小组赛动机、淘汰赛保守性、国家队样本小、旅行与休息时间。",
                "开源参考层：penaltyblog 用于 no-vig/盘口概率/ratings 思路，socceraction 用于 xT/VAEP 基本面路线，openfootball 用于 2026 赛程公开校验。",
                "执行门禁层：raw refresh、formal report publish、public artifact safety 和 active backfill 未通过时，所有金额降级为 AUD 0 可执行。",
                "复盘优化层：下注日志记录入场赔率、收盘赔率、结果、注额、CLV%、ROI 和平均 Edge，用于每日/周报回测优化。",
            ],
        },
        "evidence_policy": "FACT 来自 latest_commit、SQLite recommendations、raw/publication gates；INFERENCE 为 EV、Edge、套利率、Risk of ruin、金额和执行状态的本地计算。",
        "truthfulness_note": "本报告在 raw 或日报发布门禁失败时会把所有候选降级为研究-only，当前可执行新增金额为 AUD 0。",
        "safety_note": "该报告只生成下注研究和操作建议，不自动下注、不点击赔率、不添加投注单。",
    }
    return sanitize_public_payload(payload)


def probability_engine_framework(
    *,
    summary: dict[str, Any],
    source_registry: dict[str, Any],
    excel_reference: dict[str, Any],
) -> dict[str, Any]:
    source_summary = source_registry.get("summary") or {}
    implemented_sources = int(source_summary.get("implemented_reference_count") or 0)
    reference_count = int(source_summary.get("reference_count") or 0)
    outputs = [
        {
            "output_object": "单场",
            "typical_result": "胜/平/负概率、比分分布、进球数分布、双方xG、冷门概率",
            "current_status": "partial",
            "current_evidence": "推荐行已输出概率、EV、Edge、套利率、RoR；比分矩阵和双方xG仍为模型路线，不作为已验证事实。",
            "next_upgrade": "用 Poisson / Dixon-Coles 统一生成 1X2、OU、BTTS、比分矩阵。",
        },
        {
            "output_object": "小组",
            "typical_result": "出线概率、第一/第二/第三概率、淘汰概率",
            "current_status": "planned",
            "current_evidence": "Group Betting 已进入盘口层分析；完整第三名出线与排名模拟仍未解锁为实装结果。",
            "next_upgrade": "实现48队小组规则、净胜球、进球数、纪律分和最佳第三名排序。",
        },
        {
            "output_object": "淘汰赛",
            "typical_result": "晋级概率、加时/点球概率、对阵路径难度",
            "current_status": "planned",
            "current_evidence": "Futures 行可做阶段概率研究；路径难度、加时/点球仍需赛制模拟器。",
            "next_upgrade": "接入淘汰赛 bracket、加时/点球概率和路径强度。",
        },
        {
            "output_object": "整届世界杯",
            "typical_result": "进32强、16强、8强、4强、决赛、夺冠概率",
            "current_status": "planned",
            "current_evidence": "开源模型库含 Monte Carlo 路径参考；本报告未把整届模拟结果伪装成已上线。",
            "next_upgrade": "固定 seed 做 Monte Carlo 锦标赛模拟并保存版本化输出。",
        },
        {
            "output_object": "风控",
            "typical_result": "模型置信度、校准误差、与市场分歧、数据质量风险",
            "current_status": "implemented_partial",
            "current_evidence": "已输出模型一致性、复核优先级、Risk of ruin、资料缺口、门禁状态和安全边界。",
            "next_upgrade": "补 Brier score、log loss、校准曲线和按盘口类型的 CLV 复盘。",
        },
    ]
    modules = [
        {
            "module": "赛制规则引擎",
            "recommended_status": "必做",
            "role": "精确模拟小组、第三名、淘汰赛路径。",
            "key_output": "小组排名、最佳第三、32强对阵。",
            "current_status": "planned",
        },
        {
            "module": "球队强度评级",
            "recommended_status": "必做",
            "role": "建立球队先验实力。",
            "key_output": "攻击强度、防守强度、中立场胜率。",
            "current_status": "partial_reference",
        },
        {
            "module": "单场进球模型",
            "recommended_status": "必做",
            "role": "预测比分和胜平负。",
            "key_output": "比分矩阵、P(胜/平/负)、总进球。",
            "current_status": "partial_proxy",
        },
        {
            "module": "xG / xT / VAEP 特征",
            "recommended_status": "强烈推荐",
            "role": "衡量过程质量，而非只看比分。",
            "key_output": "射门质量、推进威胁、机会创造。",
            "current_status": "design_reference",
        },
        {
            "module": "球员与阵容层",
            "recommended_status": "强烈推荐",
            "role": "捕捉伤停、轮换、核心球员缺阵。",
            "key_output": "球员缺阵影响、首发强度。",
            "current_status": "manual_checklist",
        },
        {
            "module": "市场赔率基准",
            "recommended_status": "推荐",
            "role": "作为强基准和外部共识。",
            "key_output": "市场隐含概率、模型分歧。",
            "current_status": "implemented",
        },
        {
            "module": "Monte Carlo 模拟",
            "recommended_status": "必做",
            "role": "评估整届赛事路径。",
            "key_output": "出线率、晋级率、夺冠率。",
            "current_status": "planned",
        },
        {
            "module": "概率校准",
            "recommended_status": "必做",
            "role": "防止看似准确但概率失真。",
            "key_output": "Log loss、Brier、校准曲线。",
            "current_status": "partial",
        },
        {
            "module": "新闻/伤停监控",
            "recommended_status": "推荐",
            "role": "临赛前修正模型。",
            "key_output": "阵容更新、天气、旅行、纪律。",
            "current_status": "manual_checklist",
        },
        {
            "module": "回测与版本管理",
            "recommended_status": "必做",
            "role": "让预测可复现。",
            "key_output": "数据版本、模型版本、预测时间戳。",
            "current_status": "partial",
        },
    ]
    objective_modules = [
        {
            "module": "赔率/盘口分析",
            "goal": "判断市场价格是否合理。",
            "common_metrics": "欧赔、亚盘、大小球、隐含概率、返还率、盘口变化。",
            "output": "是否存在 value bet。",
            "current_status": "implemented_partial",
        },
        {
            "module": "球队实力分析",
            "goal": "估计双方真实强弱。",
            "common_metrics": "Elo、近期xG/xGA、净胜球、射门质量、控球推进、定位球。",
            "output": "基础胜平负概率。",
            "current_status": "partial_reference",
        },
        {
            "module": "进球模型",
            "goal": "估计比分分布。",
            "common_metrics": "泊松、双泊松、Dixon-Coles、xG-adjusted Poisson。",
            "output": "1X2、大小球、BTTS、比分概率。",
            "current_status": "planned",
        },
        {
            "module": "阵容与战术",
            "goal": "判断模型外信息。",
            "common_metrics": "伤停、轮换、首发、赛程、压迫强度、边路错位。",
            "output": "修正胜率和进球期望。",
            "current_status": "manual_checklist",
        },
        {
            "module": "赛事语境",
            "goal": "处理动机和赛制。",
            "common_metrics": "小组赛/淘汰赛、必须赢、轮换、净胜球需求。",
            "output": "调整节奏和风险偏好。",
            "current_status": "planned",
        },
        {
            "module": "市场选择",
            "goal": "选最适合的玩法。",
            "common_metrics": "1X2、亚洲让球、大小球、角球、牌数、球员数据。",
            "output": "选择赔率误差最大的市场。",
            "current_status": "implemented_partial",
        },
        {
            "module": "资金管理",
            "goal": "防止破产。",
            "common_metrics": "固定比例、半 Kelly、最大回撤、止损。",
            "output": "每注金额。",
            "current_status": "implemented_partial",
        },
        {
            "module": "复盘验证",
            "goal": "检查方法是否有效。",
            "common_metrics": "CLV、ROI、样本量、Brier score、校准曲线。",
            "output": "保留/淘汰策略。",
            "current_status": "partial",
        },
    ]
    ml_models = [
        {"model": "Logistic Regression", "task": "胜平负、是否晋级。", "strength": "可解释、稳定。", "risk": "非线性不足。", "current_decision": "baseline_candidate", "current_status": "planned"},
        {"model": "Random Forest", "task": "非线性特征。", "strength": "鲁棒。", "risk": "概率校准一般。", "current_decision": "benchmark_candidate", "current_status": "planned"},
        {"model": "XGBoost / LightGBM", "task": "表格特征融合。", "strength": "表现强。", "risk": "容易数据泄露。", "current_decision": "candidate_after_leakage_gate", "current_status": "planned"},
        {"model": "CatBoost", "task": "类别特征多。", "strength": "对类别友好。", "risk": "参数调优复杂。", "current_decision": "candidate_after_data_volume_check", "current_status": "planned"},
        {"model": "Neural Network", "task": "大规模事件序列。", "strength": "表达能力强。", "risk": "国际赛样本不足。", "current_decision": "defer_until_event_data", "current_status": "research_reference"},
        {"model": "Graph Neural Network", "task": "球员网络/传球网络。", "strength": "战术表达强。", "risk": "数据门槛高。", "current_decision": "research_reference_only", "current_status": "research_reference"},
        {"model": "Transformer", "task": "事件序列建模。", "strength": "可捕捉上下文。", "risk": "对公开数据要求高。", "current_decision": "research_reference_only", "current_status": "research_reference"},
    ]
    technical_rules = [
        {
            "name": "EV 期望下注",
            "formula": "EV = 模型认为的胜利概率 × 盘口赔率 - 1",
            "decision_rule": "EV 大于 0 才可能进入价值候选；仍需 Edge、RoR、价格容忍度和门禁复核。",
            "current_status": "implemented",
        },
        {
            "name": "RAEV 去水后价值",
            "formula": "RAEV = 模型认为的胜利概率 × 去水后盘口公平赔率 - 1",
            "decision_rule": "用于区分真实模型优势和庄家水位造成的表面优势。",
            "current_status": "planned",
        },
        {
            "name": "去水公平概率",
            "formula": "去水 = 将同一市场所有隐含概率归一化为 100%",
            "decision_rule": "先把赔率转隐含概率，再去除水位，最后比较模型概率和公平概率。",
            "current_status": "partial",
        },
        {
            "name": "Value bet纪律",
            "formula": "Edge = 模型概率 - 去水公平概率；Edge ≥ 2%-3% 且 EV > 0 才下注",
            "decision_rule": "小市场使用更高缓冲；资料缺口或盘口异常时降级为观察。",
            "current_status": "implemented_partial",
        },
        {
            "name": "CLV 信息捕获",
            "formula": "CLV = 下注时赔率是否优于 closing odds",
            "decision_rule": "长期正 CLV 才说明可能比市场更早捕捉信息；单次正 CLV 不等于策略有效。",
            "current_status": "partial",
        },
    ]
    scoring_models = [
        {
            "name": "Poisson Model",
            "formula": "主队进球数 ~ Poisson(lambda_home)；客队进球数 ~ Poisson(lambda_away)",
            "use": "用 lambda_home / lambda_away 生成比分分布、胜平负和总进球概率。",
            "current_status": "planned",
        },
        {
            "name": "Dixon-Coles-Adjusted Poisson Model",
            "formula": "在普通双泊松上修正 0-0、1-0、0-1、1-1 等低比分相关性。",
            "use": "减少低比分市场误差，尤其用于 1X2、OU、BTTS 和 Correct Score。",
            "current_status": "planned",
        },
    ]
    fundamental_layers = [
        {"layer": "Team Level", "inputs": "Home/Away、阵容、伤停、赛程、近期胜率、进球时间分布。", "decision_use": "调整基础胜平负概率、进球期望和轮换风险。", "current_status": "manual_checklist"},
        {"layer": "Player Level", "inputs": "核心球员缺阵、首发强度、替补深度、纪律停赛。", "decision_use": "修正球队强度和临场不确定性。", "current_status": "planned"},
        {"layer": "Tactical Style", "inputs": "压迫强度、边路错位、定位球、控球推进、射门质量。", "decision_use": "识别盘口类型适配度，例如总进球、BTTS、角球或牌数。", "current_status": "design_reference"},
        {"layer": "News Context", "inputs": "confirmed 新闻、rumor 新闻、天气、旅行、赛前发布会。", "decision_use": "临赛前复核，confirmed 才进入概率修正，rumor 只进风险提示。", "current_status": "planned"},
    ]
    tournament_rule_requirements = [
        {"rule": "48队 / 12组 / 每组4队", "decision_use": "所有小组出线、Group Winner、To Qualify、Stage of Elimination 概率的基础分母。", "current_status": "planned", "automation_gate": "未实装前，长线阶段盘只保留研究候选，不把路径概率伪装成真实模拟结果。"},
        {"rule": "每队小组三场", "decision_use": "赛程密度、轮换、净胜球需求和末轮动机修正。", "current_status": "planned", "automation_gate": "需要 fixtures/versioned schedule 才能进入 Monte Carlo。"},
        {"rule": "小组前二 + 8个最佳第三晋级32强", "decision_use": "第三名出线概率、保守比赛策略和小组末轮价值盘筛选。", "current_status": "planned", "automation_gate": "必须实现 best-third ranking 后，才解锁完整小组出线概率。"},
        {"rule": "小组排名 Tie-breakers", "decision_use": "同分下的净胜球、进球数、相互战绩、纪律分等排序影响组内盘口概率。", "current_status": "planned", "automation_gate": "未实现细则前，净胜球和纪律分盘口只作为人工复核项。"},
        {"rule": "32强至决赛单场淘汰", "decision_use": "晋级路径、对阵难度、加时/点球风险和资金锁定时间。", "current_status": "planned", "automation_gate": "必须生成 bracket path version 才能发布阶段概率。"},
        {"rule": "加时与点球", "decision_use": "淘汰赛晋级盘和90分钟赛果盘需要分开建模，不能混用概率。", "current_status": "planned", "automation_gate": "报告必须区分 90分钟、含加时、含点球 的盘口定义。"},
        {"rule": "中立场与主办国例外", "decision_use": "主客场标签不能直接照搬俱乐部模型；主办国和场地旅行需要额外修正。", "current_status": "manual_checklist", "automation_gate": "赛前原因必须注明中立场/旅行/休息天数是否已复核。"},
        {"rule": "时间滚动资金约束", "decision_use": "早期下注结算后会影响后续预算；不能静态把预算长期锁死。", "current_status": "implemented_partial", "automation_gate": "私有持仓未同步前，新增执行金额保持 AUD 0。"},
    ]
    prediction_contract_fields = [
        {"field": "prediction_timestamp", "required": True, "decision_use": "每条概率和操作建议必须知道生成时点，便于按4小时频率追踪新旧变化。", "current_status": "implemented"},
        {"field": "model_version", "required": True, "decision_use": "同一盘口跨日报比较时区分模型变化、数据变化和赔率变化。", "current_status": "policy_defined"},
        {"field": "data_source_version", "required": True, "decision_use": "区分 TAB raw、公开赛程、开源模型和新闻源的版本。", "current_status": "partial"},
        {"field": "odds_phase", "required": True, "decision_use": "opening / current / closing odds 分开记录，支持 CLV 和价格走差判断。", "current_status": "planned"},
        {"field": "feature_time_scope", "required": True, "decision_use": "赛前、赛中、赛后特征严格隔离，避免把赛后信息泄漏进赛前预测。", "current_status": "policy_defined"},
        {"field": "news_confidence", "required": True, "decision_use": "confirmed 新闻可修正概率，rumor 只进入风险提示和降仓判断。", "current_status": "planned"},
        {"field": "random_seed", "required": True, "decision_use": "Monte Carlo 和抽样模型可复现，避免同一输入重复运行给出漂移概率。", "current_status": "policy_defined"},
        {"field": "market_definition", "required": True, "decision_use": "区分90分钟、晋级、冠军、阶段淘汰、球员进球等盘口定义。", "current_status": "implemented_partial"},
        {"field": "execution_gate_state", "required": True, "decision_use": "raw/private/report safety 未过时，候选只能 research-only，金额降为 AUD 0。", "current_status": "implemented"},
    ]
    calibration_backtest_controls = [
        {"control": "Brier score", "purpose": "衡量概率预测平方误差，防止只看命中率。", "current_status": "planned", "automation_use": "按盘口类型和模型版本分桶。"},
        {"control": "Log loss", "purpose": "惩罚过度自信的错误预测。", "current_status": "planned", "automation_use": "用于降低高置信但校准差的模型权重。"},
        {"control": "Calibration curve", "purpose": "检查 55%、60%、70% 概率区间真实命中率是否匹配。", "current_status": "planned", "automation_use": "日/周报展示校准漂移。"},
        {"control": "CLV by market", "purpose": "判断入场价格是否长期优于收盘价。", "current_status": "partial", "automation_use": "正 CLV 策略保留，负 CLV 策略降权。"},
        {"control": "ROI with sample guard", "purpose": "真实收益必须结合样本量，避免小样本误判。", "current_status": "partial", "automation_use": "按单场/长线/小市场分开评估。"},
        {"control": "Closing odds store", "purpose": "记录 closing odds 才能回测 CLV、RAEV 和价格纪律。", "current_status": "planned", "automation_use": "赛前定时抓取并锁定 closing 快照。"},
        {"control": "Settled position import", "purpose": "把已下注、已结算、赢亏和余额变化同步到资金模型。", "current_status": "blocked_by_private_profile", "automation_use": "只读 My Bets 登录态未完成前不能解锁新增执行金额。"},
    ]
    pipeline = [
        {"step": "数据抓取", "current_status": "partial", "control": "公开 raw refresh 门禁；失败时不解锁执行金额。"},
        {"step": "数据校验", "current_status": "implemented_partial", "control": "public artifact safety、board scope、route mismatch、staged raw gate。"},
        {"step": "特征生成", "current_status": "partial", "control": "EV/Edge/RoR/市场资金代理已生成；xG/xT/VAEP仍为规划层。"},
        {"step": "模型训练", "current_status": "planned", "control": "Bayesian hierarchical / ML 模型尚未声称上线。"},
        {"step": "概率校准", "current_status": "partial", "control": "开源模型分歧复核已接入；Brier/log loss/校准曲线待补。"},
        {"step": "赛制模拟", "current_status": "planned", "control": "48队规则、第三名出线、淘汰赛路径待实装。"},
        {"step": "报告生成", "current_status": "implemented", "control": "JSON/Markdown/PDF/首页均输出研究-only报告。"},
        {"step": "模型监控", "current_status": "partial", "control": "source model freshness、raw freshness、backfill queue、CLV/ROI路线。"},
        {"step": "结果回测", "current_status": "partial", "control": "CLV/ROI回测 Dashboard 已有入口；样本与 settled 持仓仍受 private gate 影响。"},
        {"step": "异常告警", "current_status": "partial", "control": "raw/private blockers、缺失报告、stale source 显示在 Dashboard。"},
    ]
    leakage_controls = [
        {"control": "每条预测 timestamp", "required": True, "current_status": "implemented", "evidence": "payload generated_at、snapshot_id 和 report_date。"},
        {"control": "每次运行固定 random seed", "required": True, "current_status": "policy_defined", "evidence": f"seed policy={PROBABILITY_ENGINE_SEED}；完整 Monte Carlo 尚未上线。"},
        {"control": "每个数据源版本号", "required": True, "current_status": "partial", "evidence": "source_model_registry、latest_commit、raw health 有版本/时间；新闻源版本待补。"},
        {"control": "opening / closing 赔率区分", "required": True, "current_status": "planned", "evidence": "当前有入场/收盘赔率复盘口径；完整 opening/closing odds store 待补。"},
        {"control": "confirmed / rumor 新闻区分", "required": True, "current_status": "planned", "evidence": "赛前清单要求复核，尚未接新闻源分级。"},
        {"control": "赛前/赛中/赛后特征隔离", "required": True, "current_status": "policy_defined", "evidence": "下注报告仅使用赛前研究数据；赛中/赛后特征隔离规则已写入政策。"},
    ]
    metrics = [
        {"metric": "CLV", "purpose": "验证是否比收盘市场更早捕捉信息。", "current_status": "partial"},
        {"metric": "ROI", "purpose": "复盘真实收益，但样本不足时不能单独评价模型。", "current_status": "partial"},
        {"metric": "Brier score", "purpose": "衡量概率预测平方误差。", "current_status": "planned"},
        {"metric": "Log loss", "purpose": "惩罚过度自信的错误概率。", "current_status": "planned"},
        {"metric": "校准曲线", "purpose": "检查预测概率与真实命中频率是否一致。", "current_status": "planned"},
        {"metric": "模型-市场分歧", "purpose": "识别 value bet 与逆共识复核队列。", "current_status": "implemented_partial"},
    ]
    status_counts = Counter(
        item["current_status"]
        for item in modules
        + objective_modules
        + ml_models
        + technical_rules
        + scoring_models
        + fundamental_layers
        + tournament_rule_requirements
        + prediction_contract_fields
        + calibration_backtest_controls
        + pipeline
        + leakage_controls
        + metrics
    )
    return {
        "schema_version": 1,
        "status": "framework_mapped_partial_implementation",
        "truthfulness_note": "本层吸收 ChatGPT 概率工程建议，并标注当前实现状态；未上线的 Dixon-Coles、Bayesian hierarchical、MCMC、xG/xT/VAEP、Monte Carlo 和新闻监控不会被伪装成已实现。",
        "fixed_random_seed_policy": PROBABILITY_ENGINE_SEED,
        "reference_adoption": {
            "source_reference_count": reference_count,
            "implemented_reference_count": implemented_sources,
            "template_read_status": excel_reference.get("template_read_status", "static_profile"),
        },
        "outputs": outputs,
        "modules": modules,
        "objective_modules": objective_modules,
        "ml_models": ml_models,
        "technical_rules": technical_rules,
        "scoring_models": scoring_models,
        "fundamental_layers": fundamental_layers,
        "tournament_rule_requirements": tournament_rule_requirements,
        "prediction_contract_fields": prediction_contract_fields,
        "calibration_backtest_controls": calibration_backtest_controls,
        "pipeline": pipeline,
        "leakage_controls": leakage_controls,
        "metrics": metrics,
        "current_status_counts": dict(status_counts),
        "default_next_upgrade": "优先补齐 opening/closing odds store、Brier/log loss 校准、赛制规则引擎、预测合约字段和 fixed-seed Monte Carlo；再接新闻/伤停 confirmed-vs-rumor 分级。",
    }


def probability_engine_summary(engine: dict[str, Any]) -> dict[str, Any]:
    modules = engine.get("modules") or []
    leakage_controls = engine.get("leakage_controls") or []
    metrics = engine.get("metrics") or []
    objective_modules = engine.get("objective_modules") or []
    ml_models = engine.get("ml_models") or []
    technical_rules = engine.get("technical_rules") or []
    scoring_models = engine.get("scoring_models") or []
    fundamental_layers = engine.get("fundamental_layers") or []
    tournament_rule_requirements = engine.get("tournament_rule_requirements") or []
    prediction_contract_fields = engine.get("prediction_contract_fields") or []
    calibration_backtest_controls = engine.get("calibration_backtest_controls") or []
    implemented_statuses = {"implemented", "implemented_partial", "partial", "partial_proxy", "partial_reference"}
    planned_statuses = {"planned", "design_reference", "manual_checklist", "policy_defined", "blocked_by_private_profile"}
    return {
        "probability_engine_status": engine.get("status", ""),
        "probability_engine_module_count": len(modules),
        "probability_engine_implemented_or_partial_count": sum(1 for item in modules if item.get("current_status") in implemented_statuses),
        "probability_engine_planned_or_policy_count": sum(1 for item in modules if item.get("current_status") in planned_statuses),
        "probability_engine_leakage_control_count": len(leakage_controls),
        "probability_engine_leakage_policy_defined_count": sum(1 for item in leakage_controls if item.get("current_status") in {"implemented", "partial", "policy_defined"}),
        "probability_engine_metric_count": len(metrics),
        "probability_engine_calibration_metric_count": sum(1 for item in metrics if item.get("metric") in {"Brier score", "Log loss", "校准曲线"}),
        "probability_engine_objective_module_count": len(objective_modules),
        "probability_engine_ml_model_count": len(ml_models),
        "probability_engine_technical_rule_count": len(technical_rules),
        "probability_engine_implemented_technical_rule_count": sum(1 for item in technical_rules if item.get("current_status") in implemented_statuses),
        "probability_engine_scoring_model_count": len(scoring_models),
        "probability_engine_fundamental_layer_count": len(fundamental_layers),
        "probability_engine_tournament_rule_count": len(tournament_rule_requirements),
        "probability_engine_tournament_rule_ready_count": sum(1 for item in tournament_rule_requirements if item.get("current_status") in implemented_statuses),
        "probability_engine_prediction_contract_field_count": len(prediction_contract_fields),
        "probability_engine_prediction_contract_ready_count": sum(1 for item in prediction_contract_fields if item.get("current_status") in implemented_statuses | {"policy_defined"}),
        "probability_engine_backtest_control_count": len(calibration_backtest_controls),
        "probability_engine_backtest_ready_count": sum(1 for item in calibration_backtest_controls if item.get("current_status") in implemented_statuses),
    }


def model_calibration_index(output_dir: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(Path(output_dir) / MODEL_COMPARISON_JSON)
    index: dict[str, dict[str, Any]] = {}
    for row in payload.get("rows") or []:
        if not isinstance(row, dict):
            continue
        match = str(row.get("match") or "").strip()
        if match:
            index[match] = row
    return index


def model_calibration_for_recommendation(
    *,
    event: Any,
    market: Any,
    selection: Any,
    probability: Any,
    model_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    match = str(event or "").strip()
    row = model_index.get(match)
    if not row:
        return {
            "status": "model_missing",
            "match": match,
            "consistency_label": "待模型校准",
            "confidence_zh": "待校准",
            "review_priority": "中",
            "review_action": "补齐模型对比后再判断分析一致性",
            "recommendation_impact": "当前推荐仅依赖本地赔率/EV/RoR，缺少开源模型交叉验证。",
            "evidence_text": "未找到该盘口对应的开源模型对比行。",
        }
    consensus = row.get("consensus") or {}
    disagreement = row.get("disagreement") or {}
    model_key = model_market_key(row, market, selection)
    model_probability = model_market_probability(row, model_key)
    model_spread = model_market_spread(row, model_key)
    local_probability = to_float(probability)
    probability_gap = None
    if local_probability is not None and model_probability is not None:
        probability_gap = round(local_probability - model_probability, 4)
    consensus_selection = str(consensus.get("selection") or "")
    confidence = str(consensus.get("confidence") or "unknown")
    high_divergence = bool(disagreement.get("high_divergence"))
    selection_alignment = selection_alignment_label(row, market, selection, model_key)
    consistency = model_consistency_label(
        selection_alignment=selection_alignment,
        confidence=confidence,
        high_divergence=high_divergence,
        probability_gap=probability_gap,
        model_key=model_key,
    )
    priority = model_review_priority(
        selection_alignment=selection_alignment,
        confidence=confidence,
        high_divergence=high_divergence,
        probability_gap=probability_gap,
        model_key=model_key,
    )
    action = model_review_action(priority, consistency)
    impact = model_recommendation_impact(consistency, priority, probability_gap, model_key)
    return {
        "status": "model_linked",
        "source_report": MODEL_COMPARISON_JSON,
        "match": match,
        "market": str(market or ""),
        "selection": str(selection or ""),
        "consensus_selection": consensus_selection,
        "consensus_probability": to_float(consensus.get("mean_probability")),
        "consensus_confidence": confidence,
        "confidence_zh": confidence_zh(confidence),
        "model_spread": to_float(consensus.get("model_spread")),
        "max_disagreement": to_float(disagreement.get("max_abs_current_vs_elo_dc")),
        "high_divergence": high_divergence,
        "rating_source": str((row.get("ratings") or {}).get("source") or ""),
        "market_model_key": model_key,
        "market_model_probability": model_probability,
        "market_model_spread": model_spread,
        "local_probability": local_probability,
        "probability_gap_vs_model": probability_gap,
        "selection_alignment": selection_alignment,
        "consistency_label": consistency,
        "review_priority": priority,
        "review_action": action,
        "recommendation_impact": impact,
        "evidence_text": model_calibration_evidence_text(
            consensus_selection=consensus_selection,
            consensus_probability=consensus.get("mean_probability"),
            confidence=confidence,
            high_divergence=high_divergence,
            max_disagreement=disagreement.get("max_abs_current_vs_elo_dc"),
            model_key=model_key,
            model_probability=model_probability,
            probability_gap=probability_gap,
            consistency=consistency,
        ),
        "manual_use_only": "模型校准只用于一致性解释、复核优先级和降仓判断，不自动下注。",
    }


def model_market_key(model_row: dict[str, Any], market: Any, selection: Any) -> str:
    market_text = normalize_text(market)
    selection_text = normalize_text(selection)
    home = normalize_text(model_row.get("home"))
    away = normalize_text(model_row.get("away"))
    if "result" in market_text or "winner" in market_text or "match" in market_text:
        if selection_text == home:
            return "home_win"
        if selection_text == away:
            return "away_win"
        if selection_text == "draw":
            return "draw"
    if "total" in market_text or "over under" in market_text or "goals" in market_text:
        if "under" in selection_text:
            return "under_2_5"
        if "over" in selection_text:
            return "over_2_5"
    if "both teams" in market_text or "btts" in market_text:
        if "only one" in selection_text or "neither" in selection_text or selection_text in {"no", "btts no"}:
            return "btts_no"
        if "yes" in selection_text or "both" in selection_text:
            return "btts_yes"
    return ""


def model_market_probability(model_row: dict[str, Any], key: str) -> float | None:
    if not key:
        return None
    values = []
    for block_name in ["current_market_poisson", "goalmodel_market_dc_proxy", "open_source_elo_dixon_coles"]:
        value = to_float((model_row.get(block_name) or {}).get(key))
        if value is not None:
            values.append(value)
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def model_market_spread(model_row: dict[str, Any], key: str) -> float | None:
    if not key:
        return None
    values = []
    for block_name in ["current_market_poisson", "goalmodel_market_dc_proxy", "open_source_elo_dixon_coles"]:
        value = to_float((model_row.get(block_name) or {}).get(key))
        if value is not None:
            values.append(value)
    if len(values) < 2:
        return None
    return round(max(values) - min(values), 4)


def selection_alignment_label(model_row: dict[str, Any], market: Any, selection: Any, model_key: str) -> str:
    market_text = normalize_text(market)
    selection_text = normalize_text(selection)
    consensus_text = normalize_text((model_row.get("consensus") or {}).get("selection"))
    if model_key in {"home_win", "away_win", "draw"}:
        if selection_text == consensus_text:
            return "aligned_with_consensus"
        return "against_consensus"
    if model_key:
        return "market_probability_supported"
    if "qualify" in market_text or "group" in market_text:
        return "outright_context_only"
    return "unsupported_market"


def model_consistency_label(
    *,
    selection_alignment: str,
    confidence: str,
    high_divergence: bool,
    probability_gap: float | None,
    model_key: str,
) -> str:
    if not model_key and selection_alignment == "outright_context_only":
        return "模型仅作背景"
    if not model_key:
        return "模型未覆盖盘口"
    if high_divergence:
        return "模型分歧高"
    if selection_alignment == "against_consensus":
        return "逆共识价值复核"
    gap_abs = abs(probability_gap) if probability_gap is not None else None
    if gap_abs is not None and gap_abs > 0.08:
        return "模型概率偏离"
    if confidence.lower() == "high":
        return "模型一致-强"
    if confidence.lower() == "medium":
        return "模型一致-中"
    return "模型一致-低置信"


def model_review_priority(
    *,
    selection_alignment: str,
    confidence: str,
    high_divergence: bool,
    probability_gap: float | None,
    model_key: str,
) -> str:
    score = 0
    if not model_key:
        score += 1
    if high_divergence:
        score += 3
    if selection_alignment == "against_consensus":
        score += 2
        if confidence.lower() == "high":
            score += 2
    if confidence.lower() == "low":
        score += 2
    elif confidence.lower() == "medium":
        score += 1
    if probability_gap is not None and abs(probability_gap) > 0.08:
        score += 2
    if score >= 4:
        return "高"
    if score >= 2:
        return "中"
    return "低"


def model_review_action(priority: str, consistency: str) -> str:
    if priority == "高":
        return "优先人工复核，必要时降仓或放弃"
    if priority == "中":
        return "保留研究候选，赛前复核模型与基本面"
    if consistency in {"模型一致-强", "模型一致-中"}:
        return "可作为支持证据，但仍需实时赔率确认"
    return "低优先级监控"


def model_recommendation_impact(consistency: str, priority: str, probability_gap: float | None, model_key: str) -> str:
    if not model_key:
        return "该盘口超出当前比赛级模型覆盖，只能作为背景解释，不提升下注置信度。"
    if priority == "高":
        return "模型层要求复核，不能因 EV/Edge 为正直接执行；如门禁未来通过也应优先确认首发、新闻和价格。"
    if probability_gap is not None and probability_gap > 0.08:
        return "本地概率显著高于开源模型均值，价值可能来自模型差异，需降低置信度。"
    if consistency in {"模型一致-强", "模型一致-中"}:
        return "开源模型层与本地概率方向基本一致，可提高解释质量，但不解锁执行门禁。"
    return "模型层仅提供辅助解释，执行前仍以实时赔率、raw/private门禁和赛前清单为准。"


def model_calibration_evidence_text(
    *,
    consensus_selection: Any,
    consensus_probability: Any,
    confidence: str,
    high_divergence: bool,
    max_disagreement: Any,
    model_key: str,
    model_probability: Any,
    probability_gap: Any,
    consistency: str,
) -> str:
    key_text = model_key or "未映射盘口"
    return (
        f"开源模型共识 {consensus_selection or '待校准'} / {pct(consensus_probability)} / {confidence_zh(confidence)}；"
        f"最大分歧 {pct(max_disagreement)}，高分歧={high_divergence}；"
        f"盘口映射 {key_text}，模型均值 {pct(model_probability)}，本地概率差 {pp(probability_gap)}；"
        f"一致性结论：{consistency}。"
    )


def confidence_zh(value: Any) -> str:
    return {"high": "高", "medium": "中", "low": "低"}.get(str(value or "").lower(), "待校准")


def normalize_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def recommendation_rows(
    output_dir: Path,
    db_path: Path,
    latest_commit: dict[str, Any],
    limit: int = 12,
    bankroll_reference: float = DEFAULT_BANKROLL_REFERENCE_AUD,
) -> list[dict[str, Any]]:
    run_id = str(latest_commit.get("run_id") or "")
    if not run_id or not Path(db_path).exists():
        return []
    time_index = match_time_index(output_dir)
    uri = f"file:{Path(db_path).resolve()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        db_rows = conn.execute(
            """
            SELECT board_id, board_name, rank, event_name, market, selection, odds,
                   probability, expected_value, stake_aud, action, raw_json
            FROM recommendations
            WHERE run_id = ?
            ORDER BY
              CASE WHEN action = 'buy' THEN 0 ELSE 1 END,
              stake_aud DESC,
              COALESCE(expected_value, -999) DESC,
              rank ASC
            LIMIT ?
            """,
            (run_id, limit),
        ).fetchall()
    finally:
        conn.close()
    rows: list[dict[str, Any]] = []
    model_index = model_calibration_index(output_dir)
    for row in db_rows:
        raw = parse_json(row["raw_json"])
        probability = row["probability"]
        odds = row["odds"]
        breakeven = (1 / float(odds)) if odds else None
        edge = raw.get("edge")
        if edge is None and probability is not None and breakeven is not None:
            edge = float(probability) - breakeven
        stake = float(row["stake_aud"] or 0)
        risk_flags = int((raw.get("event_risk") or {}).get("flag_count") or 0)
        arbitrage_rate = value_arbitrage_rate(row["expected_value"], probability, odds)
        kelly = full_kelly_fraction(probability, odds)
        half_kelly = discounted_kelly_fraction(probability, odds)
        ruin_risk = risk_of_ruin_estimate(probability, odds, stake, bankroll_reference, risk_flags=risk_flags)
        threshold = market_edge_threshold(row["market"])
        threshold_gap = edge_threshold_gap(edge, threshold)
        risk_grade = risk_of_ruin_grade(ruin_risk)
        stake_fraction = stake_fraction_of_bankroll(stake, bankroll_reference)
        half_kelly_ratio = over_half_kelly_ratio(stake_fraction, half_kelly)
        expected_profit = expected_profit_aud(stake, row["expected_value"])
        expected_profit_100 = expected_profit_per_100_aud(row["expected_value"])
        min_acceptable_odds = minimum_acceptable_odds(probability, threshold)
        current_odds_buffer = odds_buffer(odds, min_acceptable_odds)
        current_price_tolerance = price_drift_tolerance_pct(current_odds_buffer, odds)
        stake_cap_ratio = stake_to_cap_ratio(stake_fraction)
        kelly_margin = kelly_safety_margin(half_kelly_ratio)
        value_score = risk_adjusted_value_score(row["expected_value"], threshold_gap, ruin_risk)
        value_signal = value_signal_label(row["expected_value"], threshold_gap, current_odds_buffer, ruin_risk)
        drivers = risk_drivers(
            edge=edge,
            edge_threshold_gap=threshold_gap,
            risk_of_ruin=ruin_risk,
            stake_fraction=stake_fraction,
            half_kelly_ratio=half_kelly_ratio,
            risk_flags=risk_flags,
        )
        diagnostic = decision_diagnostics(
            probability=probability,
            odds=odds,
            edge=edge,
            edge_threshold=threshold,
            edge_threshold_gap=threshold_gap,
            expected_value=row["expected_value"],
            stake_aud=stake,
            expected_profit=expected_profit,
            expected_profit_100=expected_profit_100,
            min_acceptable_odds=min_acceptable_odds,
            current_odds_buffer=current_odds_buffer,
            price_tolerance=current_price_tolerance,
            risk_of_ruin=ruin_risk,
            risk_grade=risk_grade,
            stake_fraction=stake_fraction,
            half_kelly_ratio=half_kelly_ratio,
            stake_cap_ratio=stake_cap_ratio,
            kelly_margin=kelly_margin,
            value_score=value_score,
            value_signal=value_signal,
            risk_drivers=drivers,
        )
        metric_pack = decision_metric_pack(
            probability=probability,
            breakeven=breakeven,
            edge=edge,
            edge_threshold=threshold,
            edge_threshold_gap=threshold_gap,
            arbitrage_rate=arbitrage_rate,
            expected_value=row["expected_value"],
            risk_of_ruin=ruin_risk,
            risk_grade=risk_grade,
            diagnostic=diagnostic,
            risk_drivers=drivers,
        )
        model_calibration = model_calibration_for_recommendation(
            event=row["event_name"],
            market=row["market"],
            selection=row["selection"],
            probability=probability,
            model_index=model_index,
        )
        analysis_basis = row_analysis_basis(
            row=row,
            raw=raw,
            breakeven=breakeven,
            edge=edge,
            edge_threshold=threshold,
            edge_threshold_gap=threshold_gap,
            arbitrage_rate=arbitrage_rate,
            risk_of_ruin=ruin_risk,
            risk_grade=risk_grade,
            risk_drivers=drivers,
            diagnostic=diagnostic,
            bankroll_reference=bankroll_reference,
            model_calibration=model_calibration,
        )
        funding_profile = market_funding_profile(
            board=row["board_name"],
            market=row["market"],
            selection=row["selection"],
            odds=odds,
            probability=probability,
            expected_value=row["expected_value"],
            edge=edge,
            arbitrage_rate=arbitrage_rate,
            price_drift_tolerance=current_price_tolerance,
            stake_aud=stake,
            stake_fraction=stake_fraction,
            risk_of_ruin=ruin_risk,
            risk_flags=risk_flags,
        )
        action_class = "buy" if stake > 0 else "watch"
        consistency = model_calibration.get("consistency_label") or consistency_label(raw)
        confidence = model_calibration.get("confidence_zh") or confidence_label(raw)
        reason = chinese_reason(
            row,
            raw,
            breakeven,
            edge,
            arbitrage_rate,
            ruin_risk,
            bankroll_reference,
            edge_threshold=threshold,
            edge_threshold_gap=threshold_gap,
            risk_grade=risk_grade,
            risk_drivers=drivers,
            decision_diagnostic=diagnostic,
            model_calibration=model_calibration,
        )
        reason += market_funding_reason(funding_profile)
        rows.append(
            {
                "row_key": row_key(row["board_name"], row["event_name"], row["market"], row["selection"]),
                "time": time_index.get(str(row["event_name"]), "长期/待赛程"),
                "board_id": row["board_id"],
                "board": row["board_name"],
                "rank": int(row["rank"] or 0),
                "event": row["event_name"],
                "market": row["market"],
                "selection": row["selection"],
                "odds": odds,
                "probability": probability,
                "breakeven": breakeven,
                "edge": edge,
                "edge_pp": edge,
                "edge_threshold": threshold,
                "edge_threshold_range": market_edge_threshold_range(row["market"]),
                "edge_threshold_gap": threshold_gap,
                "edge_quality": edge_quality_label(edge, threshold),
                "expected_value": row["expected_value"],
                "arbitrage_rate": arbitrage_rate,
                "minimum_acceptable_odds": min_acceptable_odds,
                "odds_buffer": current_odds_buffer,
                "expected_profit_aud": expected_profit,
                "expected_profit_per_100_aud": expected_profit_100,
                "price_drift_tolerance_pct": current_price_tolerance,
                "full_kelly_fraction": kelly,
                "discounted_kelly_fraction": half_kelly,
                "risk_of_ruin": ruin_risk,
                "risk_of_ruin_grade": risk_grade,
                "stake_fraction": stake_fraction,
                "stake_to_cap_ratio": stake_cap_ratio,
                "half_kelly_ratio": half_kelly_ratio,
                "kelly_safety_margin": kelly_margin,
                "risk_adjusted_value_score": value_score,
                "value_signal": value_signal,
                "risk_drivers": drivers,
                "edge_information": {
                    "model_probability": probability,
                    "breakeven_probability": breakeven,
                    "edge": edge,
                    "edge_threshold": threshold,
                    "edge_threshold_range": market_edge_threshold_range(row["market"]),
                    "edge_threshold_gap": threshold_gap,
                    "edge_quality": edge_quality_label(edge, threshold),
                    "expected_value": row["expected_value"],
                    "value_arbitrage_rate": arbitrage_rate,
                    "minimum_acceptable_odds": min_acceptable_odds,
                    "odds_buffer": current_odds_buffer,
                    "price_drift_tolerance_pct": current_price_tolerance,
                    "expected_profit_aud": expected_profit,
                    "expected_profit_per_100_aud": expected_profit_100,
                    "full_kelly_fraction": kelly,
                    "discounted_kelly_fraction": half_kelly,
                    "risk_of_ruin": ruin_risk,
                    "risk_of_ruin_grade": risk_grade,
                    "stake_fraction": stake_fraction,
                    "stake_to_cap_ratio": stake_cap_ratio,
                    "half_kelly_ratio": half_kelly_ratio,
                    "kelly_safety_margin": kelly_margin,
                    "risk_adjusted_value_score": value_score,
                    "value_signal": value_signal,
                    "market_funding_tendency_score": funding_profile.get("market_funding_tendency_score"),
                    "risk_drivers": drivers,
                    "bankroll_reference_aud": bankroll_reference,
                    "risk_flags": risk_flags,
                    "template_controls": {
                        "base_stake_range": "0.5%-1.0% bankroll",
                        "single_bet_cap": "2.0% bankroll",
                        "main_market_edge_threshold": "2%-3%",
                        "small_market_edge_threshold": "4%-6%",
                    },
                },
                "decision_metric_pack": metric_pack,
                "decision_diagnostics": diagnostic,
                "analysis_basis": analysis_basis,
                "model_calibration": model_calibration,
                "market_funding": funding_profile,
                "bankroll_reference_aud": bankroll_reference,
                "stake_aud": stake,
                "action": action_label(row["action"], stake),
                "action_class": action_class,
                "consistency": consistency,
                "value_label": value_label(row["expected_value"], edge, stake),
                "confidence": confidence,
                "risk_flags": risk_flags,
                "reason": reason,
                "evidence_layers": [
                    {"layer": "FACT", "text": "来自最新可信日报 run 的 SQLite recommendations 记录。"},
                    {"layer": "INFERENCE", "text": "EV、Edge、套利率、Risk of ruin、金额和置信度由本地模型、Kelly仓位规则与门禁规则计算。"},
                    {"layer": "INFERENCE", "text": "市场资金倾向分、总资金、净资金、成交量、流动性、盘口深度和日均盘口变动浮动率为盘口资金代理指标。"},
                    {"layer": "OBSERVATION", "text": "逐行判断依据包记录概率价值、价格执行、资金纪律、资料缺口和赛前复核清单。"},
                ],
            }
        )
    return rows


def apply_execution_gate(rows: list[dict[str, Any]], *, execution_allowed: bool, gate_message: str) -> list[dict[str, Any]]:
    if execution_allowed:
        return rows
    gated = []
    for item in rows:
        next_item = dict(item)
        next_item["original_action"] = item.get("action")
        next_item["original_action_class"] = item.get("action_class")
        next_item["action"] = "暂停执行"
        next_item["action_class"] = "blocked"
        next_item["value_label"] = "需刷新复核"
        next_item["executable_stake_aud"] = 0.0
        next_item["reason"] = (
            f"{gate_message} 本行仅保留为研究候选，不作为当前可执行下注。"
            f"原研究动作：{item.get('action', '')}，原研究金额：{money(item.get('stake_aud'))}。"
            f" {item.get('reason', '')}"
        ).strip()
        gated.append(next_item)
    return gated


def board_scope_index(available_strategy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = available_strategy.get("board_scope_rows") or []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in [row.get("board_id"), row.get("name")]:
            value = str(key or "").strip()
            if value:
                index[value] = row
    return index


def annotate_live_board_scope(item: dict[str, Any], scope_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    next_item = dict(item)
    scope_row = scope_index.get(str(item.get("board_id") or "").strip()) or scope_index.get(str(item.get("board") or "").strip())
    if not scope_row:
        next_item.setdefault("live_board_scope", "scope_not_available")
        next_item.setdefault("live_board_status", "not_loaded")
        next_item.setdefault("live_board_scope_label", "未加载范围门禁")
        next_item.setdefault("live_board_scope_reason", "未找到可用板块策略，本行按历史兼容口径进入候选池。")
        next_item.setdefault("live_board_report_usage", "范围门禁未加载；仅保留历史兼容。")
        return next_item
    scope = str(scope_row.get("board_scope") or "")
    next_item["live_board_scope"] = scope
    next_item["live_board_status"] = str(scope_row.get("live_nav_status") or "")
    next_item["live_board_scope_label"] = live_board_scope_label(scope)
    next_item["live_board_scope_reason"] = str(scope_row.get("reason") or "")
    next_item["live_board_report_usage"] = str(scope_row.get("report_usage") or "")
    return next_item


def live_board_scope_allowed(item: dict[str, Any]) -> bool:
    scope = str(item.get("live_board_scope") or "")
    if not scope or scope == "scope_not_available":
        return True
    return scope == "research_diagnostic_allowed"


def live_board_scope_label(scope: str) -> str:
    return {
        "research_diagnostic_allowed": "当前可研究",
        "unavailable_excluded": "板块缺失排除",
        "discovery_retry_required": "需重新发现",
        "scope_not_available": "未加载范围门禁",
    }.get(str(scope or ""), str(scope or "待校准"))


def partition_rows_by_board_scope(
    rows: list[dict[str, Any]],
    available_strategy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    index = board_scope_index(available_strategy)
    annotated = [annotate_live_board_scope(item, index) for item in rows]
    current = [item for item in annotated if live_board_scope_allowed(item)]
    excluded = [item for item in annotated if not live_board_scope_allowed(item)]
    return current, excluded, annotated


def apply_board_scope_gate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gated = []
    for item in rows:
        next_item = dict(item)
        next_item["original_action"] = item.get("action")
        next_item["original_action_class"] = item.get("action_class")
        next_item["action"] = "排除-板块缺失"
        next_item["action_class"] = "scope-blocked"
        next_item["value_label"] = "板块不可用"
        next_item["executable_stake_aud"] = 0.0
        next_item["reason"] = (
            f"TAB 当前 live nav 未确认该板块可读，范围状态：{next_item.get('live_board_scope_label')}。"
            f"本行从当前推荐池、Top pick 和汇总统计排除，仅保留审计；不得用旧盘口替代实盘。 "
            f"{item.get('reason', '')}"
        ).strip()
        gated.append(next_item)
    return gated


def summarize_rows(
    rows: list[dict[str, Any]],
    research_rows: list[dict[str, Any]],
    latest_commit: dict[str, Any],
    readiness: dict[str, Any],
    raw_health: dict[str, Any],
    active_timeline: dict[str, Any],
    available_strategy: dict[str, Any],
    execution_allowed: bool,
    *,
    all_research_rows: list[dict[str, Any]] | None = None,
    excluded_unavailable_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    all_rows = all_research_rows or research_rows
    excluded_rows = excluded_unavailable_rows or []
    candidate_count = len(rows)
    research_buy_rows = [item for item in research_rows if float(item.get("stake_aud") or 0) > 0]
    research_stake = sum(float(item.get("stake_aud") or 0) for item in research_rows)
    executable_stake = sum(float(item.get("stake_aud") or 0) for item in rows if execution_allowed and item.get("action_class") == "buy")
    ev_values = [float(item.get("expected_value")) for item in research_rows if item.get("expected_value") is not None]
    probability_values = [float(item.get("probability")) for item in research_rows if item.get("probability") is not None]
    edges = [float(item.get("edge")) for item in research_rows if item.get("edge") is not None]
    edge_gaps = [float(item.get("edge_threshold_gap")) for item in research_rows if item.get("edge_threshold_gap") is not None]
    arbitrage_rates = [float(item.get("arbitrage_rate")) for item in research_rows if item.get("arbitrage_rate") is not None]
    ruin_risks = [float(item.get("risk_of_ruin")) for item in research_rows if item.get("risk_of_ruin") is not None]
    expected_profits = [float(item.get("expected_profit_aud")) for item in research_rows if item.get("expected_profit_aud") is not None]
    expected_profit_100_values = [float(item.get("expected_profit_per_100_aud")) for item in research_rows if item.get("expected_profit_per_100_aud") is not None]
    stake_fractions = [float(item.get("stake_fraction")) for item in research_rows if item.get("stake_fraction") is not None]
    half_kelly_ratios = [float(item.get("half_kelly_ratio")) for item in research_rows if item.get("half_kelly_ratio") is not None]
    price_tolerances = [float(item.get("price_drift_tolerance_pct")) for item in research_rows if item.get("price_drift_tolerance_pct") is not None]
    stake_cap_ratios = [float(item.get("stake_to_cap_ratio")) for item in research_rows if item.get("stake_to_cap_ratio") is not None]
    kelly_margins = [float(item.get("kelly_safety_margin")) for item in research_rows if item.get("kelly_safety_margin") is not None]
    value_scores = [float(item.get("risk_adjusted_value_score")) for item in research_rows if item.get("risk_adjusted_value_score") is not None]
    diagnostic_rows = [item.get("decision_diagnostics") or {} for item in research_rows]
    basis_rows = [item.get("analysis_basis") or {} for item in research_rows]
    model_rows = [item.get("model_calibration") or {} for item in research_rows]
    timeline_summary = active_timeline.get("summary") or {}
    available_summary = available_strategy.get("summary") or {}
    top = rows[0] if rows else {}
    portfolio_risk = portfolio_risk_summary(research_rows, execution_allowed=execution_allowed)
    funding_summary = market_funding_summary(research_rows)
    return {
        "latest_report_date": str(latest_commit.get("report_date") or ""),
        "latest_run_id": str(latest_commit.get("run_id") or ""),
        "execution_allowed": execution_allowed,
        "formal_report_publish_ready": readiness.get("formal_report_publish_ready") is True,
        "raw_refresh_ready": raw_health.get("ready") is True,
        "candidate_count": candidate_count,
        "current_research_candidate_count": len(research_rows),
        "all_candidate_count_before_scope": len(all_rows),
        "unavailable_candidate_count": len(excluded_rows),
        "excluded_unavailable_candidate_count": len(excluded_rows),
        "research_buy_count": len(research_buy_rows),
        "research_candidate_stake_aud": round(research_stake, 2),
        "all_research_candidate_stake_aud": round(sum(float(item.get("stake_aud") or 0) for item in all_rows), 2),
        "excluded_unavailable_stake_aud": round(sum(float(item.get("stake_aud") or 0) for item in excluded_rows), 2),
        "executable_new_stake_aud": round(executable_stake, 2),
        "positive_ev_count": sum(1 for value in ev_values if value > 0),
        "high_value_count": sum(1 for item in research_rows if item.get("value_label") == "高价值"),
        "average_ev": round(sum(ev_values) / len(ev_values), 4) if ev_values else 0.0,
        "average_probability": round(sum(probability_values) / len(probability_values), 4) if probability_values else 0.0,
        "average_edge": round(sum(edges) / len(edges), 4) if edges else 0.0,
        "edge_threshold_pass_count": sum(1 for item in research_rows if item.get("edge_threshold_gap") is not None and float(item.get("edge_threshold_gap") or 0) >= 0),
        "average_edge_threshold_gap": round(sum(edge_gaps) / len(edge_gaps), 4) if edge_gaps else 0.0,
        "average_arbitrage_rate": round(sum(arbitrage_rates) / len(arbitrage_rates), 4) if arbitrage_rates else 0.0,
        "max_risk_of_ruin": round(max(ruin_risks), 4) if ruin_risks else 0.0,
        "average_risk_of_ruin": round(sum(ruin_risks) / len(ruin_risks), 4) if ruin_risks else 0.0,
        "high_risk_of_ruin_count": sum(1 for item in research_rows if str(item.get("risk_of_ruin_grade") or "") in {"偏高", "高"}),
        "expected_profit_at_research_stake_aud": round(sum(expected_profits), 2) if expected_profits else 0.0,
        "average_expected_profit_per_100_aud": round(sum(expected_profit_100_values) / len(expected_profit_100_values), 2) if expected_profit_100_values else 0.0,
        "ror_review_threshold": ROR_REVIEW_THRESHOLD,
        "ror_review_count": sum(1 for value in ruin_risks if value >= ROR_REVIEW_THRESHOLD),
        "stake_discipline_pass_count": sum(1 for item in diagnostic_rows if item.get("stake_discipline_status") == "通过"),
        "value_signal_pass_count": sum(1 for item in research_rows if str(item.get("value_signal") or "") == "价值通过"),
        "positive_arbitrage_count": sum(1 for value in arbitrage_rates if value > 0),
        "price_buffer_positive_count": sum(1 for item in research_rows if item.get("odds_buffer") is not None and float(item.get("odds_buffer") or 0) >= 0),
        "low_or_medium_ror_count": sum(1 for item in research_rows if str(item.get("risk_of_ruin_grade") or "") in {"低", "中"}),
        "analysis_basis_complete_count": sum(1 for item in basis_rows if item.get("summary") and item.get("probability_value_basis")),
        "analysis_data_gap_row_count": sum(1 for item in basis_rows if item.get("data_gaps")),
        "pre_bet_checklist_item_count": sum(len(item.get("pre_bet_checklist") or []) for item in basis_rows),
        "model_calibrated_count": sum(1 for item in model_rows if item.get("status") == "model_linked"),
        "model_high_divergence_count": sum(1 for item in model_rows if item.get("high_divergence")),
        "model_reverse_consensus_count": sum(1 for item in model_rows if item.get("selection_alignment") == "against_consensus"),
        "model_review_required_count": sum(1 for item in model_rows if item.get("review_priority") in {"高", "中"}),
        "model_consistency_distribution": dict(Counter(str(item.get("consistency_label") or "待模型校准") for item in model_rows)),
        "model_review_priority_distribution": dict(Counter(str(item.get("review_priority") or "待校准") for item in model_rows)),
        "average_price_drift_tolerance_pct": round(sum(price_tolerances) / len(price_tolerances), 4) if price_tolerances else 0.0,
        "average_stake_to_cap_ratio": round(sum(stake_cap_ratios) / len(stake_cap_ratios), 4) if stake_cap_ratios else 0.0,
        "average_kelly_safety_margin": round(sum(kelly_margins) / len(kelly_margins), 4) if kelly_margins else 0.0,
        "average_risk_adjusted_value_score": round(sum(value_scores) / len(value_scores), 4) if value_scores else 0.0,
        "market_funding": funding_summary,
        "market_funding_row_count": funding_summary["funding_row_count"],
        "average_market_funding_tendency_score": funding_summary["average_market_funding_tendency_score"],
        "supportive_funding_count": funding_summary["supportive_funding_count"],
        "weak_funding_count": funding_summary["weak_funding_count"],
        "total_funds_proxy_aud": funding_summary["total_funds_proxy_aud"],
        "net_funds_proxy_aud": funding_summary["net_funds_proxy_aud"],
        "turnover_proxy_aud": funding_summary["turnover_proxy_aud"],
        "average_liquidity_score": funding_summary["average_liquidity_score"],
        "average_market_depth_score": funding_summary["average_market_depth_score"],
        "average_daily_line_move_float_rate": funding_summary["average_daily_line_move_float_rate"],
        "portfolio_risk": portfolio_risk,
        "portfolio_candidate_stake_aud": portfolio_risk["candidate_stake_aud"],
        "portfolio_expected_profit_aud": portfolio_risk["expected_profit_aud"],
        "portfolio_expected_profit_per_100_aud": portfolio_risk["expected_profit_per_100_aud"],
        "portfolio_worst_case_new_loss_aud": portfolio_risk["worst_case_new_loss_aud"],
        "portfolio_risk_of_ruin": portfolio_risk["portfolio_risk_of_ruin"],
        "portfolio_risk_grade": portfolio_risk["portfolio_risk_grade"],
        "portfolio_budget_mid_usage_pct": portfolio_risk["budget_mid_usage_pct"],
        "portfolio_combined_mid_usage_pct": portfolio_risk["combined_mid_usage_pct"],
        "portfolio_budget_floor_headroom_aud": portfolio_risk["budget_floor_headroom_aud"],
        "max_stake_fraction": round(max(stake_fractions), 4) if stake_fractions else 0.0,
        "max_half_kelly_ratio": round(max(half_kelly_ratios), 4) if half_kelly_ratios else 0.0,
        "bankroll_reference_aud": float(research_rows[0].get("bankroll_reference_aud") or DEFAULT_BANKROLL_REFERENCE_AUD) if research_rows else DEFAULT_BANKROLL_REFERENCE_AUD,
        "max_research_stake_aud": max([float(item.get("stake_aud") or 0) for item in research_rows] + [0.0]),
        "top_pick": {
            "event": top.get("event", ""),
            "market": top.get("market", ""),
            "selection": top.get("selection", ""),
            "odds": top.get("odds"),
            "stake_aud": top.get("stake_aud", 0),
            "expected_value": top.get("expected_value"),
            "edge": top.get("edge"),
            "edge_threshold": top.get("edge_threshold"),
            "edge_threshold_gap": top.get("edge_threshold_gap"),
            "edge_quality": top.get("edge_quality"),
            "arbitrage_rate": top.get("arbitrage_rate"),
            "minimum_acceptable_odds": top.get("minimum_acceptable_odds"),
            "odds_buffer": top.get("odds_buffer"),
            "price_drift_tolerance_pct": top.get("price_drift_tolerance_pct"),
            "expected_profit_aud": top.get("expected_profit_aud"),
            "expected_profit_per_100_aud": top.get("expected_profit_per_100_aud"),
            "risk_of_ruin": top.get("risk_of_ruin"),
            "risk_of_ruin_grade": top.get("risk_of_ruin_grade"),
            "stake_to_cap_ratio": top.get("stake_to_cap_ratio"),
            "kelly_safety_margin": top.get("kelly_safety_margin"),
            "risk_adjusted_value_score": top.get("risk_adjusted_value_score"),
            "value_signal": top.get("value_signal"),
            "market_funding_tendency_score": (top.get("market_funding") or {}).get("market_funding_tendency_score"),
            "market_funding_bias_label": (top.get("market_funding") or {}).get("market_funding_bias_label"),
            "model_consistency": (top.get("model_calibration") or {}).get("consistency_label", ""),
            "model_review_priority": (top.get("model_calibration") or {}).get("review_priority", ""),
            "model_review_action": (top.get("model_calibration") or {}).get("review_action", ""),
            "confidence": top.get("confidence", ""),
            "action": top.get("action", ""),
        },
        "missing_analysis_day_count": int(timeline_summary.get("missing_analysis_day_count") or 0),
        "missing_report_day_count": int(timeline_summary.get("missing_report_day_count") or 0),
        "backfill_queue_count": int(timeline_summary.get("backfill_queue_count") or 0),
        "research_allowed_board_count": int(available_summary.get("research_allowed_board_count") or 0),
        "unavailable_board_count": int(available_summary.get("unavailable_board_count") or 0),
        "discovery_retry_board_count": int(available_summary.get("discovery_retry_board_count") or 0),
        "board_distribution": dict(Counter(str(item.get("board") or "") for item in research_rows)),
        "all_board_distribution_before_scope": dict(Counter(str(item.get("board") or "") for item in all_rows)),
        "excluded_unavailable_board_distribution": dict(Counter(str(item.get("board") or "") for item in excluded_rows)),
        "live_board_scope_distribution": dict(Counter(str(item.get("live_board_scope_label") or "未加载范围门禁") for item in all_rows)),
        "confidence_distribution": dict(Counter(str(item.get("confidence") or "待校准") for item in research_rows)),
        "consistency_distribution": dict(Counter(str(item.get("consistency") or "待模型校准") for item in research_rows)),
        "edge_quality_distribution": dict(Counter(str(item.get("edge_quality") or "待校准") for item in research_rows)),
        "risk_grade_distribution": dict(Counter(str(item.get("risk_of_ruin_grade") or "待校准") for item in research_rows)),
        "value_signal_distribution": dict(Counter(str(item.get("value_signal") or "待校准") for item in research_rows)),
    }


def portfolio_risk_summary(rows: list[dict[str, Any]], *, execution_allowed: bool) -> dict[str, Any]:
    active_rows = [item for item in rows if float(item.get("stake_aud") or 0) > 0]
    stake_total = round(sum(float(item.get("stake_aud") or 0) for item in active_rows), 2)
    expected_profit = round(sum(float(item.get("expected_profit_aud") or 0) for item in active_rows), 2)
    best_case_profit = round(
        sum(float(item.get("stake_aud") or 0) * max(0.0, float(item.get("odds") or 0) - 1) for item in active_rows),
        2,
    )
    weighted_ev = weighted_average(active_rows, "expected_value", weight_key="stake_aud")
    weighted_edge = weighted_average(active_rows, "edge", weight_key="stake_aud")
    weighted_arbitrage = weighted_average(active_rows, "arbitrage_rate", weight_key="stake_aud")
    weighted_ror = weighted_average(active_rows, "risk_of_ruin", weight_key="stake_aud")
    max_stake = max([float(item.get("stake_aud") or 0) for item in active_rows] + [0.0])
    concentration_ratio = round(max_stake / stake_total, 4) if stake_total > 0 else 0.0
    high_ror_count = sum(1 for item in active_rows if str(item.get("risk_of_ruin_grade") or "") in {"偏高", "高"})
    combined_mid_usage = (USER_DECLARED_COMMITTED_REFERENCE_AUD + stake_total) / USER_BUDGET_MID_AUD
    concentration_penalty = max(0.0, concentration_ratio - 0.30) * 0.03
    high_ror_penalty = min(0.03, high_ror_count * 0.005)
    budget_pressure_penalty = max(0.0, combined_mid_usage - 0.60) * 0.12
    portfolio_ror = round(
        min(0.95, max(0.0, (weighted_ror or 0.0) + concentration_penalty + high_ror_penalty + budget_pressure_penalty)),
        4,
    )
    budget_floor_headroom = round(USER_BUDGET_FLOOR_AUD - USER_DECLARED_COMMITTED_REFERENCE_AUD - stake_total, 2)
    budget_mid_headroom = round(USER_BUDGET_MID_AUD - USER_DECLARED_COMMITTED_REFERENCE_AUD - stake_total, 2)
    budget_ceiling_headroom = round(USER_BUDGET_CEILING_AUD - USER_DECLARED_COMMITTED_REFERENCE_AUD - stake_total, 2)
    ror_status = ror_review_status(portfolio_ror)
    if not active_rows:
        action = "无组合研究候选"
    elif not execution_allowed:
        action = "研究-only，新增执行AUD 0"
    elif budget_floor_headroom < 0:
        action = "预算下沿不足，需降仓"
    elif ror_status != "通过":
        action = "组合RoR复核/降仓"
    else:
        action = "组合风险通过，仍需赛前复核"
    return {
        "scenario": "用户预算区间组合压力测试",
        "verification_status": "用户声明参考值，待持仓快照同步确认；未同步前不解锁执行。",
        "budget_floor_aud": USER_BUDGET_FLOOR_AUD,
        "budget_mid_aud": USER_BUDGET_MID_AUD,
        "budget_ceiling_aud": USER_BUDGET_CEILING_AUD,
        "declared_committed_reference_aud": USER_DECLARED_COMMITTED_REFERENCE_AUD,
        "candidate_count": len(active_rows),
        "candidate_stake_aud": stake_total,
        "expected_profit_aud": expected_profit,
        "expected_profit_per_100_aud": round(100 * (weighted_ev or 0.0), 2) if active_rows else 0.0,
        "best_case_profit_if_all_win_aud": best_case_profit,
        "worst_case_new_loss_aud": stake_total,
        "weighted_ev": round(weighted_ev or 0.0, 4),
        "weighted_edge": round(weighted_edge or 0.0, 4),
        "weighted_arbitrage_rate": round(weighted_arbitrage or 0.0, 4),
        "weighted_row_ror": round(weighted_ror or 0.0, 4),
        "portfolio_risk_of_ruin": portfolio_ror,
        "portfolio_risk_grade": risk_of_ruin_grade(portfolio_ror),
        "portfolio_ror_status": ror_status,
        "high_ror_count": high_ror_count,
        "concentration_ratio": concentration_ratio,
        "concentration_penalty": round(concentration_penalty, 4),
        "high_ror_penalty": round(high_ror_penalty, 4),
        "budget_pressure_penalty": round(budget_pressure_penalty, 4),
        "budget_mid_usage_pct": round(stake_total / USER_BUDGET_MID_AUD, 4),
        "combined_mid_usage_pct": round(combined_mid_usage, 4),
        "worst_case_new_loss_pct_mid": round(stake_total / USER_BUDGET_MID_AUD, 4),
        "budget_floor_headroom_aud": budget_floor_headroom,
        "budget_mid_headroom_aud": budget_mid_headroom,
        "budget_ceiling_headroom_aud": budget_ceiling_headroom,
        "recommended_action": action,
    }


def weighted_average(rows: list[dict[str, Any]], value_key: str, *, weight_key: str) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for item in rows:
        value = to_float(item.get(value_key))
        weight = to_float(item.get(weight_key))
        if value is None or weight is None or weight <= 0:
            continue
        numerator += value * weight
        denominator += weight
    if denominator <= 0:
        return None
    return numerator / denominator


def excel_reference_profile() -> dict[str, Any]:
    base = {
        "file_name": EXCEL_TEMPLATE_FILENAME,
        "template_read_status": "static_profile",
        "sheet_count": 7,
        "sheet_names": ["状态总览", "赛前10分钟清单", "赔率与Edge", "泊松模型", "下注日志", "示例分析", "参数与说明"],
        "detected_topics": ["赛前检查", "赔率去水", "EV/Edge", "Kelly仓位", "Poisson/xG", "下注日志", "CLV/ROI"],
        "sheet_previews": [],
        "accepted_modules": [
            {
                "module": "A 赛前10分钟清单",
                "usage": "赛前最后过滤，不通过则 No Bet 或降仓。",
                "checks": ["盘口价格", "盘口去水", "首发阵容", "伤停变化", "比赛动机", "赛程疲劳", "战术匹配", "大小球节奏", "资金管理"],
                "risk_action": "任一高风险关键项待确认时，不新增执行金额或降低仓位。",
            },
            {
                "module": "B 赔率与Edge",
                "usage": "把十进制赔率转为盈亏平衡概率、EV、Edge、Kelly 和建议注额。",
                "formulas": [
                    "隐含概率 = 1 / 十进制赔率",
                    "EV = 模型概率 × 十进制赔率 - 1",
                    "Edge = 模型概率 - 盈亏平衡概率",
                    "Kelly = p - (1-p)/(odds-1)",
                ],
                "risk_controls": ["基础单注 0.5%-1.0% bankroll", "单注绝对上限 2.0% bankroll", "Kelly 折扣 0.5"],
            },
            {
                "module": "B 泊松模型",
                "usage": "使用主/客队 λ 估计 1X2、大小球、BTTS 和比分矩阵，作为概率结构，不直接替代赔率判断。",
                "inputs": ["主队λ", "客队λ", "大/小球线", "最大进球截断"],
            },
            {
                "module": "复盘日志",
                "usage": "记录入场赔率、收盘赔率、结果、注额、Profit、ROI、CLV% 和平均 Edge，用于每日/周报校准。",
                "priority": "先看 CLV，再看 ROI；样本不足时不因短期输赢推翻模型。",
            },
        ],
        "betting_preference": {
            "preferred_markets": "亚洲让球 / 大小球 > 1X2 > 角球/牌数 > 正确比分",
            "forbidden_behaviors": ["追损", "加倍", "情绪下注", "无首发重仓", "无记录下注"],
            "world_cup_adjustments": ["中立场", "小组赛动机", "淘汰赛保守性", "国家队样本小", "旅行与休息时间"],
        },
    }
    parsed = read_excel_template_profile(Path.home() / "Downloads" / EXCEL_TEMPLATE_FILENAME)
    if parsed:
        base.update(parsed)
    return base


def read_excel_template_profile(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"template_read_status": "not_found", "file_name": path.name}
    try:
        with zipfile.ZipFile(path) as archive:
            shared_strings = read_shared_strings(archive)
            sheet_refs = read_workbook_sheet_refs(archive)
            previews = []
            for sheet_name, sheet_path in sheet_refs[:10]:
                samples = read_sheet_sample_cells(archive, sheet_path, shared_strings)
                metrics = read_sheet_metrics(archive, sheet_path)
                previews.append({"sheet": sheet_name, "sample_cells": samples, **metrics})
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile):
        return {"template_read_status": "unreadable", "file_name": path.name}
    sheet_names = [name for name, _ in sheet_refs]
    sample_text = " ".join(
        str(cell.get("value", ""))
        for preview in previews
        for cell in (preview.get("sample_cells") or [])
    )
    formula_count_total = sum(int(preview.get("formula_count") or 0) for preview in previews)
    return {
        "template_read_status": "readable",
        "file_name": path.name,
        "file_size_bytes": path.stat().st_size,
        "sheet_count": len(sheet_names),
        "sheet_names": sheet_names,
        "sheet_previews": previews,
        "detected_topics": detect_excel_topics(sheet_names, sample_text),
        "formula_count_total": formula_count_total,
        "template_evidence_terms": detect_template_evidence_terms(sample_text),
        "template_decision_rules": template_decision_rules_from_text(sample_text),
    }


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    strings: list[str] = []
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    for item in root.findall(f"{ns}si"):
        parts = [node.text or "" for node in item.iter(f"{ns}t")]
        strings.append("".join(parts))
    return strings


def read_workbook_sheet_refs(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
    rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    sheet_ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rel_ns = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    rel_map = {
        rel.attrib.get("Id", ""): normalize_xlsx_target(rel.attrib.get("Target", ""))
        for rel in rels_root.findall(f"{rel_ns}Relationship")
    }
    refs: list[tuple[str, str]] = []
    for sheet in workbook_root.findall(f".//{sheet_ns}sheet"):
        name = str(sheet.attrib.get("name") or "")
        rid = str(sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id") or "")
        target = rel_map.get(rid)
        if name and target:
            refs.append((name, target))
    return refs


def normalize_xlsx_target(target: str) -> str:
    value = str(target or "").lstrip("/")
    if value.startswith("xl/"):
        return value
    return "xl/" + value


def read_sheet_sample_cells(archive: zipfile.ZipFile, sheet_path: str, shared_strings: list[str], max_cells: int = 24) -> list[dict[str, str]]:
    root = ET.fromstring(archive.read(sheet_path))
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    cells: list[dict[str, str]] = []
    for cell in root.iter(f"{ns}c"):
        coord = str(cell.attrib.get("r") or "")
        value = excel_cell_value(cell, shared_strings, ns)
        if value == "":
            continue
        cells.append({"cell": coord, "value": value[:160]})
        if len(cells) >= max_cells:
            break
    return cells


def read_sheet_metrics(archive: zipfile.ZipFile, sheet_path: str) -> dict[str, int]:
    root = ET.fromstring(archive.read(sheet_path))
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    formula_count = sum(1 for _ in root.iter(f"{ns}f"))
    non_empty_count = sum(1 for cell in root.iter(f"{ns}c") if cell.find(f"{ns}v") is not None or cell.find(f"{ns}f") is not None)
    return {"formula_count": formula_count, "non_empty_cell_count": non_empty_count}


def excel_cell_value(cell: ET.Element, shared_strings: list[str], ns: str) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{ns}t")).strip()
    value_node = cell.find(f"{ns}v")
    formula_node = cell.find(f"{ns}f")
    if value_node is None:
        if formula_node is not None and formula_node.text:
            return "=" + formula_node.text.strip()
        return ""
    value = value_node.text or ""
    if cell_type == "s":
        try:
            return shared_strings[int(value)].strip()
        except (ValueError, IndexError):
            return value.strip()
    if formula_node is not None and formula_node.text:
        return "=" + formula_node.text.strip()
    return value.strip()


def detect_excel_topics(sheet_names: list[str], sample_text: str) -> list[str]:
    haystack = " ".join(sheet_names) + " " + sample_text
    topic_checks = [
        ("赛前检查", ["赛前10分钟", "检查清单"]),
        ("赔率去水", ["赔率去水", "隐含概率"]),
        ("EV/Edge", ["EV", "Edge"]),
        ("Kelly仓位", ["Kelly", "仓位"]),
        ("Poisson/xG", ["泊松", "xG", "λ"]),
        ("下注日志", ["下注日志", "总注数"]),
        ("CLV/ROI", ["CLV", "ROI"]),
        ("Risk of ruin", ["Risk of ruin", "破产"]),
    ]
    topics = [name for name, needles in topic_checks if any(needle in haystack for needle in needles)]
    return topics or ["赛前检查", "EV/Edge", "下注日志"]


def detect_template_evidence_terms(sample_text: str) -> list[str]:
    checks = [
        ("No Bet", ["No Bet", "不通过", "放弃"]),
        ("最低可买价", ["最低可买价", "最低可接受赔率", "价格走差"]),
        ("去水公平概率", ["去水公平概率", "去水概率", "隐含概率合计"]),
        ("半Kelly", ["半Kelly", "Kelly折扣", "四分之一Kelly"]),
        ("单注上限", ["单注上限", "2.0% bankroll", "超仓"]),
        ("Poisson λ", ["泊松", "λ", "POISSON"]),
        ("CLV/ROI", ["CLV", "ROI", "收盘赔率"]),
        ("世界杯修正", ["FIFA", "世界杯", "国家队", "中立场"]),
    ]
    terms = [name for name, needles in checks if any(needle in sample_text for needle in needles)]
    return terms or ["EV/Edge", "Kelly仓位", "赛前清单"]


def template_decision_rules_from_text(sample_text: str) -> list[str]:
    rules = [
        "价格走差就放弃，不补买。",
        "Edge不足则 No Bet，不能只因单场看好而下注。",
        "首发或关键伤停未确认时降仓或 No Bet。",
        "资金管理不通过、超仓或追损时取消下注。",
        "泊松 λ 只负责概率结构，必须回到赔率表比较 EV。",
        "下注后记录入场赔率、收盘赔率、结果、ROI、CLV% 和实际 Edge。",
    ]
    if "先看CLV" in sample_text or "先看 CLV" in sample_text:
        rules.append("复盘优先看 CLV，再看 ROI；不以短期输赢单独评价模型。")
    if "世界杯" in sample_text or "国家队" in sample_text:
        rules.append("世界杯/国家队比赛额外修正中立场、小组赛动机、淘汰赛保守性和样本小问题。")
    return rules


def excel_reference_digest(profile: dict[str, Any]) -> str:
    status = str(profile.get("template_read_status") or "static_profile")
    sheet_count = int(profile.get("sheet_count") or len(profile.get("sheet_names") or []))
    topics = "、".join(str(item) for item in (profile.get("detected_topics") or [])[:6])
    formula_count = int(profile.get("formula_count_total") or 0)
    formula_text = f"，可审计公式 {formula_count} 个" if formula_count else ""
    if status == "readable":
        return f"Excel模板已读取：{sheet_count}个sheet{formula_text}，识别模块为{topics}。"
    if status == "not_found":
        return f"Excel模板未在本机 Downloads 找到，当前使用内置结构画像：{sheet_count}个预期sheet，模块为{topics}。"
    if status == "unreadable":
        return f"Excel模板存在但不可解析，当前使用内置结构画像：{sheet_count}个预期sheet，模块为{topics}。"
    return f"Excel模板结构画像：{sheet_count}个sheet，模块为{topics}。"


def excel_preview_table_rows(profile: dict[str, Any]) -> list[list[str]]:
    previews = profile.get("sheet_previews") or []
    rows: list[list[str]] = []
    for preview in previews[:8]:
        sheet = str(preview.get("sheet") or "")
        sample_values = " / ".join(str(cell.get("value", "")) for cell in (preview.get("sample_cells") or [])[:5])
        formula_count = int(preview.get("formula_count") or 0)
        rows.append([sheet, f"{sample_values or '无样例字段'}；公式 {formula_count} 个", excel_sheet_usage(sheet)])
    if rows:
        return rows
    for sheet in (profile.get("sheet_names") or [])[:8]:
        rows.append([str(sheet), "结构画像", excel_sheet_usage(sheet)])
    return rows or [["模板", "无可读sheet", "只保留内置判断框架，不伪造数据。"]]


def excel_sheet_usage(sheet: Any) -> str:
    name = str(sheet or "")
    usage_map = [
        ("状态总览", "总览模板模块，确认本报告采用范围与默认方案。"),
        ("赛前10分钟", "作为最后下注检查清单；未通过则暂停执行或降仓。"),
        ("赔率", "计算盈亏平衡概率、EV、Edge、Kelly 和建议仓位。"),
        ("Edge", "计算盈亏平衡概率、EV、Edge、Kelly 和建议仓位。"),
        ("泊松", "提供 xG/λ 到 1X2、大小球、BTTS 的概率结构。"),
        ("下注日志", "记录赔率、结果、Profit、ROI、CLV，用于日报/周报校准。"),
        ("示例", "只吸收分析结构，不把虚拟示例当真实下注依据。"),
        ("参数", "统一术语、公式、Edge门槛和资金纪律解释。"),
    ]
    for needle, usage in usage_map:
        if needle in name:
            return usage
    return "作为参考结构，不单独生成下注结论。"


def excel_template_control_matrix(profile: dict[str, Any]) -> list[dict[str, str]]:
    detected = set(str(item) for item in (profile.get("detected_topics") or []))
    rows = [
        {
            "control": "盘口价格",
            "excel_basis": "当前赔率是否仍高于最低可买价；价格走差就放弃，不补买。",
            "report_mapping": "最低可接受赔率、赔率缓冲、价格容忍度。",
            "decision_use": "低于最低赔率时从买入候选降级为观察/放弃。",
        },
        {
            "control": "盘口去水与Edge",
            "excel_basis": "模型概率需高于公平概率并超过 Edge 阈值。",
            "report_mapping": "模型概率、盈亏平衡概率、Edge、Edge门槛、门槛差。",
            "decision_use": "Edge 未达门槛时不因 EV 单项为正直接执行。",
        },
        {
            "control": "Kelly与单注上限",
            "excel_basis": "基础单注0.5%-1.0% bankroll，单注上限2%，使用半Kelly或四分之一Kelly。",
            "report_mapping": "半Kelly、仓位比例、仓位上限占用、Kelly安全垫。",
            "decision_use": "超过半Kelly或2%上限时进入降仓/放弃队列。",
        },
        {
            "control": "Poisson/xG",
            "excel_basis": "λ 负责概率结构，不负责判断赔率是否便宜。",
            "report_mapping": "Poisson/xG、Elo/DC、goalmodel proxy 与 TAB 盘口概率交叉校验。",
            "decision_use": "只用于概率校准和基本面解释，不绕过赔率价值门槛。",
        },
        {
            "control": "赛前10分钟",
            "excel_basis": "首发、伤停、动机、疲劳、战术、节奏和资金管理任一关键项不通过则 No Bet。",
            "report_mapping": "赛前事件风险、风险触发因素、RoR复核状态。",
            "decision_use": "赛前信息不完整时保持研究候选，执行前必须复核。",
        },
        {
            "control": "CLV/ROI复盘",
            "excel_basis": "先看 CLV，再看 ROI；不要只复盘输赢。",
            "report_mapping": "下注日志、入场/收盘赔率、收益率、新旧报告对比。",
            "decision_use": "用于日报/周报概率校准，不用短期输赢推翻模型。",
        },
    ]
    if "Risk of ruin" not in detected:
        rows.append(
            {
                "control": "Risk of ruin",
                "excel_basis": "模板未直接给出破产概率公式，本系统用资金比例、半Kelly偏离和风险事件做保守估计。",
                "report_mapping": "Risk of ruin、RoR等级、RoR复核队列、风险调整价值分。",
                "decision_use": "RoR 达到复核线时降仓或延后执行。",
            }
        )
    return rows


def excel_template_analysis_materials(profile: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "material": "赛前 No Bet 过滤",
            "evidence": "模板明确把盘口价格、去水、首发、伤停、动机、疲劳、战术、节奏和资金管理作为赛前10分钟检查项。",
            "report_use": "写入逐行 pre_bet_checklist 和 data_gaps，任一关键项未确认时保持研究-only或降仓。",
        },
        {
            "material": "EV/Edge/Kelly 计算链",
            "evidence": f"模板公式覆盖 {int(profile.get('formula_count_total') or 0)} 个单元；赔率表包含隐含概率、去水公平概率、EV、满Kelly、折扣Kelly、建议注额。",
            "report_use": "转化为 Edge信息、套利率、最低可接受赔率、半Kelly、Kelly安全垫和仓位上限占用。",
        },
        {
            "material": "Poisson/xG 概率结构",
            "evidence": "模板用主/客队 λ 生成比分矩阵、1X2、大小球和 BTTS 概率，并提示低比分相关性需谨慎。",
            "report_use": "作为概率基本面解释和盘口概率交叉验证，不单独绕过价格价值门槛。",
        },
        {
            "material": "复盘与模型校准",
            "evidence": "模板下注日志记录入场赔率、收盘赔率、结果、注额、ROI、CLV% 和平均 Edge。",
            "report_use": "进入日报/周报旧报告对比、CLV/ROI 复盘和概率校准队列。",
        },
        {
            "material": "世界杯特殊修正",
            "evidence": "模板参数说明要求 FIFA/世界杯国家队比赛额外修正中立场、小组赛动机、淘汰赛保守性和样本小。",
            "report_use": "写入中文原因和赛前事件风险，不把俱乐部联赛模型直接照搬到世界杯。",
        },
    ]


def render_recommendation_operations_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    compare = payload.get("old_new_compare") or {}
    calculation_policy = payload.get("calculation_policy") or {}
    source_alignment = payload.get("source_alignment") or {}
    excel_profile = calculation_policy.get("excel_reference_profile") or {}
    probability_engine = payload.get("probability_engine") or calculation_policy.get("probability_engine_framework") or {}
    portfolio = summary.get("portfolio_risk") or {}
    market_funding = summary.get("market_funding") or {}
    lines = [
        "# TAB FIFA 推荐操作 Dashboard",
        "",
        "本报告把首页推荐下注板块归档成正式研究报告。raw 或发布门禁失败时，所有候选只保留为研究参考，不作为当前可执行下注。",
        "",
        "## Executive Summary",
        "",
        f"- status: `{executive.get('status', '')}`",
        f"- current_action: `{executive.get('current_action', '')}`",
        f"- current_executable_new_stake_aud: `{money(executive.get('current_executable_new_stake_aud'))}`",
        f"- research_candidate_stake_aud: `{money(executive.get('research_candidate_stake_aud'))}`",
        f"- candidate_count: `{summary.get('candidate_count', 0)}`",
        f"- current_research_candidate_count: `{summary.get('current_research_candidate_count', summary.get('candidate_count', 0))}`",
        f"- all_candidate_count_before_scope: `{summary.get('all_candidate_count_before_scope', summary.get('candidate_count', 0))}`",
        f"- excluded_unavailable_candidate_count: `{summary.get('excluded_unavailable_candidate_count', 0)}`",
        f"- excluded_unavailable_stake_aud: `{money(summary.get('excluded_unavailable_stake_aud'))}`",
        f"- average_ev: `{pct(summary.get('average_ev'))}`",
        f"- average_edge: `{pp(summary.get('average_edge'))}`",
        f"- edge_threshold_pass_count: `{summary.get('edge_threshold_pass_count', 0)}/{summary.get('candidate_count', 0)}`",
        f"- average_edge_threshold_gap: `{pp(summary.get('average_edge_threshold_gap'))}`",
        f"- average_arbitrage_rate: `{pct(summary.get('average_arbitrage_rate'))}`",
        f"- max_risk_of_ruin: `{pct(summary.get('max_risk_of_ruin'))}`",
        f"- high_risk_of_ruin_count: `{summary.get('high_risk_of_ruin_count', 0)}`",
        f"- expected_profit_at_research_stake_aud: `{money(summary.get('expected_profit_at_research_stake_aud'))}`",
        f"- average_expected_profit_per_100_aud: `{money(summary.get('average_expected_profit_per_100_aud'))}`",
        f"- ror_review_count: `{summary.get('ror_review_count', 0)}`",
        f"- value_signal_pass_count: `{summary.get('value_signal_pass_count', 0)}/{summary.get('candidate_count', 0)}`",
        f"- positive_arbitrage_count: `{summary.get('positive_arbitrage_count', 0)}`",
        f"- price_buffer_positive_count: `{summary.get('price_buffer_positive_count', 0)}`",
        f"- low_or_medium_ror_count: `{summary.get('low_or_medium_ror_count', 0)}`",
        f"- analysis_basis_complete_count: `{summary.get('analysis_basis_complete_count', 0)}/{summary.get('candidate_count', 0)}`",
        f"- analysis_data_gap_row_count: `{summary.get('analysis_data_gap_row_count', 0)}`",
        f"- pre_bet_checklist_item_count: `{summary.get('pre_bet_checklist_item_count', 0)}`",
        f"- model_calibrated_count: `{summary.get('model_calibrated_count', 0)}/{summary.get('candidate_count', 0)}`",
        f"- model_high_divergence_count: `{summary.get('model_high_divergence_count', 0)}`",
        f"- model_reverse_consensus_count: `{summary.get('model_reverse_consensus_count', 0)}`",
        f"- model_review_required_count: `{summary.get('model_review_required_count', 0)}`",
        f"- average_price_drift_tolerance_pct: `{pct(summary.get('average_price_drift_tolerance_pct'))}`",
        f"- average_stake_to_cap_ratio: `{pct(summary.get('average_stake_to_cap_ratio'))}`",
        f"- average_risk_adjusted_value_score: `{pct(summary.get('average_risk_adjusted_value_score'))}`",
        f"- average_market_funding_tendency_score: `{summary.get('average_market_funding_tendency_score', 0)}` / supportive `{summary.get('supportive_funding_count', 0)}` / weak `{summary.get('weak_funding_count', 0)}`",
        f"- market_funding_proxy: total `{money(summary.get('total_funds_proxy_aud'))}` / net `{money(summary.get('net_funds_proxy_aud'))}` / turnover `{money(summary.get('turnover_proxy_aud'))}`",
        f"- tournament_rule_ready: `{summary.get('probability_engine_tournament_rule_ready_count', 0)}/{summary.get('probability_engine_tournament_rule_count', 0)}`",
        f"- prediction_contract_ready: `{summary.get('probability_engine_prediction_contract_ready_count', 0)}/{summary.get('probability_engine_prediction_contract_field_count', 0)}`",
        f"- backtest_control_ready: `{summary.get('probability_engine_backtest_ready_count', 0)}/{summary.get('probability_engine_backtest_control_count', 0)}`",
        f"- portfolio_risk_of_ruin: `{pct(summary.get('portfolio_risk_of_ruin'))}` / `{md(summary.get('portfolio_risk_grade'))}`",
        f"- portfolio_expected_profit_aud: `{money(summary.get('portfolio_expected_profit_aud'))}`",
        f"- portfolio_worst_case_new_loss_aud: `{money(summary.get('portfolio_worst_case_new_loss_aud'))}`",
        f"- portfolio_combined_mid_usage_pct: `{pct(summary.get('portfolio_combined_mid_usage_pct'))}`",
        f"- bankroll_reference_aud: `{money(summary.get('bankroll_reference_aud'))}`",
        f"- gate_message: {md(executive.get('gate_message'))}",
        "",
        "## 判断依据",
        "",
        "- Edge 使用 `模型概率 - 赔率盈亏平衡概率`，衡量概率优势百分点。",
        "- Edge 信息展示对应盘口门槛和门槛差：主流盘口按 2.50% 下限，小市场按 5.00% 中位阈值；门槛差为正才算通过纪律过滤。",
        "- 套利率使用 `max(0, 模型概率 × 十进制赔率 - 1)`，这里是价值套利率，不代表跨平台无风险套利。",
        "- Risk of ruin 使用中位资金池、单注比例、半Kelly偏离和盘口风险标记做保守估计，并输出低/中/偏高/高等级与触发原因；真实账户资金未同步时不读取私有余额。",
        "- 价值信号综合 EV、Edge门槛、价格缓冲和 RoR；价格容忍度为赔率还能下滑的百分比，为负时应放弃。",
        "- 仓位上限占用把单注比例和 2% 上限直接对比；Kelly安全垫为 1 - 当前仓位/半Kelly，低于 0 表示超过半Kelly。",
        "- 市场资金倾向分综合 EV、Edge、套利率、价格容忍度、流动性、盘口深度、RoR 和日均盘口变动浮动率；资金字段是代理指标，不是 TAB 官方成交数据。",
        "- 组合风险把所有当前可研究买入候选放在同一预算压力测试里，检查总研究金额、预算占用、最坏全输亏损、组合期望收益和组合 Risk of ruin。",
        "- 模型校准把开源模型对比报告映射到每条推荐：展示共识方向、分歧、模型均值概率、本地概率偏离和复核动作。",
        "- 当前推荐池只统计 TAB live nav 已确认可研究的板块；缺失或 route mismatch 板块进入排除审计队列，不参与 Top pick、Edge、套利率、Risk of ruin 汇总。",
        f"- 开源模型库：`{source_alignment.get('model_registry_status', '')}`；参考源 `{source_alignment.get('reference_count', 0)}`；已吸收 `{source_alignment.get('implemented_reference_count', 0)}`；设计参考 `{source_alignment.get('design_reference_count', 0)}`。",
    ]
    for item in calculation_policy.get("judgment_basis") or []:
        lines.append(f"- {md(item)}")
    lines.extend(
        [
            "",
            "## 概率工程吸收",
            "",
            f"- status: `{md(probability_engine.get('status'))}`",
            f"- fixed_random_seed_policy: `{md(probability_engine.get('fixed_random_seed_policy'))}`",
            f"- truthfulness_note: {md(probability_engine.get('truthfulness_note'))}",
            f"- default_next_upgrade: {md(probability_engine.get('default_next_upgrade'))}",
            "",
            "| 输出对象 | 典型结果 | 当前状态 | 当前证据 | 下一步 |",
            "|---|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("outputs") or []:
        lines.append(
            f"| {md(item.get('output_object'))} | {md(item.get('typical_result'))} | {md(item.get('current_status'))} | {md(item.get('current_evidence'))} | {md(item.get('next_upgrade'))} |"
        )
    lines.extend(
        [
            "",
            "| 模块 | 推荐状态 | 作用 | 关键输出 | 当前状态 |",
            "|---|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("modules") or []:
        lines.append(
            f"| {md(item.get('module'))} | {md(item.get('recommended_status'))} | {md(item.get('role'))} | {md(item.get('key_output'))} | {md(item.get('current_status'))} |"
        )
    lines.extend(
        [
            "",
            "## 赛制模拟与预测合约",
            "",
            "赛制规则和预测字段是进入 automation 的硬前置：未实现的路径模拟不能被当作真实概率，缺少 timestamp/source version/odds phase 的推荐不能进入自动日报执行层。",
            "",
            "| 赛制规则 | 决策用途 | 当前状态 | Automation门禁 |",
            "|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("tournament_rule_requirements") or []:
        lines.append(
            f"| {md(item.get('rule'))} | {md(item.get('decision_use'))} | {md(item.get('current_status'))} | {md(item.get('automation_gate'))} |"
        )
    lines.extend(
        [
            "",
            "| 预测合约字段 | 必须 | 决策用途 | 当前状态 |",
            "|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("prediction_contract_fields") or []:
        lines.append(
            f"| {md(item.get('field'))} | {md(item.get('required'))} | {md(item.get('decision_use'))} | {md(item.get('current_status'))} |"
        )
    lines.extend(
        [
            "",
            "| 校准/回测控制 | 作用 | 当前状态 | Automation用途 |",
            "|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("calibration_backtest_controls") or []:
        lines.append(
            f"| {md(item.get('control'))} | {md(item.get('purpose'))} | {md(item.get('current_status'))} | {md(item.get('automation_use'))} |"
        )
    lines.extend(
        [
            "",
            "## 概率工程 Pipeline 与防泄漏规则",
            "",
            "| Pipeline步骤 | 当前状态 | 控制规则 |",
            "|---|---|---|",
        ]
    )
    for item in probability_engine.get("pipeline") or []:
        lines.append(f"| {md(item.get('step'))} | {md(item.get('current_status'))} | {md(item.get('control'))} |")
    lines.extend(
        [
            "",
            "| 防泄漏/可复现要求 | 必须 | 当前状态 | 证据 |",
            "|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("leakage_controls") or []:
        lines.append(
            f"| {md(item.get('control'))} | {md(item.get('required'))} | {md(item.get('current_status'))} | {md(item.get('evidence'))} |"
        )
    lines.extend(
        [
            "",
            "## 模型监控指标",
            "",
            "| 指标 | 作用 | 当前状态 |",
            "|---|---|---|",
        ]
    )
    for item in probability_engine.get("metrics") or []:
        lines.append(f"| {md(item.get('metric'))} | {md(item.get('purpose'))} | {md(item.get('current_status'))} |")
    lines.extend(
        [
            "",
            "## 目标与指标落地",
            "",
            "| 模块 | 目标 | 常用指标 | 输出 | 当前状态 |",
            "|---|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("objective_modules") or []:
        lines.append(
            f"| {md(item.get('module'))} | {md(item.get('goal'))} | {md(item.get('common_metrics'))} | {md(item.get('output'))} | {md(item.get('current_status'))} |"
        )
    lines.extend(
        [
            "",
            "## 机器学习候选模型",
            "",
            "机器学习模型当前只作为候选路线和复核矩阵，不替代已验证的盘口门禁；上线前必须通过数据泄漏检查、概率校准和回测。",
            "",
            "| 模型 | 适合任务 | 优点 | 风险 | 当前决策 |",
            "|---|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("ml_models") or []:
        lines.append(
            f"| {md(item.get('model'))} | {md(item.get('task'))} | {md(item.get('strength'))} | {md(item.get('risk'))} | {md(item.get('current_decision'))} |"
        )
    lines.extend(
        [
            "",
            "## 技术面与模型公式",
            "",
            "- 技术面规则覆盖：EV / RAEV / CLV、去水公平概率、Value bet Edge 纪律。",
            "",
            "| 名称 | 公式 | 决策规则 | 当前状态 |",
            "|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("technical_rules") or []:
        lines.append(
            f"| {md(item.get('name'))} | {md(item.get('formula'))} | {md(item.get('decision_rule'))} | {md(item.get('current_status'))} |"
        )
    lines.extend(
        [
            "",
            "| 模型 | 公式 | 用途 | 当前状态 |",
            "|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("scoring_models") or []:
        lines.append(
            f"| {md(item.get('name'))} | {md(item.get('formula'))} | {md(item.get('use'))} | {md(item.get('current_status'))} |"
        )
    lines.extend(
        [
            "",
            "## 基本面分析层",
            "",
            "基本面层级按 Team / Player / Tactical / News 拆开；confirmed 信息才进入概率修正，rumor 只进入风险提示。",
            "",
            "| 层级 | 输入 | 决策用途 | 当前状态 |",
            "|---|---|---|---|",
        ]
    )
    for item in probability_engine.get("fundamental_layers") or []:
        lines.append(
            f"| {md(item.get('layer'))} | {md(item.get('inputs'))} | {md(item.get('decision_use'))} | {md(item.get('current_status'))} |"
        )
    lines.extend(
        [
        "",
        "## 市场资金分析",
        "",
        "该板块使用公开盘口可见信息推断资金面压力，不声称读取到 TAB 官方成交资金或订单簿。",
        "",
        f"- data_status: `{md(market_funding.get('data_status'))}`",
        f"- total_funds_proxy_aud: `{money(market_funding.get('total_funds_proxy_aud'))}`",
        f"- net_funds_proxy_aud: `{money(market_funding.get('net_funds_proxy_aud'))}`",
        f"- turnover_proxy_aud: `{money(market_funding.get('turnover_proxy_aud'))}`",
        f"- average_liquidity_score: `{pct(market_funding.get('average_liquidity_score'))}`",
        f"- average_market_depth_score: `{pct(market_funding.get('average_market_depth_score'))}`",
        f"- average_daily_line_move_float_rate: `{pct(market_funding.get('average_daily_line_move_float_rate'))}`",
        "",
            "| 时间 | 盘口 | 下注 | 资金倾向分 | 倾向 | 总资金代理 | 净资金代理 | 成交量代理 | 流动性 | 盘口深度 | 日均盘口变动浮动率 |",
            "|---|---|---|---:|---|---:|---:|---:|---|---|---:|",
        ]
    )
    for row in payload.get("recommendation_rows") or []:
        funding = row.get("market_funding") or {}
        lines.append(
            "| {time} | {market} | {selection} | {score} | {bias} | {total} | {net} | {turnover} | {liquidity} | {depth} | {float_rate} |".format(
                time=md(row.get("time")),
                market=md(f"{row.get('event', '')} / {row.get('market', '')}"),
                selection=md(row.get("selection")),
                score=md(funding.get("market_funding_tendency_score")),
                bias=md(funding.get("market_funding_bias_label")),
                total=money(funding.get("total_funds_proxy_aud")),
                net=money(funding.get("net_funds_proxy_aud")),
                turnover=money(funding.get("turnover_proxy_aud")),
                liquidity=md(f"{pct(funding.get('liquidity_score'))} / {funding.get('liquidity_grade', '')}"),
                depth=md(f"{pct(funding.get('market_depth_score'))} / {funding.get('market_depth_grade', '')}"),
                float_rate=pct(funding.get("daily_line_move_float_rate")),
            )
        )
    lines.extend(
        [
        "",
        "## 模型共识校准",
        "",
            "| 下注 | 模型一致性 | 共识方向 | 共识概率 | 模型均值 | 本地概率差 | 最大分歧 | 复核优先级 | 复核动作 |",
            "|---|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload.get("recommendation_rows") or []:
        calibration = row.get("model_calibration") or {}
        lines.append(
            "| {selection} | {consistency} | {consensus} | {consensus_prob} | {model_prob} | {gap} | {disagreement} | {priority} | {action} |".format(
                selection=md(row.get("selection")),
                consistency=md(calibration.get("consistency_label")),
                consensus=md(calibration.get("consensus_selection")),
                consensus_prob=pct(calibration.get("consensus_probability")),
                model_prob=pct(calibration.get("market_model_probability")),
                gap=pp(calibration.get("probability_gap_vs_model")),
                disagreement=pct(calibration.get("max_disagreement")),
                priority=md(calibration.get("review_priority")),
                action=md(calibration.get("review_action")),
            )
        )
    lines.extend(
        [
        "",
        "## Excel模板吸收范围",
            "",
            f"- template_read_status: `{excel_profile.get('template_read_status', 'static_profile')}`",
            f"- sheet_count: `{excel_profile.get('sheet_count', calculation_policy.get('template_sheet_count', 0))}`",
            f"- template_formula_count: `{calculation_policy.get('template_formula_count', 0)}`",
            f"- detected_topics: `{md('、'.join(str(item) for item in (excel_profile.get('detected_topics') or [])))}`",
            f"- evidence_terms: `{md('、'.join(str(item) for item in (calculation_policy.get('template_evidence_terms') or [])))}`",
            "",
            "| Sheet | 样例字段 | 当前用途 |",
            "|---|---|---|",
        ]
    )
    for preview in excel_profile.get("sheet_previews") or []:
        sample_values = " / ".join(str(cell.get("value", "")) for cell in (preview.get("sample_cells") or [])[:4])
        lines.append(f"| {md(preview.get('sheet'))} | {md(sample_values)} | {md(excel_sheet_usage(preview.get('sheet')))} |")
    if not excel_profile.get("sheet_previews"):
        for sheet in excel_profile.get("sheet_names") or []:
            lines.append(f"| {md(sheet)} | 结构画像 | {md(excel_sheet_usage(sheet))} |")
    lines.extend(
        [
            "",
            "## Excel模板证据增强",
            "",
            "| 资料 | Excel证据 | 报告落地 |",
            "|---|---|---|",
        ]
    )
    for item in calculation_policy.get("template_analysis_materials") or []:
        lines.append(f"| {md(item.get('material'))} | {md(item.get('evidence'))} | {md(item.get('report_use'))} |")
    lines.extend(
        [
            "",
            "## Excel决策规则",
            "",
        ]
    )
    for rule in calculation_policy.get("template_decision_rules") or []:
        lines.append(f"- {md(rule)}")
    discipline = calculation_policy.get("risk_discipline") or {}
    lines.extend(
        [
            "",
            "## 风控纪律",
            "",
            f"- 基础单注：{md(discipline.get('base_stake_range'))}；单注上限：{md(discipline.get('single_bet_cap'))}。",
            f"- Edge 阈值：主流市场 {md(discipline.get('main_market_edge_threshold'))}；小市场 {md(discipline.get('small_market_edge_threshold'))}。",
            f"- 优先玩法：{md(discipline.get('preferred_market_order'))}。",
            f"- 赛前复核：{md(discipline.get('late_check_window'))}",
            f"- 禁止动作：{md('、'.join(discipline.get('forbidden_behaviors') or []))}。",
            f"- 世界杯修正：{md('、'.join(discipline.get('world_cup_adjustments') or []))}。",
            f"- 复盘优先级：{md(discipline.get('review_priority'))}",
        ]
    )
    lines.extend(
        [
            "",
            "## 组合风险与预算压力",
            "",
            f"- verification_status: {md(portfolio.get('verification_status'))}",
            f"- recommended_action: `{md(portfolio.get('recommended_action'))}`",
            "",
            "| 指标 | 数值 | 解释 |",
            "|---|---:|---|",
            f"| 预算区间 | {money(portfolio.get('budget_floor_aud'))} - {money(portfolio.get('budget_ceiling_aud'))} | 用户目标总预算区间；中位预算 {money(portfolio.get('budget_mid_aud'))}。 |",
            f"| 已投入参考 | {money(portfolio.get('declared_committed_reference_aud'))} | 用户声明参考值，待持仓快照同步确认。 |",
            f"| 研究候选总金额 | {money(portfolio.get('candidate_stake_aud'))} | 当前可研究买入候选的总研究金额。 |",
            f"| 组合预计收益 | {money(portfolio.get('expected_profit_aud'))} | 按各行 EV × 注额加总。 |",
            f"| 每AUD100组合预期 | {money(portfolio.get('expected_profit_per_100_aud'))} | 注额加权 EV 转成金额。 |",
            f"| 最坏全输新增亏损 | {money(portfolio.get('worst_case_new_loss_aud'))} | 只计算本轮研究候选，不含未同步持仓。 |",
            f"| 组合Risk of ruin | {pct(portfolio.get('portfolio_risk_of_ruin'))} | 等级 {md(portfolio.get('portfolio_risk_grade'))}；复核 {md(portfolio.get('portfolio_ror_status'))}。 |",
            f"| 中位预算总占用 | {pct(portfolio.get('combined_mid_usage_pct'))} | 已投入参考 + 本轮候选金额，占 AUD 4,000 中位预算比例。 |",
            f"| 预算下沿余量 | {money(portfolio.get('budget_floor_headroom_aud'))} | 以 AUD 3,000 下沿测算，负数代表应降仓。 |",
        ]
    )
    excluded_rows = payload.get("excluded_unavailable_rows") or []
    if excluded_rows:
        lines.extend(
            [
                "",
                "## 缺失板块排除审计",
                "",
                "这些行来自历史/旧日报候选，但当前 TAB live nav 未确认板块可读，因此不进入当前推荐池。",
                "",
                "| 板块 | 盘口 | 下注 | 原动作 | 原金额 | 范围状态 | 原因 |",
                "|---|---|---|---|---:|---|---|",
            ]
        )
        for row in excluded_rows:
            lines.append(
                "| {board} | {market} | {selection} | {action} | {stake} | {scope} | {reason} |".format(
                    board=md(row.get("board")),
                    market=md(f"{row.get('event', '')} / {row.get('market', '')}"),
                    selection=md(row.get("selection")),
                    action=md(row.get("original_action") or row.get("action")),
                    stake=money(row.get("stake_aud")),
                    scope=md(row.get("live_board_scope_label")),
                    reason=md(row.get("live_board_scope_reason") or row.get("live_board_report_usage")),
                )
            )
    lines.extend(
        [
        "",
            "## 判断依据来源",
            "",
            "| 类型 | 来源/公式 | 当前作用 |",
            "|---|---|---|",
            f"| Excel模板 | {md(calculation_policy.get('template_reference'))}；{md(calculation_policy.get('template_evidence_digest'))} | 下注前清单、赔率去水、EV、Edge、Kelly、下注日志和 CLV/ROI 复盘 |",
            f"| Edge | {md(calculation_policy.get('edge_formula'))} | 判断模型概率是否超过赔率盈亏平衡 |",
            f"| 套利率 | {md(calculation_policy.get('arbitrage_rate_formula'))} | 衡量价值率；不是跨平台 surebet |",
            f"| Risk of ruin | {md(calculation_policy.get('risk_of_ruin_formula'))} | 控制单注比例、半Kelly偏离和盘口风险 |",
            f"| 最低可接受赔率 | {md(calculation_policy.get('minimum_acceptable_odds_formula'))} | 防止实时赔率下滑后继续执行过期价值 |",
            f"| 预计收益 | {md(calculation_policy.get('expected_profit_formula'))} | 把 EV 转成金额，便于按预算排序 |",
            f"| 价格容忍度 | {md(calculation_policy.get('price_drift_tolerance_formula'))} | 判断 TAB 实时赔率是否仍有执行空间 |",
            f"| 仓位上限占用 | {md(calculation_policy.get('stake_cap_usage_formula'))} | 判断是否接近或超过单注上限 |",
            f"| 风险调整价值分 | {md(calculation_policy.get('risk_adjusted_value_formula'))} | 统一比较价值与 RoR 的相对优先级 |",
            f"| 市场资金倾向分 | {md(calculation_policy.get('market_funding_tendency_formula'))} | 给首页新增资金倾向列，并作为资金面复核排序依据 |",
            f"| 市场资金代理 | {md(calculation_policy.get('market_funding_proxy_formula'))} | 输出总资金、净资金、成交量、流动性、盘口深度和盘口浮动率代理 |",
            f"| 组合RoR | {md(calculation_policy.get('portfolio_risk_formula'))} | 把多条研究候选合并成预算压力测试 |",
            f"| 开源参考 | {md(', '.join(source_alignment.get('primary_references') or []))} | 提供 no-vig、xG/Poisson/DC、事件基本面、赛程校验等补充判断依据 |",
        "",
        "## Excel赛前控制映射",
        "",
        "| 控制项 | Excel依据 | 报告映射 | 决策用途 |",
        "|---|---|---|---|",
        ]
    )
    for control in calculation_policy.get("extracted_template_controls") or []:
        lines.append(
            f"| {md(control.get('control'))} | {md(control.get('excel_basis'))} | {md(control.get('report_mapping'))} | {md(control.get('decision_use'))} |"
        )
    lines.extend(
        [
        "",
        "## 逐行判断依据包",
        "",
            "| 下注 | 证据强度 | 概率价值依据 | 价格执行依据 | 风险控制依据 | 资料缺口 | 赛前复核清单 |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in payload.get("recommendation_rows") or []:
        basis = row.get("analysis_basis") or {}
        lines.append(
            "| {selection} | {strength} | {prob_basis} | {price_basis} | {risk_basis} | {gaps} | {checklist} |".format(
                selection=md(row.get("selection")),
                strength=md(basis.get("evidence_strength")),
                prob_basis=md("；".join(str(item) for item in (basis.get("probability_value_basis") or [])[:2])),
                price_basis=md("；".join(str(item) for item in (basis.get("price_execution_basis") or [])[:2])),
                risk_basis=md("；".join(str(item) for item in (basis.get("risk_control_basis") or [])[:2])),
                gaps=md("；".join(str(item) for item in (basis.get("data_gaps") or [])[:3])),
                checklist=md("；".join(str(item) for item in (basis.get("pre_bet_checklist") or [])[:3])),
            )
        )
    lines.extend(
        [
        "",
        "## Edge/RoR 决策诊断",
        "",
            "| 下注 | 价值信号 | 当前赔率 | 最低可接受赔率 | 赔率缓冲 | 价格容忍度 | 每AUD100预期 | 本注预计收益 | 上限占用 | Kelly安全垫 | 风险调整分 | RoR复核 | 结论 |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload.get("recommendation_rows") or []:
        diagnostic = row.get("decision_diagnostics") or {}
        lines.append(
            "| {selection} | {value_signal} | {odds} | {min_odds} | {odds_buffer} | {price_tol} | {profit_100} | {profit} | {cap_ratio} | {kelly_margin} | {value_score} | {ror_status} | {conclusion} |".format(
                selection=md(row.get("selection")),
                value_signal=md(diagnostic.get("value_signal")),
                odds=decimal(row.get("odds")),
                min_odds=decimal(diagnostic.get("minimum_acceptable_odds")),
                odds_buffer=decimal_signed(diagnostic.get("odds_buffer")),
                price_tol=pct(diagnostic.get("price_drift_tolerance_pct")),
                profit_100=money(diagnostic.get("expected_profit_per_100_aud")),
                profit=money(diagnostic.get("expected_profit_aud")),
                cap_ratio=pct(diagnostic.get("stake_to_cap_ratio")),
                kelly_margin=pct(diagnostic.get("kelly_safety_margin")),
                value_score=pct(diagnostic.get("risk_adjusted_value_score")),
                ror_status=md(diagnostic.get("ror_status")),
                conclusion=md(diagnostic.get("conclusion")),
            )
        )
    lines.extend(
        [
        "",
        "## 三指标解释包",
        "",
            "| 下注 | Edge解释 | 套利率解释 | Risk of ruin解释 | 综合动作 |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload.get("recommendation_rows") or []:
        pack = row.get("decision_metric_pack") or {}
        edge_pack = pack.get("edge") or {}
        arbitrage_pack = pack.get("arbitrage_rate") or {}
        ror_pack = pack.get("risk_of_ruin") or {}
        lines.append(
            "| {selection} | {edge} | {arbitrage} | {ror} | {action} |".format(
                selection=md(row.get("selection")),
                edge=md(edge_pack.get("decision_use")),
                arbitrage=md(arbitrage_pack.get("decision_use")),
                ror=md(ror_pack.get("decision_use")),
                action=md(pack.get("combined_action")),
            )
        )
    lines.extend(
        [
        "",
        "## 新旧推荐变化",
        "",
        f"- compare_status: `{compare.get('status', '')}`",
        f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
        f"- candidate_count_delta: `{compare.get('candidate_count_delta', 0)}`",
        f"- research_stake_delta_aud: `{compare.get('research_stake_delta_aud', 0)}`",
        f"- executable_stake_delta_aud: `{compare.get('executable_stake_delta_aud', 0)}`",
        f"- top_pick_changed: `{compare.get('top_pick_changed', False)}`",
        "",
        "## 推荐操作清单",
        "",
            "| 时间 | 板块 | 盘口 | 下注 | 赔率 | 金额 | 操作 | 分析一致性 | 模型复核 | 盘口价值 | 市场资金倾向分 | Edge | Edge门槛差 | 套利率 | Risk of ruin | RoR等级 | EV | 概率 | 置信度 | 原因 |",
            "|---|---|---|---|---:|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|---|",
        ]
    )
    for row in payload.get("recommendation_rows") or []:
        calibration = row.get("model_calibration") or {}
        funding = row.get("market_funding") or {}
        lines.append(
            "| {time} | {board} | {market} | {selection} | {odds} | {stake} | {action} | {consistency} | {model_review} | {value} | {funding_score} | {edge} | {edge_gap} | {arb} | {ror} | {risk_grade} | {ev} | {prob} | {confidence} | {reason} |".format(
                time=md(row.get("time")),
                board=md(row.get("board")),
                market=md(f"{row.get('event', '')} / {row.get('market', '')}"),
                selection=md(row.get("selection")),
                odds=decimal(row.get("odds")),
                stake=money(row.get("stake_aud")),
                action=md(row.get("action")),
                consistency=md(row.get("consistency")),
                model_review=md(f"{calibration.get('review_priority', '')} / {calibration.get('review_action', '')}"),
                value=md(row.get("value_label")),
                funding_score=md(funding.get("market_funding_tendency_score")),
                edge=pp(row.get("edge")),
                edge_gap=pp(row.get("edge_threshold_gap")),
                arb=pct(row.get("arbitrage_rate")),
                ror=pct(row.get("risk_of_ruin")),
                risk_grade=md(row.get("risk_of_ruin_grade")),
                ev=pct(row.get("expected_value")),
                prob=pct(row.get("probability")),
                confidence=md(row.get("confidence")),
                reason=md(row.get("reason")),
            )
        )
    lines.extend(["", f"> {payload.get('truthfulness_note', '')}", "", f"> {payload.get('safety_note', '')}"])
    return "\n".join(lines)


def write_recommendation_operations_pdf(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    executive = payload.get("executive_status") or {}
    rows = payload.get("recommendation_rows") or []
    research_rows = payload.get("research_rows_before_gate") or rows
    compare = payload.get("old_new_compare") or {}
    calculation_policy = payload.get("calculation_policy") or {}
    source_alignment = payload.get("source_alignment") or {}
    portfolio = summary.get("portfolio_risk") or {}
    market_funding = summary.get("market_funding") or {}
    probability_engine = payload.get("probability_engine") or calculation_policy.get("probability_engine_framework") or {}
    charts = [
        chart_from_items("研究金额 by 板块", [(key, board_stake(research_rows, key)) for key in (summary.get("board_distribution") or {}).keys()], "#1F4E79"),
        chart_from_items("EV Top", [(row.get("selection", ""), float(row.get("expected_value") or 0) * 100) for row in research_rows], "#C7352B"),
        chart_from_items("概率边际 pp", [(row.get("selection", ""), max(0.0, float(row.get("edge") or 0) * 100)) for row in research_rows], "#247A5A"),
        chart_from_items("Risk of ruin", [(row.get("selection", ""), float(row.get("risk_of_ruin") or 0) * 100) for row in research_rows], "#8B1E3F"),
        chart_from_items("预计收益 AUD", [(row.get("selection", ""), float(row.get("expected_profit_aud") or 0)) for row in research_rows], "#0F766E"),
        chart_from_items("风险调整价值分", [(row.get("selection", ""), float(row.get("risk_adjusted_value_score") or 0) * 100) for row in research_rows], "#7A3E9D"),
        chart_from_items("市场资金倾向分", [(row.get("selection", ""), float((row.get("market_funding") or {}).get("market_funding_tendency_score") or 0)) for row in research_rows], "#0B7285"),
        chart_from_items(
            "组合预算压力 AUD",
            [
                ("已投入参考", portfolio.get("declared_committed_reference_aud", 0)),
                ("研究候选", portfolio.get("candidate_stake_aud", 0)),
                ("预算下沿余量", max(0.0, float(portfolio.get("budget_floor_headroom_aud") or 0))),
                ("预算中位余量", max(0.0, float(portfolio.get("budget_mid_headroom_aud") or 0))),
            ],
            "#4B5563",
        ),
        chart_from_items("置信度分布", [(key, value) for key, value in (summary.get("confidence_distribution") or {}).items()], "#6A4C93"),
        chart_from_items("模型复核优先级", [(key, value) for key, value in (summary.get("model_review_priority_distribution") or {}).items()], "#B45309"),
        chart_from_items(
            "门禁/补缺状态",
            [
                ("raw ready", 1 if summary.get("raw_refresh_ready") else 0),
                ("publish ready", 1 if summary.get("formal_report_publish_ready") else 0),
                ("missing analysis days", summary.get("missing_analysis_day_count", 0)),
                ("missing reports", summary.get("missing_report_day_count", 0)),
                ("backfill queue", summary.get("backfill_queue_count", 0)),
            ],
            "#A56710",
        ),
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA 推荐操作 Dashboard",
        subtitle="首页推荐下注板块的正式归档：时间、盘口、下注、赔率、金额、概率、EV、置信度、门禁和新旧变化；只生成研究报告，不自动下注。",
        summary_rows=[
            ("status", str(executive.get("status", ""))),
            ("current_action", str(executive.get("current_action", ""))),
            ("executable stake", money(summary.get("executable_new_stake_aud"))),
            ("research stake", money(summary.get("research_candidate_stake_aud"))),
            ("candidate_count", str(summary.get("candidate_count", 0))),
            ("all candidates before scope", str(summary.get("all_candidate_count_before_scope", summary.get("candidate_count", 0)))),
            ("excluded unavailable", str(summary.get("excluded_unavailable_candidate_count", 0))),
            ("excluded stake", money(summary.get("excluded_unavailable_stake_aud"))),
            ("average_ev", pct(summary.get("average_ev"))),
            ("average_edge", pp(summary.get("average_edge"))),
            ("edge pass", f"{summary.get('edge_threshold_pass_count', 0)}/{summary.get('candidate_count', 0)}"),
            ("avg edge gap", pp(summary.get("average_edge_threshold_gap"))),
            ("average_arbitrage_rate", pct(summary.get("average_arbitrage_rate"))),
            ("max_risk_of_ruin", pct(summary.get("max_risk_of_ruin"))),
            ("high RoR rows", str(summary.get("high_risk_of_ruin_count", 0))),
            ("expected profit", money(summary.get("expected_profit_at_research_stake_aud"))),
            ("per AUD100 EV", money(summary.get("average_expected_profit_per_100_aud"))),
            ("RoR review rows", str(summary.get("ror_review_count", 0))),
            ("value pass", f"{summary.get('value_signal_pass_count', 0)}/{summary.get('candidate_count', 0)}"),
            ("price buffer pass", str(summary.get("price_buffer_positive_count", 0))),
            ("low/mid RoR", str(summary.get("low_or_medium_ror_count", 0))),
            ("model calibrated", f"{summary.get('model_calibrated_count', 0)}/{summary.get('candidate_count', 0)}"),
            ("model high divergence", str(summary.get("model_high_divergence_count", 0))),
            ("reverse consensus", str(summary.get("model_reverse_consensus_count", 0))),
            ("model review required", str(summary.get("model_review_required_count", 0))),
            ("avg price tolerance", pct(summary.get("average_price_drift_tolerance_pct"))),
            ("avg cap usage", pct(summary.get("average_stake_to_cap_ratio"))),
            ("avg risk adj value", pct(summary.get("average_risk_adjusted_value_score"))),
            ("avg market funding score", str(summary.get("average_market_funding_tendency_score", 0))),
            ("funding proxy total", money(summary.get("total_funds_proxy_aud"))),
            ("funding proxy net", money(summary.get("net_funds_proxy_aud"))),
            ("turnover proxy", money(summary.get("turnover_proxy_aud"))),
            ("probability engine", str(summary.get("probability_engine_status", ""))),
            ("prob modules", f"{summary.get('probability_engine_implemented_or_partial_count', 0)}/{summary.get('probability_engine_module_count', 0)}"),
            ("leakage controls", f"{summary.get('probability_engine_leakage_policy_defined_count', 0)}/{summary.get('probability_engine_leakage_control_count', 0)}"),
            ("tournament rules", f"{summary.get('probability_engine_tournament_rule_ready_count', 0)}/{summary.get('probability_engine_tournament_rule_count', 0)}"),
            ("prediction contract", f"{summary.get('probability_engine_prediction_contract_ready_count', 0)}/{summary.get('probability_engine_prediction_contract_field_count', 0)}"),
            ("backtest controls", f"{summary.get('probability_engine_backtest_ready_count', 0)}/{summary.get('probability_engine_backtest_control_count', 0)}"),
            ("portfolio RoR", f"{pct(summary.get('portfolio_risk_of_ruin'))} / {summary.get('portfolio_risk_grade', '')}"),
            ("portfolio exp profit", money(summary.get("portfolio_expected_profit_aud"))),
            ("portfolio loss if all lose", money(summary.get("portfolio_worst_case_new_loss_aud"))),
            ("portfolio mid usage", pct(summary.get("portfolio_combined_mid_usage_pct"))),
            ("bankroll_reference", money(summary.get("bankroll_reference_aud"))),
            ("old-new", str(compare.get("status", ""))),
        ],
        charts=charts,
        table_headers=["时间", "板块", "盘口", "下注", "赔率", "金额", "EV", "操作"],
        table_rows=[
            [
                str(row.get("time", "")),
                str(row.get("board", "")),
                f"{row.get('event', '')} / {row.get('market', '')}",
                str(row.get("selection", "")),
                decimal(row.get("odds")),
                money(row.get("stake_aud")),
                pct(row.get("expected_value")),
                str(row.get("action", "")),
            ]
            for row in rows[:12]
        ],
        extra_tables=[
            {
                "title": "概率工程输出矩阵",
                "headers": ["输出对象", "典型结果", "当前状态", "当前证据", "下一步"],
                "rows": [
                    [
                        str(item.get("output_object", "")),
                        str(item.get("typical_result", "")),
                        str(item.get("current_status", "")),
                        str(item.get("current_evidence", "")),
                        str(item.get("next_upgrade", "")),
                    ]
                    for item in probability_engine.get("outputs") or []
                ],
            },
            {
                "title": "概率工程模块覆盖",
                "headers": ["模块", "推荐状态", "作用", "关键输出", "当前状态"],
                "rows": [
                    [
                        str(item.get("module", "")),
                        str(item.get("recommended_status", "")),
                        str(item.get("role", "")),
                        str(item.get("key_output", "")),
                        str(item.get("current_status", "")),
                    ]
                    for item in probability_engine.get("modules") or []
                ],
            },
            {
                "title": "赛制模拟规则门禁",
                "headers": ["赛制规则", "决策用途", "当前状态", "Automation门禁"],
                "rows": [
                    [
                        str(item.get("rule", "")),
                        str(item.get("decision_use", "")),
                        str(item.get("current_status", "")),
                        str(item.get("automation_gate", "")),
                    ]
                    for item in probability_engine.get("tournament_rule_requirements") or []
                ],
            },
            {
                "title": "预测合约字段",
                "headers": ["字段", "必须", "决策用途", "当前状态"],
                "rows": [
                    [
                        str(item.get("field", "")),
                        str(item.get("required", "")),
                        str(item.get("decision_use", "")),
                        str(item.get("current_status", "")),
                    ]
                    for item in probability_engine.get("prediction_contract_fields") or []
                ],
            },
            {
                "title": "校准与回测控制",
                "headers": ["控制", "作用", "当前状态", "Automation用途"],
                "rows": [
                    [
                        str(item.get("control", "")),
                        str(item.get("purpose", "")),
                        str(item.get("current_status", "")),
                        str(item.get("automation_use", "")),
                    ]
                    for item in probability_engine.get("calibration_backtest_controls") or []
                ],
            },
            {
                "title": "防泄漏与可复现规则",
                "headers": ["要求", "必须", "当前状态", "证据"],
                "rows": [
                    [
                        str(item.get("control", "")),
                        str(item.get("required", "")),
                        str(item.get("current_status", "")),
                        str(item.get("evidence", "")),
                    ]
                    for item in probability_engine.get("leakage_controls") or []
                ],
            },
            {
                "title": "模型监控指标",
                "headers": ["指标", "作用", "当前状态"],
                "rows": [
                    [
                        str(item.get("metric", "")),
                        str(item.get("purpose", "")),
                        str(item.get("current_status", "")),
                    ]
                    for item in probability_engine.get("metrics") or []
                ],
            },
            {
                "title": "目标与指标落地",
                "headers": ["模块", "目标", "常用指标", "输出", "当前状态"],
                "rows": [
                    [
                        str(item.get("module", "")),
                        str(item.get("goal", "")),
                        str(item.get("common_metrics", "")),
                        str(item.get("output", "")),
                        str(item.get("current_status", "")),
                    ]
                    for item in probability_engine.get("objective_modules") or []
                ],
            },
            {
                "title": "机器学习候选模型",
                "headers": ["模型", "任务", "优点", "风险", "当前决策"],
                "rows": [
                    [
                        str(item.get("model", "")),
                        str(item.get("task", "")),
                        str(item.get("strength", "")),
                        str(item.get("risk", "")),
                        str(item.get("current_decision", "")),
                    ]
                    for item in probability_engine.get("ml_models") or []
                ],
            },
            {
                "title": "技术面规则",
                "headers": ["名称", "公式", "决策规则", "当前状态"],
                "rows": [
                    [
                        str(item.get("name", "")),
                        str(item.get("formula", "")),
                        str(item.get("decision_rule", "")),
                        str(item.get("current_status", "")),
                    ]
                    for item in probability_engine.get("technical_rules") or []
                ],
            },
            {
                "title": "进球模型说明",
                "headers": ["模型", "公式", "用途", "当前状态"],
                "rows": [
                    [
                        str(item.get("name", "")),
                        str(item.get("formula", "")),
                        str(item.get("use", "")),
                        str(item.get("current_status", "")),
                    ]
                    for item in probability_engine.get("scoring_models") or []
                ],
            },
            {
                "title": "基本面分析层",
                "headers": ["层级", "输入", "决策用途", "当前状态"],
                "rows": [
                    [
                        str(item.get("layer", "")),
                        str(item.get("inputs", "")),
                        str(item.get("decision_use", "")),
                        str(item.get("current_status", "")),
                    ]
                    for item in probability_engine.get("fundamental_layers") or []
                ],
            },
            {
                "title": "市场资金分析",
                "headers": ["下注", "资金倾向分", "倾向", "总资金", "净资金", "成交量", "流动性", "盘口深度", "日均盘口浮动"],
                "rows": [
                    [
                        str(row.get("selection", "")),
                        str((row.get("market_funding") or {}).get("market_funding_tendency_score", "")),
                        str((row.get("market_funding") or {}).get("market_funding_bias_label", "")),
                        money((row.get("market_funding") or {}).get("total_funds_proxy_aud")),
                        money((row.get("market_funding") or {}).get("net_funds_proxy_aud")),
                        money((row.get("market_funding") or {}).get("turnover_proxy_aud")),
                        f"{pct((row.get('market_funding') or {}).get('liquidity_score'))} / {(row.get('market_funding') or {}).get('liquidity_grade', '')}",
                        f"{pct((row.get('market_funding') or {}).get('market_depth_score'))} / {(row.get('market_funding') or {}).get('market_depth_grade', '')}",
                        pct((row.get("market_funding") or {}).get("daily_line_move_float_rate")),
                    ]
                    for row in rows[:12]
                ],
            },
            {
                "title": "Edge 信息与门槛",
                "headers": ["下注", "模型概率", "盈亏平衡", "Edge", "门槛", "门槛差", "等级"],
                "rows": [
                    [
                        str(row.get("selection", "")),
                        pct(row.get("probability")),
                        pct(row.get("breakeven")),
                        pp(row.get("edge")),
                        pp(row.get("edge_threshold")),
                        pp(row.get("edge_threshold_gap")),
                        str(row.get("edge_quality", "")),
                    ]
                    for row in rows[:12]
                ],
            },
            {
                "title": "Edge / 套利率 / Risk of ruin",
                "headers": ["下注", "套利率", "Risk of ruin", "等级", "半Kelly", "仓位", "触发因素"],
                "rows": [
                    [
                        str(row.get("selection", "")),
                        pct(row.get("arbitrage_rate")),
                        pct(row.get("risk_of_ruin")),
                        str(row.get("risk_of_ruin_grade", "")),
                        pct(row.get("discounted_kelly_fraction")),
                        pct(row.get("stake_fraction")),
                        "；".join(str(item) for item in (row.get("risk_drivers") or [])) or "无明显额外触发因素",
                    ]
                    for row in rows[:12]
                ],
            },
            {
                "title": "逐行判断依据包",
                "headers": ["下注", "证据强度", "概率价值", "价格执行", "风险控制", "资料缺口", "赛前复核"],
                "rows": [
                    [
                        str(row.get("selection", "")),
                        str((row.get("analysis_basis") or {}).get("evidence_strength", "")),
                        "；".join(str(item) for item in ((row.get("analysis_basis") or {}).get("probability_value_basis") or [])[:2]),
                        "；".join(str(item) for item in ((row.get("analysis_basis") or {}).get("price_execution_basis") or [])[:2]),
                        "；".join(str(item) for item in ((row.get("analysis_basis") or {}).get("risk_control_basis") or [])[:2]),
                        "；".join(str(item) for item in ((row.get("analysis_basis") or {}).get("data_gaps") or [])[:2]),
                        "；".join(str(item) for item in ((row.get("analysis_basis") or {}).get("pre_bet_checklist") or [])[:2]),
                    ]
                    for row in rows[:12]
                ],
            },
            {
                "title": "模型共识校准",
                "headers": ["下注", "一致性", "共识方向", "共识概率", "模型均值", "本地概率差", "最大分歧", "优先级", "动作"],
                "rows": [
                    [
                        str(row.get("selection", "")),
                        str((row.get("model_calibration") or {}).get("consistency_label", "")),
                        str((row.get("model_calibration") or {}).get("consensus_selection", "")),
                        pct((row.get("model_calibration") or {}).get("consensus_probability")),
                        pct((row.get("model_calibration") or {}).get("market_model_probability")),
                        pp((row.get("model_calibration") or {}).get("probability_gap_vs_model")),
                        pct((row.get("model_calibration") or {}).get("max_disagreement")),
                        str((row.get("model_calibration") or {}).get("review_priority", "")),
                        str((row.get("model_calibration") or {}).get("review_action", "")),
                    ]
                    for row in rows[:12]
                ],
            },
            {
                "title": "Edge/RoR 决策诊断",
                "headers": ["下注", "价值信号", "最低赔率", "赔率缓冲", "价格容忍度", "每AUD100", "预计收益", "上限占用", "Kelly安全垫", "风险调整分", "RoR复核", "结论"],
                "rows": [
                    [
                        str(row.get("selection", "")),
                        str((row.get("decision_diagnostics") or {}).get("value_signal", "")),
                        decimal((row.get("decision_diagnostics") or {}).get("minimum_acceptable_odds")),
                        decimal_signed((row.get("decision_diagnostics") or {}).get("odds_buffer")),
                        pct((row.get("decision_diagnostics") or {}).get("price_drift_tolerance_pct")),
                        money((row.get("decision_diagnostics") or {}).get("expected_profit_per_100_aud")),
                        money((row.get("decision_diagnostics") or {}).get("expected_profit_aud")),
                        pct((row.get("decision_diagnostics") or {}).get("stake_to_cap_ratio")),
                        pct((row.get("decision_diagnostics") or {}).get("kelly_safety_margin")),
                        pct((row.get("decision_diagnostics") or {}).get("risk_adjusted_value_score")),
                        str((row.get("decision_diagnostics") or {}).get("ror_status", "")),
                        str((row.get("decision_diagnostics") or {}).get("conclusion", "")),
                    ]
                    for row in rows[:12]
                ],
            },
            {
                "title": "三指标解释包",
                "headers": ["下注", "Edge解释", "套利率解释", "RoR解释", "综合动作"],
                "rows": [
                    [
                        str(row.get("selection", "")),
                        str(((row.get("decision_metric_pack") or {}).get("edge") or {}).get("decision_use", "")),
                        str(((row.get("decision_metric_pack") or {}).get("arbitrage_rate") or {}).get("decision_use", "")),
                        str(((row.get("decision_metric_pack") or {}).get("risk_of_ruin") or {}).get("decision_use", "")),
                        str((row.get("decision_metric_pack") or {}).get("combined_action", "")),
                    ]
                    for row in rows[:12]
                ],
            },
            {
                "title": "组合风险与预算压力",
                "headers": ["指标", "数值", "解释"],
                "rows": [
                    ["预算区间", f"{money(portfolio.get('budget_floor_aud'))} - {money(portfolio.get('budget_ceiling_aud'))}", f"中位预算 {money(portfolio.get('budget_mid_aud'))}。"],
                    ["已投入参考", money(portfolio.get("declared_committed_reference_aud")), "用户声明参考值，待持仓快照同步确认。"],
                    ["研究候选金额", money(portfolio.get("candidate_stake_aud")), "当前可研究买入候选总金额。"],
                    ["组合预计收益", money(portfolio.get("expected_profit_aud")), "按各行 EV × 注额加总。"],
                    ["每AUD100组合预期", money(portfolio.get("expected_profit_per_100_aud")), "注额加权 EV 转成金额。"],
                    ["最坏全输新增亏损", money(portfolio.get("worst_case_new_loss_aud")), "只计算本轮研究候选。"],
                    ["组合Risk of ruin", pct(portfolio.get("portfolio_risk_of_ruin")), f"{portfolio.get('portfolio_risk_grade', '')} / {portfolio.get('portfolio_ror_status', '')}"],
                    ["中位预算总占用", pct(portfolio.get("combined_mid_usage_pct")), "已投入参考 + 本轮候选金额。"],
                    ["推荐动作", str(portfolio.get("recommended_action", "")), str(portfolio.get("verification_status", ""))],
                ],
            },
            {
                "title": "Excel赛前控制映射",
                "headers": ["控制项", "Excel依据", "报告映射", "决策用途"],
                "rows": [
                    [
                        str(item.get("control", "")),
                        str(item.get("excel_basis", "")),
                        str(item.get("report_mapping", "")),
                        str(item.get("decision_use", "")),
                    ]
                    for item in calculation_policy.get("extracted_template_controls") or []
                ],
            },
            {
                "title": "Excel模板吸收范围",
                "headers": ["Sheet", "样例字段", "当前用途"],
                "rows": excel_preview_table_rows(calculation_policy.get("excel_reference_profile") or {}),
            },
            {
                "title": "Excel模板证据增强",
                "headers": ["资料", "Excel证据", "报告落地"],
                "rows": [
                    [
                        str(item.get("material", "")),
                        str(item.get("evidence", "")),
                        str(item.get("report_use", "")),
                    ]
                    for item in calculation_policy.get("template_analysis_materials") or []
                ],
            },
            {
                "title": "判断依据来源",
                "headers": ["类型", "来源/公式", "当前作用"],
                "rows": [
                    [
                        "Excel模板",
                        f"{calculation_policy.get('template_reference', '')}; {calculation_policy.get('template_evidence_digest', '')}",
                        "赛前清单、赔率去水、EV、Edge、Kelly、下注日志和 CLV/ROI 复盘。",
                    ],
                    ["Edge", str(calculation_policy.get("edge_formula", "")), "判断模型概率是否超过赔率盈亏平衡。"],
                    ["套利率", str(calculation_policy.get("arbitrage_rate_formula", "")), "衡量价值率，不代表跨平台 surebet。"],
                    ["Risk of ruin", str(calculation_policy.get("risk_of_ruin_formula", "")), "控制单注比例、半Kelly偏离和盘口风险。"],
                    ["市场资金倾向分", str(calculation_policy.get("market_funding_tendency_formula", "")), "给首页新增资金倾向列，并作为资金面复核排序依据。"],
                    ["市场资金代理", str(calculation_policy.get("market_funding_proxy_formula", "")), "输出总资金、净资金、成交量、流动性、盘口深度和盘口浮动率代理。"],
                    ["组合RoR", str(calculation_policy.get("portfolio_risk_formula", "")), "把多条研究候选合并成预算压力测试。"],
                    [
                        "风控纪律",
                        "基础单注0.5%-1.0%，单注上限2.0%，主流市场Edge 2%-3%，小市场Edge 4%-6%。",
                        "避免追损、加倍、情绪下注、无首发重仓和无记录下注。",
                    ],
                    [
                        "开源参考",
                        ", ".join(source_alignment.get("primary_references") or []),
                        "补充 no-vig、xG/Poisson/DC、事件基本面和赛程校验。",
                    ],
                ],
            },
            {
                "title": "新旧推荐变化",
                "headers": ["字段", "值"],
                "rows": [
                    ["previous_generated_at", str(compare.get("previous_generated_at", ""))],
                    ["candidate_count_delta", str(compare.get("candidate_count_delta", 0))],
                    ["research_stake_delta_aud", money(compare.get("research_stake_delta_aud", 0))],
                    ["executable_stake_delta_aud", money(compare.get("executable_stake_delta_aud", 0))],
                    ["top_pick_changed", str(compare.get("top_pick_changed", False))],
                ],
            },
            {
                "title": "缺失板块排除审计",
                "headers": ["板块", "盘口", "下注", "原动作", "原金额", "范围状态"],
                "rows": [
                    [
                        str(row.get("board", "")),
                        f"{row.get('event', '')} / {row.get('market', '')}",
                        str(row.get("selection", "")),
                        str(row.get("original_action") or row.get("action") or ""),
                        money(row.get("stake_aud")),
                        str(row.get("live_board_scope_label", "")),
                    ]
                    for row in payload.get("excluded_unavailable_rows") or []
                ]
                or [["无", "当前没有缺失板块候选", "", "", "AUD 0", ""]],
            },
            {
                "title": "门禁解释",
                "headers": ["项目", "状态"],
                "rows": [
                    ["formal_report_publish_ready", str(summary.get("formal_report_publish_ready"))],
                    ["raw_refresh_ready", str(summary.get("raw_refresh_ready"))],
                    ["execution_allowed", str(summary.get("execution_allowed"))],
                    ["primary_user_action", str(executive.get("primary_user_action", ""))],
                ],
            },
        ],
    )


def persist_recommendation_operations(db_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    summary = public_payload.get("summary") or {}
    executive = public_payload.get("executive_status") or {}
    try:
        with connect_report_db(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendation_operation_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    latest_run_id TEXT NOT NULL DEFAULT '',
                    latest_report_date TEXT NOT NULL DEFAULT '',
                    candidate_count INTEGER NOT NULL DEFAULT 0,
                    research_candidate_stake_aud REAL NOT NULL DEFAULT 0,
                    executable_new_stake_aud REAL NOT NULL DEFAULT 0,
                    execution_allowed INTEGER NOT NULL DEFAULT 0,
                    average_ev REAL NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO recommendation_operation_snapshots(
                    snapshot_id, generated_at, status, latest_run_id, latest_report_date,
                    candidate_count, research_candidate_stake_aud, executable_new_stake_aud,
                    execution_allowed, average_ev, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    public_payload.get("snapshot_id", ""),
                    public_payload.get("generated_at", ""),
                    str(executive.get("status") or ""),
                    str(summary.get("latest_run_id") or ""),
                    str(summary.get("latest_report_date") or ""),
                    int(summary.get("candidate_count") or 0),
                    float(summary.get("research_candidate_stake_aud") or 0),
                    float(summary.get("executable_new_stake_aud") or 0),
                    int(bool(summary.get("execution_allowed"))),
                    float(summary.get("average_ev") or 0),
                    json.dumps(public_payload, ensure_ascii=False, sort_keys=True),
                ),
            )
            conn.commit()
        return {"status": "stored", "database": Path(db_path).name, "table": "recommendation_operation_snapshots"}
    except sqlite3.Error as exc:
        return {"status": "failed", "database": Path(db_path).name, "error": str(exc)}


def old_new_compare(db_path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not Path(db_path).exists():
        return {"status": "no_previous_snapshot", "candidate_count_delta": 0, "research_stake_delta_aud": 0, "executable_stake_delta_aud": 0}
    try:
        with connect_report_db(db_path) as conn:
            row = conn.execute(
                """
                SELECT generated_at, candidate_count, research_candidate_stake_aud,
                       executable_new_stake_aud, payload_json
                FROM recommendation_operation_snapshots
                ORDER BY generated_at DESC
                LIMIT 1
                """
            ).fetchone()
    except sqlite3.Error:
        return {"status": "compare_unavailable", "candidate_count_delta": 0, "research_stake_delta_aud": 0, "executable_stake_delta_aud": 0}
    if not row:
        return {"status": "no_previous_snapshot", "candidate_count_delta": 0, "research_stake_delta_aud": 0, "executable_stake_delta_aud": 0}
    previous_payload = parse_json(row["payload_json"])
    previous_rows = {str(item.get("row_key") or ""): item for item in previous_payload.get("recommendation_rows", []) if isinstance(item, dict)}
    current_rows = {str(item.get("row_key") or ""): item for item in rows}
    current_research_stake = sum(float(item.get("stake_aud") or 0) for item in rows)
    current_executable_stake = sum(float(item.get("executable_stake_aud") if item.get("executable_stake_aud") is not None else item.get("stake_aud") or 0) for item in rows if item.get("action_class") == "buy")
    previous_top = (previous_payload.get("summary") or {}).get("top_pick") or {}
    previous_summary = previous_payload.get("summary") or {}
    current_top = rows[0] if rows else {}
    current_arbitrage_values = [float(item.get("arbitrage_rate") or 0) for item in rows]
    current_risk_values = [float(item.get("risk_of_ruin") or 0) for item in rows]
    current_average_arbitrage = sum(current_arbitrage_values) / len(current_arbitrage_values) if current_arbitrage_values else 0.0
    current_max_risk = max(current_risk_values) if current_risk_values else 0.0
    return {
        "status": "compared",
        "previous_generated_at": row["generated_at"],
        "candidate_count_delta": int(len(rows) - int(row["candidate_count"] or 0)),
        "research_stake_delta_aud": round(current_research_stake - float(row["research_candidate_stake_aud"] or 0), 2),
        "executable_stake_delta_aud": round(current_executable_stake - float(row["executable_new_stake_aud"] or 0), 2),
        "average_arbitrage_rate_delta": round(current_average_arbitrage - float(previous_summary.get("average_arbitrage_rate") or 0), 4),
        "max_risk_of_ruin_delta": round(current_max_risk - float(previous_summary.get("max_risk_of_ruin") or 0), 4),
        "new_recommendations": sorted(current_rows.keys() - previous_rows.keys())[:8],
        "removed_recommendations": sorted(previous_rows.keys() - current_rows.keys())[:8],
        "top_pick_changed": row_key(previous_top.get("board", ""), previous_top.get("event", ""), previous_top.get("market", ""), previous_top.get("selection", ""))
        != row_key(current_top.get("board", ""), current_top.get("event", ""), current_top.get("market", ""), current_top.get("selection", "")),
    }


def recommendation_execution_allowed(readiness: dict[str, Any], raw_health: dict[str, Any]) -> bool:
    return readiness.get("formal_report_publish_ready") is True and raw_health.get("ready") is True


def execution_gate_message(readiness: dict[str, Any], raw_health: dict[str, Any]) -> str:
    blockers = raw_health.get("blocker_codes") or []
    if raw_health.get("ready") is not True:
        detail = f"阻塞类型：{'、'.join(str(item) for item in blockers[:3])}。" if blockers else ""
        return f"公开盘口 raw 未就绪，暂停执行新增下注；TAB 拒绝 AI controlled access 时需接入授权数据源或导入用户导出快照，再重跑日报门禁。{detail}"
    if readiness.get("formal_report_publish_ready") is not True:
        return "当前日报发布门禁未通过，暂停执行新增下注；保留研究候选，等待持仓和日报门禁恢复。"
    return "公开盘口和日报门禁已通过，可按执行清单逐项复核 TAB 实时赔率。"


def match_time_index(output_dir: Path) -> dict[str, str]:
    payload = load_json(Path(output_dir) / "tab_fifa_matches_main_markets_raw_v0_9.json")
    index: dict[str, str] = {}
    pattern = re.compile(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}\s+[A-Z][a-z]{2}\s+\d{1,2}:\d{2}\b")
    for item in payload.get("matches", []):
        match = str(item.get("match") or "")
        markets = item.get("markets") or {}
        block = "\n".join(str(value) for value in markets.values())
        found = pattern.search(block)
        if match and found:
            index[match] = found.group(0)
    return index


def action_label(action: str, stake: Any) -> str:
    try:
        if float(stake or 0) > 0:
            return "买入"
    except (TypeError, ValueError):
        pass
    if action == "watch_or_no_bet":
        return "观察/不下注"
    return str(action or "")


def consistency_label(raw: dict[str, Any]) -> str:
    signal = raw.get("model_signal") or {}
    if not signal:
        return "待模型校准"
    if signal.get("high_divergence"):
        return "模型分歧高"
    if signal.get("selection_aligned_with_consensus"):
        return "三模型一致"
    return "部分一致"


def confidence_label(raw: dict[str, Any]) -> str:
    signal = raw.get("model_signal") or {}
    value = str(signal.get("consensus_confidence") or "")
    return {"high": "高", "medium": "中", "low": "低"}.get(value.lower(), "待校准")


def value_label(expected_value: Any, edge: Any, stake: Any) -> str:
    ev = to_float(expected_value)
    stake_value = to_float(stake) or 0.0
    if stake_value <= 0:
        return "观察价值"
    if ev is not None and ev >= 0.15:
        return "高价值"
    if ev is not None and ev >= 0.05:
        return "中高价值"
    edge_value = to_float(edge)
    if edge_value is not None and edge_value > 0:
        return "小正边际"
    return "待复核"


def chinese_reason(
    row: sqlite3.Row,
    raw: dict[str, Any],
    breakeven: float | None,
    edge: Any,
    arbitrage_rate: Any,
    risk_of_ruin: Any,
    bankroll_reference: float,
    *,
    edge_threshold: Any = None,
    edge_threshold_gap: Any = None,
    risk_grade: str = "",
    risk_drivers: list[str] | None = None,
    decision_diagnostic: dict[str, Any] | None = None,
    model_calibration: dict[str, Any] | None = None,
) -> str:
    probability = row["probability"]
    odds = row["odds"]
    ev = row["expected_value"]
    stake = float(row["stake_aud"] or 0)
    if probability is not None and breakeven is not None and ev is not None:
        base = (
            f"模型概率 {pct(probability)} 高于赔率盈亏平衡 {pct(breakeven)}，"
            f"Edge {pp(edge)}，套利率 {pct(arbitrage_rate)}，EV {pct(ev)}。"
        )
    elif probability is not None and odds is not None:
        base = f"当前概率 {pct(probability)}，TAB 赔率 {float(odds):.2f}，仍需补充独立模型 EV 校准。"
    else:
        base = "当前只进入观察池，缺少足够独立概率和 EV 证据。"
    base += f" 建议执行金额 {money(stake)}，属于小仓分散下注。" if stake > 0 else " 当前不建议投入真实金额。"
    if edge_threshold is not None and edge_threshold_gap is not None:
        base += f" Edge门槛 {pp(edge_threshold)}，门槛差 {pp(edge_threshold_gap)}，纪律等级：{edge_quality_label(edge, edge_threshold)}。"
    base += f" Risk of ruin 估计 {pct(risk_of_ruin)}（{risk_grade or risk_of_ruin_grade(risk_of_ruin)}），按平衡口径资金池 {money(bankroll_reference)}、单注比例和半Kelly偏离计算。"
    if risk_drivers:
        base += f" 主要风险触发：{'；'.join(str(item) for item in risk_drivers)}。"
    diagnostic = decision_diagnostic or {}
    if diagnostic:
        base += (
            f" 赔率执行底线：最低可接受赔率 {decimal(diagnostic.get('minimum_acceptable_odds'))}，"
            f"当前赔率缓冲 {decimal_signed(diagnostic.get('odds_buffer'))}，"
            f"价格容忍度 {pct(diagnostic.get('price_drift_tolerance_pct'))}；"
            f"预计收益 {money(diagnostic.get('expected_profit_aud'))}，每 AUD100 预期 {money(diagnostic.get('expected_profit_per_100_aud'))}。"
            f" 仓位纪律：{diagnostic.get('stake_discipline_status', '待校准')}；"
            f"RoR复核：{diagnostic.get('ror_status', '待校准')}；"
            f"价值信号：{diagnostic.get('value_signal', '待校准')}；"
            f"仓位上限占用 {pct(diagnostic.get('stake_to_cap_ratio'))}，Kelly安全垫 {pct(diagnostic.get('kelly_safety_margin'))}。"
        )
    base += " 判断依据覆盖赔率去水、EV/Edge/Kelly、Poisson/xG、openfootball赛程校验、开源模型交叉验证、赛前10分钟清单和CLV/ROI复盘。"
    if model_calibration:
        base += (
            f" 模型校准：{model_calibration.get('consistency_label', '待模型校准')}，"
            f"{model_calibration.get('evidence_text', '')}"
            f" 复核动作：{model_calibration.get('review_action', '待复核')}。"
        )
    if (raw.get("event_risk") or {}).get("flag_count"):
        base += " 赛前需复核伤停、阵容和新闻事件。"
    return base


def bankroll_reference_aud(output_dir: Path, latest_commit: dict[str, Any]) -> float:
    candidates: list[Path] = []
    outputs = latest_commit.get("outputs") if isinstance(latest_commit.get("outputs"), dict) else {}
    for value in [latest_commit.get("bankroll_plan_run_copy"), latest_commit.get("bankroll_plan"), outputs.get("bankroll_plan_run_copy"), outputs.get("bankroll_plan")]:
        if value:
            candidates.append(Path(output_dir) / Path(str(value)).name)
    report_date = latest_commit.get("report_date")
    if report_date:
        candidates.append(Path(output_dir) / f"tab_fifa_bankroll_plan_{report_date}.json")
    candidates.extend(sorted(Path(output_dir).glob("tab_fifa_bankroll_plan_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:3])
    for path in candidates:
        payload = load_json(path)
        for key in ["budget_mid_aud", "bankroll_aud"]:
            value = to_float(payload.get(key))
            if value and value > 0:
                return value
    return DEFAULT_BANKROLL_REFERENCE_AUD


def value_arbitrage_rate(expected_value: Any, probability: Any, odds: Any) -> float | None:
    ev = to_float(expected_value)
    if ev is None:
        prob = to_float(probability)
        price = to_float(odds)
        if prob is None or price is None:
            return None
        ev = prob * price - 1
    return round(max(0.0, ev), 4)


def expected_profit_aud(stake_aud: Any, expected_value: Any) -> float | None:
    stake = to_float(stake_aud)
    ev = to_float(expected_value)
    if stake is None or ev is None:
        return None
    return round(stake * ev, 2)


def expected_profit_per_100_aud(expected_value: Any) -> float | None:
    ev = to_float(expected_value)
    if ev is None:
        return None
    return round(100 * ev, 2)


def minimum_acceptable_odds(probability: Any, edge_threshold: Any) -> float | None:
    prob = to_float(probability)
    threshold = to_float(edge_threshold)
    if prob is None or threshold is None:
        return None
    required_breakeven = prob - threshold
    if required_breakeven <= 0:
        return None
    return round(1 / required_breakeven, 2)


def odds_buffer(odds: Any, minimum_odds: Any) -> float | None:
    price = to_float(odds)
    floor = to_float(minimum_odds)
    if price is None or floor is None:
        return None
    return round(price - floor, 2)


def price_drift_tolerance_pct(odds_buffer_value: Any, odds: Any) -> float | None:
    buffer_value = to_float(odds_buffer_value)
    price = to_float(odds)
    if buffer_value is None or price is None or price <= 0:
        return None
    return round(buffer_value / price, 4)


def stake_to_cap_ratio(stake_fraction: Any) -> float | None:
    fraction = to_float(stake_fraction)
    if fraction is None:
        return None
    return round(fraction / SINGLE_BET_CAP_FRACTION, 4)


def kelly_safety_margin(half_kelly_ratio: Any) -> float | None:
    ratio = to_float(half_kelly_ratio)
    if ratio is None:
        return None
    return round(1 - ratio, 4)


def risk_adjusted_value_score(expected_value: Any, edge_threshold_gap_value: Any, risk_of_ruin: Any) -> float | None:
    ev = to_float(expected_value)
    risk = to_float(risk_of_ruin)
    if ev is None or risk is None:
        return None
    gap = to_float(edge_threshold_gap_value) or 0.0
    return round(ev + max(0.0, gap) - risk, 4)


def value_signal_label(expected_value: Any, edge_threshold_gap_value: Any, odds_buffer_value: Any, risk_of_ruin: Any) -> str:
    ev = to_float(expected_value)
    gap = to_float(edge_threshold_gap_value)
    buffer_value = to_float(odds_buffer_value)
    risk = to_float(risk_of_ruin)
    if ev is None or gap is None:
        return "待校准"
    if buffer_value is not None and buffer_value < 0:
        return "价格已走差"
    if ev > 0 and gap >= 0 and (risk is None or risk < ROR_REVIEW_THRESHOLD):
        return "价值通过"
    if ev > 0 and gap >= 0:
        return "价值通过但RoR复核"
    if ev > 0:
        return "EV正但Edge不足"
    return "观察或放弃"


def market_funding_profile(
    *,
    board: Any,
    market: Any,
    selection: Any,
    odds: Any,
    probability: Any,
    expected_value: Any,
    edge: Any,
    arbitrage_rate: Any,
    price_drift_tolerance: Any,
    stake_aud: Any,
    stake_fraction: Any,
    risk_of_ruin: Any,
    risk_flags: int = 0,
) -> dict[str, Any]:
    """Estimate public market-funding pressure from available odds inputs.

    TAB does not expose exchange-style matched volume/order-book depth in these
    public pages, so this is deliberately labelled as proxy analysis.
    """
    liquidity_score = market_liquidity_score(board, market)
    depth_score = market_depth_score(market, odds)
    daily_float = daily_line_move_float_rate(market, price_drift_tolerance, risk_flags)
    ev = to_float(expected_value) or 0.0
    edge_value = to_float(edge) or 0.0
    arb = to_float(arbitrage_rate) or max(0.0, ev)
    risk = to_float(risk_of_ruin) or 0.0
    tolerance = to_float(price_drift_tolerance) or 0.0
    stake_value = max(0.0, to_float(stake_aud) or 0.0)
    stake_ratio = max(0.0, to_float(stake_fraction) or 0.0)
    value_pressure = ev * 42.0 + edge_value * 220.0 + arb * 26.0 + tolerance * 18.0
    risk_pressure = risk * 80.0 + daily_float * 22.0 + max(0, risk_flags) * 1.5
    liquidity_pressure = (liquidity_score - 0.55) * 18.0 + (depth_score - 0.55) * 10.0
    tendency_score = round(clamp(50.0 + value_pressure + liquidity_pressure - risk_pressure, 0.0, 100.0), 1)
    base_pool = market_base_pool_aud(board, market)
    total_funds_proxy = round(base_pool * (0.55 + liquidity_score * 0.65 + depth_score * 0.25), 2)
    turnover_proxy = round(total_funds_proxy * clamp(0.18 + daily_float * 1.65 + stake_ratio * 12.0, 0.12, 0.95), 2)
    net_funds_proxy = round(total_funds_proxy * ((tendency_score - 50.0) / 100.0), 2)
    return {
        "data_status": "proxy_inferred_from_public_odds",
        "truthfulness_note": "TAB公开页面未提供真实成交资金或订单簿；本层为盘口资金代理指标，不是官方成交量。",
        "selection": str(selection or ""),
        "market_funding_tendency_score": tendency_score,
        "market_funding_tendency_grade": market_funding_grade(tendency_score),
        "market_funding_bias_label": market_funding_bias_label(tendency_score),
        "total_funds_proxy_aud": total_funds_proxy,
        "net_funds_proxy_aud": net_funds_proxy,
        "turnover_proxy_aud": turnover_proxy,
        "liquidity_score": round(liquidity_score, 4),
        "liquidity_grade": liquidity_grade(liquidity_score),
        "market_depth_score": round(depth_score, 4),
        "market_depth_grade": market_depth_grade(depth_score),
        "daily_line_move_float_rate": round(daily_float, 4),
        "funding_pressure_inputs": {
            "expected_value": ev,
            "edge": edge_value,
            "arbitrage_rate": arb,
            "price_drift_tolerance_pct": tolerance,
            "risk_of_ruin": risk,
            "stake_aud": stake_value,
            "stake_fraction": stake_ratio,
            "risk_flags": int(risk_flags or 0),
        },
        "decision_use": "资金倾向分越高，说明当前赔率价值、流动性和盘口深度更支持小仓研究；低分不代表必输，只代表资金/盘口结构不支持加仓。",
    }


def market_funding_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    profiles = [row.get("market_funding") or {} for row in rows if row.get("market_funding")]
    scores = [float(item.get("market_funding_tendency_score") or 0) for item in profiles]
    liquidity = [float(item.get("liquidity_score") or 0) for item in profiles]
    depth = [float(item.get("market_depth_score") or 0) for item in profiles]
    float_rates = [float(item.get("daily_line_move_float_rate") or 0) for item in profiles]
    total_funds = round(sum(float(item.get("total_funds_proxy_aud") or 0) for item in profiles), 2)
    net_funds = round(sum(float(item.get("net_funds_proxy_aud") or 0) for item in profiles), 2)
    turnover = round(sum(float(item.get("turnover_proxy_aud") or 0) for item in profiles), 2)
    return {
        "data_status": "proxy_inferred_from_public_odds",
        "funding_row_count": len(profiles),
        "average_market_funding_tendency_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "supportive_funding_count": sum(1 for score in scores if score >= 60),
        "weak_funding_count": sum(1 for score in scores if score < 45),
        "total_funds_proxy_aud": total_funds,
        "net_funds_proxy_aud": net_funds,
        "turnover_proxy_aud": turnover,
        "average_liquidity_score": round(sum(liquidity) / len(liquidity), 4) if liquidity else 0.0,
        "average_market_depth_score": round(sum(depth) / len(depth), 4) if depth else 0.0,
        "average_daily_line_move_float_rate": round(sum(float_rates) / len(float_rates), 4) if float_rates else 0.0,
        "top_funding_selection": max(
            profiles,
            key=lambda item: float(item.get("market_funding_tendency_score") or 0),
            default={},
        ).get("selection", ""),
        "truthfulness_note": "资金字段为盘口资金代理指标；没有把 TAB 未公开的真实成交资金、真实净流入或订单簿深度伪装为事实。",
    }


def market_funding_reason(profile: dict[str, Any]) -> str:
    if not profile:
        return ""
    return (
        f" 市场资金分析：倾向分 {profile.get('market_funding_tendency_score', '待校准')}，"
        f"{profile.get('market_funding_bias_label', '待校准')}；"
        f"总资金代理 {money(profile.get('total_funds_proxy_aud'))}，"
        f"净资金代理 {money(profile.get('net_funds_proxy_aud'))}，"
        f"成交量代理 {money(profile.get('turnover_proxy_aud'))}；"
        f"流动性 {pct(profile.get('liquidity_score'))}（{profile.get('liquidity_grade', '待校准')}），"
        f"盘口深度 {pct(profile.get('market_depth_score'))}（{profile.get('market_depth_grade', '待校准')}），"
        f"日均盘口变动浮动率 {pct(profile.get('daily_line_move_float_rate'))}。"
        " 以上为公开盘口代理指标，不是 TAB 官方成交资金。"
    )


def market_liquidity_score(board: Any, market: Any) -> float:
    value = f"{board} {market}".lower()
    score = 0.56
    if "matches" in value:
        score += 0.12
    if "futures" in value:
        score += 0.02
    if "group" in value:
        score -= 0.04
    if "result" in value:
        score += 0.10
    if "handicap" in value:
        score += 0.08
    if "total goals" in value or "over/under" in value:
        score += 0.07
    if "both teams" in value or "draw no bet" in value:
        score += 0.03
    if is_small_market(market):
        score -= 0.18
    return clamp(score, 0.18, 0.95)


def market_depth_score(market: Any, odds: Any) -> float:
    price = to_float(odds)
    if price is None or price <= 1:
        price_component = 0.45
    elif price <= 2.2:
        price_component = 0.78
    elif price <= 4:
        price_component = 0.66
    elif price <= 8:
        price_component = 0.52
    else:
        price_component = 0.38
    if is_small_market(market):
        price_component -= 0.12
    return clamp(price_component, 0.15, 0.9)


def daily_line_move_float_rate(market: Any, price_drift_tolerance: Any, risk_flags: int = 0) -> float:
    tolerance = abs(to_float(price_drift_tolerance) or 0.0)
    base = 0.035 if not is_small_market(market) else 0.065
    risk_add = min(0.045, max(0, risk_flags) * 0.009)
    return clamp(base + min(0.18, tolerance * 0.42) + risk_add, 0.015, 0.28)


def market_base_pool_aud(board: Any, market: Any) -> float:
    value = f"{board} {market}".lower()
    base = 18000.0
    if "matches" in value:
        base = 36000.0
    elif "futures" in value:
        base = 28000.0
    elif "group" in value:
        base = 15000.0
    if "result" in value:
        base *= 1.18
    elif "handicap" in value:
        base *= 1.12
    elif "total goals" in value or "over/under" in value:
        base *= 1.08
    if is_small_market(market):
        base *= 0.42
    return round(base, 2)


def market_funding_grade(score: Any) -> str:
    value = to_float(score)
    if value is None:
        return "待校准"
    if value >= 75:
        return "强"
    if value >= 60:
        return "中强"
    if value >= 45:
        return "中性"
    if value >= 30:
        return "偏弱"
    return "弱"


def market_funding_bias_label(score: Any) -> str:
    value = to_float(score)
    if value is None:
        return "待校准"
    if value >= 65:
        return "资金倾向支持"
    if value >= 55:
        return "轻微支持"
    if value >= 45:
        return "资金中性"
    return "资金倾向不支持"


def liquidity_grade(score: Any) -> str:
    value = to_float(score)
    if value is None:
        return "待校准"
    if value >= 0.75:
        return "高"
    if value >= 0.55:
        return "中"
    return "低"


def market_depth_grade(score: Any) -> str:
    value = to_float(score)
    if value is None:
        return "待校准"
    if value >= 0.7:
        return "深"
    if value >= 0.5:
        return "中"
    return "浅"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def market_edge_threshold(market: Any) -> float:
    return SMALL_MARKET_EDGE_THRESHOLD if is_small_market(market) else MAIN_MARKET_EDGE_THRESHOLD


def market_edge_threshold_range(market: Any) -> str:
    return "4%-6%" if is_small_market(market) else "2%-3%"


def is_small_market(market: Any) -> bool:
    value = str(market or "").lower()
    small_terms = [
        "correct score",
        "scorecast",
        "first goalscorer",
        "anytime goalscorer",
        "cards",
        "corners",
        "player",
        "exact",
        "method",
        "minute",
    ]
    return any(term in value for term in small_terms)


def edge_threshold_gap(edge: Any, threshold: Any) -> float | None:
    edge_value = to_float(edge)
    threshold_value = to_float(threshold)
    if edge_value is None or threshold_value is None:
        return None
    return round(edge_value - threshold_value, 4)


def edge_quality_label(edge: Any, threshold: Any) -> str:
    gap = edge_threshold_gap(edge, threshold)
    if gap is None:
        return "待校准"
    if gap >= 0.02:
        return "强通过"
    if gap >= 0:
        return "通过"
    if gap >= -0.01:
        return "接近门槛"
    return "未达门槛"


def risk_of_ruin_grade(value: Any) -> str:
    risk = to_float(value)
    if risk is None:
        return "待校准"
    if risk < 0.02:
        return "低"
    if risk < 0.05:
        return "中"
    if risk < 0.10:
        return "偏高"
    return "高"


def stake_fraction_of_bankroll(stake_aud: Any, bankroll_reference: Any) -> float | None:
    stake = to_float(stake_aud)
    bankroll = to_float(bankroll_reference)
    if stake is None or bankroll is None or bankroll <= 0:
        return None
    return round(max(0.0, stake / bankroll), 4)


def over_half_kelly_ratio(stake_fraction: Any, half_kelly: Any) -> float | None:
    stake_value = to_float(stake_fraction)
    kelly_value = to_float(half_kelly)
    if stake_value is None or kelly_value is None or kelly_value <= 0:
        return None
    return round(stake_value / kelly_value, 4)


def risk_drivers(
    *,
    edge: Any,
    edge_threshold_gap: Any,
    risk_of_ruin: Any,
    stake_fraction: Any,
    half_kelly_ratio: Any,
    risk_flags: int,
) -> list[str]:
    drivers: list[str] = []
    gap = to_float(edge_threshold_gap)
    if gap is not None and gap < 0:
        drivers.append("Edge未达门槛")
    edge_value = to_float(edge)
    if edge_value is not None and edge_value < 0:
        drivers.append("模型概率低于盈亏平衡")
    stake_value = to_float(stake_fraction)
    if stake_value is not None and stake_value > SINGLE_BET_CAP_FRACTION:
        drivers.append("单注超过2%资金上限")
    ratio = to_float(half_kelly_ratio)
    if ratio is not None and ratio > 1:
        drivers.append("仓位超过半Kelly")
    risk = to_float(risk_of_ruin)
    if risk is not None and risk >= 0.05:
        drivers.append("RoR偏高")
    if risk_flags > 0:
        drivers.append(f"赛前事件风险{risk_flags}项")
    return drivers[:4]


def stake_discipline_status(stake_fraction: Any, half_kelly_ratio: Any) -> str:
    stake_value = to_float(stake_fraction)
    ratio = to_float(half_kelly_ratio)
    if stake_value is None:
        return "待校准"
    if stake_value > SINGLE_BET_CAP_FRACTION:
        return "超过2%上限"
    if ratio is not None and ratio > 1:
        return "超过半Kelly"
    if stake_value <= 0:
        return "观察"
    return "通过"


def ror_review_status(risk_of_ruin: Any) -> str:
    risk = to_float(risk_of_ruin)
    if risk is None:
        return "待校准"
    if risk >= ROR_REVIEW_THRESHOLD:
        return "需复核/降仓"
    return "通过"


def decision_diagnostics(
    *,
    probability: Any,
    odds: Any,
    edge: Any,
    edge_threshold: Any,
    edge_threshold_gap: Any,
    expected_value: Any,
    stake_aud: Any,
    expected_profit: Any,
    expected_profit_100: Any,
    min_acceptable_odds: Any,
    current_odds_buffer: Any,
    price_tolerance: Any,
    risk_of_ruin: Any,
    risk_grade: str,
    stake_fraction: Any,
    half_kelly_ratio: Any,
    stake_cap_ratio: Any,
    kelly_margin: Any,
    value_score: Any,
    value_signal: str,
    risk_drivers: list[str],
) -> dict[str, Any]:
    edge_gap = to_float(edge_threshold_gap)
    ev = to_float(expected_value)
    ror_status = ror_review_status(risk_of_ruin)
    stake_status = stake_discipline_status(stake_fraction, half_kelly_ratio)
    odds_margin = to_float(current_odds_buffer)
    pass_edge = edge_gap is not None and edge_gap >= 0
    pass_odds = odds_margin is None or odds_margin >= 0
    pass_risk = ror_status == "通过"
    pass_stake = stake_status in {"通过", "观察"}
    if ev is not None and ev > 0 and pass_edge and pass_odds and pass_risk and pass_stake:
        conclusion = "研究买入候选"
    elif ev is not None and ev > 0 and pass_edge:
        conclusion = "正EV但需复核"
    else:
        conclusion = "观察或放弃"
    return {
        "model_probability": to_float(probability),
        "current_odds": to_float(odds),
        "minimum_acceptable_odds": to_float(min_acceptable_odds),
        "odds_buffer": odds_margin,
        "price_drift_tolerance_pct": to_float(price_tolerance),
        "edge": to_float(edge),
        "edge_threshold": to_float(edge_threshold),
        "edge_threshold_gap": edge_gap,
        "expected_value": ev,
        "expected_profit_aud": to_float(expected_profit),
        "expected_profit_per_100_aud": to_float(expected_profit_100),
        "stake_aud": to_float(stake_aud),
        "stake_fraction": to_float(stake_fraction),
        "half_kelly_ratio": to_float(half_kelly_ratio),
        "stake_to_cap_ratio": to_float(stake_cap_ratio),
        "kelly_safety_margin": to_float(kelly_margin),
        "risk_of_ruin": to_float(risk_of_ruin),
        "risk_of_ruin_grade": risk_grade,
        "risk_adjusted_value_score": to_float(value_score),
        "value_signal": value_signal,
        "ror_review_threshold": ROR_REVIEW_THRESHOLD,
        "stake_discipline_status": stake_status,
        "ror_status": ror_status,
        "risk_drivers": risk_drivers,
        "conclusion": conclusion,
        "decision_sentence": (
            f"{value_signal} / {conclusion}：赔率需不低于 {decimal(min_acceptable_odds)}，"
            f"当前缓冲 {decimal_signed(current_odds_buffer)}，价格容忍度 {pct(price_tolerance)}；"
            f"每 AUD100 预期 {money(expected_profit_100)}，"
            f"RoR {pct(risk_of_ruin)}（{risk_grade or risk_of_ruin_grade(risk_of_ruin)}），"
            f"仓位上限占用 {pct(stake_cap_ratio)}。"
        ),
    }


def decision_metric_pack(
    *,
    probability: Any,
    breakeven: Any,
    edge: Any,
    edge_threshold: Any,
    edge_threshold_gap: Any,
    arbitrage_rate: Any,
    expected_value: Any,
    risk_of_ruin: Any,
    risk_grade: str,
    diagnostic: dict[str, Any],
    risk_drivers: list[str],
) -> dict[str, Any]:
    gap = to_float(edge_threshold_gap)
    arb = to_float(arbitrage_rate)
    risk = to_float(risk_of_ruin)
    edge_grade = edge_quality_label(edge, edge_threshold)
    ror_status = str(diagnostic.get("ror_status") or ror_review_status(risk_of_ruin))
    conclusion = str(diagnostic.get("conclusion") or "待校准")
    value_signal = str(diagnostic.get("value_signal") or "待校准")

    if gap is None:
        edge_use = "Edge缺少可用概率或赔率，不能作为买入依据。"
    elif gap >= 0:
        edge_use = (
            f"Edge {pp(edge)} 已高于本盘口门槛 {pp(edge_threshold)}，"
            f"门槛差 {pp(gap)}，可进入价值候选。"
        )
    else:
        edge_use = (
            f"Edge {pp(edge)} 未达到本盘口门槛 {pp(edge_threshold)}，"
            f"门槛差 {pp(gap)}，应降级观察或放弃。"
        )

    if arb is None:
        arbitrage_use = "套利率缺少EV输入，暂不能比较价值率。"
    elif arb > 0:
        arbitrage_use = (
            f"价值套利率 {pct(arb)} 为正，每 AUD100 预期 {money(diagnostic.get('expected_profit_per_100_aud'))}；"
            "这是模型价值率，不是跨平台无风险套利。"
        )
    else:
        arbitrage_use = "价值套利率不为正，赔率相对模型概率没有可执行价值。"

    if risk is None:
        ror_use = "Risk of ruin 缺少资金或概率输入，执行前必须重新校准。"
    elif risk >= ROR_REVIEW_THRESHOLD:
        ror_use = (
            f"Risk of ruin {pct(risk)}（{risk_grade or risk_of_ruin_grade(risk)}）达到复核线，"
            "需降仓、等待更好价格或放弃。"
        )
    else:
        ror_use = (
            f"Risk of ruin {pct(risk)}（{risk_grade or risk_of_ruin_grade(risk)}）低于复核线，"
            "风险层面允许继续赛前复核。"
        )
    if risk_drivers:
        ror_use += f" 风险触发：{'；'.join(str(item) for item in risk_drivers)}。"

    return {
        "edge": {
            "model_probability": to_float(probability),
            "breakeven_probability": to_float(breakeven),
            "edge": to_float(edge),
            "threshold": to_float(edge_threshold),
            "threshold_gap": gap,
            "quality": edge_grade,
            "decision_use": edge_use,
        },
        "arbitrage_rate": {
            "value": arb,
            "expected_value": to_float(expected_value),
            "expected_profit_per_100_aud": to_float(diagnostic.get("expected_profit_per_100_aud")),
            "type": "value_arbitrage_not_surebet",
            "decision_use": arbitrage_use,
        },
        "risk_of_ruin": {
            "value": risk,
            "grade": risk_grade or risk_of_ruin_grade(risk),
            "review_status": ror_status,
            "drivers": risk_drivers,
            "decision_use": ror_use,
        },
        "combined_signal": value_signal,
        "combined_action": (
            f"{value_signal} / {conclusion}；执行前仍需确认实时赔率、首发/伤停和 raw/private 门禁。"
        ),
        "manual_use_only": "只用于研究排序和人工复核，不自动下注、不点击赔率、不添加投注单。",
    }


def row_analysis_basis(
    *,
    row: sqlite3.Row,
    raw: dict[str, Any],
    breakeven: float | None,
    edge: Any,
    edge_threshold: Any,
    edge_threshold_gap: Any,
    arbitrage_rate: Any,
    risk_of_ruin: Any,
    risk_grade: str,
    risk_drivers: list[str],
    diagnostic: dict[str, Any],
    bankroll_reference: float,
    model_calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signal = raw.get("model_signal") or {}
    event_risk = raw.get("event_risk") or {}
    calibration = model_calibration or {}
    confidence = calibration.get("confidence_zh") or confidence_label(raw)
    consistency = calibration.get("consistency_label") or consistency_label(raw)
    edge_gap = to_float(edge_threshold_gap)
    ev = to_float(row["expected_value"])
    odds_margin = to_float(diagnostic.get("odds_buffer"))
    ror_status = str(diagnostic.get("ror_status") or "待校准")
    stake_status = str(diagnostic.get("stake_discipline_status") or "待校准")
    pass_value = bool(ev is not None and ev > 0 and edge_gap is not None and edge_gap >= 0)
    pass_price = odds_margin is None or odds_margin >= 0
    pass_risk = ror_status == "通过"
    if pass_value and pass_price and pass_risk and confidence == "高":
        evidence_strength = "强"
    elif pass_value and pass_price and pass_risk:
        evidence_strength = "中"
    elif ev is not None and ev > 0:
        evidence_strength = "观察"
    else:
        evidence_strength = "弱"

    probability_basis = [
        f"模型概率 {pct(row['probability'])} vs 盈亏平衡 {pct(breakeven)}，Edge {pp(edge)}。",
        f"Edge门槛 {pp(edge_threshold)}，门槛差 {pp(edge_threshold_gap)}，纪律等级 {edge_quality_label(edge, edge_threshold)}。",
        f"EV {pct(row['expected_value'])}，价值套利率 {pct(arbitrage_rate)}，每AUD100预期 {money(diagnostic.get('expected_profit_per_100_aud'))}。",
    ]
    price_basis = [
        f"TAB当前赔率 {decimal(row['odds'])}，最低可接受赔率 {decimal(diagnostic.get('minimum_acceptable_odds'))}。",
        f"赔率缓冲 {decimal_signed(diagnostic.get('odds_buffer'))}，价格容忍度 {pct(diagnostic.get('price_drift_tolerance_pct'))}。",
        "若赛前 TAB 实时赔率低于最低可接受赔率，本行从买入候选降级为观察或放弃。",
    ]
    risk_basis = [
        f"研究金额 {money(row['stake_aud'])}，参考资金池 {money(bankroll_reference)}，仓位 {pct(diagnostic.get('stake_fraction'))}。",
        f"半Kelly偏离 {pct(diagnostic.get('half_kelly_ratio'))}，Kelly安全垫 {pct(diagnostic.get('kelly_safety_margin'))}，单注上限占用 {pct(diagnostic.get('stake_to_cap_ratio'))}。",
        f"Risk of ruin {pct(risk_of_ruin)}（{risk_grade or risk_of_ruin_grade(risk_of_ruin)}），RoR复核状态 {ror_status}。",
    ]
    if risk_drivers:
        risk_basis.append(f"风险触发因素：{'；'.join(str(item) for item in risk_drivers)}。")
    else:
        risk_basis.append("未识别额外赛前事件风险，但仍需执行前复核。")

    source_basis = [
        "FACT：最新 SQLite recommendations 记录提供板块、盘口、下注、赔率、模型概率、EV、研究金额。",
        "INFERENCE：Edge、套利率、最低可接受赔率、Kelly、Risk of ruin 和风险调整价值分由本地公式计算。",
        "TEMPLATE：ChatGPT Excel 参考模板用于赛前10分钟清单、赔率去水、Edge门槛、半Kelly、单注上限、下注日志和 CLV/ROI 复盘。",
        "OPEN-SOURCE：penaltyblog、goalmodel、socceraction、openfootball 等公开模型/赛程思路提供交叉校验框架。",
    ]
    if signal:
        source_basis.append(
            "MODEL：模型信号 "
            f"confidence={signal.get('consensus_confidence', 'unknown')}，"
            f"aligned={signal.get('selection_aligned_with_consensus', 'unknown')}，"
            f"divergence={signal.get('high_divergence', 'unknown')}。"
        )
    if model_calibration:
        source_basis.append(
            "MODEL-CALIBRATION："
            f"{model_calibration.get('evidence_text', '模型校准待生成')}；"
            f"复核动作={model_calibration.get('review_action', '待复核')}。"
        )

    data_gaps: list[str] = []
    if confidence != "高":
        data_gaps.append(f"模型共识置信度为{confidence}，需要赛前信息或其他模型进一步确认。")
    if consistency != "三模型一致":
        data_gaps.append(f"分析一致性为{consistency}，不能只靠单一模型结论。")
    if event_risk.get("flag_count"):
        data_gaps.append("存在赛前事件风险标记，需复核伤停、首发、新闻和动机。")
    if odds_margin is not None and odds_margin < 0:
        data_gaps.append("当前赔率低于最低可接受赔率，价格已经走差。")
    if edge_gap is not None and edge_gap < 0:
        data_gaps.append("Edge未达到对应盘口门槛。")
    if ror_status != "通过":
        data_gaps.append("Risk of ruin 达到复核线，需降仓或延后。")
    if stake_status not in {"通过", "观察"}:
        data_gaps.append("仓位纪律未通过，需降仓或放弃。")
    if model_calibration:
        if model_calibration.get("review_priority") == "高":
            data_gaps.append(f"模型校准为高优先级复核：{model_calibration.get('consistency_label')}。")
        elif model_calibration.get("status") != "model_linked":
            data_gaps.append("模型校准未关联到当前比赛，不能提高分析一致性。")
    if not data_gaps:
        data_gaps.append("无重大结构性缺口；执行前仍需确认实时赔率、首发和持仓快照。")

    pre_bet_checklist = [
        f"TAB 实时赔率必须 >= {decimal(diagnostic.get('minimum_acceptable_odds'))}。",
        f"模型校准动作：{(model_calibration or {}).get('review_action', '确认模型对比已刷新')}。",
        "赛前10分钟确认首发、伤停、动机、赛程疲劳、战术匹配和大小球节奏。",
        "单注不超过 2% bankroll，且不超过半Kelly纪律线。",
        "确认 raw/public safety/private position 门禁通过；未通过时新增执行金额保持 AUD 0。",
        "下注后记录入场赔率、收盘赔率、结果、Profit、ROI、CLV% 和实际 Edge。",
    ]

    return {
        "summary": (
            f"{row['selection']}：{diagnostic.get('value_signal', '待校准')}，"
            f"{diagnostic.get('conclusion', '待校准')}；Edge {pp(edge)}，"
            f"套利率 {pct(arbitrage_rate)}，Risk of ruin {pct(risk_of_ruin)}。"
        ),
        "evidence_strength": evidence_strength,
        "probability_value_basis": probability_basis,
        "price_execution_basis": price_basis,
        "risk_control_basis": risk_basis,
        "source_basis": source_basis,
        "data_gaps": data_gaps,
        "pre_bet_checklist": pre_bet_checklist,
        "decision_use": "用于研究排序、金额复核和赛前检查；不作为自动下注授权。",
    }


def full_kelly_fraction(probability: Any, odds: Any) -> float | None:
    prob = to_float(probability)
    price = to_float(odds)
    if prob is None or price is None or price <= 1:
        return None
    fraction = prob - (1 - prob) / (price - 1)
    return round(max(0.0, fraction), 4)


def discounted_kelly_fraction(probability: Any, odds: Any, discount: float = KELLY_DISCOUNT) -> float | None:
    kelly = full_kelly_fraction(probability, odds)
    if kelly is None:
        return None
    return round(kelly * discount, 4)


def risk_of_ruin_estimate(
    probability: Any,
    odds: Any,
    stake_aud: Any,
    bankroll_reference: float = DEFAULT_BANKROLL_REFERENCE_AUD,
    *,
    risk_flags: int = 0,
) -> float | None:
    prob = to_float(probability)
    price = to_float(odds)
    stake = to_float(stake_aud) or 0.0
    bankroll = float(bankroll_reference or DEFAULT_BANKROLL_REFERENCE_AUD)
    if prob is None or price is None or price <= 1 or bankroll <= 0:
        return None
    if stake <= 0:
        return 0.0
    prob = max(0.0, min(1.0, prob))
    stake_fraction = min(1.0, max(0.0, stake / bankroll))
    ev = prob * price - 1
    loss_probability = max(0.0, 1 - prob)
    half_kelly = discounted_kelly_fraction(prob, price) or 0.0
    risk = 0.01 + min(0.2, loss_probability * stake_fraction * 1.5)
    if ev <= 0:
        risk += 0.12 + min(0.35, loss_probability * stake_fraction * 4)
    else:
        overbet_ratio = stake_fraction / max(half_kelly, 0.002)
        if overbet_ratio > 1:
            risk += min(0.4, (overbet_ratio - 1) * 0.08)
        elif overbet_ratio < 0.5:
            risk *= 0.5
    risk += min(0.06, max(0, risk_flags) * 0.015)
    return round(max(0.0, min(0.95, risk)), 4)


def board_stake(rows: list[dict[str, Any]], board: str) -> float:
    return sum(float(row.get("stake_aud") or 0) for row in rows if row.get("board") == board)


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not Path(path).exists():
            return {}
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def parse_json(value: Any) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def snapshot_id(generated_at: str) -> str:
    return "recommendation-operations-" + generated_at.replace(":", "").replace("+", "-").replace(".", "-")


def row_key(board: Any, event: Any, market: Any, selection: Any) -> str:
    return "|".join(str(item or "").strip() for item in [board, event, market, selection])


def money(value: Any) -> str:
    try:
        return f"AUD {float(value):,.0f}"
    except (TypeError, ValueError):
        return "AUD 0"


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "待校准"


def pp(value: Any) -> str:
    try:
        return f"{float(value) * 100:+.2f}pp"
    except (TypeError, ValueError):
        return "待校准"


def decimal(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "待校准"


def decimal_signed(value: Any) -> str:
    try:
        return f"{float(value):+.2f}"
    except (TypeError, ValueError):
        return "待校准"


def md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
