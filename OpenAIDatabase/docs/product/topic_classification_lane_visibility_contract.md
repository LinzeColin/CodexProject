# Memory Atlas topic classification lane 可见性合同

适用版本：Memory Atlas v1.1.6 Stage 2 Phase 4

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、搜索、写回逻辑或长期记忆。

## 1. 目标

Stage 2 Phase 4 解决“主题分类虽然有明细字段，但用户无法在工作台里判断主题强弱、趋势、证据、关联资产和下一步”的问题。`topic_classification_lane` 必须把主题分类呈现为可扫描、可比较、可展开、可追溯、可进入 Inspector 的主题列表。

本 phase 只定义 topic classification lane 的可见性、排序、分组和交互合同，不实现 React/CSS、不启动浏览器、不执行 Playwright 截图、不进入 Search 2.0、复盘、总结迭代、Data Map 2.0、完整 proposal 编辑器或 agent apply。

## 2. Lane 定位

`topic_classification_lane` 是明细可见性工作台中的主题解释 lane。它不是 tag 列表，也不是数据库字段直出。每条主题分类必须帮助用户判断：

1. 主题是什么。
2. 主题当前强度和趋势如何。
3. 主题是在增强、衰退、新生、冲突、低价值循环还是过期。
4. 证据和记录是否足够。
5. 它和哪些层级资产、建议动作、星系 cluster、时间河窗口相关。
6. 下一步是继续投入、复盘、整合、验证、降噪、延后还是观察。
7. 是否需要进入 Inspector 或生成 proposal-only draft。

## 3. 主题卡信息层级

每条主题卡必须分为三层：

| 层级 | 必须性 | 字段 |
|---|---|---|
| `topic_scan_row` | required | topic_label、topic_state、topic_strength、trend、confidence、record_count、evidence_count |
| `topic_decision_row` | required | matched_reason、recommended_topic_action、linked_asset_ids、linked_action_ids、related_topic_ids |
| `topic_evidence_drawer` | required | evidence_refs、source_scope、linked_starfield_cluster_id、linked_river_range、proposal_hint、rollback_hint |

`topic_scan_row` 必须适合快速扫视；长 matched_reason、证据和解释不得塞入一行或表格单元。

## 4. 必备字段

每条 topic classification 必须包含：

| 字段 | 必须性 | 说明 |
|---|---|---|
| `topic_id` | required | 稳定 ID，供 Inspector、星系、时间河、搜索和 proposal 引用 |
| `topic_label` | required | 中文短标签，建议不超过 18 个中文字符 |
| `topic_state` | required | dominant / rising / declining / emerging / conflict / black_hole / stale |
| `topic_strength` | required | 主题强度，建议 0-1 或 low / medium / high |
| `trend` | required | up / down / flat / new / volatile |
| `confidence` | required | high / medium / low |
| `record_count` | required | 关联脱敏记录数量 |
| `evidence_count` | required | 脱敏证据数量 |
| `evidence_refs` | required | redacted evidence 或 Inspector 引用 |
| `source_scope` | required | all / memory_atlas / codex |
| `linked_asset_ids` | required | 关联层级资产 |
| `linked_action_ids` | required | 关联建议动作 |
| `linked_starfield_cluster_id` | required | 关联记忆星系 cluster 或后续星系入口 |
| `linked_river_range` | required | 关联记忆时间河窗口 |
| `related_topic_ids` | required | 相关主题 |
| `matched_reason` | required | 为什么归入该主题，必须人类可读 |
| `recommended_topic_action` | required | continue / review / consolidate / validate / reduce_noise / defer / watch |
| `proposal_hint` | required | 是否建议 proposal-only 调整 |
| `rollback_hint` | required | 后续应用后如何撤回或复核 |

## 5. 分组和排序

Lane 默认分组：

1. `dominant`：当前最强、最影响系统判断的主题。
2. `rising`：近期强度或活动正在上升的主题。
3. `emerging`：proto-star、早期机会或潜在新方向。
4. `conflict`：证据、决策或行动建议之间存在冲突的主题。
5. `black_hole`：重复消耗、低 ROI 或高摩擦主题。
6. `declining`：近期关注下降、资产冷却或证据减少的主题。
7. `stale`：长期未维护、低置信或需复核主题。

每组内默认排序：

1. topic_strength 高。
2. trend 为 up / new / volatile。
3. confidence 不低于 medium。
4. record_count 和 evidence_count 足够。
5. 与当前 selection_focus、source_scope、time_window 相关。

不得只按创建时间或任意数组顺序展示。

## 6. 状态徽标

每条主题卡必须显示以下徽标或等价视觉状态：

- `dominant` / `rising` / `declining` / `emerging` / `conflict` / `black_hole` / `stale`。
- `high_strength` / `medium_strength` / `low_strength`。
- `trend_up` / `trend_down` / `trend_flat` / `trend_new` / `trend_volatile`。
- `high_confidence` / `medium_confidence` / `low_confidence`。
- `evidence_ready` / `evidence_thin` / `missing_evidence`。
- `proposal_recommended` / `proposal_not_needed`。

徽标必须可读，不得只依赖颜色。

## 7. 展开和比较

Lane 必须支持：

- expand topic：打开 `topic_decision_row` 和 `topic_evidence_drawer`。
- compare topics：至少可比较 topic_strength、trend、confidence、record_count 和 evidence_count。
- pin topic：临时置顶，但不写长期记忆。
- mark reviewed：只改变前端临时状态或生成 proposal hint，不直接写 active memory。
- jump to linked asset：跳到关联层级资产或交给 Inspector 解释关联。
- jump to linked action：跳到关联建议动作或交给 Inspector 解释关联。
- jump to starfield：跳到记忆星系 cluster 或保留后续实现入口。
- jump to river：跳到记忆时间河窗口或保留后续实现入口。
- clear temporary state：清除本地临时 pin/reviewed 状态。

## 8. Inspector 交接

点击主题卡必须同步 Inspector，并至少传递：

- source_lane = `topic_classification_lane`。
- target_type = `topic_classification`。
- topic_id。
- topic_label。
- topic_state。
- topic_strength。
- trend。
- confidence。
- record_count。
- evidence_count。
- evidence_refs。
- source_scope。
- linked_asset_ids。
- linked_action_ids。
- linked_starfield_cluster_id。
- linked_river_range。
- related_topic_ids。
- matched_reason。
- recommended_topic_action。
- proposal_hint。
- rollback_hint。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 9. proposal-only 边界

Lane 可以提示用户调整：

- topic_category。
- importance。
- priority。
- hidden_until。
- stale_override。
- confidence_note。

前端不得直接修改 active memory、topic_category、importance、priority、memory_tier、GitHub 数据或模型参数。所有持久化调整必须生成 proposal-only draft，并保留 conflict check、agent/human apply 和 rollback 边界。

## 10. 空态、错误态与低证据态

必须定义：

- empty_state：没有主题分类时说明“当前没有可展示的主题分类”，并提示查看层级资产或建议动作。
- low_evidence_state：证据不足时显示 evidence_thin 或 missing_evidence，而不是隐藏该主题。
- conflict_state：主题冲突时显示 conflict 和 matched_reason，不得把冲突静默折叠为普通主题。
- black_hole_state：低价值循环必须标记 black_hole，不得伪装成普通 declining。
- stale_state：过期或待复核主题必须显示 stale，不得伪装成 dominant / rising。
- error_state：字段缺失时显示合同错误，不用 mock 数据伪造主题。
- loading_state：数据加载中不显示假主题。

## 11. 后续截图入口

后续实现 phase 必须补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 七类主题状态至少四类可见，至少一条主题展开 |
| Tablet 768x1024 | 主题卡堆叠可读，展开内容不遮挡 Inspector |
| Mobile 390x844 | topic_scan_row 不溢出，state、strength、trend、confidence 和动作入口可点击 |

## 12. 非目标

本 phase 不覆盖：

- 运行时 React 实现。
- CSS 或视觉 polish。
- Playwright 截图。
- Search 2.0。
- Review / Summary / Iteration。
- Data Map 2.0。
- 完整 Proposal 编辑工作区。
- agent apply。
- GitHub main 上传。

## 13. 验收

Stage 2 Phase 4 通过条件：

1. 合同定义 topic_classification_lane 是主题解释 lane，不是 tag 列表。
2. 合同覆盖 topic_scan_row、topic_decision_row、topic_evidence_drawer 三层信息架构。
3. 合同覆盖必备字段、七类主题状态分组、排序、状态徽标、展开、比较、pin、mark reviewed、jump to linked asset、jump to linked action、jump to starfield、jump to river 和清除临时状态。
4. 合同定义 Inspector 交接内容和 raw/private 安全边界。
5. 合同明确 proposal-only，不直接写长期记忆。
6. 验收文件提供字段检查、失败条件和后续截图入口。
7. 记录文件登记目标、范围、风险、验收和回滚。

## 14. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
