# EVA_OS Command Center 2026-06-07

## Summary
- System: `EVA_OS`
- Status: `ReadyForResearch`
- Reason: 核心证据闸门、报告证据和本地价值台账已闭合，可继续研究。
- Generated At: `2026-06-07T13:51:25`

## Scorecards
| metric | value | status | evidence |
| --- | --- | --- | --- |
| Daily Readiness | ReadyForResearch | Pass | gates=5 |
| Integration Audit | Pass | Pass | summary={'pass': 6, 'review': 0, 'fail': 0, 'item_count': 6} |
| Risk Gates | 8/8 Pass | Pass | DataTrust=Pass, IntegrationAudit=Pass, NoLiveTradingBoundary=Pass, ReportEvidence=Pass, LatestWordReport=Pass, EntityRegistry=Pass, WorkflowInputs=Pass, ResearchBusInterop=Pass |
| Token ROI Ledger | 180 | Pass | quantified=0; unquantified=180 |
| Latest Report | SampleBacktestReport_07062026.docx | Pass | /Users/linzezhang/Downloads/量化回测分析/2026-06-07/SampleBacktestReport_07062026.docx |

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
| P1 | Open | QuantLab | If using Moomoo real data, start Moomoo OpenD first; this system remains quote/research-only. | Daily Readiness |
| P1 | Open | QuantLab | Configure provider API keys only for the data sources you actually use; do not store keys in source code. | Daily Readiness |
| P1 | Open | QuantLab | Open the latest report from Report Center and check data quality, cross-source validation, and risk gates before using it. | Daily Readiness |
| P2 | Open | Value Layer | 为高价值产物补充真实节省时间、避免损失、复用价值或成本数据；未量化前 ROI 保持空值。 | Token ROI Ledger |

## Evidence Sources
| source | status | path | schema |
| --- | --- | --- | --- |
| Daily Readiness | Present | /Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance/data/systemAudit/QuantLabDailyReadiness_07062026.json | QuantLabDailyReadinessV1 |
| Integration Audit | Present | /Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance/data/systemAudit/QuantLabIntegrationAudit_07062026.json | QuantLabIntegrationAuditV1 |
| Data Trust Audit | Present | /Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance/data/systemAudit/QuantLabDataTrustAudit_07062026.json | QuantLabDataTrustAuditV1 |
| Token ROI Ledger | Present | data/value/EVATokenROILedger_latest.json | EVATokenROILedgerV1 |
| Latest Report | Present | /Users/linzezhang/Downloads/量化回测分析/2026-06-07/SampleBacktestReport_07062026.docx | Backtest Word Report |

## Token ROI Summary
| record_count | quantified_records | unquantified_records | roi_status |
| --- | --- | --- | --- |
| 180 | 0 | 180 | Unquantified |

## Assumptions
- 总控驾驶舱只聚合本地证据，不刷新行情、不启动 Moomoo OpenD、不修改持仓、不连接实盘。
- 所有输入必须进入证据层；没有证据的结论降级为观察或待复核。
- 所有结论必须经过风控层；Blocked 或 NeedsReview 不应作为交易前参考。
- 所有产出必须进入 Token ROI 台账；没有真实金额输入时不伪造收益、节省成本或 ROI。
- Research-only boundary remains active: no live trading, no real orders, no payments, no betting execution.
