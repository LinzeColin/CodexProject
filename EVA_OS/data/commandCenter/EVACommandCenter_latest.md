# EVA_OS Command Center 2026-06-13

## Summary
- System: `EVA_OS`
- Status: `NeedsReview`
- Reason: 需要复核：Company CashFlow Command, Policy Intelligence Radar, Consumption Guard
- Generated At: `2026-06-13T16:33:21`

## Scorecards
| metric | value | status | evidence |
| --- | --- | --- | --- |
| Daily Readiness | ReadyForResearch | Pass | gates=5 |
| Integration Audit | Pass | Pass | summary={'pass': 6, 'review': 0, 'fail': 0, 'item_count': 6} |
| Risk Gates | 8/8 Pass | Pass | DataTrust=Pass, IntegrationAudit=Pass, NoLiveTradingBoundary=Pass, ReportEvidence=Pass, LatestWordReport=Pass, EntityRegistry=Pass, WorkflowInputs=Pass, ResearchBusInterop=Pass |
| Token ROI Ledger | 178 | Pass | quantified=0; unquantified=178 |
| Latest Report | SampleBacktestReport_07062026.docx | Pass | /Users/linzezhang/Downloads/量化回测分析/2026-06-07/SampleBacktestReport_07062026.docx |
| Company CashFlow Command | MissingBalance | Review | balance=None; net=0.0; runway_days=None; pending=0; missing_evidence=0 |
| Policy Intelligence Radar | MissingPolicyEvidence | Review | opportunities=0; actionable=0; watch=0; pending=0; missing_evidence=0 |
| Consumption Guard | MissingConsumptionEvidence | Review | spend=0.0; impulse=0.0; fixed=0.0; pressure=None; pending=0; missing_evidence=0 |

## Risk Gates
| gate | status | evidence | next_action |
| --- | --- | --- | --- |
| DataTrust | Pass | audit_status=Pass; review=0; rejected=0 | Keep evidence audit clean before using research outputs. |
| IntegrationAudit | Pass | summary={'pass': 6, 'review': 0, 'fail': 0, 'item_count': 6} | Run scripts/auditQuantLabIntegration.sh --no-write if not Pass. |
| NoLiveTradingBoundary | Pass | No live order path must remain enforced. | Remove or fail closed any real-order code path. |
| ReportEvidence | Pass | run_metadata=31; report_evidence_layer=Pass | Generate a report with RunMetadata before using results. |
| LatestWordReport | Pass | /Users/linzezhang/Downloads/量化回测分析/2026-06-07/SampleBacktestReport_07062026.docx | Generate at least one Word report for the current research session. |
| EntityRegistry | Pass | Entity Registry schema=QuantLabEntityRegistryV1; records=28. | 确认 ProxyMapped 和 MissingSymbol 的报告口径。 |
| WorkflowInputs | Pass | Workflow inputs are queryable; rows=3. | 新报告应引用 workflow_input_id 或明确标注 ManualOrLocalOnly。 |
| ResearchBusInterop | Pass | ResearchBus interoperability status=Pass. | 继续保持跨系统同步审计。 |

## Action Queue
| priority | status | owner | action | source |
| --- | --- | --- | --- | --- |
| P1 | Open | QuantLab | Configure provider API keys only for the data sources you actually use; do not store keys in source code. | Daily Readiness |
| P1 | Open | QuantLab | Open the latest report from Report Center and check data quality, cross-source validation, and risk gates before using it. | Daily Readiness |
| P2 | Open | Value Layer | 为高价值产物补充真实节省时间、避免损失、复用价值或成本数据；未量化前 ROI 保持空值。 | Token ROI Ledger |
| P0 | Open | Company CashFlow Command | 录入并复核最新公司现金余额 BalanceSnapshot，附上可复核证据。 | Company CashFlow Command: BalanceSnapshot |
| P0 | Open | Policy Intelligence Radar | 录入至少一条政策机会，并附上官方、监管或政府来源证据。 | Policy Intelligence Radar: Policy Evidence |
| P0 | Open | Consumption Guard | 录入至少一条消费事件，并附上账单、截图、导出 CSV 或可复核说明。 | Consumption Guard: Consumption Evidence |

## Evidence Sources
| source | status | path | schema |
| --- | --- | --- | --- |
| Daily Readiness | Present | /Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/data/systemAudit/QuantLabDailyReadiness_07062026.json | QuantLabDailyReadinessV1 |
| Integration Audit | Present | /Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/data/systemAudit/QuantLabIntegrationAudit_07062026.json | QuantLabIntegrationAuditV1 |
| Data Trust Audit | Present | /Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/data/systemAudit/QuantLabDataTrustAudit_07062026.json | QuantLabDataTrustAuditV1 |
| Token ROI Ledger | Present | data/value/EVATokenROILedger_latest.json | EVATokenROILedgerV1 |
| Latest Report | Present | /Users/linzezhang/Downloads/量化回测分析/2026-06-07/SampleBacktestReport_07062026.docx | Backtest Word Report |
| Company CashFlow Command | Missing | /Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/data/cashflow/CompanyCashFlowCommand_latest.json | EVAOSCompanyCashFlowCommandV1 |
| Policy Intelligence Radar | Present | data/policy/PolicyIntelligenceRadar_latest.json | EVAOSPolicyIntelligenceRadarV1 |
| Consumption Guard | Present | data/consumption/ConsumptionGuard_latest.json | EVAOSConsumptionGuardV1 |

## Token ROI Summary
| record_count | quantified_records | unquantified_records | roi_status |
| --- | --- | --- | --- |
| 178 | 0 | 178 | Unquantified |

## Business Systems Summary
| subsystem | status | metric | value | evidence |
| --- | --- | --- | --- | --- |
| Company CashFlow Command | Review | cashflow_status | MissingBalance | balance=None; net=0.0; runway_days=None; pending=0; missing_evidence=0 |
| Policy Intelligence Radar | Review | policy_status | MissingPolicyEvidence | opportunities=0; actionable=0; watch=0; pending=0; missing_evidence=0 |
| Consumption Guard | Review | guard_status | MissingConsumptionEvidence | spend=0.0; impulse=0.0; fixed=0.0; pressure=None; pending=0; missing_evidence=0 |

## Assumptions
- 总控驾驶舱只聚合本地证据，不刷新行情、不启动 Moomoo OpenD、不修改持仓、不连接实盘。
- 所有输入必须进入证据层；没有证据的结论降级为观察或待复核。
- 所有结论必须经过风控层；Blocked 或 NeedsReview 不应作为交易前参考。
- 所有产出必须进入 Token ROI 台账；没有真实金额输入时不伪造收益、节省成本或 ROI。
- CashFlow、Policy、Consumption 只读取本地 latest 快照或 fail-closed fallback，不连接银行、支付、政府平台、支付宝、税务、工资或券商系统。
- Research-only boundary remains active: no live trading, no real orders, no payments, no betting execution.
