# Memory Atlas Project Model Parameters

更新时间：2026-07-01

本文件定义 Memory Atlas 当前真实使用的模型假设、输入、处理方法、输出、公式、函数、阈值、门槛和迭代策略。它不是功能清单，也不是开发记录。功能、交付运行方式、验收标准和历史过程记录见 `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`。

## 0. 文档边界

- 模型：假设、输入、处理、方法、策略、输出、迭代。
- 参数：公式、函数、权重、阈值、等级门槛、筛选规则、失败条件。
- 不属于模型参数：页面功能列表、开发日志、提交记录、部署说明、UI 需求。这些只在影响公式或阈值时引用。
- 真实性规则：没有实现的模型必须标为“当前未实现”，不得为了完整感编造公式。

## 1. 记忆权重模型

模型假设：

- 对未来 agent 最有价值的记忆由三类信号共同决定：记忆层级、重要性、置信度。
- 核心画像应该比一般项目上下文和临时信息有更高基础权重。
- 高置信和高重要信息应更容易被可视化放大和召回。

输入：

- `memory_tier`
- `importance`
- `confidence`

处理方法：

- 先把层级归一到 `核心画像`、`一般`、`临时`。
- 再用加权和计算 `weight_score`。

参数与阈值：

- `TIER_WEIGHT = {"核心画像": 1.0, "一般": 0.66, "临时": 0.28}`
- `IMPORTANCE_WEIGHT = {"高": 1.0, "中": 0.62, "低": 0.32}`
- `CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.72, "low": 0.45}`
- `memory_weight = tier_score * 0.5 + importance_score * 0.3 + confidence_score * 0.2`
- 输出四位小数。

输出：

- `metrics.weight_score`
- 影响 Galaxy/Graph 节点大小、ROI 排序、视觉亮度和 agent 召回优先级。

迭代规则：

- 如果用户认为“核心画像”召回过少，优先提高 tier 权重。
- 如果低置信内容噪声过高，优先降低 low confidence 权重或增加人工确认门槛。

## 2. ROI Leverage 模型

模型假设：

- 一条记忆的 ROI 不只取决于重要性，还取决于是否是决策、是否敏感、是否过期。
- 敏感信息可以存在于数据库体系中，但公开可视化与 GitHub 备份必须降低其直接可用性。

输入：

- `memory_weight`
- `category`
- `sensitivity`
- `validity`
- `date`

处理方法：

- 按日期计算新鲜度。
- 决策类增加杠杆分。
- 敏感或 secret 信息扣分。

参数与阈值：

- `recency_days = today - date`
- `sensitivity_penalty = 0.35` 当 `sensitivity in {"sensitive", "secret"}`，否则 `0.1`
- `decision_impact = 1` 当 `category == "decision"`，否则 `0`
- `leverage_score = max(0, memory_weight + decision_impact * 0.15 - sensitivity_penalty)`
- 过期状态：
  - `validity == "临时"` 且 `recency_days > 30` => `stale_short_term`
  - `recency_days > 180` => `needs_review`
  - 其他有日期记录 => `current`
  - 无日期 => `unknown`

输出：

- `metrics.roi.leverage_score`
- `metrics.roi.staleness_status`
- `metrics.roi.recommended_action`

迭代规则：

- ROI Dashboard 默认按 `leverage_score` 排序。
- 后续可以加入“实际执行收益/时间投入/机会窗口”字段，但当前没有真实执行收益数据，不应伪造。

## 3. 全局活动强度模型 activity_score.v2

模型假设：

- 用户和 agent 的使用强度不能只看对话数；消息、记忆增量、候选、决策、工具调用、错误、中断都代表不同成本和价值信号。
- 工具调用和决策比普通消息更能代表执行投入。

输入：

- `conversation_count`
- `message_count`
- `memory_count`
- `candidate_count`
- `decision_count`
- `tool_call_count`
- `error_event_count`
- `abort_count`

处理方法：

- 对每个日/周/月桶聚合计数后计算活动分。
- 再按该周期内最大分归一成 0-5 等级。

参数与阈值：

- `activity_score = conversation_count * 5 + message_count + memory_count * 3 + candidate_count + decision_count * 4 + tool_call_count * 2 + error_event_count + abort_count * 2`
- `activity_level = 0` 当 `score <= 0` 或 `max_score <= 0`
- 否则 `activity_level = ceil(score / max_score * 5)`，限制在 1-5。
- 分位数：
  - `p50 = ceil(0.50 * n) - 1`
  - `p75 = ceil(0.75 * n) - 1`
  - `p90 = ceil(0.90 * n) - 1`
  - `p95 = ceil(0.95 * n) - 1`

输出：

- `contribution.daily/weekly/monthly`
- Contribution Grid 的热度、增量分析、时间尺度对比。

迭代规则：

- 如果工具调用过多但实际产出低，应新增“有效交付完成数”而不是继续提高工具调用权重。
- 如果错误/中断代表返工成本，可以从正向活动分拆成“摩擦分”。

## 4. Codex 本地行为活动模型

模型假设：

- Codex 行为分析只能使用脱敏摘要，不直接上传原始 transcript、绝对路径、secrets。
- 一个 session 的强度由消息数、用户消息、工具调用、主题覆盖和错误事件共同表示。

输入：

- 本机 Codex session jsonl 摘要。
- `message_count`
- `user_message_count`
- `tool_call_count`
- `topic_labels`
- `error_event_count`

处理方法：

- 解析本机 Codex 历史，生成 redacted session manifest。
- 主题和偏好信号只保存标签与计数。

参数与阈值：

- `session_activity_score = message_count + user_message_count * 2 + tool_call_count * 3 + len(topic_labels) * 4 + error_event_count * 2`
- Codex 日聚合 `activity_level = ceil(score * 5 / max_score)`，限制在 1-5。
- `backup_policy = redacted_summary_only_no_raw_transcript_no_plaintext_secret`

输出：

- `data/processed/codex/codex_activity_snapshot.json`
- `data/derived/agent_context/agent_context_pack.json`
- Memory Atlas 的 Codex 数据源视图、行为模式、agent personalization。

迭代规则：

- 新增微信/小红书/抖音等来源时，必须先适配 canonical event contract，不能把平台私有字段直接塞进 Atlas。
- 如果要分析真实 productivity，应新增“完成事项/提交/报告/验证通过”信号。

## 5. Contribution Grid 热度映射模型

模型假设：

- 人眼需要看到低频与空值差异，不能让低频都黑掉。
- 高值不能线性压扁低值，使用 log 映射更适合长尾互动数据。

输入：

- `activity_score`
- `max_activity_score`
- `activity_level`

处理方法：

- 先用等级锚点保证 1-5 等级可见。
- 再用 `log1p(score) / log1p(max_score)` 捕捉长尾。
- 最后插值到近黑、冷蓝灰、深海蓝、钴蓝、亮蓝、冰蓝色带。

参数与阈值：

- `heatLevelAnchors = [0, 0.16, 0.34, 0.54, 0.74, 0.93]`
- `rawRatio = score / maxScore`
- `logRatio = log1p(score) / log1p(maxScore)`
- `ratio = max(levelAnchor, logRatio * 0.82 + rawRatio * 0.18)`
- `heatIntensity = clamp(0.04 + ratio * 0.96, min=0.08, max=1)`
- 空值颜色：`#0f1116`
- 色带 stops：`#0f1116 -> #17223a -> #1d3f77 -> #1f6db2 -> #1f9bd1 -> #48c7e8 -> #7ee0f8 -> #a7ecff`

输出：

- 日/周/月/年 Contribution Grid 色值。
- 周/月/年内部趋势段。

迭代规则：

- 如果低频仍不可见，提高 `levelAnchor[1]` 或提高 `logRatio` 权重。
- 如果高频差异不明显，提高 `rawRatio` 权重。

## 6. Timeline 动态窗口模型

模型假设：

- Timeline 的核心价值是看到阶段、突增、转折和事件序列，而不是只看事件列表。
- 真实事件日期是主轴，月份网格只是背景定位。

输入：

- `timeline[]`
- `nodeMap`
- UI 控制：`zoom`、`center`、`cursor`

处理方法：

- 全量事件先按日期排序。
- `zoom` 控制可见时间窗口大小。
- `center` 控制窗口中心。
- `cursor` 控制播放游标，用于区分已经经过与未来窗口事件。
- 密度轨用 48 个全局时间 bin；画布背景密度用 36 个可见窗口 bin。

参数与阈值：

- `zoom` 范围：1 到 8。
- `center` 范围：0 到 1。
- `cursor` 范围：0 到 1。
- `visibleSpan = totalSpan / zoom`
- `cursorMs = windowStartMs + visibleSpan * cursor`
- 可见事件上限：最近 260 个窗口内事件，避免单屏过载。
- 轨道上限：7 条，按层级/分类聚合。
- 事件半径：
  - 高重要：9
  - 决策：8
  - 其他：5

输出：

- `events`
- `eventTicks`
- `densityBands`
- `densityBars`
- `rangeLabel`
- `cursorLabel`
- 可交互 hover/detail/click 同步 Inspector。

迭代规则：

- 如果高连接/高密度阶段仍难读，下一轮增加 brushing、局部展开、阶段聚类摘要。
- 如果事件太多，优先加入按层级/主题的视觉聚合，不退回列表。

## 7. 写回提案版本控制模型

模型假设：

- 前端可以帮助用户形成写回建议，但不能直接修改长期记忆。
- 所有修改必须可审计、可导出、可回滚、可由 agent 二次核验。

输入：

- 当前节点 `node`
- 草稿文本 `draftText`
- 用户填写的原因/证据/回滚说明
- 本地 proposal history

处理方法：

- 新增提案时生成 `proposal_id`、`revision`、`parent_proposal_id`。
- 计算可读 diff。
- 生成 agent apply 指引。
- 回滚时新增 `rollback_to_version` 提案，而不是直接覆盖旧版本。

参数与阈值：

- `revision = latest.revision + 1`
- `rollback_unit = policy.rollback_unit || "per_memory_version"`
- `length_delta = len(proposed_text) - len(base_text)`
- `changed_segments = added_readable_segments + removed_readable_segments`
- 禁止 payload：`plaintext secrets`、`raw conversation text`、`record hashes`、`local absolute paths`
- 状态固定为 `draft_pending_agent_apply`

输出：

- 本地 `memory-atlas.writeback.proposals.v1`
- 最新 proposal JSON
- 版本链 JSON
- rollback proposal JSON

迭代规则：

- 后续 agent apply 时必须重新读取数据库、冲突检测、写 proposal history、git commit。
- 若 active memory 已有更新版本，必须先生成冲突报告，不能静默覆盖。

## 8. Shared State Store 状态模型

review_status: `stage_6_whole_stage_review_passed`

模型假设：

- Memory Atlas 的各板块不应各自重复维护 selection、filter、time range
  和 focus 状态；否则 Home、Galaxy、Timeline、Inspector、ROI Dashboard 会
  产生不一致焦点。
- 全局状态必须小而显式，只记录可解释 identity 和 filter schema，不保存
  raw transcript、secret、完整数据库对象或不可回滚写入。
- 视图只能通过显式 action 更新 shared state，派生视图读取 state，避免双向
  effect 循环。

输入：

- `activeView`
- selected `AtlasNode`
- Timeline brush `SharedTimelineTimeRangeSelection`
- Atlas filter fields: `query`, `source`, `tier`, `category`, `theme`
- ROI filter schema field: `roi`
- contribution period identity and summary metrics

处理方法：

- `sharedAtlasReducer` 接收 `select_node`、`select_time_range`、
  `clear_time_range`、`set_filters`、`set_filter`、`clear_filter`、
  `reset_filters`、`select_contribution_period`、`switch_view` 和
  `clear_focus` action。
- `selectionFromNode` 只提取 `nodeId`、`nodeKind`、`clusterId`、`recordId`
  和当前 `timeRangeId`。
- `focusFromSelection` 把同一 `SharedAtlasFocusTarget` 投射给 Home、Galaxy、
  Timeline、Inspector 和 ROI Dashboard。
- `clearSharedAtlasFilter` 只清理指定 filter；例如清理 `source` 不会同时清理
  `tier`、`category` 或 `theme`。

参数与失败条件：

- `schema_version = memory_atlas_shared_state.v1`
- `loopGuard.mode = single-dispatch-reducer`
- `loopGuard.derivedViews = read-only`
- 默认 Atlas filters：
  - `query = ""`
  - `source = "all"`
  - `tier = "all"`
  - `category = "all"`
  - `theme = "all"`
- 默认 ROI filter：`roi = "all"`
- 失败条件：
  - action 后 `focus.home`、`focus.galaxy`、`focus.timeline`、
    `focus.inspector`、`focus.roiDashboard` 不一致。
  - 清理单个 filter 改动了其它 filter 或旧 state object。
  - UI 直接写 active memory，而不是生成 proposal。

输出：

- `SharedAtlasState`
- `SharedAtlasSelectionState`
- `SharedAtlasFilterState`
- `SharedAtlasFocusState`
- `sync.revision`、`sync.updatedBy`、`sync.lastAction`
- Home、Galaxy、Timeline、Inspector 的 `data-shared-*` contract。

迭代规则：

- Stage 6 整体复审已确认 shared-state schema、sync actions、filter clearing
  和 cross-view focus contract 均通过；后续变更必须继续跑
  `validate:stage6`。
- Stage 6.2 可以从 shared state 读取 Inspector explanation/proposal
  所需焦点，但不得直接写长期记忆。
- 新增 filter 时先进入 `SharedAtlasFilterState` 和 validator，再接 UI。
- 如果后续出现跨板块循环更新，优先收紧 reducer action，而不是增加组件内
  effect 同步。

## 9. 情绪分模型

状态：当前未实现。

原因：

- 当前 Memory Atlas 已有活动强度、ROI、记忆层级、重要性、置信度、错误/中断等信号，但没有真实情绪标注、情感词典校准、人工样本、跨语种语义校验，也没有把情绪分写入数据 schema。
- 因此不能声称已经有 emotion score。

未来可行输入：

- 用户消息语气信号。
- 重复纠错/不满表达。
- 中断、返工、否定反馈。
- 高压任务词。
- 明确满意/不满意反馈。

未来建议公式草案：

- 先做 `friction_score`，不要直接做情绪判断。
- `friction_score = correction_count * 3 + repeated_requirement_count * 2 + abort_count * 2 + error_event_count + explicit_negative_feedback * 4`
- 需要人工验证样本后才能进入正式模型参数。

## 10. 质量门槛模型

模型假设：

- Memory Atlas 是决策与记忆平台，质量不能只靠 build 成功。
- 需要同时检查数据安全、视觉密度、中文界面、运行缓存、Cloudflare readiness、本地 app runtime。

输入：

- 源码
- `memory_atlas.json`
- docs
- build output
- local app bundle

处理方法：

- `audit_memory_atlas_release.py` 检查发布目录安全。
- `audit_memory_atlas_visual_acceptance.py` 检查视觉和交互契约。
- `audit_memory_atlas_acceptance.py` 汇总数据、源码、文档、Cloudflare、本地 app。

参数与阈值：

- 所有导航板块默认可视化程度目标：80%+。
- GitHub 不允许 raw exports、明文 secrets、cookies、sessions、auth files。
- 本地 runtime manifest 必须匹配当前 git HEAD。
- 关闭 tab 后本地 runtime 必须支持 release/shutdown，减少后台线程和缓存占用。

输出：

- PASS/FAIL JSON。
- 失败时停止发布或同步。

迭代规则：

- 每次新增视觉要求都要同步到 audit，防止下一轮退化。
- 每次新增数据源都要先增加 registry/source contract，再增加 UI 选择。

## 11. Inspector 解释与 Proposal 安全模型

review_status: `stage_6_whole_stage_review_passed`

模型假设：

- Inspector 默认层应该先帮助人理解“为什么这条记忆重要、怎么算出来、有哪些脱敏证据”，而不是暴露 agent 内部字段。
- 写回长期记忆是高风险动作；前端只能生成 proposal JSON，不能直接修改 active memory。
- Debug 信息有用，但默认展示会增加认知负担和误用风险，因此必须手动开启。

输入：

- `AtlasNode`
- `edgeCount`
- `SharedAtlasState`
- `source_contract.writeback_policy`
- 用户在写回面板输入的 `action`、`proposed_text`、`reason`

处理方法：

- 默认解释面板只读取派生字段：层级、分类、日期、时效、连接数、来源、ROI、共享焦点。
- `node.statement` 低敏数据库摘要只放入 Debug / Agent Inspector，默认关闭。
- proposal preview 和保存逻辑共用 `buildWritebackProposalDraft`，避免 preview 与真实本地提案结构漂移。
- 保存提案只写入浏览器本地 proposal queue，不写 active memory 文件。

参数与公式：

- `memory_weight = tier_score * 0.5 + importance_score * 0.3 + confidence_score * 0.2`
- `TIER_WEIGHT = {"核心画像": 1.0, "一般": 0.66, "临时": 0.28}`
- `IMPORTANCE_WEIGHT = {"高": 1.0, "中": 0.62, "低": 0.32}`
- `CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.72, "low": 0.45}`
- `decision_impact = 1` 当 `category == "decision"`，否则 `0`
- `sensitivity_penalty = 0.35` 当 `visual.sensitive == true` 或分类属于 `temporary_or_sensitive` / `security_boundary`，否则 `0.1`
- `leverage_score = max(0, memory_weight + decision_impact * 0.15 - sensitivity_penalty)`
- proposal safety 必须保持：
  - `direct_frontend_mutation_of_active_memory = false`
  - `requires_conflict_check = true`
  - `requires_agent_or_human_apply = true`

输出：

- Inspector explanation panel：人类解释、公式、参数、脱敏证据、安全说明。
- Debug / Agent Inspector：agent memory/meta 字段、低敏数据库摘要、结构化字段。
- Writeback proposal JSON：`schema_version`、`proposal_id`、`target_ref`、`payload`、`diff`、`version`、`review`、`safety`。

失败条件：

- 默认 Inspector 展示 raw transcript、secret、cookie、session 或本地绝对路径。
- Debug / Agent Inspector 默认打开。
- 前端直接修改 active memory 或 proposal safety 字段不是 fail-closed。
- proposal preview 和保存的 proposal 结构不一致。

迭代规则：

- Stage 6 整体复审已确认 Inspector explanation、Debug separation、proposal
  JSON preview 和 fail-closed writeback safety 均通过。
- Stage 6 整体复审必须同时跑 `validate:shared-state` 和 `validate:inspector-proposal`。
- 后续 agent apply CLI 必须重新读库、做冲突检查、写 history、生成 git 回滚点；不能复用前端状态直接写库。
- 如果默认解释面板过密，优先折叠公式细节，不把 raw 摘要移回默认层。

## 12. Stage 7.1 视觉验收模型

状态：Stage 7.1 已实现，Stage 7 整体复审未完成。

模型假设：

- Memory Atlas 的关键视觉面板不能只靠源码字符串验收；Galaxy 和 Memory River
  必须在真实浏览器中渲染、截图，并通过非空或结构质量 gate。
- Galaxy 是 WebGL canvas，适合用 bounded pixel signal 验证不是空白、纯黑、
  fallback-only 或静态点云。
- Memory River 是 SVG 视觉系统，适合用截图文件和 DOM 结构验证 Macro / Meso /
  Micro 河道、证据层、marker 和密度上下文没有退化成静态列表。

输入：

- Vite production preview output: `apps/memory-atlas/dist`
- Playwright Chromium 页面
- `window.__memoryAtlasGalaxySignal()`
- `.memory-river-canvas` DOM contract
- Browser screenshots

处理方法：

- `validate:stage7-visual` 启动 `vite preview --host 127.0.0.1 --port 4177
  --strictPort`。
- 使用 Playwright 打开页面，等待 `networkidle` 后依次切换到 Galaxy 和 Timeline。
- Galaxy：读取 bounded pixel signal，捕获 `stage7-galaxy-desktop.png`。
- Memory River：检查 SVG contract，捕获 `stage7-memory-river-desktop.png`。
- 验证结束后关闭 preview server，并确认 4177 不再响应。

参数与阈值：

- Galaxy canvas signal:
  - `lit > 100`
  - `alpha > 100`
  - `max > 42`
  - `width > 100`
  - `height > 100`
  - `rendererMode == "memory-starfield"`
  - `fallbackMode != "legacy"`
  - `points > 0`
  - `triangles > 0`
  - `terrainFeatureCount > 0`
  - `flowFieldStrength > 0`
- Screenshot file:
  - `stage7-galaxy-desktop.png` size `> 20000` bytes
  - `stage7-memory-river-desktop.png` size `> 20000` bytes
- Memory River structure:
  - `data-utc-time-scale == "true"`
  - Macro / Meso / Micro level labels all present
  - `laneFlows >= 3`
  - `laneLabels >= 3`
  - evidence layers include `black-hole-lifecycle`, `proto-star-lifecycle`,
    `stale-deprecated`
  - `evidenceSegments > 0`
  - black-hole lifecycle band contract is present through `black-hole-lifecycle`
  - `protoStarMarkers > 0`
  - `totalMarkers >= 3`
  - `densityBands >= 24`

输出：

- PASS/FAIL JSON
- `outputDir`
- Galaxy screenshot path and signal object
- Memory River screenshot path and structure object
- server cleanup result through 4177 port close assertion

失败条件：

- Browser console/page error appears during visual validation.
- Galaxy pixel signal is blank, too dark, legacy fallback, or missing terrain /
  flow-field evidence.
- Memory River lacks Macro / Meso / Micro, evidence layers, opportunity markers, density
  context, or screenshot proof.
- Preview server remains alive on 4177 after validation.

迭代规则：

- Stage 7.2 may add FPS and adaptive quality metrics, but must not weaken
  Stage 7.1 non-empty visual gates.
- Stage 7.3 may add privacy/accessibility checks, but must keep screenshots
  redacted and avoid browser profile/cookie/session capture.
