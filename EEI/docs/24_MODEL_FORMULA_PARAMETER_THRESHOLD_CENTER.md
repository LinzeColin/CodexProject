# 24 - 模型、公式、参数、门槛与自定义中心

## 1. 结论

系统采用“**默认可用、公式透明、参数可调、影响可预览、版本可回滚**”的模型中心。Markdown 文档用于解释；真正可执行的配置由 `config/model_profiles/*.json`、`config/thresholds/*.json` 和 JSON Schema 管理。用户既可以在线修改，也可以编辑机器可读配置后导入。

任何参数修改都不得直接覆盖历史版本。

## 2. 模型分层

```text
公开证据与事实
  -> 标准化指标（0-100）
  -> 组件分数
  -> 关系重要性 / 节点战略优先级 / 事件告警分
  -> 证据质量与覆盖修正
  -> 图谱排序、节点大小、边宽、告警和聚合
```

### 2.1 证据质量

```text
EQ = 0.28*source_authority
   + 0.18*locator_precision
   + 0.14*temporal_fit
   + 0.16*cross_source_confirmation
   + 0.12*source_independence
   + 0.12*entity_resolution_quality
```

### 2.2 时间衰减

```text
RF = exp(-ln(2) * age_days / half_life_days)
```

半衰期按事件类型配置，不允许用一个统一时效处理并购、长期合同和短期新闻线索。

### 2.3 节点商业版图优先级

```text
RawPriority =
    w_sc * SupplyChainCriticality
  + w_sd * StrategicDependency
  + w_cm * CapitalMomentum
  + w_ci * ControlInfluence
  + w_pe * PolicyExposure
  + w_td * TechnologyDependency
  + w_ss * StrategicSignal
  + w_tr * TimeRelevance

QualityFactor  = 0.45 + 0.55 * EQ/100
CoverageFactor = 0.65 + 0.35 * Coverage/100
AdjustedPriority = RawPriority * QualityFactor * CoverageFactor
```

默认权重见 `config/model_profiles/balanced-v2.json`。权重必须合计 1.0。

### 2.4 关系重要性

```text
EdgeMateriality =
    0.35*relationship_strength
  + 0.25*strategic_dependency
  + 0.20*transaction_materiality
  + 0.10*evidence_quality
  + 0.10*time_relevance
```

关系在图上是否显示由 `EdgeMateriality`、证据门槛、当前视角和图预算共同决定。

### 2.5 战略信号

```text
StrategicSignal =
    0.28*capex_acceleration
  + 0.20*investment_and_mna
  + 0.18*capacity_and_long_contracts
  + 0.14*talent_and_hiring
  + 0.10*patent_product_signal
  + 0.10*policy_alignment
```

该分数用于形成研究假设，不代表股价方向或收益概率。

### 2.6 变化告警

```text
AlertScore =
    0.35*score_delta
  + 0.25*novelty
  + 0.20*evidence_quality
  + 0.20*watchlist_relevance
```

## 3. 在线模型中心导航

左侧导航：`数据与模型 -> 模型与参数`。

页面必须包含：

1. 当前生效配置、版本、创建时间、最后校准；
2. 公式树和每个输入的贡献；
3. 综合权重；
4. 组件内部权重；
5. 关系显示门槛；
6. 证据/数据质量门槛；
7. 时间半衰期；
8. 图谱预算和聚合门槛；
9. 告警门槛；
10. 动画与反馈参数；
11. 即时预览影响区；
12. 保存、激活、回滚、恢复默认和导入/导出。

## 4. 修改模式

| 模式 | 是否写数据库 | 刷新范围 | 目标延迟 | 用途 |
|---|---:|---|---:|---|
| 草稿编辑 | 否 | 参数面板 | < 50ms | 输入与校验 |
| 即时预览 | 否 | 当前已加载的全部可视化 | p95 < 250ms | 看排序、大小、边和告警变化 |
| 应用于当前会话 | 否/会话态 | 当前主体的所有板块 | p95 < 700ms | 临时研究偏好 |
| 保存新版本 | 是 | 生成配置版本 | p95 < 1s | 可审计持久化 |
| 激活配置 | 是 | 增量重算并原子切换快照 | 小范围 < 5s；大范围异步 | 全局使用 |
| 回滚 | 是 | 切回历史版本并重算 | 同激活 | 恢复 |

“立即刷新全体数据呈现”指：当前浏览器中所有已加载视图立即预览；持久化全库重算通过增量任务完成，完成前继续显示上一个成功快照并明确标记“正在重算”。

## 5. 参数合法性

- 综合权重合计必须为 `1.0 ± 0.0001`；
- 单一综合权重 `0-0.70`；
- 分数和门槛 `0-100`；
- 半衰期 `30-1825` 天；
- 首页节点 `12-120`，边 `16-240`；
- 预览 debounce `50-500ms`；
- 动画局部反馈 `80-240ms`，空间重排 `220-520ms`；
- 推断关系默认至少 2 个相互独立来源；
- 缺失值不得当作 0，默认 `renormalize_available` 并显示 coverage；
- 任何公式结构变化生成新的 model version；
- 配置激活必须记录原因、旧值、新值、操作者和时间。

## 6. 文件修改流程

```bash
python scripts/validate_model_config.py \
  config/model_profiles/balanced-v2.json \
  config/thresholds/default-v2.json

python scripts/apply_model_config.py --dry-run \
  --profile config/model_profiles/balanced-v2.json \
  --thresholds config/thresholds/default-v2.json

python scripts/apply_model_config.py \
  --profile config/model_profiles/balanced-v2.json \
  --thresholds config/thresholds/default-v2.json \
  --reason "adjust supply-chain emphasis"
```

Codex 必须先实现 `--dry-run`，再实现写入；配置失败不得产生半成功版本。

## 7. 影响预览

每次修改至少可视化显示：

- Top 20 节点排名前后变化；
- 节点大小与边宽变化；
- 被门槛隐藏/重新显示的关系数量；
- 告警新增/消失数量；
- 受影响公司和行业数量；
- 证据质量与覆盖是否导致排名反转；
- 当前查询重算耗时。

## 8. 验收

1. 参数中心在一级导航可见。
2. 所有公式、默认值、范围、单位和验证规则可读。
3. 滑块或数字输入变化后，当前商业版图、供应链、资本、控制、政策和信号视图同步预览。
4. 非法权重不能保存或激活。
5. 参数可导出为 JSON，也可导入并预览 diff。
6. 保存后生成不可变版本；激活、回滚和恢复默认写操作日志。
7. 任一分数均可查看每项输入、标准化结果、贡献和证据来源。
