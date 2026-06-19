# 02 - Scope, Boundaries and Definitions

## 1. Default scope

### Research universe

- P0 30 家：MVP 深挖入口。
- P1 50 家：首轮网络扩展。
- P2 40 家：事件触发观察。
- X 20 个：与美国核心节点存在实质关系时展开的全球关键节点。

完整列表见 `data/research_universe.csv`。研究宇宙是入口，不是封闭世界；供应商、客户、基金、政府、设施和产品可按材料性扩展。

## 2. Product scope

P0 包含：用户首页、行业分类、Watchlist、公司焦点页、递归 reroot、八层商业地图、证据抽屉、路径、评分自定义、操作日志、14 天校准、SEC connector 和导出。

P0 不包含复杂权限、多租户、自动交易、全量全球贸易数据库或生产云 SLA。

## 3. Concept boundaries

| Concept | Definition | Must not be confused with |
|---|---|---|
| Legal entity | 可由注册、监管或公司文件识别的主体 | 品牌、产品、业务分部 |
| Corporate group | 所有权/控制构成的法律或会计集团 | 合作伙伴和供应链生态 |
| Business empire view | 集团、业务、供应链、资本、政策和战略的综合视图 | 新的法律控制事实 |
| Supply-chain relation | 商品、服务、设备、材料、能源或渠道依赖 | 股权控制 |
| Economic dependency | 具有收入、容量、切换成本或瓶颈意义的关系 | 法律所有权 |
| Capital event | 融资、债务、并购、合同、投资、回购、CapEx | 完整持续现金流 |
| Strategic signal | 多条证据的方向性聚合 | 股价或收益概率 |
| Focus entity | 当前用于组织所有视图的主体 | 永久 root 或唯一重要节点 |
| Reroot | 把关联节点设为新焦点并重建局部视图 | 无状态页面跳转 |

## 4. Recursion boundary

- 逻辑上可不断 reroot。
- 单次查询 hops <=2、nodes <=500、edges <=2000、path length <=8。
- 默认 1 hop、80 nodes；单次展开 40 nodes。
- 超出预算必须截断、分组或要求新工作区。
- 不得自动沿每条边继续爬取形成无限任务。

## 5. Disclosure and inference boundary

- 未披露为 unknown，不是 0 或不存在。
- 13F 是报告期持仓快照，不是实时资金流。
- 合同上限、义务额、支出额、投资承诺和已交割金额分开。
- 私企结构和融资只记录可验证公开事实。
- derived edge 必须保留输入和规则版本。
- 低于事实展示门槛的线索进入 research queue。

## 6. Scoring boundary

- 分数用于排序和聚焦。
- raw strategic score、evidence quality、adjusted score 分开。
- 用户可调整，但不得隐藏公式和缺失值。
- 校准不以短期股价表现优化。
- 调整 profile 不改变底层事实。

## 7. Expansion rule

实体/关系进入正式图的条件由 `docs/12` 和 `docs/17` 定义。核心原则：材料性、证据、时间、关系类型和预算共同决定，不因节点知名或视觉中心而自动纳入。


## v4.2 UI/UX 决策

MVP 默认采用 Watchlist 驱动的可视化研究工作台。独立行业卡片首页不属于批准方案。关系、上下游、业务板块、资本和政策结构首先以可视化表达；摘要、表格和证据作为解释与可访问替代。
