# Memory Atlas 明细可见性工作台合同

适用版本：Memory Atlas v1.1.6 Stage 2 Phase 1

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、搜索、写回逻辑或长期记忆。

## 1. 目标

Stage 2 Phase 1 解决“首页能看到摘要，但缺少统一明细工作台”的问题。记忆总览、建议动作、层级资产和主题分类必须能进入一个结构一致、可展开、可筛选、可排序、可交接 Inspector 的明细可见性工作台。

本 phase 只定义工作台 IA 与交互合同，不实现 React/CSS、不启动浏览器、不执行 Playwright 截图、不进入完整 proposal 编辑工作区、不进入 Search 2.0、复盘、总结迭代或 Data Map 2.0。

## 2. 工作台定位

明细可见性工作台是 Stage 1 合同的统一呈现层。它不是搜索页，不是复盘页，也不是 proposal 编辑器。它必须帮助用户回答：

1. 哪些建议动作值得处理。
2. 哪些层级资产需要确认、降噪、复活或更新。
3. 哪些主题正在增强、衰退、冲突或形成低价值循环。
4. 每条明细为什么出现，证据是什么，下一步是什么。
5. 点击后如何进入 Inspector，并在需要时生成 proposal-only draft。

## 3. 信息架构

工作台必须包含以下区域：

| 区域 | 必须性 | 说明 |
|---|---|---|
| `workbench_header` | required | 显示当前 source_scope、time_window、selection_focus 和数据 freshness |
| `scope_controls` | required | 切换 总数据源 / ChatGPT / Codex；不包含外部搜索 |
| `density_mode` | required | `summary` / `expanded` 两种密度，默认 summary |
| `suggested_action_lane` | required | 建议动作明细列表 |
| `tier_asset_lane` | required | 层级资产明细列表 |
| `topic_classification_lane` | required | 主题分类明细列表 |
| `inspector_handoff` | required | 点击任一明细同步 Inspector focus |
| `proposal_entry_hint` | required | 显示 proposal-only 入口提示，但不实现完整编辑器 |
| `empty_state` | required | 无数据时说明原因和下一步 |
| `error_state` | required | 合同错误或数据不可用时不伪造明细 |

## 4. 三类明细 lane

### 4.1 suggested_action_lane

每条建议动作至少显示：

- action_id。
- title。
- action_type。
- reason。
- roi_score。
- effort_cost。
- urgency。
- confidence。
- evidence_count。
- next_step。
- proposal_hint。
- open_inspector。

默认排序：urgency 高、roi_score 高、effort_cost 低、confidence 不低于 medium、evidence_count 足够。

### 4.2 tier_asset_lane

每条层级资产至少显示：

- asset_id。
- asset_tier。
- title。
- summary。
- importance。
- priority。
- confidence。
- staleness_status。
- evidence_count。
- linked_action_ids。
- recommended_asset_action。
- proposal_hint。
- open_inspector。

默认排序：importance 高、priority 高、staleness_status 为 needs_review 或 stale、confidence 不低于 medium。

### 4.3 topic_classification_lane

每个主题至少显示：

- topic_id。
- topic_label。
- topic_state。
- topic_strength。
- trend。
- confidence。
- record_count。
- evidence_count。
- linked_asset_ids。
- linked_action_ids。
- recommended_topic_action。
- proposal_hint。
- open_inspector。

默认排序：dominant、rising、emerging、conflict、black_hole、declining、stale；同类内按 topic_strength、trend、confidence 和 evidence_count 排序。

## 5. 展开交互

每条明细必须支持：

1. collapsed summary：一行标题、状态、优先级或强度、证据数量和下一步。
2. expanded detail：显示 reason / matched_reason、redacted evidence_refs、linked ids、proposal_hint 和 rollback_hint。
3. open_inspector：同步 Inspector focus，保留当前 source_scope 和 time_window。
4. jump_to_related：跳转到关联 lane 中的 linked action / asset / topic。
5. proposal_only_entry：只生成 proposal draft 入口提示，不直接写 active memory。

展开状态必须稳定，不得因为 hover、tooltip、证据数量或标签长度导致列表布局大幅跳动。

## 6. 筛选与排序

本 phase 允许工作台内筛选与排序，但不实现 Search 2.0。必须覆盖：

- source_scope：all / memory_atlas / codex。
- confidence：high / medium / low。
- evidence_count：has_evidence / missing_evidence。
- proposal_hint：recommended / none。
- suggested action：urgency、effort_cost、action_type。
- tier asset：asset_tier、importance、priority、staleness_status。
- topic：topic_state、trend。

所有筛选必须保留 clear filters 入口，并在空结果时说明是“无匹配”还是“数据缺失”。

## 7. Inspector 交接

点击任一明细时，Inspector 至少接收：

- source_lane。
- target_id。
- target_type。
- display_title。
- status_or_state。
- confidence。
- evidence_refs。
- linked_action_ids。
- linked_asset_ids。
- linked_topic_ids。
- reason_or_matched_reason。
- recommended_next_step。
- proposal_hint。
- rollback_hint。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 8. 空态、错误态与隐私边界

必须定义：

- empty_state：没有建议动作、资产或主题时显示用户可执行下一步。
- loading_state：数据加载或生成中不显示假明细。
- error_state：合同字段缺失时显示错误，不用 mock 数据填充。
- private_boundary：不读取 raw/private/cookie/session/secret 数据。
- no_direct_writeback：工作台不得直接修改 active memory、importance、priority、topic_category 或 GitHub 数据。

## 9. 后续截图入口

后续实现 phase 必须补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 三个 lane 同屏或可清晰切换，至少各有一条展开明细 |
| Tablet 768x1024 | lane 可堆叠，展开明细不遮挡 Inspector |
| Mobile 390x844 | 单 lane 可切换，标签、按钮和证据数量不溢出 |

## 10. 非目标

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

## 11. 验收

Stage 2 Phase 1 通过条件：

1. 合同定义明细可见性工作台，而不是普通摘要列表。
2. 合同覆盖 suggested_action_lane、tier_asset_lane、topic_classification_lane。
3. 合同覆盖三类 lane 的最小字段、默认排序、展开详情和 Inspector 交接。
4. 合同定义 scope controls、density mode、筛选、clear filters、empty/loading/error 状态。
5. 合同明确 proposal-only、no direct writeback 和 raw/private 安全边界。
6. 验收文件提供字段检查、失败条件和后续截图入口。
7. 记录文件登记目标、范围、风险、验收和回滚。

## 12. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
