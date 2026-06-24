#!/usr/bin/env python3
"""Generate Review 8 governance views from canonical machine sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_project_governance as structural


sys.dont_write_bytecode = True

ROOT = structural.ROOT
GENERATOR_VERSION = "4.0.0"
COMPLETED_TASK_STATES = {"completed", "rejected", "deprecated"}
EXECUTABLE_TASK_STATES = {"ready", "in_progress", "blocked", "planned"}
ASSURANCE_STATUSES = {"VERIFIED", "PARTIAL", "UNVERIFIED", "FAILED", "NOT_APPLICABLE"}
PROJECT_REPOSITORIES = {
    "Alpha": "https://github.com/LinzeColin/Alpha",
    "EEI": "https://github.com/LinzeColin/CodexProject/tree/main/EEI",
    "EVA_OS": "https://github.com/LinzeColin/EVA_OS",
    "FIFA": "https://github.com/LinzeColin/FIFA",
    "OpMe_System": "https://github.com/LinzeColin/OpMe_System",
    "OpenAIDatabase": "https://github.com/LinzeColin/CodexProject/tree/main/OpenAIDatabase",
    "PFI_BIG_DATA_SIMULATOR": "https://github.com/LinzeColin/CodexProject/tree/main/PFI/%E5%A4%A7%E6%95%B0%E6%8D%AE%E6%A8%A1%E6%8B%9F%E5%99%A8",
    "Serenity-Alipay": "https://github.com/LinzeColin/Serenity-Alipay",
    "whkmSalary": "https://github.com/LinzeColin/whkmSalary",
    "arxiv-daily-push": "https://github.com/LinzeColin/CodexProject/tree/main/arxiv-daily-push",
}


ASSURANCE_POLICY = {
    "Alpha": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否提供生产数据、paper broker 与 live execution policy 证据，或继续保持 blocked。",
        "blockers": ["production validation evidence", "broker policy decision", "calibration evidence"],
    },
    "EEI": {
        "empirical": "partial",
        "operational": "partial",
        "readiness": "blocked",
        "decision": "是否继续 24 小时 operator soak；当前 4 小时证据只支持 partial。",
        "blockers": ["24h operator soak evidence", "historical event binding backlog"],
    },
    "EVA_OS": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否投入 137 个 remaining parameter reviews 和来源/校准证据。",
        "blockers": ["parameter review backlog", "source and calibration evidence"],
    },
    "FIFA": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否关闭 17 个 parser/validation 参数人工复核。",
        "blockers": ["17 active parameters need semantic review", "TAB production evidence not claimed"],
    },
    "OpMe_System": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否补齐 calibration、prompt/provider policy 与 owner sign-off 证据。",
        "blockers": ["calibration evidence", "prompt/provider policy", "owner sign-off"],
    },
    "OpenAIDatabase": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否继续补齐 memory routing 分支和 FORM-010 语义复核。",
        "blockers": ["remaining semantic review", "calibration/source evidence"],
    },
    "PFI_BIG_DATA_SIMULATOR": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "conditional",
        "decision": "是否关闭 PARAM-110/PARAM-111 或保留 human review required。",
        "blockers": ["two implementation parameters need review", "calibration evidence"],
    },
    "Serenity-Alipay": {
        "empirical": "unknown",
        "operational": "partial",
        "readiness": "conditional",
        "decision": "是否启动 empirical calibration evidence task；实现一致性已经 machine verified。",
        "blockers": ["empirical calibration unknown", "owner evidence decision"],
    },
    "whkmSalary": {
        "empirical": "unknown",
        "operational": "blocked",
        "readiness": "blocked",
        "decision": "是否提供一手政策、法域、生效日期、计税基础和舍入证据。",
        "blockers": ["policy source evidence", "jurisdiction/effective date evidence"],
    },
    "arxiv-daily-push": {
        "empirical": "partial",
        "operational": "partial",
        "readiness": "blocked",
        "decision": "是否启动生产 trial；当前只有本地两日模拟，生产启动和 30 天验收仍 blocked。",
        "blockers": ["production trial not started", "30-day acceptance absent", "historical event binding backlog"],
    },
}


REVIEW8_DECISION_POLICY = {
    "Alpha": {
        "owner_role": "model_owner + risk_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否投入资源用真实历史行情、交易成本和样本外窗口验证 Alpha 动量筛选、风险评分和交易前门禁是否优于简单基线，同时保持零实盘执行。",
        "recommendation": "A: fund historical-data validation before any stronger delivery claim",
        "option_a": "投入真实历史数据、walk-forward、成本/滑点和买入持有基线验证。",
        "option_b": "保持研究/模拟用途，所有生产和实盘相关声明继续 blocked。",
        "option_c": "暂停 Alpha 交付声称，只保留代码与治理同步。",
        "effort": "P1; model_owner + risk_owner review plus data preparation",
        "resource": "historical market data, cost/slippage assumptions, review time",
        "benefit": "判断当前信号和风险门禁是否有样本外价值，而不把实现一致性误认为有效性。",
        "risks": "future leakage, overfitting, data/vendor limits, transaction-cost understatement",
        "evidence": "versioned market snapshot, baseline metrics, OOS report, sensitivity table",
        "priority": "P1",
        "no_decision": "Alpha remains FAILED for operational/delivery readiness and cannot support production claims.",
    },
    "EEI": {
        "owner_role": "product_owner + data_owner + risk_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否继续投入 24 小时 operator soak 和人工黄金集，验证 EEI 实体解析、关系抽取、证据覆盖与撤回能力。",
        "recommendation": "A: complete 24h soak and gold-set validation before publishing stronger claims",
        "option_a": "补齐人工裁决黄金集、24h soak、来源撤回和冲突演练。",
        "option_b": "保持 partial，仅允许内部研究和人工复核。",
        "option_c": "暂停关系发布相关交付声明。",
        "effort": "P2; product/data/risk owners plus operator time",
        "resource": "official-source access, labeled gold set, soak runner time",
        "benefit": "降低未经证实企业关系被发布为事实的风险。",
        "risks": "source license limits, stale relationships, false relation assertions",
        "evidence": "gold-set labels, precision/recall, source coverage, soak manifest",
        "priority": "P2",
        "no_decision": "EEI remains FAILED/PARTIAL and publication readiness stays blocked.",
    },
    "EVA_OS": {
        "owner_role": "model_owner + research_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否投入参数来源、样本外、成本和报告 claim-to-evidence 验证，证明 EVA_OS 研究结论可复现且不夸大。",
        "recommendation": "A: fund parameter review and OOS evidence hardening",
        "option_a": "完成剩余参数来源、OOS、成本压力和报告主张抽检。",
        "option_b": "保持研究假设，不提升 readiness。",
        "option_c": "暂停对外报告交付声明。",
        "effort": "P1; research/model owner review",
        "resource": "historical data, experiment logs, report evidence manifest",
        "benefit": "把实验实现与真实可复现证据分开，避免选择性报告。",
        "risks": "parameter instability, cost omissions, cherry-picked reports",
        "evidence": "OOS protocol, rerun logs, claim ledger, sensitivity results",
        "priority": "P1",
        "no_decision": "EVA_OS remains FAILED for operational and delivery readiness.",
    },
    "FIFA": {
        "owner_role": "research_owner + risk_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否补齐授权赛前赔率快照、概率校准和报告事实复核，且继续保证 stake/executable amount 为 0。",
        "recommendation": "A: validate historical odds snapshots under zero-stake boundary",
        "option_a": "建立赛前快照数据合同、Brier/log loss/ECE 校准和事实抽检。",
        "option_b": "维持研究用途，不声称预测有效。",
        "option_c": "暂停 FIFA 概率/价值报告交付。",
        "effort": "P1; research and risk review",
        "resource": "authorized odds snapshots, match results, report audit samples",
        "benefit": "判断概率和报告是否比市场/简单基线更有用，同时避免下注风险。",
        "risks": "post-event leakage, unauthorized data, betting misuse",
        "evidence": "timestamped odds data, calibration report, zero-stake gate evidence",
        "priority": "P1",
        "no_decision": "FIFA remains UNVERIFIED and cannot support value/recommendation claims.",
    },
    "OpMe_System": {
        "owner_role": "engineering_owner + safety_owner + operations_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否由工程/安全/运营责任人投入专家裁决案例，验证 OpMe 诊断、严重度、LLM 路由和危险漏报失效安全。",
        "recommendation": "A: fund expert-labeled safety validation before operational use",
        "option_a": "完成专家双评、危险漏报专项集、回退演练和报告可执行性复核。",
        "option_b": "保持内部辅助研究，所有现场/生产建议需工程师复核。",
        "option_c": "暂停高风险诊断和操作建议交付。",
        "effort": "P0; engineering, safety, operations owners required",
        "resource": "de-identified industrial cases, expert adjudication, safety review time",
        "benefit": "降低危险故障漏报和无依据操作建议风险。",
        "risks": "unsafe advice, missing expert labels, provider outage,现场适用性不足",
        "evidence": "expert labels, severity-weighted errors, dangerous false-negative rate, fallback logs",
        "priority": "P0",
        "no_decision": "OpMe_System remains UNVERIFIED and must not be treated as production safety tooling.",
    },
    "OpenAIDatabase": {
        "owner_role": "privacy_owner + product_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否投入去标识黄金集和隐私攻击测试，验证记忆提取、脱敏、冲突/去重、检索和建议效用不会泄漏高风险秘密。",
        "recommendation": "A: fund privacy-first gold-set validation before persistent memory write claims",
        "option_a": "建立同意样本/高保真合成集、秘密泄漏测试、检索和建议盲评。",
        "option_b": "保留本地只读研究，写入前继续人工确认。",
        "option_c": "暂停持久记忆和自动建议交付。",
        "effort": "P0; privacy and product owner review",
        "resource": "consented/de-identified exports, adversarial secret set, evaluator time",
        "benefit": "验证系统有用且不会把私密内容错误持久化或泄漏。",
        "risks": "PII/secret leakage, stale memory, false user facts",
        "evidence": "gold labels, leakage-rate report, retrieval metrics, human write approval logs",
        "priority": "P0",
        "no_decision": "OpenAIDatabase remains FAILED for delivery readiness and cannot claim safe memory operation.",
    },
    "PFI_BIG_DATA_SIMULATOR": {
        "owner_role": "model_owner + risk_owner + research_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否投入多市场、OOS、成本和多重检验控制，验证 PFI 策略族不是数据挖掘赢家。",
        "recommendation": "A: validate OOS and multiple-testing controls before ranking strategy claims",
        "option_a": "执行预注册、walk-forward、FDR/Reality Check、快筛-精确一致性和成本压力。",
        "option_b": "保持模拟研究，不提升策略有效性状态。",
        "option_c": "暂停策略族交付声称。",
        "effort": "P1; model/risk/research owner review",
        "resource": "multi-market snapshots, compute time, multiple-testing protocol",
        "benefit": "区分真实稳健表现与大规模搜索偏差。",
        "risks": "data mining, survivor bias, underestimated costs, resource blowups",
        "evidence": "pre-registration, OOS metrics, corrected significance, sensitivity results",
        "priority": "P1",
        "no_decision": "PFI remains UNVERIFIED and cannot support strategy approval.",
    },
    "Serenity-Alipay": {
        "owner_role": "model_owner + risk_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否投入历史基金快照、基准、OOS、消融和敏感性，验证评分权重、等级阈值、硬门禁和 Top5 衰减是否有稳定区分力。",
        "recommendation": "A: fund empirical calibration and OOS validation; implementation is already machine-verified",
        "option_a": "补齐基金快照、基准、OOS、消融和参数敏感性证据。",
        "option_b": "保持规则实现已核对，不宣称策略有效。",
        "option_c": "暂停基金评分交付声明。",
        "effort": "P1; model/risk owner plus data preparation",
        "resource": "historical fund snapshots, benchmark series, calibration protocol",
        "benefit": "判断当前权重/阈值/门禁是否有风险控制和排序价值。",
        "risks": "survivorship bias, overfitting, stale fund availability, investment misuse",
        "evidence": "versioned snapshots, OOS metrics, ablation, sensitivity and gate-value report",
        "priority": "P1",
        "no_decision": "Serenity remains UNVERIFIED for empirical/delivery readiness despite machine-verified implementation.",
    },
    "whkmSalary": {
        "owner_role": "payroll_owner + legal_or_policy_owner + product_owner",
        "assignment": "HUMAN_ASSIGNMENT_REQUIRED",
        "question": "是否由工资、法务/政策和产品责任人提供权威政策、法域、生效日期、税务和舍入证据，验证 whkmSalary 可用于真实算薪。",
        "recommendation": "A: fund policy and payroll reconciliation evidence before any production payroll use",
        "option_a": "补齐政策来源、司法辖区、生效日期、税务、舍入和匿名历史对账。",
        "option_b": "保持演示/研究用途，禁止生产算薪。",
        "option_c": "暂停工资计算交付声明。",
        "effort": "P0; payroll + legal/policy + product owner sign-off",
        "resource": "authoritative policy docs, approved payroll examples, reviewer time",
        "benefit": "避免把未经授权或过期规则用于工资、税费和绩效结算。",
        "risks": "legal error, payroll under/overpayment, PII leakage, unfair impact",
        "evidence": "policy refs, jurisdiction/effective-date matrix, reconciliation results, approval memo",
        "priority": "P0",
        "no_decision": "whkmSalary remains FAILED and must not be used for production payroll.",
    },
    "arxiv-daily-push": {
        "decision_id": "DEC-arxiv-daily-push-V5-S1-001",
        "review_id": "REVIEW8",
        "owner_role": "content_owner + product_owner",
        "assignment": "CODEX_CAN_CONTINUE_WITH_V5_CONTRACT",
        "question": "是否继续执行 S1-07，生成 B1/arXiv 的高信息密度中文讲解教学邮件，而不是启动生产 trial。",
        "recommendation": "A: implement S1-07 B1/arXiv text teaching email before any production enablement",
        "option_a": "继续 S1-07，完成 B1/arXiv 中文讲解报告、邮件文本/HTML 和审计工件。",
        "option_b": "暂停在 S1-06，等待人工重审文本讲解标准。",
        "option_c": "恢复旧 Phase 12 media path；不推荐，且会偏离 V5 Stage 1。",
        "effort": "P1; content and product implementation",
        "resource": "local tests only; no real SMTP, no Release upload, no video generation",
        "benefit": "把 arXiv 输出从日报摘要提升为可长期运行的讲解教学邮件。",
        "risks": "shallow digest quality, unsupported claims, old media path leakage, premature production enablement",
        "evidence": "B1 report artifact, email preview, claim evidence, focused tests, governance records",
        "priority": "P1",
        "no_decision": "arxiv-daily-push remains at S1-06 and cannot reach ARXIV_PRODUCTION_ACCEPTED.",
    },
}


def decision_policy_for(project_id: str, next_task: dict[str, Any]) -> dict[str, Any]:
    policy = dict(REVIEW8_DECISION_POLICY.get(project_id, {}))
    task_id = str(next_task.get("task_id") or "")
    if project_id == "arxiv-daily-push" and task_id == "S1-08-LOCAL_RUNTIME_RECOVERY-001":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-V5-S1-002",
                "review_id": "REVIEW8",
                "owner_role": "engineering_owner + operations_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V5_CONTRACT",
                "question": "是否继续执行 S1-08，补齐本地 tick、watchdog、backup、restore、runtime audit 和 scheduler install/uninstall 恢复控制。",
                "recommendation": "A: implement S1-08 local runtime recovery controls before migration packaging",
                "option_a": "继续 S1-08，完成本地运行、恢复、备份和调度控制的低资源代码与证据。",
                "option_b": "暂停在 S1-07，只保留 B1 报告/邮件预览，不进入本地运行恢复门禁。",
                "option_c": "跳过 S1-08 直接迁移；不推荐，因为会缺少恢复和调度证据。",
                "effort": "P1; local runtime and operations implementation",
                "resource": "local tests only; no production schedule install, no real SMTP, no large replay",
                "benefit": "让 arXiv Stage 1 从文本预览能力推进到可恢复、可审计、可迁移的本地运行骨架。",
                "risks": "scheduler side effects, stale heartbeat, unsafe restore, secret leakage, oversized artifacts",
                "evidence": "tick/watchdog reports, backup/restore fixtures, scheduler dry-run evidence, focused tests, governance records",
                "priority": "P1",
                "no_decision": "arxiv-daily-push remains at S1-07 and cannot reach ARXIV_PRODUCTION_ACCEPTED.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "S1-09-MIGRATION_PACKAGE-001":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-V5-S1-003",
                "review_id": "REVIEW8",
                "owner_role": "engineering_owner + operations_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V5_CONTRACT",
                "question": "是否继续执行 S1-09，产出新机器迁移包、低资源运行证据和长期运行交接清单。",
                "recommendation": "A: implement S1-09 migration package before historical previews and live-day evidence",
                "option_a": "继续 S1-09，完成新机器迁移清单、低资源 smoke 证据、恢复路径和运行交接材料。",
                "option_b": "暂停在 S1-08，只保留本地运行恢复控制，不进入迁移准备。",
                "option_c": "跳过迁移包直接跑历史预览；不推荐，因为长期稳定运行和换机恢复证据不足。",
                "effort": "P1; migration and operations documentation",
                "resource": "local fixture tests and migration checklist only; no production schedule install, no real SMTP, no large replay",
                "benefit": "把 arXiv Stage 1 从可恢复本地骨架推进到可迁移、可交接、可长期运行的低资源操作包。",
                "risks": "migration checklist gaps, hidden local-state dependency, resource pressure, premature production enablement",
                "evidence": "migration package, low-resource smoke evidence, restore checklist, focused tests, governance records",
                "priority": "P1",
                "no_decision": "arxiv-daily-push remains at S1-08 and cannot reach ARXIV_PRODUCTION_ACCEPTED.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "S1-10-POST_MIGRATION_BOOTSTRAP-001":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-V5-S1-004",
                "review_id": "REVIEW8",
                "owner_role": "engineering_owner + operations_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V5_CONTRACT",
                "question": "是否继续执行 S1-10，在迁移后目标环境验证 runtime 边界，再进入历史预览和 live-day 证据。",
                "recommendation": "A: run post-migration bootstrap before historical previews and live-day evidence",
                "option_a": "继续 S1-10，验证新机器或云 runner 的 Python、Git、SSL、SQLite、runtime smoke、secret-name 和 no-production-side-effect 边界。",
                "option_b": "暂停在 S1-09，只保留迁移包，不执行目标环境 bootstrap。",
                "option_c": "跳过 bootstrap 直接做历史预览；不推荐，因为运行环境可能仍是本机或缺少可恢复证据。",
                "effort": "P1; target runtime bootstrap and evidence collection",
                "resource": "target runner smoke tests only; no production schedule install, no real SMTP, no Release upload, no large replay",
                "benefit": "确认 arXiv Stage 1 后续长期运行不依赖当前 Mac 后台，并为重验证与生产验收建立目标环境证据。",
                "risks": "wrong runner boundary, SSL/network failure, hidden local-state dependency, secret leakage, premature production enablement",
                "evidence": "bootstrap report, migration verify report, runtime audit/tick/watchdog smoke, no-secret readiness refs, governance records",
                "priority": "P1",
                "no_decision": "arxiv-daily-push remains at S1-09 and cannot reach ARXIV_PRODUCTION_ACCEPTED.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "S1-11-HISTORICAL_B1_PREVIEWS-001":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-V5-S1-005",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + engineering_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V5_CONTRACT",
                "question": "是否继续执行 S1-11，生成 30 份独立历史 B1/arXiv 报告和邮件预览证据。",
                "recommendation": "A: run S1-11 historical B1 previews before live-day email evidence",
                "option_a": "继续 S1-11，产出 30 份独立历史 B1 报告/邮件预览、Claim evidence 和内容台账证据。",
                "option_b": "暂停在 S1-10，只保留迁移后 bootstrap，不进入历史预览证据。",
                "option_c": "跳过历史预览直接做 live-day delivery；不推荐，因为内容质量和独立样本证据不足。",
                "effort": "P1; historical preview evidence generation",
                "resource": "local fixture/replay artifacts only; no production schedule install, no real SMTP, no Release upload, no video generation",
                "benefit": "在 live-day 发送前证明 B1/arXiv 文本报告和邮件预览能跨 30 个独立历史样本稳定生成。",
                "risks": "fixture overfitting, duplicate historical samples, unsupported claims, stale content ledger, premature production acceptance",
                "evidence": "30 B1 report/email preview artifacts, Claim evidence audit, content ledger rows, focused tests, governance records",
                "priority": "P1",
                "no_decision": "arxiv-daily-push remains at S1-10 and cannot reach ARXIV_PRODUCTION_ACCEPTED.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-V5-S1-006",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + engineering_owner + operations_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V5_CONTRACT",
                "question": "是否继续执行 S1-12，在目标 runner 上收集两个真实自然日的受控 B1/arXiv 邮件发送证据。",
                "recommendation": "A: run S1-12 controlled live B1 email days before production acceptance",
                "option_a": "继续 S1-12，按目标 runner、实时 arXiv 输入、B1 讲解邮件、Gmail SMTP 发送证据和无 secret 泄露记录两天。",
                "option_b": "暂停在 S1-11，只保留 30 份历史预览，不进入真实邮件证据。",
                "option_c": "跳过两天证据直接启用生产定时；不推荐，因为缺少 live-day delivery evidence。",
                "effort": "P1; controlled target-runner live delivery evidence",
                "resource": "GitHub/cloud runner, Gmail SMTP secret names, live arXiv metadata access, durable evidence refs",
                "benefit": "证明 Stage 1 B1/arXiv 每日邮件在真实运行边界能稳定送达，而不是只在离线历史预览中通过。",
                "risks": "SMTP secret readiness, live arXiv availability, target runner drift, accidental scheduler enablement, local Mac fallback",
                "evidence": "two natural-day B1 email delivery refs, target-runner refs, B1 report/email artifacts, no-secret delivery audits, no production scheduler",
                "priority": "P1",
                "no_decision": "arxiv-daily-push remains at S1-11 and cannot reach ARXIV_PRODUCTION_ACCEPTED.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "S1P5T03-R-REAL_ARXIV_30_DAY_BACKFILL_AND_LEDGER_RECONCILE":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-V6-S1P5T03R-001",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + engineering_owner + operations_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V6_CONTRACT",
                "question": "是否继续执行 S1P5T03-R，在 GitHub/cloud runner 上补跑过去 30 个真实 arXiv as-of date 并持久化 CONTENT_LEDGER。",
                "recommendation": "A: complete S1P5T03-R cloud backfill before restoring strict ARXIV_PRODUCTION_ACCEPTED",
                "option_a": "继续 S1P5T03-R，等待 PR CI 生成 30 天真实 backfill artifact 并核对 CONTENT_LEDGER。",
                "option_b": "暂停 strict acceptance，保留本地控制跑和代码但不恢复 production accepted。",
                "option_c": "跳到邮件模板或 Stage 2；不推荐，因为用户已明确要求先补真实 30 天历史数据。",
                "effort": "P0; cloud runner evidence and ledger reconciliation",
                "resource": "GitHub Actions ubuntu-latest, live arXiv Atom API access, compact text artifacts only",
                "benefit": "把一次性实时发送成功与长期候选队列/已讲未讲账本闭环区分开，避免伪 accepted。",
                "risks": "arXiv API throttling, cloud artifact mismatch, CONTENT_LEDGER drift, premature production schedule enablement",
                "evidence": "GitHub Actions run id, artifact id, 30/30 replay report, CONTENT_LEDGER selected/queued/email/artifact rows",
                "priority": "P0",
                "no_decision": "Strict Stage 1 remains reopened and ARXIV_PRODUCTION_ACCEPTED must not be restored.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "ADP-S1P5T04-SYDNEY-SERVICE-DATE-039":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-SERVICE-DATE-001",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + product_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V6_CONTRACT",
                "question": "是否在悉尼服务日期修复 PR 合并后执行一次受控 Gmail SMTP test10，以验证邮件主题日期与云端 workflow 均正确。",
                "recommendation": "A: open PR and wait for CI; keep production disabled",
                "option_a": "将悉尼服务日期修复走 PR/CI，CI 绿并合并后再由 owner 单独确认是否发 test10。",
                "option_b": "继续沿用 workflow_dispatch 手动填 generated_at；不推荐，会制造人工负担。",
                "option_c": "跳过日期纠偏直接启用 production；禁止，因为会继续发错服务日期。",
                "effort": "P1; workflow correction, PR CI, then one controlled manual email if approved",
                "resource": "GitHub Actions ubuntu-latest, existing Gmail SMTP secret names, no local background process",
                "benefit": "确保每日邮件和 daily artifacts 按 Australia/Sydney 人类服务日期生成，而不是 UTC 截日。",
                "risks": "PR CI failure, accidental duplicate test email, premature production schedule enablement",
                "evidence": "workflow tests, GitHub PR CI, post-merge controlled test10 scheduled-execution artifact",
                "priority": "P1",
                "no_decision": "Stage 1 arXiv acceptance remains recorded, but controlled email cannot be accepted as daily-service evidence.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "ADP-S1P5T04-POST-MERGE-TEST10-040":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-SERVICE-DATE-TEST10-001",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + product_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V6_CONTRACT",
                "question": "是否现在从 main 触发一次受控 Gmail SMTP test10，以验证悉尼服务日期、中文教学邮件和云端 workflow。",
                "recommendation": "A: trigger controlled test10 from main; keep production disabled",
                "option_a": "从 main 触发一次 manual B1 text SMTP test10，验证邮件标题日期、中文正文和 artifact。",
                "option_b": "继续等待；安全但 Stage 1 邮件前台和日期修复缺少 post-merge 真实邮件证据。",
                "option_c": "直接启用 production schedule；禁止，因为 test10 尚未证明 post-merge 邮件路径。",
                "effort": "P1; one GitHub Actions manual run plus artifact verification",
                "resource": "GitHub Actions ubuntu-latest and one Gmail SMTP test email; no local background production process",
                "benefit": "把已合并的悉尼服务日期修复、中文教学型邮件前台、全 arXiv daily input、候选队列摘要和 Gmail SMTP 云端发送闭环绑定到一次真实 post-merge 证据。",
                "risks": "误选非 main 分支、重复发送测试邮件、过早启用 production schedule",
                "evidence": "manual test10 run id, scheduled-execution artifact, SMTP sent state, Sydney-date email subject, production scheduled job skipped or disabled",
                "priority": "P1",
                "no_decision": "Stage 1 arXiv acceptance remains recorded, but post-merge test10 proof remains incomplete.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "ADP-S1P5T04-PRODUCTION-SCHEDULE-OWNER-DECISION-041":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-PRODUCTION-SCHEDULE-001",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + product_owner",
                "assignment": "OWNER_DECISION_REQUIRED",
                "question": "是否在 test10 已通过后单独启用每日生产定时。",
                "recommendation": "A: keep production schedule disabled until a separate owner-approved enablement run",
                "option_a": "保持 production schedule disabled，先确认你确实要每天自动发送。",
                "option_b": "进入邮件模板质量优化，不改变 production flags。",
                "option_c": "启用生产定时；只允许在你明确批准并核对 GitHub variables/secrets 后执行。",
                "effort": "P1; explicit owner decision plus GitHub variable/secret verification",
                "resource": "GitHub Actions ubuntu-latest and Gmail SMTP; no local Mac background process",
                "benefit": "把 Stage 1 已验收和真正每日自动发送分开，避免未授权生产邮件。",
                "risks": "误启用 ADP_PRODUCTION_ENABLED 或 ADP_SCHEDULED_RUN_ENABLED 会造成每日真实发送；错误 SMTP/Release flags 会破坏 fail-closed 边界。",
                "evidence": "owner approval, repository variable state, scheduled workflow run evidence, SMTP sent artifact, no secret/body logging",
                "priority": "P1",
                "no_decision": "Stage 1 remains accepted, but production schedule stays disabled and no daily automatic send occurs.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "ADP-S1P5T05-LOCAL-PRODUCTION-AND-MIGRATION-PREP":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-LOCAL-RUNNER-001",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + engineering_owner + operations_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_LOCAL_RUNNER_BOUNDARY",
                "question": "是否按本机 Mac + Codex/local runner 作为 Stage 1 生产运行策略，并准备 2026-06-30 新电脑迁移。",
                "recommendation": "A: keep GitHub cloud schedule disabled and finish local runner migration prep",
                "option_a": "使用本机 Codex/local runner，每日状态写入本地 state dir，GitHub 只做代码、PR/CI、证据、状态和备份。",
                "option_b": "暂停自动运行，仅保留手动 smoke test；安全但不会自动补每日邮件。",
                "option_c": "重新启用 GitHub cloud scheduled production；当前不采用，除非 owner 另开明确任务。",
                "effort": "P1; local CLI, launchd package draft, state persistence, migration runbook, smoke evidence",
                "resource": "current Mac until 2026-06-30, then new Mac; Gmail SMTP only through local environment or Keychain-backed setup",
                "benefit": "把用户确认的低复杂度部署策略落到可复制、可验证、可迁移的本地运行路径。",
                "risks": "本地环境变量缺失、launchd 误安装、旧电脑和新电脑 state 不一致、GitHub cloud schedule 被误当生产 runner",
                "evidence": "local-runner tests, local preflight report, queue/ledger/email preview state files, launchd package draft, migration runbook",
                "priority": "P1",
                "no_decision": "Stage 1 remains accepted, but daily local production is not ready for owner-controlled smoke and migration.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "S2P1T01":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-S2P1T01-001",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + engineering_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_STAGE2_CONTRACT",
                "question": "是否开始 Stage 2 的第一个 source promotion：bioRxiv 与 medRxiv。",
                "recommendation": "A: start S2P1T01 after S1 local runner migration prep",
                "option_a": "开始 bioRxiv/medRxiv source adapter 和 shadow-mode gate，不影响现有 arXiv 本地生产路径。",
                "option_b": "先只做 Stage 1 本地 smoke，不进入新来源；风险更低但 Stage 2 不推进。",
                "option_c": "越过 source gate 直接把新来源放进正式邮件；禁止。",
                "effort": "P1/P2; source adapter, fixtures, 30-day replay plan, 48h shadow contract, arXiv no-regression tests",
                "resource": "local development and GitHub PR/CI evidence; no GitHub cloud scheduled production runner",
                "benefit": "在保持 arXiv 稳定运行的前提下，逐步把 Stage 2 扩展到生命科学与医学预印本。",
                "risks": "源身份混淆、重复 canonical paper、许可/全文越权、shadow 数据影响正式 arXiv 邮件",
                "evidence": "source adapter tests, source registry gate, fixture parse, replay/shadow reports, arXiv no-regression evidence",
                "priority": "P1",
                "no_decision": "Stage 1 local production prep remains complete, but Stage 2 does not begin.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "S2PCT03":
        policy.update(
            {
                "decision_id": "DEC-ADP-S2PCT03-LANCET-001",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + product_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_STAGE2_CONTRACT",
                "question": "是否继续 S2PCT03 / legacy S2P2T03 The Lancet 主刊 metadata-only no-send shadow evidence，同时保持 D2 source-domain acceptance 与 production inclusion false。",
                "recommendation": "A: continue S2PCT03 Lancet metadata-only shadow after completed Nature and Science shadow evidence",
                "option_a": "继续 The Lancet metadata-only adapter、医学文章类型门、PubMed/Online First 关系门和 no-send shadow daily，不影响现有 arXiv 本地生产路径。",
                "option_b": "暂停在 S2PCT02，只保留 Nature/Science shadow evidence；风险更低但 D2 顶刊覆盖不完整。",
                "option_c": "越过 D2 source gate 或 V7 3+1 合同直接放进正式邮件；禁止。",
                "effort": "P1/P2; source adapter, fixtures, article-type gates, shadow queue/ledger/email preview, semantic governance, changed-only project validation",
                "resource": "local development and GitHub PR/CI evidence; no GitHub cloud scheduled production runner",
                "benefit": "在保持 arXiv 稳定运行的前提下，逐步把 D2 top-journal shadow 从 Nature/Science 扩展到医学顶刊 The Lancet。",
                "risks": "医学文章类型误判、PubMed/Online First 关系错误、重复 DOI、许可/全文越权、shadow 数据影响正式 arXiv 邮件",
                "evidence": "Lancet source adapter tests, fixture parse, no-send shadow report, semantic extractor, project governance validator, arXiv no-regression evidence",
                "priority": "P1",
                "no_decision": "S2PCT02 Science remains completed as no-send shadow evidence, but D2 top-journal coverage stops before Lancet.",
            }
        )
    if project_id == "arxiv-daily-push" and task_id == "ADP-PHASE12-EMAIL-HUMAN-FORMAT-036":
        policy.update(
            {
                "decision_id": "DEC-arxiv-daily-push-V5-FRONTSTAGE-001",
                "review_id": "REVIEW8",
                "owner_role": "content_owner + product_owner",
                "assignment": "CODEX_CAN_CONTINUE_WITH_V5_CONTRACT",
                "question": "是否继续优化 arXiv 邮件前台模板，但不阻塞已通过的 Stage 1 arXiv 生产验收。",
                "recommendation": "A: defer template redesign until Stage 1 acceptance evidence is synchronized",
                "option_a": "保留当前可运行邮件模板，先完成 Stage 1 accepted 证据同步和生产开关核对。",
                "option_b": "进入邮件前台模板优化，按人类刻度、中文讲解密度和可操作性重做布局。",
                "option_c": "跳过模板优化直接扩大到 Stage 2；不推荐，因为用户已明确不满意前台体验。",
                "effort": "P1; content/product iteration after acceptance",
                "resource": "local rendering tests and one controlled manual email if template changes",
                "benefit": "把已可运行的 arXiv 交付继续提升为高信息密度教学邮件，而不把模板问题误判为 Stage 1 acceptance blocker。",
                "risks": "邮件可读性不足、信息密度低、过早进入 Stage 2、误开启生产定时",
                "evidence": "email render tests, scheduled_execution regression, controlled manual SMTP evidence if frontstage changes",
                "priority": "P1",
                "no_decision": "Stage 1 arXiv acceptance remains recorded, but human-facing email quality stays below owner preference.",
            }
        )
    return policy


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def current_commit() -> str:
    value = git_output(["rev-parse", "HEAD"])
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else "0" * 40


def current_tree_hash() -> str:
    value = git_output(["rev-parse", "HEAD^{tree}"])
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else "0" * 40


def configured_source_base() -> str | None:
    value = os.environ.get("GOVERNANCE_SOURCE_BASE_COMMIT", "").strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def configured_source_tree() -> str | None:
    value = os.environ.get("GOVERNANCE_SOURCE_TREE_HASH", "").strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def assurance_status(value: str | None) -> str:
    normalized = str(value or "unknown").strip().lower()
    mapping = {
        "pass": "VERIFIED",
        "verified": "VERIFIED",
        "machine_verified": "VERIFIED",
        "partial": "PARTIAL",
        "blocked": "FAILED",
        "failed": "FAILED",
        "unknown": "UNVERIFIED",
        "unverified": "UNVERIFIED",
        "not_applicable": "NOT_APPLICABLE",
        "not applicable": "NOT_APPLICABLE",
        "n/a": "NOT_APPLICABLE",
    }
    return mapping.get(normalized, "UNVERIFIED")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def canonical_input_paths(project_path: Path) -> list[Path]:
    candidates = [
        project_path / "VERSION",
        project_path / "CHANGELOG.md",
        project_path / "docs/governance/MODEL_SPEC.md",
        project_path / "docs/governance/model_registry.yaml",
        project_path / "docs/governance/formula_registry.yaml",
        project_path / "docs/governance/parameter_registry.csv",
        project_path / "docs/governance/DEVELOPMENT_LEDGER.md",
        project_path / "docs/governance/development_events.jsonl",
        project_path / "docs/governance/DELIVERY_PLAN.md",
        project_path / "docs/governance/delivery_tasks.yaml",
        project_path / "docs/governance/VERSION_MATRIX.yaml",
        project_path / "docs/governance/TRACEABILITY_MATRIX.csv",
        ROOT / "governance/projects.yaml",
    ]
    return [path for path in candidates if path.is_file()]


def source_snapshot_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: rel(item)):
        digest.update(rel(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def active_registry_counts(project_path: Path) -> dict[str, int]:
    parameters = read_csv(project_path / "docs/governance/parameter_registry.csv")
    active_params = [row for row in parameters if str(row.get("status") or "").lower() == "active"]
    checked_params = [
        row
        for row in active_params
        if row.get("source_selector") and row.get("extracted_value") not in {None, ""} and row.get("evidence_hash")
    ]
    formula_data = structural.load_yaml(project_path / "docs/governance/formula_registry.yaml")
    formulas = structural.as_list(formula_data.get("formulas")) if isinstance(formula_data, dict) else []
    active_formulas = [
        row for row in formulas if isinstance(row, dict) and str(row.get("status") or "").lower() == "active"
    ]
    checked_formulas = [
        row
        for row in active_formulas
        if row.get("implementation_refs") and row.get("implementation_fingerprint") and row.get("evidence_hash")
    ]
    return {
        "total_parameters": len(parameters),
        "active_parameters": len(active_params),
        "checked_parameters": len(checked_params),
        "total_formulas": len(formulas),
        "active_formulas": len(active_formulas),
        "checked_formulas": len(checked_formulas),
    }


def collect_unresolved_fact_ids(project_id: str, parsed: dict[str, Any], counts: dict[str, int]) -> list[str]:
    ids: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"unknown_task_ids", "semantic_review_task_ids", "unresolved_fact_ids"}:
                    for ref in structural.as_list(item):
                        text = str(ref).strip()
                        if text:
                            ids.add(text)
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for key in ("models", "formulas", "parameters", "tasks", "traceability", "version_matrix"):
        visit(parsed.get(key))
    if counts["checked_parameters"] < counts["active_parameters"]:
        ids.add(f"FACT-{project_id}-IMPLEMENTATION-PARAMETER-REVIEW")
    if counts["checked_formulas"] < counts["active_formulas"]:
        ids.add(f"FACT-{project_id}-IMPLEMENTATION-FORMULA-REVIEW")
    policy = ASSURANCE_POLICY.get(project_id, {})
    if policy.get("empirical") in {"unknown", "partial"}:
        ids.add(f"FACT-{project_id}-EMPIRICAL-EVIDENCE")
    if policy.get("operational") in {"blocked", "partial", "unknown"}:
        ids.add(f"FACT-{project_id}-OPERATIONAL-EVIDENCE")
    return sorted(ids)


def load_events(project_path: Path) -> list[dict[str, Any]]:
    path = project_path / "docs/governance/development_events.jsonl"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def event_time(event: dict[str, Any]) -> str:
    return str(event.get("timestamp") or event.get("date") or "")


def max_event_time(events: list[dict[str, Any]]) -> str:
    values = [event_time(event) for event in events if event_time(event)]
    return max(values) if values else "UNKNOWN"


def pending_event_count(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        commit = str(event.get("result_commit") or event.get("git_commit") or "").upper()
        if commit in {"", "PENDING", "PENDING_CI"}:
            count += 1
    return count


def event_binding_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "tree_bound_events": 0,
        "commit_bound_events": 0,
        "legacy_unbound_events": 0,
        "precommit_pending_events": 0,
    }
    for event in events:
        binding = str(event.get("binding_status") or "").strip().lower()
        commit = str(event.get("result_commit") or event.get("git_commit") or "").strip()
        has_commit = bool(re.fullmatch(r"[0-9a-f]{7,40}", commit))
        if binding == "precommit_tree_bound":
            counts["tree_bound_events"] += 1
        elif has_commit or event.get("ci_attestation_ref"):
            counts["commit_bound_events"] += 1
        elif binding in {"pre_commit_pending", "precommit_pending"}:
            counts["precommit_pending_events"] += 1
        else:
            counts["legacy_unbound_events"] += 1
    return counts


def final_commit_binding(events: list[dict[str, Any]]) -> str:
    if not events:
        return "PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION"
    latest = events[-1]
    commit = str(latest.get("result_commit") or latest.get("git_commit") or "").strip()
    if re.fullmatch(r"[0-9a-f]{7,40}", commit):
        ref = str(latest.get("ci_run_reference") or latest.get("ci_attestation_ref") or "").strip()
        return f"CI_ATTESTED:{commit}" + (f" {ref}" if ref else "")
    ref = str(latest.get("ci_attestation_ref") or "").strip()
    if ref:
        return f"CI_ATTESTED:{ref}"
    return "PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION"


def completed_task_ids(tasks: list[dict[str, Any]]) -> set[str]:
    return {
        str(task.get("task_id"))
        for task in tasks
        if isinstance(task, dict) and str(task.get("status") or "") in COMPLETED_TASK_STATES
    }


def task_is_stale_or_satisfied(project_id: str, task: dict[str, Any], counts: dict[str, int], impl_status: str) -> str:
    objective = str(task.get("objective") or "").lower()
    task_id = str(task.get("task_id") or "")
    if project_id == "Serenity-Alipay" and task_id == "TASK-A-001":
        baseline_exists = (
            counts["active_parameters"] > 0
            and counts["active_formulas"] > 0
            and impl_status == "VERIFIED"
        )
        if baseline_exists and "first" in objective and "governance baseline" in objective:
            return "Serenity-Alipay baseline exists and implementation congruence is VERIFIED; the first-baseline task is stale."
    if "create the first" in objective and counts["active_parameters"] > 0 and counts["active_formulas"] > 0:
        return "Task objective says to create the first baseline, but active formula and parameter registries already exist."
    return ""


def select_next_task(
    project_id: str,
    tasks: list[dict[str, Any]],
    counts: dict[str, int],
    impl_status: str,
    current_phase: str = "",
    arxiv_stage1_accepted: bool = False,
) -> dict[str, Any]:
    completed = completed_task_ids(tasks)
    candidates: list[dict[str, Any]] = []
    stale: list[dict[str, str]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("task_id") or "")
        status = str(task.get("status") or "")
        if status not in EXECUTABLE_TASK_STATES:
            continue
        stale_reason = task_is_stale_or_satisfied(project_id, task, counts, impl_status)
        if stale_reason:
            stale.append({"task_id": task_id, "reason": stale_reason})
            continue
        dependencies = [str(dep) for dep in structural.as_list(task.get("dependencies")) if str(dep)]
        unmet = [dep for dep in dependencies if dep not in completed]
        if unmet or not task.get("acceptance_ids"):
            continue
        if status != "blocked" and not task.get("test_commands"):
            continue
        if (
            project_id == "arxiv-daily-push"
            and arxiv_stage1_accepted
            and status == "blocked"
            and task_id.startswith("ADP-PHASE11-")
        ):
            stale.append(
                {
                    "task_id": task_id,
                    "reason": "Legacy Phase 11 blocked trial task is superseded by V5/V6 Stage 1 accepted evidence; production variable enablement is tracked as a separate fail-closed operational action.",
                }
            )
            continue
        candidates.append(task)
    if not candidates:
        return {
            "task_id": "NONE",
            "status": "not_applicable",
            "reason": "No ready or in_progress task has completed dependencies, Acceptance IDs, and test commands.",
            "acceptance_ids": [],
            "owner": "project owner",
            "human_owner_role": "project_owner",
            "unblock_condition": "Define a ready/in_progress/blocked task with completed dependencies, Acceptance IDs, and evidence policy.",
            "stale_candidates": stale,
        }
    use_current_phase_priority = project_id == "arxiv-daily-push" and str(current_phase).startswith("S")
    if use_current_phase_priority:
        phase_candidates = [
            task
            for task in candidates
            if str(task.get("phase") or "") == current_phase and str(task.get("status") or "") != "blocked"
        ]
        if phase_candidates:
            phase_priority = {"in_progress": 0, "ready": 1, "planned": 2}
            phase_candidates.sort(key=lambda task: (phase_priority.get(str(task.get("status")), 9), str(task.get("task_id"))))
            candidates = phase_candidates

    priority = {"blocked": 0, "in_progress": 1, "ready": 2, "planned": 3}
    candidates.sort(key=lambda task: (priority.get(str(task.get("status")), 9), str(task.get("task_id"))))
    task = candidates[0]
    role = REVIEW8_DECISION_POLICY.get(project_id, {}).get("owner_role", "project_owner")
    status = str(task.get("status") or "")
    if status == "blocked":
        unblock = str(task.get("risk") or task.get("objective") or "Human owner must provide the missing evidence before this task can complete.")
    else:
        command = structural.as_list(task.get("test_commands"))[0] if task.get("test_commands") else "listed acceptance command"
        if str(command).strip().upper() == "PENDING":
            unblock = "Define concrete acceptance test commands before marking this task complete, then attach the listed evidence refs."
        else:
            unblock = f"Run `{command}` and attach the listed evidence refs."
    return {
        "task_id": str(task.get("task_id") or "NONE"),
        "status": status,
        "reason": str(task.get("objective") or ""),
        "acceptance_ids": structural.as_list(task.get("acceptance_ids")),
        "owner": role,
        "human_owner_role": role,
        "unblock_condition": unblock,
        "stale_candidates": stale,
    }


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "null"
    return json.dumps(str(value), ensure_ascii=False)


def dump_yaml(value: Any, indent: int = 0) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if item == []:
                lines.append(f"{pad}{key}: []")
                continue
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{pad}[]"]
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return lines
    return [f"{pad}{yaml_scalar(value)}"]


def existing_assurance_base(project_path: Path) -> str | None:
    path = project_path / "docs/governance/ASSURANCE_STATUS.yaml"
    if not path.exists():
        return None
    match = re.search(r"(?m)^source_base_commit:\s*\"?([0-9a-f]{40})\"?\s*$", path.read_text(encoding="utf-8"))
    commit = match.group(1) if match else ""
    return commit if re.fullmatch(r"[0-9a-f]{40}", commit) else None


def existing_assurance_tree(project_path: Path) -> str | None:
    path = project_path / "docs/governance/ASSURANCE_STATUS.yaml"
    if not path.exists():
        return None
    match = re.search(r"(?m)^source_tree_hash:\s*\"?([0-9a-f]{40})\"?\s*$", path.read_text(encoding="utf-8"))
    tree = match.group(1) if match else ""
    return tree if re.fullmatch(r"[0-9a-f]{40}", tree) else None


def existing_assurance_status(project_path: Path) -> dict[str, Any]:
    path = project_path / "docs/governance/ASSURANCE_STATUS.yaml"
    if not path.exists():
        return {}
    data = structural.load_yaml(path)
    return data if isinstance(data, dict) else {}


def existing_root_base() -> str | None:
    for path in (ROOT / "GOVERNANCE_DASHBOARD.md", ROOT / "OWNER_PORTFOLIO.md", ROOT / "README.md"):
        if not path.exists():
            continue
        match = re.search(r"source_base_commit:\s*`?([0-9a-f]{40})`?", path.read_text(encoding="utf-8"))
        commit = match.group(1) if match else ""
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            return commit
    return None


def existing_root_tree() -> str | None:
    for path in (ROOT / "GOVERNANCE_DASHBOARD.md", ROOT / "OWNER_PORTFOLIO.md", ROOT / "README.md"):
        if not path.exists():
            continue
        match = re.search(r"source_tree_hash:\s*`?([0-9a-f]{40})`?", path.read_text(encoding="utf-8"))
        tree = match.group(1) if match else ""
        if re.fullmatch(r"[0-9a-f]{40}", tree):
            return tree
    return None


def latest_manifest(project_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_dir = ROOT / "governance/run_manifests"
    event_refs: list[str] = []
    if events:
        event_refs.extend(str(ref) for ref in structural.as_list(events[-1].get("evidence_refs")))

    def load_manifest(ref: str) -> dict[str, Any]:
        path = ROOT / ref
        if path.suffix != ".json" or not path.is_file() or manifest_dir not in path.parents:
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if str(data.get("project_id") or "") != project_id:
            return {}
        data["_path"] = rel(path)
        return data

    for ref in reversed(event_refs):
        data = load_manifest(ref)
        if data:
            return data
    for ref in reversed([str(path.relative_to(ROOT)) for path in sorted(manifest_dir.glob("*.json"))]):
        data = load_manifest(ref)
        if data:
            return data
    return {}


def arxiv_stage1_acceptance_proven(project_id: str, events: list[dict[str, Any]], manifest: dict[str, Any]) -> bool:
    if project_id != "arxiv-daily-push":
        return False
    if (
        manifest.get("production_acceptance_claimed") is False
        and (
            str(manifest.get("task_id") or "").startswith("S1P5T03-R")
            or str(manifest.get("status") or "").lower() == "pending_cloud_ci"
        )
    ):
        return False
    manifest_claims_acceptance = (
        manifest.get("production_acceptance_claimed") is True
        and manifest.get("accepted_for_production") is True
        and str(manifest.get("arxiv_production_acceptance_label") or "") == "ARXIV_PRODUCTION_ACCEPTED"
        and str(manifest.get("status") or "").lower() in {"pass", "completed"}
    )
    if manifest_claims_acceptance:
        return True
    for event in reversed(events):
        if event.get("production_acceptance_claimed") is False and str(event.get("task_id") or "").startswith("S1P5T03-R"):
            return False
        if (
            event.get("production_acceptance_claimed") is True
            and str(event.get("arxiv_production_acceptance_label") or "") == "ARXIV_PRODUCTION_ACCEPTED"
            and str(event.get("result") or "").lower() in {"pass", "completed"}
        ):
            return True
    return False


def load_project(project: dict[str, Any]) -> dict[str, Any]:
    project_id = structural.project_scope(project)
    project_path = ROOT / str(project.get("path") or "")
    parsed_validation = structural.Validation()
    parsed = structural.parse_project_governance(project_path, parsed_validation, True, project_id)
    tasks = [task for task in structural.as_list(parsed.get("tasks")) if isinstance(task, dict)]
    events = load_events(project_path)
    matrix = parsed.get("version_matrix") if isinstance(parsed.get("version_matrix"), dict) else {}
    counts = active_registry_counts(project_path)
    manifest = latest_manifest(project_id, events)
    source_paths = canonical_input_paths(project_path)
    source_hash = source_snapshot_hash(source_paths)
    base_commit = configured_source_base() or existing_assurance_base(project_path) or current_commit()
    tree_hash = configured_source_tree() or existing_assurance_tree(project_path) or current_tree_hash()
    policy = dict(ASSURANCE_POLICY.get(project_id, {}))
    arxiv_stage1_accepted = arxiv_stage1_acceptance_proven(project_id, events, manifest)
    if arxiv_stage1_accepted:
        policy.update(
            {
                "empirical": "verified",
                "operational": "verified",
                "readiness": "verified",
                "decision": "Stage 1 arXiv accepted; production schedule remains controlled by GitHub Variables/Secrets and fail-closed gates.",
                "blockers": [],
            }
        )
    unresolved = collect_unresolved_fact_ids(project_id, parsed, counts)
    if arxiv_stage1_accepted:
        accepted_s1_resolved = {
            "ADP-PHASE8-VIDEO-001",
            "FACT-arxiv-daily-push-EMPIRICAL-EVIDENCE",
            "FACT-arxiv-daily-push-OPERATIONAL-EVIDENCE",
        }
        unresolved = [item for item in unresolved if item not in accepted_s1_resolved]
    impl_status = (
        "NOT_APPLICABLE"
        if counts["active_parameters"] == 0 and counts["active_formulas"] == 0
        else "VERIFIED"
        if counts["checked_parameters"] == counts["active_parameters"]
        and counts["checked_formulas"] == counts["active_formulas"]
        else "PARTIAL"
    )
    parameter_source_status = "VERIFIED" if counts["checked_parameters"] == counts["active_parameters"] else "PARTIAL"
    event_counts = event_binding_counts(events)
    evidence_freshness_status = "PARTIAL" if event_counts["legacy_unbound_events"] else "VERIFIED"
    methodological_status = "UNVERIFIED" if policy.get("empirical") in {"unknown", "partial"} else "VERIFIED"
    existing_assurance = existing_assurance_status(project_path)
    existing_owner_decision = (
        existing_assurance.get("owner_decision")
        if isinstance(existing_assurance.get("owner_decision"), dict)
        else {}
    )
    next_task = select_next_task(
        project_id,
        tasks,
        counts,
        impl_status,
        str(matrix.get("current_phase") or ""),
        arxiv_stage1_accepted=arxiv_stage1_accepted,
    )
    decision_policy = decision_policy_for(project_id, next_task)
    if decision_policy.get("owner_role") and str(next_task.get("task_id") or "") != "NONE":
        next_task = {
            **next_task,
            "owner": str(decision_policy.get("owner_role")),
            "human_owner_role": str(decision_policy.get("owner_role")),
        }
    release_gate = str(matrix.get("current_gate") or "UNKNOWN")
    if (
        project_id == "arxiv-daily-push"
        and not arxiv_stage1_accepted
        and str(next_task.get("task_id") or "").startswith("S1P5T03-R")
    ):
        release_gate = "STRICT_ARXIV_PRODUCTION_ACCEPTANCE_REOPENED_PENDING_S1P5T03R_CLOUD_CI"
    owner_decision = {
        "required": True,
        "decision_id": str(decision_policy.get("decision_id") or f"DEC-{project_id}-REVIEW8-001"),
        "review_id": str(decision_policy.get("review_id") or "REVIEW8"),
        "project_id": project_id,
        "decision_question": str(decision_policy.get("question") or policy.get("decision") or "Decide the next evidence investment."),
        "question": str(decision_policy.get("question") or policy.get("decision") or "Decide the next evidence investment."),
        "human_owner_role": str(decision_policy.get("owner_role") or "project_owner"),
        "human_assignment_status": str(decision_policy.get("assignment") or "HUMAN_ASSIGNMENT_REQUIRED"),
        "current_recommendation": str(decision_policy.get("recommendation") or "A: fund project-specific evidence collection"),
        "option_a": str(decision_policy.get("option_a") or "Collect the project-specific evidence required by the current blocker."),
        "option_b": str(decision_policy.get("option_b") or "Keep the project blocked or conditional until evidence exists."),
        "option_c": str(decision_policy.get("option_c") or "Pause this project from delivery claims."),
        "options": [
            str(decision_policy.get("option_a") or "Collect the project-specific evidence required by the current blocker."),
            str(decision_policy.get("option_b") or "Keep the project blocked or conditional until evidence exists."),
            str(decision_policy.get("option_c") or "Pause this project from delivery claims."),
        ],
        "estimated_effort": str(decision_policy.get("effort") or "project_owner review required"),
        "estimated_cost_or_resource": str(decision_policy.get("resource") or "owner time and evidence collection"),
        "expected_benefit": str(decision_policy.get("benefit") or "close the current evidence blocker"),
        "principal_risks": str(decision_policy.get("risks") or "evidence remains missing or unsuitable"),
        "evidence_required": str(decision_policy.get("evidence") or "project-specific evidence manifest"),
        "decision_deadline_or_priority": str(decision_policy.get("priority") or "P1"),
        "consequence_of_no_decision": str(decision_policy.get("no_decision") or "readiness remains blocked"),
        "unblock_task_id": next_task["task_id"],
        "acceptance_ids": next_task["acceptance_ids"] or ["HUMAN-ACTION-REQUIRED"],
        "generated_from_refs": [f"{project.get('path')}/docs/governance/ASSURANCE_STATUS.yaml", f"{project.get('path')}/docs/governance/delivery_tasks.yaml"],
        "last_reviewed_at": max_event_time(events),
    }
    existing_owner_task = str(existing_owner_decision.get("unblock_task_id") or "")
    if not existing_owner_task or existing_owner_task == str(next_task.get("task_id") or ""):
        for key, value in existing_owner_decision.items():
            if value not in (None, ""):
                owner_decision[key] = value
    if "decision_question" not in owner_decision and "question" in owner_decision:
        owner_decision["decision_question"] = owner_decision["question"]
    if "question" not in owner_decision and "decision_question" in owner_decision:
        owner_decision["question"] = owner_decision["decision_question"]

    delivery_readiness = {
        "status": assurance_status(str(policy.get("readiness") or "blocked")),
        "release_gate": release_gate,
        "blocker_ids": unresolved[:8],
    }
    if project_id == "arxiv-daily-push" and "V7_1" in release_gate:
        delivery_readiness.update(
            {
                "v7_contract": str(matrix.get("current_v7_contract_version") or "UNKNOWN"),
                "v7_contract_hash": str(matrix.get("v7_product_contract_sha256") or "UNKNOWN"),
                "v7_roadmap_hash": str(matrix.get("v7_roadmap_sha256") or "UNKNOWN"),
                "v7_parallel_audit": str(matrix.get("v7_parallel_audit_version") or "UNKNOWN"),
                "v7_parallel_audit_hash": str(matrix.get("v7_parallel_audit_sha256") or "UNKNOWN"),
                "open_p0_findings": matrix.get("v7_open_p0_findings", "UNKNOWN"),
                "open_p1_findings": matrix.get("v7_open_p1_findings", "UNKNOWN"),
                "production_forbidden_until": str(matrix.get("stage2_production_forbidden_until") or "UNKNOWN"),
                "stage2_stop_gate": str(matrix.get("stage2_stop_gate") or "UNKNOWN"),
                "stage2_integrated_production_accepted": bool(
                    matrix.get("stage2_integrated_production_accepted", False)
                ),
                "parallel_shadow_source_task": str(matrix.get("current_v7_shadow_source_task_id") or "UNKNOWN"),
                "current_v7_task_id": str(matrix.get("current_v7_task_id") or "UNKNOWN"),
            }
        )

    assurance = {
        "project_id": project_id,
        "as_of_event_id": str(events[-1].get("event_id") or events[-1].get("iteration_id") or "NONE") if events else "NONE",
        "source_snapshot_hash": source_hash,
        "source_base_commit": base_commit,
        "source_tree_hash": tree_hash,
        "snapshot_event_time": max_event_time(events),
        "generator_version": GENERATOR_VERSION,
        "final_commit_binding": final_commit_binding(events),
        "dimensions": {
            "structural_completeness": {
                "status": "VERIFIED",
                "fact_level": "EXTRACTED",
                "evidence_refs": ["scripts/validate_project_governance.py"],
            },
            "implementation_congruence": {
                "status": impl_status,
                "machine_verified_means": "documented implementation values and fingerprints match extractable code/config sources only",
                "fact_level": "EXTRACTED",
                "checked_active_parameters": counts["checked_parameters"],
                "total_active_parameters": counts["active_parameters"],
                "checked_active_formulas": counts["checked_formulas"],
                "total_active_formulas": counts["active_formulas"],
                "unresolved_fact_ids": [
                    item for item in unresolved if "IMPLEMENTATION" in item or "PARAM" in item or "FORM" in item
                ],
                "evidence_refs": [
                    f"{project.get('path')}/docs/governance/parameter_registry.csv",
                    f"{project.get('path')}/docs/governance/formula_registry.yaml",
                ],
            },
            "parameter_source_quality": {
                "status": parameter_source_status,
                "fact_level": "EXTRACTED" if parameter_source_status == "VERIFIED" else "UNKNOWN",
                "checked_active_parameters": counts["checked_parameters"],
                "total_active_parameters": counts["active_parameters"],
                "evidence_refs": [f"{project.get('path')}/docs/governance/parameter_registry.csv"],
            },
            "methodological_rationale": {
                "status": methodological_status,
                "fact_level": "UNKNOWN" if methodological_status == "UNVERIFIED" else "EXTRACTED",
                "machine_verified_means": "methodological, calibration, and baseline rationale are tracked separately from implementation congruence",
                "unresolved_fact_ids": [item for item in unresolved if "EMPIRICAL" in item],
                "evidence_refs": [f"{project.get('path')}/docs/governance/MODEL_SPEC.md"],
            },
            "empirical_validation": {
                "status": assurance_status(str(policy.get("empirical") or "unknown")),
                "fact_level": "UNKNOWN" if assurance_status(str(policy.get("empirical") or "unknown")) == "UNVERIFIED" else "EXTRACTED",
                "unresolved_fact_ids": [item for item in unresolved if "EMPIRICAL" in item],
                "evidence_refs": [f"{project.get('path')}/docs/governance/delivery_tasks.yaml"],
            },
            "operational_validation": {
                "status": assurance_status(str(policy.get("operational") or "unknown")),
                "fact_level": "UNKNOWN"
                if assurance_status(str(policy.get("operational") or "unknown")) == "UNVERIFIED"
                else "EXTRACTED",
                "unresolved_fact_ids": [item for item in unresolved if "OPERATIONAL" in item],
                "evidence_refs": [f"{project.get('path')}/docs/governance/development_events.jsonl"],
            },
            "delivery_evidence": {
                "status": assurance_status(str(policy.get("readiness") or "blocked")),
                "fact_level": "EXTRACTED",
                "evidence_refs": [f"{project.get('path')}/docs/governance/delivery_tasks.yaml"],
            },
            "evidence_freshness": {
                "status": evidence_freshness_status,
                "fact_level": "EXTRACTED",
                "tree_bound_events": event_counts["tree_bound_events"],
                "commit_bound_events": event_counts["commit_bound_events"],
                "legacy_unbound_events": event_counts["legacy_unbound_events"],
                "precommit_pending_events": event_counts["precommit_pending_events"],
                "evidence_refs": [f"{project.get('path')}/docs/governance/development_events.jsonl"],
            },
        },
        "delivery_readiness": delivery_readiness,
        "next_executable_task": next_task,
        "owner_decision": owner_decision,
    }
    return {
        "project_id": project_id,
        "path": str(project.get("path") or ""),
        "ci_mode": str(project.get("ci_mode") or ""),
        "product_version": str(matrix.get("product_version") or "UNKNOWN"),
        "current_iteration": str(matrix.get("current_iteration") or "UNKNOWN"),
        "current_phase": str(matrix.get("current_phase") or "UNKNOWN"),
        "current_gate": str(matrix.get("current_gate") or "UNKNOWN"),
        "counts": counts,
        "models": len(structural.as_list(parsed.get("models"))),
        "tasks": tasks,
        "events": events,
        "latest_event": events[-1] if events else {},
        "latest_manifest": manifest,
        "pending_event_count": pending_event_count(events),
        "event_binding_counts": event_counts,
        "unresolved_fact_ids": unresolved,
        "policy_blockers": list(policy.get("blockers") or []),
        "assurance": assurance,
    }


def brief_list(values: list[str], limit: int = 3) -> str:
    if not values:
        return "none"
    text = ", ".join(values[:limit])
    if len(values) > limit:
        text += f", +{len(values) - limit}"
    return text


def render_readme(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    rows = "\n".join(
        f"| `{item['project_id']}` | `{item['path']}` | {PROJECT_REPOSITORIES.get(item['project_id'], 'UNKNOWN')} |"
        for item in projects
    )
    return f"""# CodexProject

Active Codex-related project hub for LinzeColin.

## Governance Entry

- Lean v2 standard: [docs/governance/STANDARD.md](docs/governance/STANDARD.md)
- Project human-entry files: `功能清单`, `开发记录`, `模型参数文件`

## Snapshot Metadata

- source_base_commit: `{meta['source_base_commit']}`
- source_tree_hash: `{meta['source_tree_hash']}`
- source_snapshot_hash: `{meta['source_snapshot_hash']}`
- generator_version: `{GENERATOR_VERSION}`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Assurance Vocabulary

- `structural_completeness`: required governance files parse and cross-reference.
- `implementation_congruence`: documented implementation values and fingerprints match extractable code/config sources.
- `parameter_source_quality`: active parameter values have source selectors or explicit unresolved tasks.
- `empirical_validation`: model claims are supported by calibration, backtest, fixture, or experiment evidence.
- `operational_validation`: runtime, CI, soak, or production-trial evidence exists.
- `delivery_evidence`: delivery gates and completed tasks have acceptance evidence.
- `evidence_freshness`: events are tree-bound, commit-bound, or honestly listed as legacy unbound.

`machine_verified` is not a production claim. It only maps to implementation congruence when code/config extraction proves documented facts.

## Projects

| Project | Path | Repository |
|---|---|---|
{rows}

## Required Checks

```bash
python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main
python3 scripts/generate_governance_dashboard.py --write --root-artifact-dir /tmp/governance-generated-views
```

This repository is the source-level project hub. Each project directory must keep Lean v2 canonical facts and human-entry files synchronized with implementation evidence. Root dashboards and portfolio summaries are generated on demand as CI artifacts instead of committed source files.
"""


def render_dashboard(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    lines = [
        "# Governance Dashboard",
        "",
        f"- source_base_commit: `{meta['source_base_commit']}`",
        f"- source_tree_hash: `{meta['source_tree_hash']}`",
        f"- source_snapshot_hash: `{meta['source_snapshot_hash']}`",
        f"- snapshot_event_time: `{meta['snapshot_event_time']}`",
        f"- generator_version: `{GENERATOR_VERSION}`",
        "- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`",
        "",
        "| Project | Version | Phase | Impl | Param Source | Methodology | Empirical | Operational | Freshness | Readiness | Next |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in projects:
        assurance = item["assurance"]
        dims = assurance["dimensions"]
        next_task = assurance["next_executable_task"]["task_id"]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item['project_id']}`",
                    f"`{item['product_version']}`",
                    f"`{item['current_phase']}`",
                    f"`{dims['implementation_congruence']['status']}`",
                    f"`{dims['parameter_source_quality']['status']}`",
                    f"`{dims['methodological_rationale']['status']}`",
                    f"`{dims['empirical_validation']['status']}`",
                    f"`{dims['operational_validation']['status']}`",
                    f"`{dims['evidence_freshness']['status']}`",
                    f"`{assurance['delivery_readiness']['status']}`",
                    f"`{next_task}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Implementation congruence only means documented values and fingerprints match code/config sources.",
            "- Empirical validation and operational validation are separate dimensions and may remain UNVERIFIED, PARTIAL, or FAILED.",
            "- Branch protection details remain `UNVERIFIED` unless checked by authenticated GitHub API or UI evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_owner_portfolio(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    decision_projects = [item for item in projects if item["assurance"]["owner_decision"]["required"]]
    blockers: list[str] = []
    for item in projects:
        for blocker in item["policy_blockers"][:2]:
            blockers.append(f"{item['project_id']}: {blocker}")
    buckets = {status: [] for status in sorted(ASSURANCE_STATUSES)}
    for item in projects:
        status = item["assurance"]["delivery_readiness"]["status"]
        buckets.setdefault(status, []).append(item)
    bucket_total = sum(len(values) for values in buckets.values())
    next_task = next(
        (
            item["assurance"]["next_executable_task"]
            for item in projects
            if item["assurance"]["next_executable_task"]["task_id"] != "NONE"
        ),
        {"task_id": "NONE", "reason": "No executable governance task selected."},
    )
    lines = [
        "# OWNER_PORTFOLIO",
        "",
        "## 1. 当前结论",
        "",
        "Review8-A 后，本仓库的 Owner 视图必须把结构完整、实现一致、方法依据、实证、运行和交付分开；当前 Portfolio 不是生产可用声明。",
        "",
        "## 2. 本次运行改变了什么",
        "",
        "- 状态桶现在覆盖 `FAILED`、`PARTIAL`、`UNVERIFIED`、`VERIFIED`、`NOT_APPLICABLE`，总数必须等于登记项目数。",
        "- Owner 决策改为项目特定的人类责任角色、资源、收益、风险、证据和不决策后果。",
        "- 陈旧的“创建首个治理基线”任务不得在事实已满足时继续作为下一任务。",
        "",
        "## 3. 为什么重要",
        "",
        "没有这些约束，仓库可能在 CI 绿色时仍输出错误汇总、陈旧任务或无责任人的资金/上线决策。",
        "",
        "## 4. 需要人类决定什么",
        "",
        "优先决定 P0/P1 项目是否投入真实数据、专家/法务/隐私/风险 owner 时间和验收证据；Codex 只能执行治理和验证，不能替代人类批准。",
        "",
        "## 5. 默认建议",
        "",
        f"- 下一唯一任务：`{next_task['task_id']}` - {next_task['reason']}",
        "- 默认策略：先关闭 P0 证据和人类责任 blocker，再进入项目 C0-C7 实证闭环。",
        "",
        "## 6. 不决策后果",
        "",
        "没有 owner 决策和证据投入的项目保持 `FAILED`、`PARTIAL` 或 `UNVERIFIED`，不得提升为交付就绪。",
        "",
        "## 7. 下一行动、责任角色和验收证据",
        "",
        f"- human_owner_role: `{next_task.get('human_owner_role') or next_task.get('owner')}`",
        f"- acceptance_ids: `{brief_list([str(x) for x in next_task.get('acceptance_ids', [])])}`",
        f"- unblock_condition: {next_task.get('unblock_condition')}",
        "",
        "## 8. 九层 Assurance 状态",
        "",
        f"- project_total: `{len(projects)}`",
        f"- bucket_total: `{bucket_total}`",
        f"- failed: `{len(buckets.get('FAILED', []))}`",
        f"- partial: `{len(buckets.get('PARTIAL', []))}`",
        f"- unverified: `{len(buckets.get('UNVERIFIED', []))}`",
        f"- verified: `{len(buckets.get('VERIFIED', []))}`",
        f"- not_applicable: `{len(buckets.get('NOT_APPLICABLE', []))}`",
        "",
        "| Bucket | Count | Projects |",
        "|---|---:|---|",
    ]
    for status in ["FAILED", "PARTIAL", "UNVERIFIED", "VERIFIED", "NOT_APPLICABLE"]:
        values = buckets.get(status, [])
        lines.append(f"| `{status}` | `{len(values)}` | {brief_list([item['project_id'] for item in values], 20)} |")
    lines.extend(
        [
            "",
            "## 9. 技术元数据",
            "",
        ]
    )
    lines.extend(
        [
        f"- source_base_commit: `{meta['source_base_commit']}`",
        f"- source_tree_hash: `{meta['source_tree_hash']}`",
        f"- source_snapshot_hash: `{meta['source_snapshot_hash']}`",
        f"- snapshot_event_time: `{meta['snapshot_event_time']}`",
        f"- generator_version: `{GENERATOR_VERSION}`",
        "- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`",
        "- branch_protection: `UNVERIFIED` unless authenticated setup doctor evidence is attached",
        "",
        "## 10. Top 5 Blockers",
        "",
        ]
    )
    for blocker in blockers[:5]:
        lines.append(f"- {blocker}")
    lines.extend(
        [
            "",
            "## 11. Owner Decisions",
            "",
        ]
    )
    for item in decision_projects:
        decision = item["assurance"]["owner_decision"]
        lines.extend(
            [
                f"### `{decision['decision_id']}`",
                "",
                f"- human_owner_role: `{decision['human_owner_role']}`",
                f"- recommendation: {decision['current_recommendation']}",
                f"- estimated_effort: {decision['estimated_effort']}",
                f"- estimated_cost_or_resource: {decision['estimated_cost_or_resource']}",
                f"- expected_benefit: {decision['expected_benefit']}",
                f"- principal_risks: {decision['principal_risks']}",
                f"- evidence_required: {decision['evidence_required']}",
                f"- no_decision_consequence: {decision['consequence_of_no_decision']}",
                "",
            ]
        )
    lines.extend(["", "## 12. Executable Tasks", ""])
    for item in projects:
        task = item["assurance"]["next_executable_task"]
        lines.append(f"- `{item['project_id']}`: `{task['task_id']}` - {task['reason']}")
    lines.extend(["", "## 13. Next Unique Governance Task", ""])
    lines.append(f"- `{next_task['task_id']}` - {next_task['reason']}")
    lines.extend(["", "## 14. Assurance Dimensions", ""])
    lines.append("| Project | Structural | Impl | Param Source | Methodology | Empirical | Operational | Delivery | Freshness | Readiness | Owner action |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for item in projects:
        dims = item["assurance"]["dimensions"]
        lines.append(
            f"| `{item['project_id']}` | `{dims['structural_completeness']['status']}` | "
            f"`{dims['implementation_congruence']['status']}` | `{dims['parameter_source_quality']['status']}` | "
            f"`{dims['methodological_rationale']['status']}` | "
            f"`{dims['empirical_validation']['status']}` | `{dims['operational_validation']['status']}` | "
            f"`{dims['delivery_evidence']['status']}` | `{dims['evidence_freshness']['status']}` | "
            f"`{item['assurance']['delivery_readiness']['status']}` | {item['assurance']['owner_decision']['decision_question']} |"
        )
    return "\n".join(lines) + "\n"


def render_status(item: dict[str, Any]) -> str:
    assurance = item["assurance"]
    dims = assurance["dimensions"]
    counts = item["counts"]
    delivery = assurance["delivery_readiness"]
    v7_delivery_lines = ""
    if delivery.get("stage2_stop_gate"):
        stage2_accepted = str(bool(delivery.get("stage2_integrated_production_accepted"))).lower()
        v7_delivery_lines = (
            f"- V7 contract: `{delivery.get('v7_contract', 'UNKNOWN')}`\n"
            f"- V7 contract hash: `{delivery.get('v7_contract_hash', 'UNKNOWN')}`\n"
            f"- V7 roadmap hash: `{delivery.get('v7_roadmap_hash', 'UNKNOWN')}`\n"
            f"- V7.1 parallel audit: `{delivery.get('v7_parallel_audit', 'UNKNOWN')}`\n"
            f"- V7.1 audit hash: `{delivery.get('v7_parallel_audit_hash', 'UNKNOWN')}`\n"
            f"- Open audit blockers: `P0={delivery.get('open_p0_findings', 'UNKNOWN')} / P1={delivery.get('open_p1_findings', 'UNKNOWN')}`\n"
            f"- Production-forbidden until: `{delivery.get('production_forbidden_until', 'UNKNOWN')}`\n"
            f"- Stage 2 stop gate: `{delivery.get('stage2_stop_gate', 'UNKNOWN')}`\n"
            f"- Stage 2 integrated accepted: `{stage2_accepted}`\n"
            f"- Next governance task: `{delivery.get('current_v7_task_id', 'UNKNOWN')}`\n"
            f"- Parallel shadow source task: `{delivery.get('parallel_shadow_source_task', 'UNKNOWN')}`\n"
        )
    return f"""# Project Governance Status

## Snapshot Metadata

- source_base_commit: `{assurance['source_base_commit']}`
- source_tree_hash: `{assurance['source_tree_hash']}`
- source_snapshot_hash: `{assurance['source_snapshot_hash']}`
- snapshot_event_time: `{assurance['snapshot_event_time']}`
- generator_version: `{GENERATOR_VERSION}`
- final_commit_binding: `{assurance['final_commit_binding']}`

## Current State

- Project: `{item['project_id']}`
- Path: `{item['path']}`
- Product version: `{item['product_version']}`
- Phase/Gate: `{item['current_phase']} / {item['current_gate']}`
- Models/Formulas/Parameters total: `{item['models']} / {counts['total_formulas']} / {counts['total_parameters']}`
- Active formulas/parameters: `{counts['active_formulas']} / {counts['active_parameters']}`
- Machine checked formulas/parameters: `{counts['checked_formulas']} / {counts['checked_parameters']}`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `{dims['structural_completeness']['status']}` | `{brief_list(dims['structural_completeness']['evidence_refs'])}` |
| implementation_congruence | `{dims['implementation_congruence']['status']}` | `{brief_list(dims['implementation_congruence']['evidence_refs'])}` |
| parameter_source_quality | `{dims['parameter_source_quality']['status']}` | `{brief_list(dims['parameter_source_quality']['evidence_refs'])}` |
| methodological_rationale | `{dims['methodological_rationale']['status']}` | `{brief_list(dims['methodological_rationale']['evidence_refs'])}` |
| empirical_validation | `{dims['empirical_validation']['status']}` | `{brief_list(dims['empirical_validation']['evidence_refs'])}` |
| operational_validation | `{dims['operational_validation']['status']}` | `{brief_list(dims['operational_validation']['evidence_refs'])}` |
| delivery_evidence | `{dims['delivery_evidence']['status']}` | `{brief_list(dims['delivery_evidence']['evidence_refs'])}` |
| evidence_freshness | `{dims['evidence_freshness']['status']}` | `{brief_list(dims['evidence_freshness']['evidence_refs'])}` |

## Delivery

- Readiness: `{assurance['delivery_readiness']['status']}`
- Release gate: `{assurance['delivery_readiness']['release_gate']}`
{v7_delivery_lines}- Next executable task: `{assurance['next_executable_task']['task_id']}`
- Pending/stale events: `{item['pending_event_count']}`
- Tree-bound events: `{item['event_binding_counts']['tree_bound_events']}`
- Commit-bound events: `{item['event_binding_counts']['commit_bound_events']}`
- Legacy unbound events: `{item['event_binding_counts']['legacy_unbound_events']}`
- Unresolved fact IDs: `{len(item['unresolved_fact_ids'])}`
"""


def render_owner_status(item: dict[str, Any]) -> str:
    assurance = item["assurance"]
    dims = assurance["dimensions"]
    counts = item["counts"]
    next_task = assurance["next_executable_task"]
    decision = assurance["owner_decision"]
    blockers = item["policy_blockers"][:3] or [decision["evidence_required"]]
    while len(blockers) < 3:
        blockers.append(f"{decision['human_owner_role']} must provide project-specific evidence before readiness can improve.")
    option_a = decision["option_a"]
    option_b = decision["option_b"]
    option_c = decision["option_c"]
    changed_summary = "Owner 视图现在把实现一致性、参数来源、方法依据、实证验证、运行验证、交付证据和证据新鲜度分开，避免把 `MACHINE_VERIFIED` 误读为模型有效或可上线。"
    if assurance["delivery_readiness"]["status"] == "VERIFIED" and item["project_id"] == "arxiv-daily-push":
        current_conclusion = (
            f"{item['project_id']} 当前治理结论：Stage 1 B1/arXiv 已达到 `ARXIV_PRODUCTION_ACCEPTED`，"
            "`ADP-S1P5T05` 已完成本机 Codex/local runner 与 2026-06-30 迁移准备；"
            "GitHub 只保留代码、PR/CI、证据、状态和备份角色，不作为每日生产 runner。"
        )
        if next_task["task_id"] == "ADP-S1P5T04-PRODUCTION-SCHEDULE-OWNER-DECISION-041":
            changed_summary = (
                "test10 已从 `main` 在 GitHub-hosted Ubuntu runner 上完成：run `28059194999` / run_number `10` "
                "证明邮件主题使用 Sydney 服务日期 `20260624`，Gmail SMTP 已发送到 `linzezhang35@gmail.com`。"
                "本次没有启用 production schedule、没有上传 Release、没有引入视频要求。"
            )
        elif next_task["task_id"] == "S2P1T01":
            changed_summary = (
                "`ADP-S1P5T05` 已把生产策略切到本机 Mac + Codex/local runner："
                "新增 local daily CLI、local preflight、queue/ledger/report/email preview 本地持久化、"
                "launchd package 草案和 2026-06-30 迁移 runbook。"
                "没有启用 GitHub cloud schedule、没有真实 SMTP 生产发送、没有 Release 上传、没有视频要求。"
            )
    else:
        current_conclusion = (
            f"{item['project_id']} 当前治理结论：实现一致性为 `{dims['implementation_congruence']['status']}`，"
            f"方法/实证为 `{dims['methodological_rationale']['status']}` / `{dims['empirical_validation']['status']}`，"
            f"交付状态为 `{assurance['delivery_readiness']['status']}`；这不是生产上线声明。"
        )
    return f"""# OWNER_STATUS

## 1. 当前结论

{current_conclusion}

## 2. 本次运行改变了什么

{changed_summary}

## 3. 为什么重要

{decision['expected_benefit']}

## 4. 需要人类决定什么

- decision_id: `{decision['decision_id']}`
- decision_question: {decision['decision_question']}
- human_owner_role: `{decision['human_owner_role']}`
- human_assignment_status: `{decision['human_assignment_status']}`

## 5. 默认建议

- current_recommendation: {decision['current_recommendation']}
- estimated_effort: {decision['estimated_effort']}
- estimated_cost_or_resource: {decision['estimated_cost_or_resource']}

## 6. 不决策后果

{decision['consequence_of_no_decision']}

## 7. 下一行动、责任角色和验收证据

- next_task_id: `{next_task['task_id']}`
- responsible_role: `{next_task['human_owner_role']}`
- acceptance_ids: `{brief_list([str(x) for x in next_task.get('acceptance_ids', [])])}`
- unblock_condition: {next_task['unblock_condition']}

## 8. 九层 Assurance 状态

- structural_completeness: `{dims['structural_completeness']['status']}`
- implementation_congruence: `{dims['implementation_congruence']['status']}` ({counts['checked_parameters']}/{counts['active_parameters']} active parameters, {counts['checked_formulas']}/{counts['active_formulas']} active formulas)
- parameter_source_quality: `{dims['parameter_source_quality']['status']}`
- methodological_rationale: `{dims['methodological_rationale']['status']}`
- empirical_validation: `{dims['empirical_validation']['status']}`
- operational_validation: `{dims['operational_validation']['status']}`
- delivery_evidence: `{dims['delivery_evidence']['status']}`
- evidence_freshness: `{dims['evidence_freshness']['status']}`
- delivery_readiness: `{assurance['delivery_readiness']['status']}`

## 9. A/B/C Choice Matrix

| Decision Item | Current Recommendation | Choice A | Choice B | Choice C | No Decision Consequence |
|---|---|---|---|---|---|
| `{decision['decision_id']}` | {decision['current_recommendation']} | {option_a} | {option_b} | {option_c} | {decision['consequence_of_no_decision']} |

## 10. Current Blockers

1. {blockers[0]}
2. {blockers[1]}
3. {blockers[2]}

## 11. Evidence Required To Unblock

- evidence_required: {decision['evidence_required']}
- principal_risks: {decision['principal_risks']}
- generated_from_refs: `{brief_list([str(x) for x in decision.get('generated_from_refs', [])])}`

## 12. Model Formula Parameter Change

- model_count: `{item['models']}`
- total_formulas: `{counts['total_formulas']}`
- active_formulas: `{counts['active_formulas']}`
- total_parameters: `{counts['total_parameters']}`
- active_parameters: `{counts['active_parameters']}`
- active_values_changed_by_this_view: `0`

## 13. Tests And Acceptance

- required_commands: `validate_project_governance --all --semantic --drift-report`; `generate_governance_dashboard --write`
- release_gate: `{assurance['delivery_readiness']['release_gate']}`

## 14. Evidence Freshness

- final_commit_binding: `{assurance['final_commit_binding']}`
- tree_bound_events: `{item['event_binding_counts']['tree_bound_events']}`
- commit_bound_events: `{item['event_binding_counts']['commit_bound_events']}`
- legacy_unbound_events: `{item['event_binding_counts']['legacy_unbound_events']}`
- precommit_pending_events: `{item['event_binding_counts']['precommit_pending_events']}`
- pending_or_stale_events: `{item['pending_event_count']}`

## 15. UNKNOWN

- unresolved_fact_ids: `{len(item['unresolved_fact_ids'])}`

## 16. 技术元数据

- source_base_commit: `{assurance['source_base_commit']}`
- source_tree_hash: `{assurance['source_tree_hash']}`
- source_snapshot_hash: `{assurance['source_snapshot_hash']}`
- snapshot_event_time: `{assurance['snapshot_event_time']}`
- generator_version: `{GENERATOR_VERSION}`
- version: `{item['product_version']}`
- phase/gate: `{item['current_phase']} / {item['current_gate']}`

## 17. Next Unique Task

- task_id: `{next_task['task_id']}`
- reason: {next_task['reason']}
"""


def render_binding_backlog(projects: list[dict[str, Any]], meta: dict[str, str]) -> str:
    payload = {
        "generated_by": "scripts/generate_governance_dashboard.py",
        "generator_version": GENERATOR_VERSION,
        "task_id": "GOV-REVIEW7-BINDING-BACKLOG-001",
        "source_base_commit": meta["source_base_commit"],
        "source_tree_hash": meta["source_tree_hash"],
        "source_snapshot_hash": meta["source_snapshot_hash"],
        "status": "open",
        "policy": "Legacy events are not rewritten. Future meaningful runs must be PRECOMMIT_TREE_BOUND before commit and commit-bound by CI attestation after merge.",
        "projects": [
            {
                "project_id": item["project_id"],
                "tree_bound_events": item["event_binding_counts"]["tree_bound_events"],
                "commit_bound_events": item["event_binding_counts"]["commit_bound_events"],
                "legacy_unbound_events": item["event_binding_counts"]["legacy_unbound_events"],
                "precommit_pending_events": item["event_binding_counts"]["precommit_pending_events"],
                "next_task": "GOV-REVIEW7-BINDING-BACKLOG-001"
                if item["event_binding_counts"]["legacy_unbound_events"]
                else "NOT_APPLICABLE",
            }
            for item in projects
        ],
    }
    return "\n".join(dump_yaml(payload)) + "\n"


ROOT_OUTPUT_REL_PATHS = [
    "README.md",
    "GOVERNANCE_DASHBOARD.md",
    "OWNER_PORTFOLIO.md",
    "governance/binding_backlog.yaml",
]


def select_projects(
    projects: list[dict[str, Any]], *, project_filter: str | None = None, changed_only: bool = False, base_ref: str | None = None
) -> tuple[list[dict[str, Any]], bool]:
    if project_filter:
        selected = [
            project
            for project in projects
            if project_filter in {str(project.get("project_id")), str(project.get("path"))}
        ]
        if not selected:
            raise SystemExit(f"Unknown project: {project_filter}")
        return selected, False
    if changed_only:
        changed = structural.git_changed_files(base_ref)
        selected = [project for project in projects if structural.project_matches_changed(project, changed)]
        include_root = any(path in changed for path in ROOT_OUTPUT_REL_PATHS)
        return selected, include_root
    return projects, True


def generate(
    write: bool,
    *,
    project_filter: str | None = None,
    changed_only: bool = False,
    base_ref: str | None = None,
    root_artifact_dir: Path | None = None,
) -> dict[str, Any]:
    config = structural.load_yaml(structural.PROJECTS_FILE)
    projects = [project for project in structural.as_list(config.get("projects")) if isinstance(project, dict)]
    selected_projects, include_root = select_projects(projects, project_filter=project_filter, changed_only=changed_only, base_ref=base_ref)
    infos = [load_project(project) for project in selected_projects]
    all_infos = [load_project(project) for project in projects] if include_root else infos
    portfolio_hash = source_snapshot_hash(
        [ROOT / "governance/projects.yaml"] + [ROOT / i["path"] / "docs/governance/parameter_registry.csv" for i in all_infos]
    )
    event_times = [info["assurance"]["snapshot_event_time"] for info in all_infos if info["assurance"]["snapshot_event_time"] != "UNKNOWN"]
    meta = {
        "source_base_commit": configured_source_base() or existing_root_base() or current_commit(),
        "source_tree_hash": configured_source_tree() or existing_root_tree() or current_tree_hash(),
        "source_snapshot_hash": portfolio_hash,
        "snapshot_event_time": max(event_times) if event_times else "UNKNOWN",
    }
    outputs: list[str] = []
    if include_root:
        root_outputs = {
            ROOT / "README.md": render_readme(all_infos, meta),
            ROOT / "GOVERNANCE_DASHBOARD.md": render_dashboard(all_infos, meta),
            ROOT / "OWNER_PORTFOLIO.md": render_owner_portfolio(all_infos, meta),
            ROOT / "governance" / "binding_backlog.yaml": render_binding_backlog(all_infos, meta),
        }
        for path, text in root_outputs.items():
            if write:
                target = root_artifact_dir / rel(path) if root_artifact_dir else path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            outputs.append(rel(path))
    for info in infos:
        base = ROOT / info["path"] / "docs/governance"
        assurance_path = base / "ASSURANCE_STATUS.yaml"
        assurance_text = "\n".join(dump_yaml(info["assurance"])) + "\n"
        status_path = base / "STATUS.md"
        owner_path = base / "OWNER_STATUS.md"
        if write:
            assurance_path.write_text(assurance_text, encoding="utf-8")
            status_path.write_text(render_status(info), encoding="utf-8")
            owner_path.write_text(render_owner_status(info), encoding="utf-8")
        outputs.extend([rel(assurance_path), rel(status_path), rel(owner_path)])
    return {
        "status": "PASS",
        "write": write,
        "source_base_commit": meta["source_base_commit"],
        "source_snapshot_hash": meta["source_snapshot_hash"],
        "snapshot_event_time": meta["snapshot_event_time"],
        "generator_version": GENERATOR_VERSION,
        "outputs": outputs,
        "root_output_mode": "artifact" if root_artifact_dir else "tracked",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated governance views.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="Generate all root and project governance views.")
    scope.add_argument("--project", help="Generate governance views for one project id or path.")
    scope.add_argument("--changed-only", action="store_true", help="Generate governance views for changed projects only.")
    parser.add_argument("--base-ref", help="Optional base ref for --changed-only.")
    parser.add_argument(
        "--root-artifact-dir",
        type=Path,
        help="Write root generated views under this artifact directory instead of the tracked repository root.",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            generate(
                args.write,
                project_filter=args.project,
                changed_only=args.changed_only,
                base_ref=args.base_ref,
                root_artifact_dir=args.root_artifact_dir,
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
