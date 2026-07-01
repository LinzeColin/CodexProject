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

## 13. Stage 7.2 性能验收模型

状态：Stage 7.2 已实现，Stage 7 整体复审未完成。

模型假设：

- FPS 验收必须来自真实浏览器 production preview，不用静态源码推断。
- 高质量和中质量需要明确阈值；低质量的核心验收是不空白、不退回 legacy。
- 自适应质量不能剥夺人工回滚路径；手动选择 `high` / `mid` / `low`
  会关闭自动质量，`Auto` toggle 可重新启用。
- 资源清理验收不只看 preview server 退出，还要看 Galaxy unmount 的 RAF、
  WebGL renderer、Worker 和 AudioContext lifecycle contract。

输入：

- `window.__memoryAtlasGalaxySignal()`
- `window.__memoryAtlasGalaxyLifecycle`
- `.galaxy-performance-overlay`
- Vite production preview output: `apps/memory-atlas/dist`
- Playwright Chromium 页面

处理方法：

- `validate:stage7-performance` 启动 `vite preview --host 127.0.0.1
  --port 4177 --strictPort`。
- 进入 Galaxy 并切到 Analysis mode，等待 `.galaxy-performance-overlay` 和
  `__memoryAtlasGalaxySignal()` 的 FPS sample。
- 分别切换 `high`、`mid`、`low` quality；manual quality selection 作为
  fallback/rollback path。
- 重新启用 `Auto`，确认 adaptive quality 可以恢复。
- 切到 Timeline 触发 Galaxy unmount，读取 lifecycle signal。
- 关闭 preview server 并确认 4177 不再响应。

参数与阈值：

- FPS:
  - high quality: `fps >= 45`
  - mid quality: `fps >= 30`
  - sample window: `>= 0.8s`
  - `renderTicks > 8`
- Quality:
  - default adaptive quality starts at `mid`
  - low quality `fallbackMode == "low-quality"`
  - low quality still requires `lit > 100`, `alpha > 100`, `points > 0`,
    `triangles > 0`
- Adaptive quality:
  - warmup `2400ms`
  - cooldown `4200ms`
  - high below `45 FPS` may downgrade to `mid`
  - mid below `30 FPS` may downgrade to `low`
  - low at or above `45 FPS` may upgrade to `mid`
  - mid at or above `52 FPS` may upgrade to `high`
- Cleanup:
  - `activeRaf == false`
  - `rafCancelled == true`
  - `rendererDisposed == true`
  - `webglContextLost == true`
  - `workersClosed == true`
  - `audioContextClosed == true`
  - `__memoryAtlasGalaxySignal` removed after unmount

输出：

- PASS/FAIL JSON
- `stage7-performance-report.json`
- high/mid/low signal snapshots
- adaptive overlay contract snapshot
- cleanup lifecycle snapshot
- server cleanup result through 4177 port close assertion

失败条件：

- high or mid quality FPS is below threshold.
- FPS overlay or adaptive data contract is missing.
- low quality is blank, missing render stats, or does not expose low-quality fallback.
- Auto quality cannot resume after manual quality selection.
- Galaxy unmount leaves RAF signal, renderer, WebGL context, Worker/Audio contract,
  or `__memoryAtlasGalaxySignal` active.
- Browser console/page errors appear during performance validation.
- Preview server remains alive on 4177 after validation.

迭代规则：

- Stage 7.2 must keep Stage 7.1 visual gates passing.
- Stage 7.3 may add privacy/accessibility checks but must not relax the FPS,
  adaptive quality or cleanup lifecycle thresholds.

## 14. Stage 7.3 隐私与无障碍验收模型

状态：Stage 7.3 已实现，Stage 7 整体复审未完成。

模型假设：

- 发布产物只能作为 public redacted read-only visualization 使用；不能把
  raw/private/cookie/session/secret 或本机绝对路径带入 `dist`。
- reduced motion 必须使用浏览器偏好验证，不能只靠 UI 文案判断。
- 伪触感和音频是用户显式 opt-in 的反馈；默认必须保持安静，不调用
  `navigator.vibrate` 或 `AudioContext`。
- Stage 7.3 只增加验收 gate 和安全 DOM contract，不改变写回、数据摄取或
  Cloudflare 发布边界。

输入：

- `apps/memory-atlas/dist`
- `apps/memory-atlas/dist/memory_atlas.json`
- `scripts/audit_memory_atlas_release.py`
- Playwright Chromium 页面
- `prefers-reduced-motion` browser media emulation
- Timeline feedback DOM contract

处理方法：

- `validate:stage7-privacy-accessibility` 先运行 release privacy audit。
- 扫描 publish artifact，确认无 sourcemap，且 `memory_atlas.json` 的
  `source_contract.mode == "public_redacted_read_only_visualization"`。
- 启动 Vite production preview。
- 用 `reducedMotion: "reduce"` 的 browser context 打开 Timeline，确认
  Reduced Motion 默认开启、播放按钮禁用、Memory River transition 被关闭。
- 用 `reducedMotion: "no-preference"` 的 browser context 清空本地反馈偏好，
  确认伪触感和音频默认关闭。
- 安装 vibration / AudioContext spy，点击 Memory River marker，确认默认
  不调用 vibration 或 AudioContext。
- 关闭 preview server 并确认 4177 不再响应。

参数与阈值：

- Privacy artifact:
  - `memory_atlas.json` exists
  - `schema_version == "memory_atlas.v1"`
  - `source_contract.mode == "public_redacted_read_only_visualization"`
  - `direct_frontend_mutation_of_active_memory == false`
  - no `.map` files in `dist`
  - forbidden text patterns absent:
    - `PRIVATE CORE DETAIL`
    - `SECRET DETAIL`
    - `sk-*`
    - private key headers
    - `OpenAI-export.zip`
    - `chatgpt_memory_vault`
    - `.local_keys`
    - `/Users/<name>/`
- Reduced motion:
  - browser `matchMedia("(prefers-reduced-motion: reduce)").matches == true`
  - Reduced Motion checkbox checked
  - `data-reduced-motion == "true"`
  - `data-feedback-reduced-motion == "true"`
  - play button disabled
  - Memory River lane/marker transition duration `0s`
- Feedback defaults:
  - pseudo-haptic checkbox unchecked
  - audio checkbox unchecked
  - `data-feedback-pseudo-haptic == "disabled"`
  - `data-feedback-audio == "disabled"`
  - `data-feedback-defaults == "silent-by-default"`
  - marker click leaves vibration spy count `0`
  - marker click leaves AudioContext spy count `0`

输出：

- PASS/FAIL JSON
- `stage7-privacy-accessibility-report.json`
- release privacy audit result
- publish artifact privacy summary
- reduced-motion browser contract snapshot
- silent feedback default probe snapshot
- server cleanup result through 4177 port close assertion

失败条件：

- Release privacy audit fails.
- Publish artifact contains sourcemaps or forbidden private/secret patterns.
- `memory_atlas.json` does not advertise public redacted read-only mode.
- Browser reduced-motion preference does not enable Reduced Motion behavior.
- Playback remains available under reduced motion.
- Pseudo-haptic or audio feedback defaults on.
- Default marker interaction calls vibration or AudioContext.
- Browser console/page errors appear during validation.
- Preview server remains alive on 4177 after validation.

迭代规则：

- Stage 7.3 must keep Stage 7.1 visual gates and Stage 7.2 performance gates
  passing.
- Stage 7 whole-stage review may start only after 7.1, 7.2 and 7.3 validators
  all pass on the same current branch base.

## 15. Stage 7 整体复审状态

状态：`stage_7_whole_stage_review_passed`。

Stage 7 整体复审已确认：

- 7.1 Visual Acceptance 已通过真实浏览器截图、Galaxy canvas pixel signal 和
  Memory River DOM/screenshot gate。
- 7.2 Performance Acceptance 已通过 FPS overlay、high/mid FPS threshold、
  low-quality non-blank fallback、adaptive quality 和 cleanup lifecycle gate。
- 7.3 Privacy and Accessibility 已通过 release artifact privacy scan、
  reduced motion browser behavior 和 silent feedback default gate。
- `validate:stage7` 会同时检查 phase review docs、package validators、
  visual acceptance hooks、模型参数、changelog 和 delivery record 是否一致。
- 发布产物必须继续满足
  `source_contract.mode == "public_redacted_read_only_visualization"`。
- 前端写回边界保持
  `direct_frontend_mutation_of_active_memory == false`。
- Stage 7 整体复审不包含 Cloudflare live deploy、Access policy change、
  raw/private data read、direct active-memory writeback 或 Stage 8 packaging。

下一阶段：

- Stage 8: 打包、部署、回滚。

## 16. Stage 8.1 本地 App 打包验收模型

状态：`stage_8_1_local_app_packaging_passed`。

范围：

- 8.1.1 local build。
- 8.1.2 launcher check。
- 8.1.3 default route check。

验收门槛：

- `validate:stage8-local-app` 必须通过。
- Production build 必须生成 `dist/index.html` 与 `dist/memory_atlas.json`。
- Installer 必须能在临时目录创建 executable `Memory Atlas.app` bundle，
  `Info.plist`、`MemoryAtlas.icns` 和 `PkgInfo` 必须存在。
- 无 Pillow 环境下必须使用标准库 `.icns` fallback，不得阻塞
  `python3 scripts/install_memory_atlas_app.py`。
- Launcher 必须只打开 `launching.html` 状态页，不直接打开第二个 `$URL`
  窗口；状态页在 ready 后跳转到本地 app。
- Launcher 必须支持 npm-first / pnpm-fallback dependency install and build，
  并在 Finder 启动环境中注入 Codex bundled runtime PATH（存在时）。
- pnpm `.pnpm/.../node_modules/lightningcss` dependency layout 必须被视为
  ready。
- 本地 runtime 必须写入 `memory_atlas_build.json`，且 `git_commit` 匹配当前
  git HEAD。
- Managed server 必须支持 `MEMORY_ATLAS_PID_FILE`，在 release、idle 或 TTL
  正常退出时清理自己的 pid file。
- 默认 production route 必须打开 `记忆总览`，`data-view="home"` 且
  `.home-overview-view` 可见。
- 关闭验证后 4177 不得留下 listener。

已验证：

- `python3 -m unittest OpenAIDatabase.tests.test_memory_atlas_launcher -q` PASS。
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:stage8-local-app`
  PASS，默认首页 screenshot `504546` bytes。
- `python3 OpenAIDatabase/scripts/install_memory_atlas_app.py --repo-root OpenAIDatabase`
  PASS，已安装 Downloads 与 `/Applications` app bundle。
- `python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py --repo-root OpenAIDatabase --publish-dir "$HOME/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime" --require-local-apps`
  PASS。
- Runtime manifest 当前记录
  `bb4cbd9d4eedbdfe9d95a5850994a293488fa742`。

边界：

- Stage 8.1 不包含 Stage 8.2 Release Safety。
- Stage 8.1 不包含 Cloudflare live deploy 或 Access policy change。
- Stage 8.1 不读取 raw/private/cookie/session/secret 数据。
- Stage 8.1 不新增 direct active-memory writeback。

下一阶段：

- Stage 8.2 Release Safety。

## 17. Stage 8.2 Release Safety 验收模型

状态：`stage_8_2_release_safety_passed`。

范围：

- 8.2.1 Feature Flag Rollback。
- 8.2.2 Acceptance Audit。
- 8.2.3 Release Notes。

验收门槛：

- `validate:stage8-release-safety` 必须通过。
- Production build 必须生成 `dist/index.html` 与 `dist/memory_atlas.json`。
- `audit_memory_atlas_release.py` 与 `audit_memory_atlas_acceptance.py` 必须
  对同一 production dist 通过。
- Galaxy 默认 renderer 必须保持 `memory-starfield`，回滚 renderer 必须保持
  `legacy`。
- Timeline 默认 renderer 必须保持 `memory-river`，回滚 renderer 必须保持
  `legacy`。
- URL rollback 必须支持 `?galaxyRenderer=legacy` 与
  `?timelineRenderer=legacy`。
- localStorage rollback/restore 必须使用
  `memory-atlas.galaxy-renderer` 与 `memory-atlas.timeline-renderer`。
- 环境变量 rollback contract 必须保留
  `VITE_MEMORY_ATLAS_GALAXY_RENDERER` 与
  `VITE_MEMORY_ATLAS_TIMELINE_RENDERER`。
- 真实浏览器必须验证 legacy rollback、新 renderer restore、localStorage
  persistence、screenshot 非空、console/network 无 actionable error。
- 验证结束后 4177 不得留下 listener。

边界：

- Stage 8.2 不包含 Stage 8 whole-stage review。
- Stage 8.2 不包含 Cloudflare live deploy 或 Access policy change。
- Stage 8.2 不读取 raw/private/cookie/session/secret 数据。
- Stage 8.2 不新增 direct active-memory writeback；前端写回仍为
  proposal-only。
- Stage 8.2 不上传 GitHub main。

下一阶段：

- Stage 8 整体复审。

## 18. Stage 8 整体复审状态

状态：`stage_8_whole_stage_review_passed`。

Stage 8 整体复审已确认：

- 8.1 Local App Packaging 已通过 production build、临时 app bundle、
  launcher single-window contract、default `记忆总览` route 和 pid cleanup
  gate。
- 8.2 Release Safety 已通过 Galaxy/Timeline legacy rollback、new renderer
  restore、localStorage persistence、release audit、overall acceptance audit
  和 release notes gate。
- `validate:stage8` 会同时运行 `validate:stage8-local-app`、
  `validate:stage8-release-safety`、offline Cloudflare Pages + Access
  preflight、Stage 8 文档一致性检查和 4177 cleanup assertion。
- offline Cloudflare Pages + Access preflight 只验证 templates、runbook、
  wrangler config 和 release-safe dist，不执行 live deploy。
- 发布产物必须继续满足
  `source_contract.mode == "public_redacted_read_only_visualization"`。
- 前端写回边界保持
  `direct_frontend_mutation_of_active_memory == false`。

边界：

- Stage 8 整体复审不包含 Cloudflare live deploy 或 Access policy change。
- Stage 8 整体复审不读取 raw/private/cookie/session/secret 数据。
- Stage 8 整体复审不新增 direct active-memory writeback。
- GitHub main 上传必须在复审通过后再做 final fast-forward 检查。

下一阶段：

- GitHub main 上传后进入 Stage 9 后续增强迭代。

## 19. Stage 9.1 Obsidian Graph E Iteration 验收模型

状态：`stage_9_1_obsidian_graph_iteration_passed`。

范围：

- 9.1.1 局部图谱优化。
- 9.1.2 标签阈值优化。
- 9.1.3 与记忆星系同步。

验收门槛：

- `validate:stage9-obsidian` 必须通过。
- Obsidian Graph 默认仍可进入 global graph，且默认 label density 不得挤满
  全图。
- Local graph 必须有 bounded neighborhood budget，当前阈值为
  `LOCAL_GRAPH_PRIMARY_NODE_LIMIT = 34`、
  `LOCAL_GRAPH_SECONDARY_NODE_LIMIT = 52`、
  `LOCAL_GRAPH_CLUSTER_MEMBER_LIMIT = 42`、
  `LOCAL_GRAPH_MAX_NODES = 96`。
- Local Graph Budget 必须暴露 primary、secondary、hidden local neighbor 和
  label budget evidence。
- 标签规则必须区分 selected、hover、local-neighbor、zoom-priority、hub 和
  hidden。
- Galaxy shared focus 必须通过 `sharedState.focus` 传入 Obsidian Graph；
  `sourceView == "galaxy"` 且存在 cluster 时，Obsidian 必须显示 bounded local
  cluster graph。
- 验证结束后 4177 不得留下 listener。

边界：

- Stage 9.1 不包含 Stage 9.2 Visual Semantics Enrichment。
- Stage 9.1 不包含 Stage 9 whole-stage review。
- Stage 9.1 不读取 raw/private/cookie/session/secret 数据。
- Stage 9.1 不新增 direct active-memory writeback。
- Stage 9.1 不上传 GitHub main。

下一阶段：

- Stage 9.2 Visual Semantics Enrichment。

## 20. Stage 9.2 Visual Semantics Enrichment 验收模型

状态：`stage_9_2_visual_semantics_enrichment_passed`。

范围：

- 9.2.1 Memory Terrain v2。
- 9.2.2 Memory Weather v2。
- 9.2.3 ROI Visual Gradient。

验收门槛：

- `validate:stage9-visual-semantics` 必须通过。
- Home 必须显示 Memory Weather v2，并暴露 stability、momentum、risk、
  opportunity、confidence 和 signal list；状态判断只能来自现有
  `DeltaStats`、topic rows、black-hole/proto-star 节点和 redacted derived
  nodes。
- Galaxy `memory-starfield` 的 Analysis Mode 必须显示
  `data-memory-terrain-v2="analysis-only"`、terrain semantic role、coverage、
  intensity、sample evidence 和 ROI Capability Gradient；Presentation Mode
  不承载这些分析面板。
- Memory River 必须显示 `data-roi-gradient="capability-growth"`，并把
  `leverage_score` 与 capability-growth event 合成 12 段 ROI gradient band。
- 浏览器验证必须覆盖 Home、Galaxy、Timeline 三面，且 actionable
  console/network error 为 0；`/__memory_atlas_heartbeat` 本地运行探针 404
  不计入资源失败。
- 验证结束后 4177 不得留下 listener。

边界：

- Stage 9.2 不包含 Stage 9 whole-stage review。
- Stage 9.2 不上传 GitHub main。
- Stage 9.2 不部署 Cloudflare，不修改 Access policy。
- Stage 9.2 不读取 raw/private/cookie/session/secret 数据。
- Stage 9.2 不新增 direct active-memory writeback。

下一阶段：

- Stage 9 整体复审与修复；通过后再做 GitHub main 上传。

## 21. Stage 9 整体复审状态

状态：`stage_9_whole_stage_review_passed`。

Stage 9 整体复审已确认：

- 9.1 Obsidian Graph E Iteration 已通过 `validate:stage9-obsidian`：
  bounded local graph、label rules、Galaxy shared-focus sync 和 4177 cleanup
  均通过。
- 9.2 Visual Semantics Enrichment 已通过
  `validate:stage9-visual-semantics`：Memory Weather v2、Memory Terrain v2、
  Galaxy ROI gradient、Memory River ROI/capability gradient、browser
  console/network 和 4177 cleanup 均通过。
- `validate:stage9` 会同时运行 Stage 9.1 validator、Stage 9.2 validator、
  visual acceptance、release audit、overall acceptance、Stage 9 文档一致性检查
  和 4177 cleanup assertion。
- `audit_memory_atlas_visual_acceptance.py` 必须继续包含
  `stage9_1_obsidian_graph_iteration_ready` 和
  `stage9_2_visual_semantics_enrichment_ready`。
- 发布产物必须继续满足
  `source_contract.mode == "public_redacted_read_only_visualization"`。
- 前端写回边界保持
  `direct_frontend_mutation_of_active_memory == false`。

边界：

- Stage 9 整体复审不包含 Cloudflare live deploy 或 Access policy change。
- Stage 9 整体复审不读取 raw/private/cookie/session/secret 数据。
- Stage 9 整体复审不新增 direct active-memory writeback。
- Stage 9 整体复审不进入 Stage 10。
- GitHub main 上传必须在复审通过后再做 final fast-forward 检查。

下一阶段：

- GitHub main 上传后，Stage 9 交付关闭；后续新需求另开下一阶段。

## 22. Part 1 Stage 0 复审门槛

状态：`part_1_stage_0_review_passed`。

范围：

- Phase 0.1 Scope & Naming Freeze。
- Phase 0.2 Memory Overview / Memory Starfield / Memory River / Universe State
  contracts。
- Phase 0.3 isolated spike scaffold continuity。

验收门槛：

- `validate:part1-stage0` 必须通过。
- Phase 0.1 必须同时包含首批模块、中文命名、默认入口、隐私边界、不改
  route/production UI 和 rollback。
- Phase 0.2 必须同时覆盖 Memory Weather、Black Hole、Proto-Star、Next
  Actions、Mini Starfield、River Pulse、Presentation / Analysis mode、zoom、
  brush、theme lanes、pseudo-haptic 和 reduced motion。
- Phase 0.3 scaffold continuity 必须保留 isolated directory、README
  contract、redacted fixture boundary、acceptance criteria、rollback，以及
  production source 不引用 spike 目录的证据。
- 参数文件必须保留 `product_target: Memory Atlas v1.1.5`、schema marker、
  validation hints、`raw_private_data_allowed: false`、
  `plaintext_secrets_allowed: false`、`local_absolute_paths_allowed: false` 和
  `writeback_allowed: false`。

边界：

- 本 Part 1 复审不进入 Part 2。
- 本 Part 1 复审不执行整项目复审。
- 本 Part 1 复审不上传 GitHub main。
- 本 Part 1 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 1 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 1 复审不新增 direct active-memory writeback。

下一阶段：

- 单独执行 Part 2 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 23. Part 2 Stage 1 复审门槛

状态：`part_2_stage_1_review_passed`。

范围：

- Phase 1.1 Memory Starfield Spike。
- Phase 1.2 Memory River Spike。
- Phase 1.3 Universe State Generator Spike。

验收门槛：

- `validate:part2-stage1` 必须通过。
- Phase 1.1 必须保留 isolated runnable Memory Starfield workspace、Three.js
  canvas、默认 10k particle path、LOD、Flow Field、gravitational disk、Black
  Hole、Proto-Star、Memory Terrain、reduced motion、hover card、smoke
  instrumentation 和 false safety flags。
- Phase 1.2 必须保留 isolated runnable Memory River workspace、D3 UTC scale、
  zoom、brush、macro/meso/micro lanes、Black Hole band、Proto-Star marker、
  pseudo-haptic visual feedback、reduced motion、hover card、smoke
  instrumentation 和 false safety/writeback flags。
- Phase 1.3 必须保留 Universe State adapter、score functions、schema/sample
  gate、parameter drift check、`dominant/rising/declining/conflict/black_hole/
  proto_star/stale` 输出、consumer map、proposal-only next actions 和 all-false
  privacy/writeback diagnostics。
- TypeScript/Vite build 必须通过。
- Production source 不得引用 isolated Stage 1 spike/generator workspaces。

参数边界：

- Universe State score weights 必须继续从
  `config/visualization/model_parameters.universe_state.yaml` 镜像并通过 drift
  check。
- `black_hole`、`proto_star`、`stale` weight groups 必须各自保持 sum `1.0`。
- `recommended_next_actions[*].proposal_only == true`。

边界：

- 本 Part 2 复审不进入 Part 3。
- 本 Part 2 复审不执行整项目复审。
- 本 Part 2 复审不上传 GitHub main。
- 本 Part 2 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 2 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 2 复审不新增 direct active-memory writeback。
- 本 Part 2 复审不把 Stage 1 spike/generator 接入 production UI。

下一阶段：

- 单独执行 Part 3 复审与修复；所有 part-level 复审完成后再进入整项目复审。
