# Memory Atlas tier asset lane 可见性合同

适用版本：Memory Atlas v1.1.6 Stage 2 Phase 3

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、搜索、写回逻辑或长期记忆。

## 1. 目标

Stage 2 Phase 3 解决“层级资产虽然有明细字段，但用户无法在工作台里判断哪些资产重要、过期、需要复盘或可转成行动”的问题。`tier_asset_lane` 必须把层级资产呈现为可扫描、可比较、可展开、可追溯、可进入 Inspector 的资产列表。

本 phase 只定义 tier asset lane 的可见性、排序、分组和交互合同，不实现 React/CSS、不启动浏览器、不执行 Playwright 截图、不进入 Search 2.0、复盘、总结迭代、Data Map 2.0、完整 proposal 编辑器或 agent apply。

## 2. Lane 定位

`tier_asset_lane` 是明细可见性工作台中的资产判断 lane。它不是原始记忆列表，也不是数据库字段直出。每条层级资产必须帮助用户判断：

1. 它属于哪个资产层级。
2. 它为什么重要。
3. 它是否仍有效或需要复核。
4. 它和哪些建议动作、主题、时间窗口相关。
5. 下一步是保留、复盘、整合、降权、重新验证还是延后。
6. 是否需要进入 Inspector 或生成 proposal-only draft。

## 3. 资产卡信息层级

每条资产卡必须分为三层：

| 层级 | 必须性 | 字段 |
|---|---|---|
| `asset_scan_row` | required | title、asset_tier、importance、priority、confidence、staleness_status、evidence_count |
| `asset_decision_row` | required | summary、recommended_asset_action、linked_action_ids、linked_theme_ids、linked_time_range |
| `asset_evidence_drawer` | required | evidence_refs、source_scope、last_seen_range、proposal_hint、rollback_hint |

`asset_scan_row` 必须适合快速扫视；长 summary、证据和解释不得塞入一行或表格单元。

## 4. 必备字段

每条 tier asset 必须包含：

| 字段 | 必须性 | 说明 |
|---|---|---|
| `asset_id` | required | 稳定 ID，供 Inspector、搜索、时间河、星系和 proposal 引用 |
| `asset_tier` | required | core_profile / project / decision / workflow / knowledge / opportunity / stale |
| `title` | required | 中文短标题，建议不超过 18 个中文字符 |
| `summary` | required | 两行内人类可读摘要 |
| `importance` | required | high / medium / low |
| `priority` | required | p0 / p1 / p2 / p3 / watch |
| `confidence` | required | high / medium / low |
| `staleness_status` | required | current / needs_review / stale / unknown |
| `evidence_count` | required | 脱敏证据数量 |
| `evidence_refs` | required | redacted evidence 或 Inspector 引用 |
| `source_scope` | required | all / memory_atlas / codex |
| `linked_action_ids` | required | 关联建议动作 |
| `linked_theme_ids` | required | 关联主题或后续主题分类入口 |
| `linked_time_range` | required | 关联时间窗口或时间河入口 |
| `recommended_asset_action` | required | keep / review / consolidate / lower_priority / validate / defer |
| `proposal_hint` | required | 是否建议 proposal-only 调整 |
| `rollback_hint` | required | 后续应用后如何撤回或复核 |

## 5. 分组和排序

Lane 默认分组：

1. `core_profile`：核心画像、长期稳定偏好、工作边界和高价值规则。
2. `project`：正在推进或历史上仍有参考价值的项目资产。
3. `decision`：已做出的选择、取舍、授权、停止条件或边界。
4. `workflow`：可复用流程、检查清单、执行规范或验收方式。
5. `knowledge`：可复用概念、事实、技术、研究或经验。
6. `opportunity`：proto-star、新方向、潜在项目或验证窗口。
7. `stale`：过期、低置信、冲突、长期未维护或可能应降权的资产。

每组内默认排序：

1. importance 高。
2. priority 高。
3. staleness_status 为 needs_review 或 stale。
4. confidence 不低于 medium。
5. evidence_count 足够。
6. 与当前 selection_focus、source_scope、time_window 相关。

不得只按创建时间或任意数组顺序展示。

## 6. 状态徽标

每条资产卡必须显示以下徽标或等价视觉状态：

- `core_profile` / `project` / `decision` / `workflow` / `knowledge` / `opportunity` / `stale`。
- `high_importance` / `medium_importance` / `low_importance`。
- `p0` / `p1` / `p2` / `p3` / `watch`。
- `current` / `needs_review` / `stale` / `unknown`。
- `evidence_ready` / `evidence_thin` / `missing_evidence`。
- `proposal_recommended` / `proposal_not_needed`。

徽标必须可读，不得只依赖颜色。

## 7. 展开和比较

Lane 必须支持：

- expand asset：打开 `asset_decision_row` 和 `asset_evidence_drawer`。
- compare assets：至少可比较 importance、priority、confidence、staleness_status 和 evidence_count。
- pin asset：临时置顶，但不写长期记忆。
- mark reviewed：只改变前端临时状态或生成 proposal hint，不直接写 active memory。
- jump to linked action：跳到关联建议动作或交给 Inspector 解释关联。
- clear temporary state：清除本地临时 pin/reviewed 状态。

## 8. Inspector 交接

点击资产卡必须同步 Inspector，并至少传递：

- source_lane = `tier_asset_lane`。
- target_type = `tier_asset`。
- asset_id。
- asset_tier。
- title。
- summary。
- importance。
- priority。
- confidence。
- staleness_status。
- evidence_refs。
- source_scope。
- linked_action_ids。
- linked_theme_ids。
- linked_time_range。
- recommended_asset_action。
- proposal_hint。
- rollback_hint。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 9. proposal-only 边界

Lane 可以提示用户调整：

- importance。
- priority。
- hidden_until。
- stale_override。
- confidence_note。
- action_status。

前端不得直接修改 active memory、memory_tier、importance、priority、topic_category、GitHub 数据或模型参数。所有持久化调整必须生成 proposal-only draft，并保留 conflict check、agent/human apply 和 rollback 边界。

## 10. 空态、错误态与低证据态

必须定义：

- empty_state：没有层级资产时说明“当前没有可展示的层级资产”，并提示查看建议动作或主题分类。
- low_evidence_state：证据不足时显示 evidence_thin 或 missing_evidence，而不是隐藏该资产。
- stale_conflict_state：资产过期、冲突或待复核时显示 needs_review / stale / unknown，不得伪装成 current。
- error_state：字段缺失时显示合同错误，不用 mock 数据伪造资产。
- loading_state：数据加载中不显示假资产。

## 11. 后续截图入口

后续实现 phase 必须补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 七类资产分组至少三个可见，至少一条资产展开 |
| Tablet 768x1024 | 资产卡堆叠可读，展开内容不遮挡 Inspector |
| Mobile 390x844 | asset_scan_row 不溢出，tier、importance、priority、staleness 和动作入口可点击 |

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

Stage 2 Phase 3 通过条件：

1. 合同定义 tier_asset_lane 是资产判断 lane，不是原始记忆列表。
2. 合同覆盖 asset_scan_row、asset_decision_row、asset_evidence_drawer 三层信息架构。
3. 合同覆盖必备字段、七类资产分组、排序、状态徽标、展开、比较、pin、mark reviewed、jump to linked action 和清除临时状态。
4. 合同定义 Inspector 交接内容和 raw/private 安全边界。
5. 合同明确 proposal-only，不直接写长期记忆。
6. 验收文件提供字段检查、失败条件和后续截图入口。
7. 记录文件登记目标、范围、风险、验收和回滚。

## 14. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
