# PFI Feature Disposition

Version: PFI-001

PFI OS keeps only capabilities that support investment research, portfolio
understanding, strategy validation, evidence, or system reliability.

| Legacy capability | Decision | PFI destination | Notes |
| --- | --- | --- | --- |
| Executive command center | Rebuild | 首页 | Rebuild around daily brief, blockers, holdings impact, market/policy events, data freshness, and task status. |
| Company cashflow command | Drop from MVP | None | Do not expose as an active PFI product surface. |
| Policy radar | Rebuild | 研究 -> 政策与政府文件 | Use official sources, versions, clauses, impact map, and evidence. |
| Consumption guard | Drop | None | Keep only investment-behavior methods if directly relevant to discipline. |
| Single-symbol backtest | Keep kernel, rebuild UI | 策略实验室 -> 回测 | Must pass regression tests and reproduce data/cost/version metadata. |
| Sentiment analysis | Merge/rebuild | 市场 -> 热度与情绪 | Merge with hotspots, breadth, catalysts, and holdings impact. |
| Hotspot analysis | Merge/rebuild | 市场 -> 热度与情绪 | No independent primary page. |
| Market-feel training | Keep and rebuild | 策略实验室 -> 训练模式 | Required by user. Must hide future data and record review outcome. |
| Holdings | Rebuild | 持仓 | Use operational store, event ledger, attribution, risk, and optimization. |
| Personal profile | Merge/rebuild | 持仓 -> 行为与纪律 | Keep investment behavior only. |
| Portfolio rotation | Split/reuse | 持仓优化 + 策略实验室 | Portfolio risk belongs to holdings; validation belongs to Strategy Lab. |
| Report center | Merge/rebuild | 研究 -> 研究库与证据 | Reports are evidence objects, not a separate product. |
| Industry research reports | Merge/rebuild | 研究 | Company, fund, industry, and policy evidence share one research model. |
| ResearchBus page | Delete user entrance | Internal workflow/event layer | Not a second product or official fact source. |
| ResearchBus data ability | Merge | PFI workflow and event layer | Formal facts move to operational and analytical stores. |
| Big-data simulation | Defer | 策略实验室 -> 高级模拟 | Not MVP unless verified and scoped. |
| Parameter scan | Keep kernel, rebuild UI | 策略实验室 | Connect to stability, train/test, and walk-forward validation. |
| Strategy library | Rebuild | 策略实验室 -> 策略注册 | Version, parameters, applicability, stop conditions, review status. |
| Data center | Rebuild | 数据与系统 | User-facing sources, jobs, quality, privacy, backup, diagnostics. |
| External subsystem orchestration | Drop by default | Optional adapter | Only keep adapters that fit PFI contracts. |
| 52ETF reference | Optional adapter | 数据源 | Not an MVP hard dependency or trading evidence. |

## PFI-001 Guardrails

- Do not rename packages or directories in PFI-001.
- Do not build the new Web Shell in PFI-001.
- Do not preserve a legacy feature unless it passes PFI relevance, data
  boundary, testability, and maintenance gates.
