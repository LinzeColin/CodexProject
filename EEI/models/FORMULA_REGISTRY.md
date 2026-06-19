# Formula Registry v4.2

本文件是 11 个正式公式的快速索引。完整方程、缺失值策略和默认门槛以 `data/formula_registry.csv` 为机器单一事实来源；可执行参数位于 `config/`，字段约束位于 `specs/model_config_schema.json`。

| Formula ID | Name | Output | Main use |
|---|---|---:|---|
| F-EQ-001 | Evidence Quality | 0-100 | 证据可信度、发布门槛与排序修正 |
| F-RF-001 | Recency Factor | 0-1 | 按事实/事件类型进行时间衰减 |
| F-NP-001 | Node Priority | 0-100 | 节点排名、大小、路径与 Watchlist 优先级 |
| F-EM-001 | Edge Materiality | 0-100 | 关系显示、宽度、聚合与 Top-N |
| F-SC-001 | Supply Chain Criticality | 0-100 | 上游瓶颈、替代性和关键路径 |
| F-CI-001 | Control Influence | 0-100 | 经济权益、投票权、任命权与特殊权利 |
| F-CM-001 | Capital Momentum | 0-100 | 资本开支、融资、并购与长期承诺 |
| F-PE-001 | Policy Exposure | 0-100 | 政府合同、补贴、监管、出口和司法辖区 |
| F-SS-001 | Strategic Signal | 0-100 | 战略主题、趋势信号与反证研究 |
| F-AS-001 | Alert Score | 0-100 | 变化事件与 Watchlist 告警优先级 |
| F-DR-001 | Dependency Risk | 0-100 | 跨供应链、技术、商业和政策依赖风险 |

战略依赖和技术依赖是综合优先级/依赖风险的输入组件，不在 v4.2 中重复登记为独立公式。完整定义见 `docs/24_MODEL_FORMULA_PARAMETER_THRESHOLD_CENTER.md`。
