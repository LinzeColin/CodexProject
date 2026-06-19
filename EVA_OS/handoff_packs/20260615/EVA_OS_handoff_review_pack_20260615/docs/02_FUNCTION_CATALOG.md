# EVA_OS 功能清单

## System Overview

EVA_OS 是主系统身份，QuantLab 是当前主要可操作入口。系统由 9 个规划子系统和若干共享底座组成。

## Main Subsystems

| No. | Subsystem | Chinese Name | Current State | Primary Artifacts |
| --- | --- | --- | --- | --- |
| 01 | Executive Command Center | 总控驾驶舱 | Partial product | `src/quantlab/executive/command_center.py`, `data/commandCenter/*latest*` |
| 02 | Token ROI Ledger | Token经济转化台账 | Partial product | `src/quantlab/value/token_roi.py`, `data/value/*latest*` |
| 03 | Company CashFlow Command | 公司经营现金流系统 | Partial product | `src/quantlab/business/cashflow.py`, `docs/CompanyCashFlowCommand.md` |
| 04 | QuantLab | 量化研究与回测系统 | Usable core | `src/quantlab/backtest`, `src/quantlab/strategies`, Streamlit app |
| 05 | Policy Intelligence Radar | 政策机会情报系统 | Partial product | `src/quantlab/policy/radar.py`, `data/policy/*latest*` |
| 06 | Consumption Guard | 个人消费止血系统 | Partial product | `src/quantlab/consumption/guard.py`, `data/consumption/*latest*` |
| 07 | AI Research Engine | AI行业研究系统 | Planned / partially represented | Docs and research report paths |
| 08 | Sports Market Lab | 赛事市场分析系统 | Planned / external adjacent | Open questions mention future calibration/reporting |
| 09 | CodexForge Factory | Codex工程交付工厂 | Planned / workflow layer | Task packs, handoff, packaging conventions |

## Shared Foundation Layers

| Layer | Purpose | Current Implementation |
| --- | --- | --- |
| Evidence Layer | Track evidence, source, freshness, and limitation | Docs and generated artifacts use evidence levels |
| Data Layer | Normalize and record data quality | Data providers, data quality reports, data lake manifest |
| Market Event Layer | Convert OHLCV bars into deterministic events | `MarketEventLog_latest.*` |
| Reproducible Data Lake | Register immutable local data assets | `DataLakeManifest_latest.*` |
| Event Replay | Feed deterministic replay batches to future research engines | `EventReplay_latest.*` |
| Decision Layer | Downgrade conclusions when evidence is missing | Command Center and report decision support |
| Engineering Layer | Scripts, tests, docs, handoff, repeatable checks | `scripts/**`, `tests/**`, `HANDOFF.md` |
| Value Layer | Register outputs into Token ROI | `EVATokenROILedger_latest.*` |

## Current User-Facing Functions

| Function | What It Does | User Benefit |
| --- | --- | --- |
| macOS app launcher | Opens EVA_OS from Desktop, Downloads, or Applications | Faster daily access |
| Streamlit QuantLab app | Provides research, backtest, holdings, reports, profile, workbench views | Main interactive experience |
| Single-symbol backtest | Runs strategy tests on selected market data | Strategy exploration |
| Parameter scan | Compares strategy parameter ranges | Research efficiency |
| Strategy library | Maintains strategy templates and categories | Repeatable experiments |
| Report center | Finds and reads generated Word/PDF/Markdown reports | Decision traceability |
| Data provider checks | Supports sample, Yahoo, AKShare, TuShare, Alpha Vantage, Polygon paths | Data flexibility |
| Data quality and cross-source validation | Checks freshness and agreement across sources | Lower false-confidence risk |
| Research bus | Shares local artifacts and messages across systems | Future multi-system orchestration |
| 52ETF reference integration | Initial read-only reference path | External ETF context |

## Current Generated Latest Artifacts

| Artifact Family | Latest Files |
| --- | --- |
| Command Center | `data/commandCenter/EVACommandCenter_latest.json/md/pdf` |
| Token ROI | `data/value/EVATokenROILedger_latest.json/csv/md/pdf` |
| Policy Radar | `data/policy/PolicyIntelligenceRadar_latest.json/csv/md/pdf` |
| Consumption Guard | `data/consumption/ConsumptionGuard_latest.json/csv/md/pdf` |
| Report Decision Support | `data/reportDecision/ReportDecisionSupportIndex_latest.json/csv/md/pdf` |
| Report Gap Tasks | `data/reportDecision/ReportEvidenceGapTasks_latest.json/csv/md/pdf` |
| Market Events | `data/marketEvents/MarketEventLog_latest.json/jsonl/csv/md` |
| Data Lake | `data/dataLake/DataLakeManifest_latest.json/md/assets.csv/replay_cursors.json` |
| Event Replay | `data/replay/EventReplay_latest.json/csv/md` |
| Validation Queue | `data/validationQueue/*latest*` |

## Explicit Non-Functions

EVA_OS currently does not do these things:

- No autonomous real-money trading.
- No real broker order placement.
- No automatic betting.
- No automatic payments, tax filings, or government submissions.
- No storing brokerage passwords or secrets in source.
- No guarantee that generated research is investment advice.
- No claim that all external data provider paths are currently authenticated or live-validated.
