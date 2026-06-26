# PFI OS Information Architecture

Version: PFI V0.2 Stage 0 compatibility baseline

## L1 Workspaces

PFI V0.2 target product navigation is fixed to exactly eight first-level
entries:

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与同步
7. 建议与复盘
8. 报告与洞察

The current Web Shell still exposes exactly six compatibility workspaces until
the Stage 1 UI migration is implemented:

1. 首页
2. 市场
3. 研究
4. 持仓
5. 策略实验室
6. 数据与系统

PFI V0.2 Stage 0 keeps every current entry accessible and maps it into the
eight-entry target model. The compatibility source of truth is
`docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md`.

Do not add Assistant, notifications, task center, global search, evidence
viewer, settings, ResearchBus, workers, model versions, report center, cost
accounting, cashflow, consumption, Alpha, system/development, or any rejected
Alpha variant as primary navigation items.


## V0.2 Compatibility Mapping

| Current compatibility workspace | V0.2 target entry |
| --- | --- |
| 首页 | 首页总览 |
| 市场 | 投资管理 > 市场观察 |
| 研究 | 报告与洞察 |
| 持仓 | 账户与资产 / 投资管理 |
| 策略实验室 | 投资管理 > 策略实验室 |
| 数据与系统 | 数据源与同步 |

`PFI/大数据模拟器` and any `qbvs/` runtime found in another checkout must remain
accessible and map to `投资管理 > 策略实验室 / 大数据模拟器`.


## L2 Structure

### 首页

- 今日简报
- 待处理事项
- 持仓异动
- 市场与政策事件
- 最近研究
- 最近策略运行
- 数据新鲜度与阻塞

### 市场

- 大盘概览
- 热度与情绪
- 行业与主题
- 事件与催化
- 市场宽度与资金代理
- 自选监控

### 研究

- 全局研究搜索
- 公司与股票
- 基金与 ETF
- 行业与主题
- 政策与政府文件
- 预测与估值
- 研究库与证据

### 持仓

- 组合总览
- 收益与归因
- 风险与暴露
- 行为与纪律
- 优化与情景
- 决策队列
- 导入与对账

### 策略实验室

- 回测
- 参数扫描
- 多资产与轮动
- 模拟
- 策略注册
- 训练模式
- 实验与验证

Market-feel training lives under 训练模式. It is not a top-level workspace.
Strategy backtesting, parameter scan, walk-forward validation, robustness
checks, strategy registry, and simulation belong here.

### 数据与系统

- 数据源
- 抓取与任务
- 数据质量与血缘
- 模型与 Agent
- 隐私与备份
- 系统诊断
- 设置

ResearchBus is an internal event/workflow compatibility layer surfaced only as
diagnostics or lineage when needed.

## L3 Page Contract

Major task pages use this page frame:

1. 结论 / Snapshot
2. 分析 / Explore
3. 证据 / Evidence
4. 模拟 / Simulate
5. 保存与行动 / Save & Act
6. 历史 / History

Ordinary users see Snapshot, Explore, and Evidence by default. Raw parameters,
developer terms, model details, and bus/workflow internals belong in collapsible
areas or a right-side evidence drawer.

## Global Context

PFI OS preserves these values across page switches:

- current market
- current security, fund, industry, or policy entity
- current portfolio
- as-of time
- currency
- data freshness
- current research task
- current evidence set
- current simulation scenario
