# 15 - 评分模型、公式公开与用户可调参数

## 1. 设计结论

系统提供默认评分，但评分不是黑盒结论。用户必须能够：

1. 查看每个分数的公式、输入字段、归一化、缺失值处理、时间衰减和规则版本；
2. 使用默认 profile；
3. 克隆并修改权重、阈值和时间半衰期；
4. 在保存前预览对节点排序、路径和告警的影响；
5. 保存版本、写变更原因、比较、回滚和恢复默认；
6. 查看操作日志和两周校准报告。

评分只用于排序、聚焦和形成研究假设，不代表投资收益概率。

## 2. 分数分层

### 2.1 原始事实与指标

直接来自证据或可复核计算，例如供应商集中度、合同期限、披露金额、关系年龄、来源等级。

### 2.2 组件分数（0-100）

- `supply_chain_criticality`
- `strategic_dependency`
- `capital_momentum`
- `ownership_control_influence`
- `policy_exposure`
- `technology_data_dependency`
- `time_relevance`
- `evidence_quality`

### 2.3 综合排序分数

默认 Balanced profile：

```text
raw_priority =
  0.28 * supply_chain_criticality
+ 0.20 * strategic_dependency
+ 0.16 * capital_momentum
+ 0.12 * ownership_control_influence
+ 0.10 * policy_exposure
+ 0.08 * technology_data_dependency
+ 0.06 * time_relevance
```

证据质量不直接与战略含义混为一体。UI 同时显示：

```text
raw_priority
quality_factor = 0.50 + 0.50 * evidence_quality / 100
adjusted_priority = raw_priority * quality_factor
```

默认排序使用 `adjusted_priority`，但用户可切换查看 raw 与 quality。低证据关系不能仅靠高原始分数占据首位。

## 3. 组件示例公式

### 3.1 供应链关键性

```text
SC = 0.25*bottleneck
   + 0.20*(100-substitutability)
   + 0.18*concentration
   + 0.12*lead_time_risk
   + 0.10*capacity_scarcity
   + 0.08*geographic_risk
   + 0.07*operational_materiality
```

所有输入归一化为 0-100。缺失值不得默认为 0；按可见输入重新归一化，并显示 coverage。

### 3.2 战略依赖

```text
SD = 0.25*revenue_or_volume_exposure
   + 0.20*switching_cost
   + 0.15*technical_uniqueness
   + 0.12*exclusivity
   + 0.10*contract_duration
   + 0.10*customer_or_supplier_concentration
   + 0.08*operational_coupling
```

### 3.3 资本动量

```text
CM = 0.24*capex_signal
   + 0.20*investment_and_mna
   + 0.18*contract_commitment
   + 0.14*financing_activity
   + 0.10*capacity_expansion
   + 0.08*event_acceleration
   + 0.06*source_diversity
```

不同 `amount_kind` 分桶标准化，不得直接求和。金额缺失的事件可贡献事件强度，但不能贡献金额强度。

### 3.4 所有权与控制影响

```text
OC = 0.30*voting_control
   + 0.22*economic_interest
   + 0.18*board_appointment_power
   + 0.12*veto_or_special_rights
   + 0.10*control_chain_strength
   + 0.08*governance_persistence
```

### 3.5 政策暴露

```text
PE = 0.22*government_contract_or_grant
   + 0.20*regulatory_intensity
   + 0.18*export_trade_restriction
   + 0.14*industrial_policy_dependency
   + 0.10*jurisdiction_concentration
   + 0.08*lobbying_activity
   + 0.08*litigation_or_approval_risk
```

## 4. 时间衰减

默认指数半衰期：

```text
recency_factor = exp(-ln(2) * age_days / half_life_days)
```

默认半衰期：

| 信息类型 | 默认半衰期 |
|---|---:|
| 重大并购/控制变化 | 730 天 |
| 长期供应/容量合同 | 540 天 |
| 资本开支/融资 | 365 天 |
| 政策/监管事件 | 270 天 |
| 产品/合作公告 | 180 天 |
| 新闻线索/候选关系 | 90 天 |
| 价格或短期市场数据 | 非 MVP |

用户可按 profile 调整 30-1825 天；0 或负值非法。

## 5. 证据质量

```text
EQ = 0.30*source_authority
   + 0.20*source_independence
   + 0.15*locator_precision
   + 0.15*temporal_fit
   + 0.10*cross_source_confirmation
   + 0.10*entity_resolution_quality
```

冲突不通过降低 EQ 隐藏；`disputed` 必须单独显示并触发 contradiction penalty 或人工复核。

## 6. 默认 profiles

| Profile | 目的 | 主要变化 |
|---|---|---|
| Balanced | 通用探索 | 使用默认综合权重 |
| Supply Chain | 找瓶颈与关键上游 | SC 45%，SD 25% |
| Capital | 找资金与扩张方向 | CM 45%，OC 15% |
| Control | 查集团和权力链 | OC 50%，SD 20% |
| Policy | 查政策/政府影响 | PE 45%，SC 15% |
| Fresh Signals | 看近期变化 | time_relevance 25%，CM 30% |
| Custom | 用户定义 | 必须版本化和可回滚 |

## 7. 参数约束

- 综合权重必须合计 1.0，容差 0.0001；
- 单一权重范围 0-0.70，避免一个维度完全垄断；
- 组件内部权重合计 1.0；
- 阈值、半衰期和归一化方法有 schema 校验；
- 缺失值策略仅允许 `renormalize_available`、`mark_unscored`、`conservative_penalty`；默认第一种并显示 coverage；
- 任何公式变化生成新 model version，不能覆盖历史结果。

## 8. 用户配置流程

1. 打开“模型与排序”；
2. 查看当前公式、输入和解释；
3. 克隆默认 profile；
4. 使用滑块/数字输入调整；
5. 实时显示权重总和和非法项；
6. 预览 Top-N、节点大小和告警变化；
7. 输入简短原因并保存；
8. profile 生成新版本并激活；
9. 操作日志写入 old/new diff；
10. 可一键回滚或恢复默认。

## 9. API/数据要求

- `GET /v1/scoring/models`
- `GET /v1/scoring/models/{id}`
- `GET /v1/scoring/profiles`
- `POST /v1/scoring/profiles`
- `POST /v1/scoring/preview`
- `POST /v1/scoring/profiles/{id}/activate`
- `POST /v1/scoring/profiles/{id}/rollback`
- `GET /v1/scoring/explain/{objectType}/{objectId}`

解释接口返回输入值、来源、缺失项、归一化、每项贡献、raw/quality/adjusted、model/profile version。

## 10. 验收

- 默认 profile 可用且无需配置；
- 公式和所有输入对用户可见；
- 用户可以保存至少两个自定义 profile；
- 非法总权重不能保存；
- preview 不写入正式结果；
- 保存后日志包含 old/new/reason/timestamp/version；
- 切换 profile 后同一 graph query 可复现排序；
- 历史 score result 可按 model/profile version 重现；
- 未知输入不被当作 0；
- UI 不使用“上涨概率”“收益概率”等语言。
