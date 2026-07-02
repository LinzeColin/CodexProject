# Memory Atlas suggested action lane 可见性合同

适用版本：Memory Atlas v1.1.6 Stage 2 Phase 2

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、搜索、写回逻辑或长期记忆。

## 1. 目标

Stage 2 Phase 2 解决“建议动作虽然有字段，但用户无法快速比较和决定下一步”的问题。`suggested_action_lane` 必须把建议动作呈现为可扫描、可比较、可展开、可追溯、可进入 Inspector 的行动列表。

本 phase 只定义 suggested action lane 的可见性、排序、分组和交互合同，不实现 React/CSS、不启动浏览器、不执行 Playwright 截图、不进入 Search 2.0、复盘、总结迭代、Data Map 2.0、完整 proposal 编辑器或 agent apply。

## 2. Lane 定位

`suggested_action_lane` 是明细可见性工作台中的行动决策 lane。它不是普通待办列表，也不是搜索结果。每条建议动作必须帮助用户判断：

1. 为什么建议做这件事。
2. 预期 ROI 是多少。
3. 努力成本和紧急度如何。
4. 证据是否足够。
5. 下一步是继续、复盘、整合、探索还是延后。
6. 是否需要进入 Inspector 或生成 proposal-only draft。

## 3. 行动卡信息层级

每条行动卡必须分为三层：

| 层级 | 必须性 | 字段 |
|---|---|---|
| `scan_row` | required | title、action_type、urgency、roi_score、effort_cost、confidence、evidence_count |
| `decision_row` | required | reason、next_step、recommended_time_window、linked_theme_ids、linked_asset_ids |
| `evidence_drawer` | required | evidence_refs、source_scope、matched_reason、proposal_hint、rollback_hint |

`scan_row` 必须适合快速扫视；长 reason、证据和解释不得塞入一行或表格单元。

## 4. 必备字段

每条 suggested action 必须包含：

| 字段 | 必须性 | 说明 |
|---|---|---|
| `action_id` | required | 稳定 ID，供 Inspector 和 proposal 引用 |
| `title` | required | 中文短标题，建议不超过 18 个中文字符 |
| `action_type` | required | continue / review / consolidate / explore / defer |
| `reason` | required | 为什么推荐该动作 |
| `roi_score` | required | ROI 或收益判断 |
| `effort_cost` | required | low / medium / high |
| `urgency` | required | now / this_week / later / watch |
| `confidence` | required | high / medium / low |
| `evidence_count` | required | 脱敏证据数量 |
| `evidence_refs` | required | redacted evidence 或 Inspector 引用 |
| `source_scope` | required | all / memory_atlas / codex |
| `linked_theme_ids` | required | 关联主题 |
| `linked_asset_ids` | required | 关联层级资产 |
| `next_step` | required | 用户下一步动作 |
| `recommended_time_window` | required | 建议执行窗口 |
| `proposal_hint` | required | 是否建议 proposal-only 调整 |
| `rollback_hint` | required | 后续应用后如何撤回或复核 |

## 5. 分组和排序

Lane 默认分组：

1. `now`：需要立即判断或处理。
2. `this_week`：本周建议处理。
3. `later`：可延后但仍有价值。
4. `watch`：观察，不打断当前工作。

每组内默认排序：

1. roi_score 高。
2. urgency 高。
3. effort_cost 低。
4. confidence 不低于 medium。
5. evidence_count 足够。
6. 与当前 selection_focus、source_scope、time_window 相关。

不得只按创建时间或任意数组顺序展示。

## 6. 状态徽标

每条行动卡必须显示以下徽标或等价视觉状态：

- `high_roi` / `medium_roi` / `low_roi`。
- `low_effort` / `medium_effort` / `high_effort`。
- `urgent_now` / `this_week` / `later` / `watch`。
- `evidence_ready` / `evidence_thin` / `missing_evidence`。
- `proposal_recommended` / `proposal_not_needed`。

徽标必须可读，不得只依赖颜色。

## 7. 展开和比较

Lane 必须支持：

- expand action：打开 `decision_row` 和 `evidence_drawer`。
- compare actions：至少可比较 roi_score、effort_cost、urgency、confidence。
- pin action：临时置顶，但不写长期记忆。
- mark reviewed：只改变前端临时状态或生成 proposal hint，不直接写 active memory。
- clear temporary state：清除本地临时 pin/reviewed 状态。

## 8. Inspector 交接

点击行动卡必须同步 Inspector，并至少传递：

- source_lane = `suggested_action_lane`。
- target_type = `suggested_action`。
- action_id。
- title。
- action_type。
- reason。
- roi_score。
- effort_cost。
- urgency。
- confidence。
- evidence_refs。
- linked_theme_ids。
- linked_asset_ids。
- next_step。
- recommended_time_window。
- proposal_hint。
- rollback_hint。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 9. proposal-only 边界

Lane 可以提示用户调整：

- priority。
- action_status。
- due_window。
- hidden_until。
- confidence_note。

前端不得直接修改 active memory、建议动作来源数据、长期记忆、GitHub 数据或模型参数。所有持久化调整必须生成 proposal-only draft，并保留 conflict check、agent/human apply 和 rollback 边界。

## 10. 空态、错误态与低证据态

必须定义：

- empty_state：没有建议动作时说明“当前没有建议动作”，并提示查看层级资产或主题分类。
- low_evidence_state：证据不足时显示 evidence_thin 或 missing_evidence，而不是隐藏该动作。
- error_state：字段缺失时显示合同错误，不用 mock 数据伪造动作。
- loading_state：数据加载中不显示假动作。

## 11. 后续截图入口

后续实现 phase 必须补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | now / this_week / later / watch 至少两个组可见，至少一条行动展开 |
| Tablet 768x1024 | 行动卡堆叠可读，展开内容不遮挡 Inspector |
| Mobile 390x844 | scan_row 不溢出，徽标、ROI、effort、urgency 和动作入口可点击 |

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

Stage 2 Phase 2 通过条件：

1. 合同定义 suggested_action_lane 是行动决策 lane，不是普通待办列表。
2. 合同覆盖 scan_row、decision_row、evidence_drawer 三层信息架构。
3. 合同覆盖必备字段、分组、排序、状态徽标、展开、比较、pin、mark reviewed 和清除临时状态。
4. 合同定义 Inspector 交接内容和 raw/private 安全边界。
5. 合同明确 proposal-only，不直接写长期记忆。
6. 验收文件提供字段检查、失败条件和后续截图入口。
7. 记录文件登记目标、范围、风险、验收和回滚。

## 14. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
