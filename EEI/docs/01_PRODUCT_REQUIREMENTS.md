# 01 - Product Requirements Document

## 1. Product statement

构建一个面向美国大型企业及其全球关键依赖的公开证据研究平台。用户从行业、Watchlist、搜索或最近路径进入任意公司，以该公司为主体查看商业帝国、集团和业务板块、完整供应链、所有权治理、资本与并购、技术与商业依赖、政策暴露和战略信号；点击任何关联节点后可把它设为新主体继续同样的分析。

## 2. Default recommendation

首页默认采用：

1. 行业入口；
2. Watchlist；
3. 全局搜索；
4. 最近探索路径；
5. 重要变化与数据新鲜度。

不使用全局网络图作为首页。网络图只在用户确定行业或焦点后出现，并默认局部加载。

## 3. Primary users

| Persona | Job to be done | Current failure | MVP outcome |
|---|---|---|---|
| 个人/投资研究者 | 理解企业真实业务、依赖和资本方向 | 信息散落、关系类型混淆 | 在 10 分钟内形成带证据的公司版图 |
| 产业分析者 | 从公司递归追踪供应链和跨行业控制点 | 只能读静态行业报告 | 连续 reroot 并比较每个节点的上下游和政策 |
| 调研编辑/知识管理者 | 保存、复核和更新事实 | 链接失效、结论无出处 | 每条边有来源、时间、状态和版本 |
| 数据工程维护者 | 稳定更新、发现变化和校准模型 | 脚本不可重复、模型黑盒 | 幂等采集、日志、校准和回滚 |

## 4. P0 user outcomes

1. 首页按行业或 Watchlist 找到研究对象。
2. 从行业页三次主要操作内进入公司焦点页。
3. 公司页以人类可读摘要回答业务、关键上下游、资金、控制、政策、战略和数据缺口。
4. 在集团业务、供应链、所有权治理、资本并购、商业技术依赖、政策政府、战略信号、时间变化八层间切换。
5. 点击任意可聚焦节点执行 reroot，并连续完成至少三次。
6. reroot 后继承时间、layers、filters 和 scoring profile；breadcrumb、back/forward、URL 可恢复。
7. 上下游、控制、资本、政策和瓶颈路径可查询，并逐边展示证据。
8. 使用默认评分或克隆自定义 profile；公式、输入、缺失值和时间衰减可见。
9. 修改 profile 前 preview，保存后可激活、回滚和恢复默认。
10. 操作日志记录 old/new/diff/reason/version。
11. 每 14 天生成校准报告，建议不自动激活。
12. 导出当前研究范围的实体、关系、事件、分数、路径和 provenance。

## 5. P1 outcomes

- 两实体并排比较；
- 保存工作区和研究路径；
- 人工审核候选边；
- 更多来源连接器；
- 主题订阅和告警；
- 设施级全球贸易/能源网络。

## 6. Product principles

- 证据优先；
- 时间优先；
- 关系层级分离；
- 未知和冲突显式；
- 递归探索、单次有界；
- 默认可用、高级可调；
- 评分可解释、可版本化、可回滚；
- 来源决定更新频率；
- 任何结论都不替代投资判断。

## 7. Research universe

- P0 深挖：30 个。
- P1 扩展：50 个。
- P2 观察：40 个。
- 全球外部关键节点：20 个。

具体对象、来源、指标和筛选门槛见 `docs/12_RESEARCH_UNIVERSE_SOURCE_METRICS_SCREENING.md` 和 `data/research_universe.csv`。

## 8. Success metrics

| Metric | MVP target |
|---|---:|
| P0 seed entities loaded | 30 |
| Total research universe represented | 140 |
| P0 company focal pages available | 30 fixtures/seed records; live depth varies by source |
| Published relationship evidence coverage | 100% |
| Three consecutive reroot E2E | PASS |
| URL/back/breadcrumb state restoration | 100% tested scenarios |
| Custom profile preview/save/activate/rollback | PASS |
| Profile weight validation | 100% invalid cases rejected |
| Operation log coverage for configurable actions | 100% |
| Calibration cadence | exactly 14 days |
| Entity resolution precision | >=95% on gold sample |
| Relationship precision | >=90% on gold sample |
| Graph initial render | <=2s at 300 nodes/1000 edges in recorded environment |
| Common filter/reroot response | <=250ms server fixture target, excluding layout |

## 9. Out of scope

- 自动交易、价格目标、收益保证；
- 订单流或实时机构仓位；
- 非公开或违规数据；
- 复杂权限、多租户和付费体系；
- 无预算全图；
- 未经复核的 LLM 事实写入。


## v4.2 UI/UX 决策

MVP 默认采用 Watchlist 驱动的可视化研究工作台。独立行业卡片首页不属于批准方案。关系、上下游、业务板块、资本和政策结构首先以可视化表达；摘要、表格和证据作为解释与可访问替代。
