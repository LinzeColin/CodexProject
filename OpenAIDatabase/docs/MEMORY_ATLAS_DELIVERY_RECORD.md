# Memory Atlas Delivery Record

更新时间：2026-07-01

本文件记录 Memory Atlas 的功能清单、交付运行方式、验收标准、历史过程记录、待开发清单和下一位 agent 的接手顺序。模型假设、处理方法、公式和阈值不写在这里，见 `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`。

## 1. 当前目标

Memory Atlas 是一个独立运行但统一承载多数据源的本地优先记忆可视化平台。它不是第三方插件，也不是多个分裂 app。平台首页支持选择分析对象：

1. 总数据源：所有数据来源放在一起。
2. ChatGPT：OpenAI export / memory database 派生数据。
3. Codex：本机 Codex 使用记录、聊天/开发记录、工具调用、错误/中断、偏好信号。

后续微信、小红书、抖音等数据源必须先进入 source registry 和 canonical event contract。没有真实脱敏 ingestion 前，不得在首页展示假数据源或空数据源。

## 2. 交付运行方式

本地运行：

- 技术栈：Vite + React + Three.js。
- 运行目录：`apps/memory-atlas`。
- 构建命令：`npm run build --prefix apps/memory-atlas`。
- 预览命令：`npm run preview --prefix apps/memory-atlas -- --port <port>`。
- 数据快照：本地 app 每次启动先运行真实 Codex/source redacted sync 并重建 `data/derived/visualization/memory_atlas.json`，再复制到 runtime；前端运行时 fetch `/memory_atlas.json`，使用 cache-busted no-store 请求，确保每次打开看到最新快照生成时间，而不是只更新读取时间。

本地 app 入口：

- `~/Downloads/Memory Atlas.app`
- `/Applications/Memory Atlas.app`
- app 图标由 `scripts/install_memory_atlas_app.py` 生成并写入 bundle。
- `MEMORY_ATLAS_REFRESH=1` 表示强制完整 runtime rebuild；默认启动已经会刷新数据快照。
- 关闭 tab 后本地 runtime 通过 heartbeat/release 机制释放后台线程，减少缓存和内存占用。

Cloudflare 方案：

- Cloudflare Pages + Access。
- 构建输出：`apps/memory-atlas/dist`。
- 配置与检查：
  - `wrangler.jsonc`
  - `config/cloudflare/pages_direct_upload.template.json`
  - `config/cloudflare/access_self_hosted_application.template.json`
  - `scripts/preflight_cloudflare_pages_access.py`
  - `docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md`

未来可选：

- 稳定后考虑 Tauri，但每轮开发要提醒用户：前端 writeback 只能生成 proposal；真正写库需受控 agent apply、版本控制、rollback。

## 3. 当前功能清单

全局要求：

- 全中文优先显示。
- 所有板块共享筛选状态、数据源选择、主题/层级/分类筛选和右侧详情同步；Stage 6.1 起 selection/filter/time range/focus 由 typed shared-state reducer 统一管理。
- 所有页面默认可视化程度目标 80%+；列表只能作为 drill-down，不能成为主体验。
- 人类版输出优先：话题、需要做什么、记得做什么、建议做什么、机会、风险、ROI、能力成长，不只显示 agent 内部字段。
- 所有派生数据上传 GitHub 备份；本地临时缓存、构建缓存、`.DS_Store`、Python cache 尽量清理。

导航板块：

- Galaxy：主视觉为银河星云/宇宙天体形态，不是简单光点。按重要性、关联性、层级、主题形成核心、旋臂、星云、天体、邻域层级。支持 hover、点击聚焦、相机飞近、局部邻域分层、折叠高连接主题边线。
- 数据导图：应使用框架导图格式展示来源、画像、项目决策和行动机会，不是普通列表。
- ROI Dashboard：显示 leverage score、推荐动作、层级、主题、增量信号；用于 ROI 排序和决策。
- Obsidian Graph：支持 global/local graph、图谱设置折叠、Focus - Connectivity、节点显示名 `层级 · 主题 · 关键词`，并同步 Inspector。
- Timeline：默认使用 Memory River 渲染器，以 UTC 日期尺度展示 Macro / Meso / Micro 河道、主题/项目/分类 lane、密度背景、真实事件日期 tick、播放游标、black-hole / proto-star / event marker；保留 legacy Timeline feature flag 回滚。Stage 5.2 已支持 Pan/Brush 模式、横向拖拽平移、UTC 时间段 brush selection、Interaction Lens / 首页 / 星系 heading 同步、hover/click redacted event card、click 锁定事件并同步 Inspector，以及 Reduced Motion / optional pseudo-haptic / optional audio 的安全反馈设置。Stage 5.3 已支持 black-hole lifecycle band、proto-star lifecycle growth path、stale/deprecated cooling fade layer，均只使用 redacted derived snapshot 信号。
- Contribution Grid：支持日/周/月/年和年份选择。日/周共享 7 行 x 52-54 列全年坐标，周模式以一整列自然周为对象；月/年共享两年 24 列，年视图纵向展示。
- Word Cloud：Heatmap、Bubble Chart、Word Cloud 三层都可点击并同步右侧详情。
- Search/Review：搜索与复盘必须输出人能直接用的结论和行动，不只给数据库字段。
- Summary & Iteration：包含给 ChatGPT/Codex 使用的建议 `Personalization / Memory`、`Agents.md / 执行规则`、`config.toml`、`Memory`，显示更新时间，标明新增/修改/降权含义。
- Shared State Store：`src/state/sharedAtlasState.ts` 统一记录 selected node、cluster、record、time range、signal、data source、tier/layer、category、theme、ROI filter 和 sync revision；Home、Galaxy、Timeline、Inspector、ROI Dashboard 读取同一 focus target。
- Inspector：Stage 6.2 起默认显示人类可读解释、记忆权重公式、ROI leverage 公式、共享焦点公式、参数和脱敏证据摘要；agent 结构化字段和低敏数据库摘要只在手动开启 Debug / Agent Inspector 后显示。

Writeback：

- 前端允许生成长期记忆写回 proposal，但不能直接修改 active memory。
- Stage 6.2 起写回区提供 proposal JSON preview 和 safety strip；前端状态必须保持 `direct_frontend_mutation_of_active_memory=false`、`requires_conflict_check=true`、`requires_agent_or_human_apply=true`。
- proposal 必须包含 diff、版本链、parent proposal id、导出历史、rollback proposal。
- 真正 apply 必须由 agent/human 重新读库、冲突检查、写 history、git commit。

模型参数：

- 每个项目都要维护模型参数文件。
- “模型”是模型假设、处理、方法、策略、输入、输出、迭代。
- “参数”是公式、函数、阈值、门槛、数值。
- 功能清单和开发记录不能冒充模型参数。

## 4. 验收标准

必须通过：

- `python3 scripts/audit_memory_atlas_visual_acceptance.py`
- `python3 scripts/audit_memory_atlas_release.py --publish-dir apps/memory-atlas/dist`
- `python3 scripts/audit_memory_atlas_acceptance.py --publish-dir apps/memory-atlas/dist`
- `python3 scripts/preflight_cloudflare_pages_access.py --publish-dir apps/memory-atlas/dist`
- `npm run build --prefix apps/memory-atlas`
- `npm run validate:shared-state --prefix apps/memory-atlas`
- `npm run validate:inspector-proposal --prefix apps/memory-atlas`
- 关键浏览器 smoke：页面可打开、导航可切换、Timeline 动态控件可见、Obsidian/summary 不空白。

安全验收：

- GitHub 不提交 raw exports、明文 secrets、cookies、sessions、auth files。
- 公开 `memory_atlas.json` 只包含脱敏派生摘要，不包含本地绝对路径、record hashes、raw transcript refs、writeback conflict tokens。
- Finance/trading 等高风险 agent 只能发现 `secret_ref`，不能从 GitHub 读取明文高危 secret；真实交易/支付动作必须 fail closed 并等待用户明确授权。

视觉验收：

- Galaxy 不能退回小学生光点点云。
- Timeline 不能退回 table/list/static scatter。
- Contribution Grid 不能横向溢出或失去全年全景。
- Notion/Obsidian/ROI/Timeline/Word Cloud/Summary 都要有证据承载的视觉形态。

## 5. 历史过程记录

- 2026-06-15：建立 OpenAI-export ingest、记忆蒸馏、周/月复盘、人类版输出、GitHub 备份方向。
- 2026-06-17：确定 Memory Atlas 作为统一可视化平台，优先级 Galaxy > Notion > ROI > Obsidian，同时需要 Timeline 和 Contribution Grid。
- 2026-06-18：补多数据源架构，首页数据源为 总数据源 / ChatGPT / Codex；新增 Codex 本地数据红线：真实脱敏摘要，不上传 raw transcript。
- 2026-06-18：重做 Obsidian Graph、贡献网格、Galaxy 局部邻域、运行缓存释放、本地 app icon 与 Downloads/Applications app 入口。
- 2026-06-19：本轮重点修复 Timeline 动态交互、writeback proposal 版本控制/rollback、模型参数文档边界、交付历史记录。
- 2026-06-19：修复 `.app` 每次打开刷新最新快照时依赖 Documents 仓库权限的问题；installer 现在同步 Application Support source workspace，launcher 每次从该运行副本刷新数据并写入 runtime。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 2.1 默认首页集成计划；当前生产入口仍为 Galaxy，实际切换到 `记忆总览` 延后到 Stage 3.1 实施和浏览器验收。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 2.2 Galaxy 替换计划；当前生产 Galaxy 未替换，新旧 renderer feature flag、回滚路径、截图/FPS/隐私验收进入后续 Stage 4 实施。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 2.3 Timeline 替换计划；当前生产 Timeline 未替换，新旧 renderer feature flag、UTC 时间尺度、brush、hover、Inspector 同步和 reduced motion 验收进入后续 Stage 5 实施。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 2 整体复审；复审确认本阶段只新增计划和记录文件，未替换生产路由、Galaxy、Timeline 或写回行为。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 5.3 Evidence Layers；Memory River 增加黑洞生命周期、机会生命周期和冷却/废弃 fade layer。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 5 整体复审；复审确认 5.1 River Rendering、5.2 River Interaction、5.3 Evidence Layers 均通过，Stage 5 整阶段复审通过，仍未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 6.1 Shared State Store；新增 typed shared-state reducer、selection/filter/time range/focus schema、single-dispatch loop guard、`validate:shared-state` 和 `stage6_1_shared_state_store_ready` visual acceptance 钩子；Home、Galaxy、Timeline、Inspector、ROI Dashboard 共享同一 focus target；Stage 6.2 Inspector/Proposal、Stage 6 整体复审、GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 6.2 Inspector and Proposal；Inspector 默认解释面板显示公式、参数、脱敏证据和人类可读解释；Debug / Agent Inspector 默认关闭；写回区只生成 proposal JSON preview 和本地版本提案，仍不直接修改 active memory；Stage 6 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 6 整体复审；复审确认 6.1 Shared State Store 与 6.2 Inspector/Proposal 均通过，Stage 6 整阶段复审通过，仍未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆，GitHub main 上传需在最终远端检查后执行。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 7.1 Visual Acceptance；新增真实浏览器 `validate:stage7-visual`，自动启动 Vite preview、截图 Galaxy 和 Memory River、验证 Galaxy WebGL 非空像素信号、验证 Memory River 河道/证据层/marker 质量，并确认 4177 关闭后无残留；Stage 7.2 Performance Acceptance、Stage 7.3 Privacy and Accessibility、Stage 7 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 7.2 Performance Acceptance；Galaxy WebGL signal 新增 FPS、frame time、quality threshold、adaptive quality decision 和 cleanup lifecycle；Analysis 模式新增 FPS overlay 和 Auto quality toggle；新增 `validate:stage7-performance`，真实浏览器验证 high quality `>=45 FPS`、mid quality `>=30 FPS`、low quality 不空白、Auto 可恢复、unmount 后 RAF/WebGL 资源释放并确认 4177 无残留；Stage 7.3 Privacy and Accessibility、Stage 7 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 7.3 Privacy and Accessibility；Timeline feedback 增加 reduced motion、伪触感、音频和 silent-by-default DOM contract；新增 `validate:stage7-privacy-accessibility`，扫描发布产物隐私边界、确认 `memory_atlas.json` 为 public redacted read-only visualization、确认默认无 sourcemap、浏览器 emulation 验证 reduced motion 自动启用并禁用播放、验证伪触感/音频默认关闭且 marker 点击不调用 vibration 或 AudioContext；Stage 7 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 7 整体复审；复审确认 7.1 Visual Acceptance、7.2 Performance Acceptance、7.3 Privacy and Accessibility 均通过，新增 `validate:stage7` 保持 phase review、package validators、visual hooks、模型参数、changelog 和交付记录一致；Stage 7 整阶段复审通过，下一阶段为 Stage 8: 打包、部署、回滚；仍未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆，GitHub main 上传需在最终远端检查后执行。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 8.1 Local App Packaging；新增 `validate:stage8-local-app`，真实 production build、临时 app bundle、launcher 单窗口合同和默认 `记忆总览` 路由均通过；installer 增加无 Pillow `.icns` fallback、npm/pnpm fallback、pnpm dependency readiness、Codex runtime PATH 注入和 managed pid cleanup；已重装 `~/Downloads/Memory Atlas.app` 与 `/Applications/Memory Atlas.app`，Application Support runtime manifest 匹配当前 git HEAD；Stage 8.2 Release Safety、Cloudflare live deploy、Access policy change、direct writeback 仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 8.2 Release Safety；新增 `validate:stage8-release-safety`，真实 production build、release audit、overall acceptance audit、source-contract check、真实浏览器 URL rollback、in-app toggle restore、localStorage persistence、screenshot、console/network、文档一致性和 4177 cleanup 均通过；Galaxy 默认 `memory-starfield`、Timeline 默认 `memory-river`，均保留 `legacy` 回滚；Stage 8 整体复审、Cloudflare live deploy、Access policy change、GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 8 整体复审；复审确认 8.1 Local App Packaging 与 8.2 Release Safety 均通过，新增 `validate:stage8` 统一复跑本地 App 打包、release safety、offline Cloudflare Pages + Access preflight、文档一致性和 4177 cleanup；Stage 8 整阶段复审通过，下一阶段为 Stage 9 后续增强迭代；仍未部署 Cloudflare、未修改 Access policy、未读取 raw/private 数据、未直接写回长期记忆；GitHub main 上传需在最终 fast-forward 远端检查后执行。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 9.1 Obsidian Graph E Iteration；Obsidian Graph 新增 bounded local graph budget、selected/hover/local-neighbor/zoom-priority/hub 标签规则和 Galaxy cluster shared-focus 同步；新增 `validate:stage9-obsidian`，真实浏览器验证默认标签密度、局部图预算、Galaxy cluster 同步、截图、console/network 和 4177 cleanup；Stage 9.2 Visual Semantics Enrichment、Stage 9 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 9.2 Visual Semantics Enrichment；首页新增 Memory Weather v2 稳定性/动量/风险/机会/置信度信号，Galaxy Analysis Mode 新增 Memory Terrain v2 语义角色、覆盖率和 ROI Capability Gradient，Memory River 新增 ROI/capability gradient overlay；新增 `validate:stage9-visual-semantics`，真实浏览器验证 Home/Galaxy/Timeline 三面、console/network 和 4177 cleanup；Stage 9 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 9 整体复审；复审确认 9.1 Obsidian Graph E Iteration 与 9.2 Visual Semantics Enrichment 均通过，新增 `validate:stage9` 统一复跑 Stage 9 两个 phase validator、visual acceptance、release audit、overall acceptance、文档一致性和 4177 cleanup；Stage 9 整阶段复审通过，下一阶段为整项目复审；仍未部署 Cloudflare、未修改 Access policy、未读取 raw/private 数据、未直接写回长期记忆；GitHub main 上传需在整项目复审通过并完成 final fast-forward 远端检查后执行。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 1 复审；本轮只覆盖 Phase 0.1 / 0.2 / 0.3，确认 scope/naming freeze、Memory Overview/Starfield/River/Universe State 合同、Phase 0.3 scaffold continuity、fixture safety 和 production isolation；新增 `validate:part1-stage0`，并补充两个 spike README 的 Phase 0.3 scaffold continuity 说明；未进入 Part 2、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 2 复审；本轮只覆盖 Phase 1.1 / 1.2 / 1.3，确认 Memory Starfield Spike、Memory River Spike、Universe State Generator Spike、fixture safety、Universe State schema/sample、parameter drift gate、production isolation 和 build；新增 `validate:part2-stage1`；未进入 Part 3、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 3 复审；本轮只覆盖 Phase 2.1 / 2.2 / 2.3，确认 Default Home Integration Plan、Galaxy Replacement Plan、Timeline Replacement Plan、Stage 2 historical runtime note、当前 later-stage runtime markers、production experiment isolation、build、visual acceptance 和 overall acceptance；新增 `validate:part3-stage2`；未进入 Part 4、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 4 复审；本轮覆盖 Stage 3.1 / 3.2 / Stage 3 overall，确认默认 `记忆总览`、Home Information Architecture、Universe State 状态卡、proposal-only next actions、Mini Starfield、River Pulse、Inspector Deep Link、focus-preserving navigation、visual acceptance hooks、production experiment isolation、build、visual acceptance 和 overall acceptance；新增 `validate:part4-stage3`；未进入 Part 5、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 5 复审；本轮覆盖 Stage 4.1 / 4.2 / 4.3 / Stage 4 overall，确认 `memory-starfield` 默认 Galaxy renderer、legacy rollback、Flow Field trajectories、quality fallback、parameter-backed mass/particle/terrain mapping、hover preview、capped click focus、Freeze/Resume Flow、Presentation/Analysis mode、visual acceptance hooks、production experiment isolation、Starfield mapping/interaction validators、build、visual acceptance 和 overall acceptance；新增 `validate:part5-stage4`，并修正 `validate_memory_starfield_mapping.mjs` 对当前 `Memory Terrain v2 analysis panel` runtime marker 的检查；未进入 Part 6、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 6 复审；本轮覆盖 Stage 5.1 / 5.2 / 5.3 / Stage 5 overall，确认 `memory-river` 默认 Timeline renderer、legacy rollback、UTC time scale、Macro/Meso/Micro river lanes、Pan/Brush interaction、selected-range sync、redacted event cards、safe feedback defaults、black-hole lifecycle、proto-star lifecycle、stale/deprecated evidence layers、visual acceptance hooks、production experiment isolation、Memory River validators、build、release audit、visual acceptance 和 overall acceptance；新增 `validate:part6-stage5`，并修正 `validate_memory_river_interaction.mjs` 对当前 `TimelineTimeRangeSelection = SharedTimelineTimeRangeSelection` 类型别名的检查；未进入 Part 7、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 7 复审；本轮覆盖 Stage 6.1 / 6.2 / Stage 6 overall，确认 shared selection/filter/time-range/focus reducer、cross-view shared focus、filter clearing、loop guard、Inspector explanation panel、proposal-only JSON、Debug separation、visual acceptance hooks、production experiment isolation、Stage 6 validators、build、release audit、visual acceptance 和 overall acceptance；新增 `validate:part7-stage6`；未进入 Part 8、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 8 复审；本轮覆盖 Stage 7.1 / 7.2 / 7.3 / Stage 7 overall，确认真实浏览器视觉截图、Galaxy pixel signal、Memory River 结构、FPS overlay、high/mid FPS thresholds、low-quality non-blank fallback、adaptive quality、cleanup lifecycle、release artifact privacy scan、reduced motion、silent feedback defaults、Stage 7 validators、build、release audit、visual acceptance 和 overall acceptance；新增 `validate:part8-stage7`，并修正 Stage 7.1 / 7.2 / 7.3 模型参数中仍写着 `Stage 7 整体复审未完成` 的旧状态；未进入 Part 9、未进入 Stage 8 复审、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 9 复审；本轮覆盖 Stage 8.1 / 8.2 / Stage 8 overall，确认 local app packaging、release safety、Stage 8 整体复审、renderer rollback、offline Cloudflare preflight、production experiment isolation、Stage 8 validators 和 local app acceptance；新增 `validate:part9-stage8`，重装 `~/Downloads/Memory Atlas.app` 与 `/Applications/Memory Atlas.app`，修复 `/Applications/Memory Atlas.app` 缺失和 runtime manifest 指向旧 commit 的漂移，并把 Stage 8.1 模型参数中的硬编码 runtime commit 改为实时 audit contract；未进入 Part 10、未进入 Stage 9 复审、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 10 复审；本轮覆盖 Stage 9.1 / 9.2 / Stage 9 overall，确认 Obsidian bounded local graph、label rules、Galaxy shared-focus sync、Memory Weather v2、Memory Terrain v2、Galaxy ROI gradient、Memory River ROI/capability gradient、Stage 9 validators、visual acceptance、release audit 和 overall acceptance；新增 `validate:part10-stage9`，并修正 Stage 9 记录中“Stage 9 后直接 GitHub main 上传”的边界，明确下一阶段必须先整项目复审，通过后再做 final remote checks 和 GitHub main 上传；未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 整项目复审；本轮在 Part 1-10 全部复审通过后新增 `validate:whole-project`，统一复跑 Part 1-10 validators、production build、OpenAIDatabase unittest discover、visual acceptance、release audit、overall acceptance、offline Cloudflare preflight、roadmap v2 final acceptance coverage、diff-driven governance sync、canonical remote/upload boundary 和 4177 cleanup；复审发现本地 app runtime 必须在本 commit 后刷新并用 `--require-local-apps` 复验，GitHub main 上传仍需 final remote ancestry、clean tree 和 push target 检查；未上传 GitHub main、未部署 Cloudflare、未修改 Access policy、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 3.1 默认首页实现；`记忆总览` 成为启动板块，左侧导航保留，首页显示 Memory Weather、Universe State 状态卡、Black Hole / Proto-Star 信号和 proposal-only 行动建议；Galaxy 与 Timeline 仍未替换。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 3.2 首页预览组件；首页新增轻量 `Mini Starfield`、近期主题变化 `River Pulse` 和 `Inspector Deep Link`，点击前同步当前焦点再进入 Galaxy、Timeline 或详情检索；Stage 3 整体复审通过，仍未替换 Galaxy/Timeline、未直接写回长期记忆、未读取 raw/private 数据。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 4.1 Galaxy Rendering Integration；`memory-starfield` 成为 Galaxy 默认生产 renderer，`legacy` 可通过 feature flag 回滚；生产 Galaxy 增加 Flow Field 动态、轨迹线、语义信号标记、quality selector 和低质量 fallback，仍未进入 Stage 4.2 数据映射或 Stage 4.3 交互扩展。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 4.2 Data Mapping；生产 Galaxy 的 cluster mass、粒子大小/亮度/颜色、轨迹强度和 Memory Terrain 映射改为读取 `config/visualization/model_parameters.memory_starfield.yaml`；Presentation 保持轻提示，Analysis panel 可解释 ridge、shoreline、valley、basin、fault-line 地形；仍未进入 Stage 4.3 交互扩展、Timeline 替换、写回或 Cloudflare 部署。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 4.3 Starfield Interaction；生产 Galaxy 保留 hover preview 和 capped click focus，新增 Freeze / Resume Flow，新增 Presentation / Analysis mode selector；Analysis 显示公式摘要、terrain legend 和当前 Inspector 上下文；Stage 5 Timeline 替换、写回、Cloudflare 部署和 raw/private data 仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 4 整体复审；复审确认 visual roadmap `记忆星系生产集成` 的 4.1/4.2/4.3 均通过，本地 contract、build、visual acceptance、release acceptance、preview HTTP 和 4177 清理通过；随后用 Chrome CDP 隔离 profile 补齐桌面/移动 WebGL screenshot、canvas-pixel 和 FPS 证据，并修复 390px 移动端 Galaxy 横向溢出与首屏画布露出不足问题。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 5.1 Memory River Rendering；生产 Timeline 默认进入 `memory-river` renderer，保留 `legacy` 回滚；新增 UTC 日期尺度、Macro/Meso/Micro 河道、主题/项目/分类 lane、black-hole/proto-star/event markers、Stage 5.1 validator、visual acceptance 钩子和 Memory River 参数文件更新；Stage 5.2 brush、hover/click event card、多模态反馈仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 5.2 Memory River Interaction；新增 Pan/Brush 模式、pointer pan、UTC brush range selection、range overlay、Interaction Lens/Home/Galaxy range sync、hover/click redacted event card、click lock + Inspector sync、Reduced Motion / optional pseudo-haptic / optional audio 安全反馈设置，并新增 Stage 5.2 validator 和 visual acceptance 钩子；Stage 5.3 evidence layers、Stage 5 整体复审和 GitHub main 上传仍未进入。

近期提交参考：

- `3e50dd2` / `8e25c80` / `12d7a70`：Contribution Grid 趋势渐变与布局优化。
- `f1ec3f9`：Obsidian Graph 重做。
- `ef23323`：Memory Atlas runtime cleanup and visual density。
- 本轮后续提交：Timeline 动态交互、writeback rollback、模型参数/交付记录、Application Support source workspace 启动刷新。

## 6. 待开发清单

高优先级：

- Stage 9.2 Visual Semantics Enrichment：Memory Terrain v2、Memory Weather v2、ROI Visual Gradient。
- Timeline 后续增强多阶段聚类摘要、相邻时间段差异解释，以及 evidence layer 碰撞规避和阈值校准。
- Writeback 增加 agent apply CLI：读取 proposal、冲突检测、写 history、更新 active memory、生成 git rollback commit。
- Summary & Iteration 增加更强人类版输出：ROI 建议、能力成长建议、机会地图、下周行动建议。
- Galaxy 增强天体语义：核心画像为核心星系，项目为旋臂，决策为高亮事件，临时信息为外层低亮星云。

中优先级：

- 数据导图重做为成熟框架导图形态，突出数据来源、画像偏好、项目决策和行动机会。
- ROI Dashboard 加入执行收益、时间投入、机会窗口等真实数据后再升级模型。
- Codex 行为分析加入完成事项、commit、测试通过、报告生成等“有效产出”指标。

低优先级：

- Tauri 桌面封装。
- 多用户/权限模型。
- 远程 MCP search/fetch 只读服务。

## 7. Agent 接手顺序

新 agent 接手时按以下顺序读取：

1. `docs/USER_REQUIREMENTS.md`
2. `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
3. `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
4. `docs/MEMORY_ATLAS_COMPETITOR_ARCHITECTURE_MATRIX.md`
5. `README.md`
6. `scripts/audit_memory_atlas_visual_acceptance.py`
7. `scripts/audit_memory_atlas_acceptance.py`
8. `apps/memory-atlas/src/App.tsx`
9. `apps/memory-atlas/src/components/GalaxyScene.tsx`
10. `apps/memory-atlas/src/components/ObsidianGraphScene.tsx`

停止条件：

- 任何安全审计失败。
- 任何发布目录包含 raw export、secret、cookie/session/auth。
- Timeline/Contribution/Galaxy 等关键视觉板块退化为静态列表或空白画布。
- 本地 app runtime manifest 与当前 git HEAD 不一致。

## 8. Memory Atlas v1.1.6 修补包记录

### Stage 0 Phase 0.1：Encoding & Text Audit

状态：`phase_0_1_contract_created`。

本 phase 是 v1.1.6 修补包的第一轮，只建立中文编码与文本可读性合同，不替换 UI、不修 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/chinese_ui_quality_contract.md`
- `docs/acceptance/chinese_text_audit.md`

本 phase 解决的缺口：

- 乱码与 mojibake 缺少阻断验收。
- 中文主标签、按钮、卡片、Inspector 标签缺少统一规范。
- 表格、按钮、卡片承载长句导致不可读的风险缺少合同约束。
- proposal-only 行为需要在用户界面明确说明“不直接写入长期记忆”。
- 低宽度视口的中文溢出、重叠和横向撑破需要进入验收清单。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 0 Phase 0.1。
- Stage 0 Phase 0.2 `Visual Readability Baseline` 已在后续 phase 单独完成。
- Stage 1-10 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不上传 GitHub main；整 Stage 0 完成、复审并修复后再进入上传流程。

下一步：

- Stage 0 两个 phase 均完成后进行 Stage 0 整体复审，修复复审发现的问题，再准备 GitHub main 上传。

### Stage 0 Phase 0.2：Visual Readability Baseline

状态：`phase_0_2_contract_created_stage_0_review_passed_pending_upload`。

本 phase 是 v1.1.6 修补包的第二轮，只建立页面视觉密度基线和截图验收矩阵，不替换 UI、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/acceptance/visual_density_baseline.md`

本 phase 冻结的视觉门槛：

- 记忆总览视觉化程度 `>= 70%`。
- 记忆星系视觉化程度 `>= 90%`。
- 记忆时间河视觉化程度 `>= 85%`。
- 数据导图视觉化程度 `>= 80%`。

本 phase 解决的缺口：

- 每个板块必须有默认视觉主区，不能只有列表和卡片。
- 记忆星系不得退回普通点线图、随机粒子或普通 Obsidian Graph。
- 记忆时间河不得退回日期列表、表格或静态散点。
- 数据导图必须呈现来源、主题、资产、行动四层结构。
- 后续实现 phase 必须补桌面、平板、移动截图证据，不能只口头说明。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 0 Phase 0.2。
- Stage 0 的 Phase 0.1 / 0.2 均已本地完成，Stage 0 整体复审已通过。
- Stage 1-10 未进入。
- 不上传 GitHub main；需等 Stage 0 复审通过并解决复审暴露问题后再做上传。

复审修复：

- 复审发现 Phase 0.1 / 0.2 有静态检查和记录，但缺少固定的 Stage 0
  review artifact 与 deterministic validator。
- 已新增 `docs/reviews/memory_atlas_v1_1_6_stage0_review.md`。
- 已新增 `validate:v1.1.6-stage0`，用于固定 Phase 0.1 / 0.2 合同、记录、
  review 文档、改动范围和边界。

Stage 0 整体复审状态：`stage_0_review_passed_pending_upload`。

下一步：

- 执行 final remote checks。
- 只 staging 本轮 Stage 0 相关文件，不 staging `.DS_Store`。
- commit 后处理 `origin/main` behind 状态。
- 重新运行 `validate:v1.1.6-stage0` 和可用治理检查。
- 上传 GitHub main。

### Stage 1 Phase 1：Memory Overview Usage Contract

Stage 1 Phase 1 状态：`phase_1_1_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包进入“记忆总览与系统使用说明”的第一轮，只建立可用性合同和验收文件，不替换运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/memory_overview_usage_contract.md`
- `docs/acceptance/memory_overview_usage_acceptance.md`
- `validate:v1.1.6-stage1-phase1`

本 phase 解决的缺口：

- 记忆总览需要被明确为系统操作中枢，而不是欢迎页或普通 dashboard。
- 首页必须能解释今日状态、Memory Weather、建议动作、低价值循环、新生机会、层级资产摘要、主题分类摘要、Mini 记忆星系和记忆时间河脉冲。
- 系统使用说明必须告诉用户如何从总览进入 Inspector、记忆星系、记忆时间河、搜索、复盘、总结与迭代。
- Presentation / Analysis 模式、Inspector 和 Proposal 的边界必须可被用户理解。
- proposal-only 必须保持为前端调整边界，不直接写长期记忆。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 1。
- Stage 1 整体复审未执行。
- Stage 2-5 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- Stage 1 Phase 2 已承接建议动作明细合同；后续继续补层级资产模型和主题分类模型。
- Stage 1 所有 phase 完成后进行 Stage 1 整体复审，修复复审发现的问题。

### Stage 1 Phase 2：Suggested Action Detail Contract

Stage 1 Phase 2 状态：`phase_1_2_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的建议动作明细合同轮次，只定义建议动作展开后的字段、解释、排序、Inspector 交接和 proposal-only 边界，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/suggested_action_detail_contract.md`
- `docs/acceptance/suggested_action_detail_acceptance.md`
- `validate:v1.1.6-stage1-phase2`

本 phase 解决的缺口：

- 建议动作不能只有短句列表，必须能展开为可判断、可追溯、可调整的行动解释。
- 每条建议动作必须包含 reason、ROI、effort cost、urgency、confidence、evidence、next step、proposal hint 和 rollback hint。
- `continue`、`review`、`consolidate`、`explore`、`defer` 五类动作必须有明确语义。
- 点击建议动作进入 Inspector 时必须能解释原因、证据、ROI、努力成本、紧急度和下一步。
- 建议动作只能引导 proposal-only 调整，不得直接写 active memory 或长期记忆。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 2。
- 层级资产和主题分类完整模型未进入。
- Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- Stage 1 Phase 3 已承接层级资产明细模型合同；后续继续补主题分类模型。
- Stage 1 所有 phase 完成后进行 Stage 1 整体复审，修复复审发现的问题。

### Stage 1 Phase 3：Tier Asset Detail Contract

Stage 1 Phase 3 状态：`phase_1_3_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的层级资产明细合同轮次，只定义层级资产展开后的资产层级、字段、排序、Inspector 交接和 proposal-only 边界，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/tier_asset_detail_contract.md`
- `docs/acceptance/tier_asset_detail_acceptance.md`
- `validate:v1.1.6-stage1-phase3`

本 phase 解决的缺口：

- 层级资产不能只有摘要，必须能展开为可判断、可追溯、可调整的结构化资产。
- 层级资产必须覆盖 core_profile、project、decision、workflow、knowledge、opportunity、stale 七类。
- 每个资产必须包含 asset_id、asset_tier、summary、importance、priority、confidence、staleness_status、evidence、linked actions、recommended asset action、proposal hint 和 rollback hint。
- 点击层级资产进入 Inspector 时必须能解释重要性、优先级、置信度、有效性、证据和下一步。
- 层级资产只能引导 proposal-only 调整，不得直接写 active memory 或长期记忆。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 3。
- 主题分类完整模型未进入。
- Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- Stage 1 Phase 4 已承接主题分类明细模型合同；后续继续补 proposal-only 调整入口合同或进入 Stage 1 复审前检查。
- Stage 1 所有 phase 完成后进行 Stage 1 整体复审，修复复审发现的问题。

### Stage 1 Phase 4：Topic Classification Detail Contract

Stage 1 Phase 4 状态：`phase_1_4_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的主题分类明细合同轮次，只定义主题状态、字段、趋势、证据、关联板块、Inspector 交接和 proposal-only 边界，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/topic_classification_detail_contract.md`
- `docs/acceptance/topic_classification_detail_acceptance.md`
- `validate:v1.1.6-stage1-phase4`

本 phase 解决的缺口：

- 主题分类不能只是 tag 列表，必须能展开为可解释、可追溯、可调整的语义聚合。
- 主题分类必须覆盖 dominant、rising、declining、emerging、conflict、black_hole、stale 七类主题状态。
- 每个主题必须包含 topic_strength、trend、confidence、record_count、evidence_count、linked assets、linked actions、matched reason、recommended topic action、proposal hint 和 rollback hint。
- 点击主题分类进入 Inspector 时必须能解释强度、趋势、置信度、记录数、证据和跨板块链接。
- 主题分类只能引导 proposal-only 调整，不得直接写 active memory 或长期记忆。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 4。
- Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- 继续 Stage 1 的下一个 phase，补 proposal-only 调整入口合同或做 Stage 1 复审前收敛检查。
- Stage 1 所有 phase 完成后进行 Stage 1 整体复审，修复复审发现的问题。

### Stage 1 Phase 5：Proposal-only Adjustment Entry Contract

Stage 1 Phase 5 状态：`phase_1_5_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的 proposal-only 调整入口合同轮次，只定义从记忆总览、建议动作明细、层级资产明细、主题分类明细和 Inspector 进入 proposal draft 的安全入口，不实现完整 proposal 编辑工作区、不实现 agent apply、不修改运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/proposal_only_adjustment_entry_contract.md`
- `docs/acceptance/proposal_only_adjustment_entry_acceptance.md`
- `validate:v1.1.6-stage1-phase5`

本 phase 解决的缺口：

- 用户看懂明细后需要能提出 importance、priority、topic_category、action_status、due_window、hidden_until、stale_override 或 confidence_note 调整。
- 调整入口必须说明 proposal draft 不会直接写 active memory。
- 每个 proposal draft 必须包含 proposal_id、parent_snapshot_id、entry_surface、target_type、target_id、field、old_value_ref、proposed_value、reason、evidence_refs、created_at、requires_conflict_check、requires_agent_or_human_apply 和 rollback_hint。
- 调整入口必须覆盖 memory_overview、suggested_action_detail、tier_asset_detail、topic_classification_detail 和 Inspector。
- 后续 apply 必须由 agent/human 在前端之外做冲突检查、history、版本链和 rollback。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 5 的 proposal-only 调整入口合同。
- 完整 Proposal 编辑工作区、agent apply、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- Stage 1 phase 已本地完成，下一轮必须执行 Stage 1 整体复审并修复复审发现的问题。
- Stage 1 整体复审未执行前，不进入 Stage 2，不上传 GitHub main。

### Stage 1 整体复审

Stage 1 整体复审状态：`stage_1_review_passed_pending_stage2`。

本复审覆盖 v1.1.6 Stage 1 Phase 1-5，只确认合同、验收、validator、记录、review artifact 和进入 Stage 2 前边界一致，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage1_review.md`
- `validate:v1.1.6-stage1`

复审发现的问题：

- Phase 1.1-1.5 已有合同、验收和 phase validator，但缺少 Stage 1 整体 review artifact 和 deterministic stage-level validator。

修复：

- 新增 Stage 1 review artifact。
- 新增 `validate:v1.1.6-stage1`。
- 更新 delivery、model、feature、development、model parameter 和 changelog 记录，标记 Stage 1 复审通过并等待 Stage 2。

验收边界：

- Stage 1 复审通过不表示 runtime UI、浏览器截图、完整 Proposal 编辑工作区、agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 2.0 已完成。
- Stage 2-5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

下一步：

- 进入 Stage 2 的第一个 bounded run。
- 若 Stage 1 文件后续变化，必须重新运行 `validate:v1.1.6-stage1`。

### Stage 2 Phase 1：Detail Visibility Workbench Contract

Stage 2 Phase 1 状态：`phase_2_1_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包进入“明细可见性工作台”的第一轮，只定义建议动作、层级资产和主题分类三类明细的统一工作台 IA、展开、筛选、排序、Inspector 交接和 proposal-only 入口提示，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/detail_visibility_workbench_contract.md`
- `docs/acceptance/detail_visibility_workbench_acceptance.md`
- `validate:v1.1.6-stage2-phase1`

本 phase 解决的缺口：

- Stage 1 已定义明细字段，但缺少统一工作台来承载三类明细。
- 工作台必须包含 suggested_action_lane、tier_asset_lane 和 topic_classification_lane。
- 每条明细必须支持 collapsed summary、expanded detail、open_inspector、jump_to_related 和 proposal_only_entry。
- 工作台必须定义 source_scope、confidence、evidence_count、proposal_hint、urgency、effort_cost、action_type、asset_tier、importance、priority、staleness_status、topic_state、trend 和 clear_filters。
- 空态、加载态、错误态必须明确，不允许用 mock 数据伪造明细。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 2 Phase 1 的明细可见性工作台合同。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 Proposal 编辑工作区和 agent apply 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- 继续 Stage 2 的下一个 phase，补建议动作 lane 具体可见性合同或实现隔离原型。
- Stage 2 整体复审未执行前，不进入 Stage 3，不上传 GitHub main。

### Stage 2 Phase 2：Suggested Action Lane Visibility Contract

Stage 2 Phase 2 状态：`phase_2_2_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的 suggested_action_lane 具体可见性合同轮次，只定义建议动作 lane 的扫描行、决策行、证据抽屉、分组排序、状态 badge、展开比较、Inspector 交接和 proposal-only 调整边界，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/suggested_action_lane_visibility_contract.md`
- `docs/acceptance/suggested_action_lane_visibility_acceptance.md`
- `validate:v1.1.6-stage2-phase2`

本 phase 解决的缺口：

- 建议动作不能只作为首页摘要，必须在工作台里可扫描、可比较、可展开证据。
- 每个建议动作必须包含 action_id、title、action_type、reason、roi_score、effort_cost、urgency、confidence、evidence_count、evidence_refs、source_scope、linked_theme_ids、linked_asset_ids、next_step、recommended_time_window、proposal_hint 和 rollback_hint。
- suggested_action_lane 必须支持 now、this_week、later、watch 分组，以及 ROI、urgency、effort、confidence、evidence_count 排序。
- suggested_action_lane 必须支持 expand action、compare actions、pin action、mark reviewed 和 clear temporary state。
- 点击建议动作进入 Inspector 时必须带 source_lane = suggested_action_lane、target_type = suggested_action 和证据/下一步/proposal hint 交接字段。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 2 Phase 2 的 suggested_action_lane 可见性合同。
- tier_asset_lane、topic_classification_lane、Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 Proposal 编辑工作区和 agent apply 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。
- Stage 2 整体复审未执行。

下一步：

- 继续 Stage 2 的下一个 phase，补 tier_asset_lane 具体可见性合同。
- Stage 2 整体复审未执行前，不进入 Stage 3，不上传 GitHub main。

### Stage 2 Phase 3：Tier Asset Lane Visibility Contract

Stage 2 Phase 3 状态：`phase_2_3_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的 tier_asset_lane 具体可见性合同轮次，只定义层级资产 lane 的资产扫描行、决策行、证据抽屉、七类资产分组、排序、状态 badge、展开比较、Inspector 交接和 proposal-only 调整边界，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/tier_asset_lane_visibility_contract.md`
- `docs/acceptance/tier_asset_lane_visibility_acceptance.md`
- `validate:v1.1.6-stage2-phase3`

本 phase 解决的缺口：

- 层级资产不能只作为首页摘要或原始记忆列表，必须在工作台里可扫描、可比较、可展开证据。
- 每个层级资产必须包含 asset_id、asset_tier、title、summary、importance、priority、confidence、staleness_status、evidence_count、evidence_refs、source_scope、linked_action_ids、linked_theme_ids、linked_time_range、recommended_asset_action、proposal_hint 和 rollback_hint。
- tier_asset_lane 必须支持 core_profile、project、decision、workflow、knowledge、opportunity、stale 七类资产分组，以及 importance、priority、staleness_status、confidence、evidence_count 排序。
- tier_asset_lane 必须支持 expand asset、compare assets、pin asset、mark reviewed、jump to linked action 和 clear temporary state。
- 点击层级资产进入 Inspector 时必须带 source_lane = tier_asset_lane、target_type = tier_asset 和证据/关联/下一步/proposal hint 交接字段。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 2 Phase 3 的 tier_asset_lane 可见性合同。
- topic_classification_lane、Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 Proposal 编辑工作区和 agent apply 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。
- Stage 2 整体复审未执行。

下一步：

- 继续 Stage 2 的下一个 phase，补 topic_classification_lane 具体可见性合同。
- Stage 2 整体复审未执行前，不进入 Stage 3，不上传 GitHub main。

### Stage 2 Phase 4：Topic Classification Lane Visibility Contract

Stage 2 Phase 4 状态：`phase_2_4_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的 topic_classification_lane 具体可见性合同轮次，只定义主题分类 lane 的主题扫描行、决策行、证据抽屉、七类主题状态分组、排序、状态 badge、展开比较、Inspector 交接和 proposal-only 调整边界，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/topic_classification_lane_visibility_contract.md`
- `docs/acceptance/topic_classification_lane_visibility_acceptance.md`
- `validate:v1.1.6-stage2-phase4`

本 phase 解决的缺口：

- 主题分类不能只是 tag 列表，必须在工作台里可扫描、可比较、可展开证据。
- 每个主题分类必须包含 topic_id、topic_label、topic_state、topic_strength、trend、confidence、record_count、evidence_count、evidence_refs、source_scope、linked_asset_ids、linked_action_ids、linked_starfield_cluster_id、linked_river_range、related_topic_ids、matched_reason、recommended_topic_action、proposal_hint 和 rollback_hint。
- topic_classification_lane 必须支持 dominant、rising、emerging、conflict、black_hole、declining、stale 七类主题状态分组，以及 topic_strength、trend、confidence、record_count、evidence_count 排序。
- topic_classification_lane 必须支持 expand topic、compare topics、pin topic、mark reviewed、jump to linked asset、jump to linked action、jump to starfield、jump to river 和 clear temporary state。
- 点击主题分类进入 Inspector 时必须带 source_lane = topic_classification_lane、target_type = topic_classification 和证据/关联/下一步/proposal hint 交接字段。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 2 Phase 4 的 topic_classification_lane 可见性合同。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 Proposal 编辑工作区和 agent apply 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。
- Stage 2 整体复审未执行。

下一步：

- 继续 Stage 2 整体复审，补 review artifact 和 stage-level validator，并修复复审暴露的问题。
- Stage 2 整体复审未执行前，不进入 Stage 3，不上传 GitHub main。

### Stage 2 整体复审

Stage 2 整体复审状态：`stage_2_review_passed_pending_stage3`。

本复审覆盖 v1.1.6 Stage 2 Phase 1-4，只确认合同、验收、validator、记录、review artifact 和进入 Stage 3 前边界一致，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage2_review.md`
- `validate:v1.1.6-stage2`

复审发现的问题：

- Phase 2.1-2.4 已有合同、验收和 phase validator，但缺少 Stage 2 整体 review artifact 和 deterministic stage-level validator。

修复：

- 新增 Stage 2 review artifact。
- 新增 `validate:v1.1.6-stage2`。
- 更新 delivery、model、feature、development、model parameter 和 changelog 记录，标记 Stage 2 复审通过并等待 Stage 3。

验收边界：

- Stage 2 复审通过不表示 runtime UI、浏览器截图、完整 Proposal 编辑工作区、agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 2.0 已完成。
- Stage 3-5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

下一步：

- 进入 Stage 3 的第一个 bounded run。
- 若 Stage 2 文件后续变化，必须重新运行 `validate:v1.1.6-stage2`。

### Stage 3 Phase 1：Proposal-only Adjustment Workspace Contract

Stage 3 Phase 1 状态：`phase_3_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S3P01`。

本 phase 是 v1.1.6 修补包进入 proposal-only 调整层的第一轮，只定义 proposal-only 调整工作区的信息架构、字段、schema、状态、diff preview、安全复核、Inspector 交接和 rollback 边界，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply。

新增产物：

- `docs/product/proposal_only_adjustment_workspace_contract.md`
- `docs/acceptance/proposal_only_adjustment_workspace_acceptance.md`
- `validate:v1.1.6-stage3-phase1`

本 phase 解决的缺口：

- Stage 1 只定义 proposal-only 调整入口，尚未定义完整工作区。
- 用户需要在同一工作区看到 proposal_queue、target_context_panel、field_editor_panel、proposal_diff_preview、safety_review_panel 和 rollback_panel。
- 工作区必须允许 proposal-only 调整 importance、priority、topic_category、action_status、due_window、hidden_until、stale_override 和 confidence_note。
- 每个 proposal draft 必须包含 proposal_id、parent_snapshot_id、target_id、field、old_value、proposed_value、reason、created_at、rollback_hint、requires_conflict_check 和 requires_agent_or_human_apply。
- proposal 状态必须区分 draft、needs_review、ready_for_agent_apply、rejected 和 superseded。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 3 Phase 1 的 proposal-only 调整工作区合同。
- agent apply、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

### Stage 8 Phase 1：Release Rollback Contract

Stage 8 Phase 1 状态：`phase_8_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S8P01`。

本 phase 是 v1.1.6 修补包进入“发布、本地 App 与回滚安全”的第一轮，只定义
`memory_atlas_release_rollback_contract` 合同、验收、validator 和治理记录一致性。
它把本地 macOS app、runtime manifest、redacted static artifact、offline
Cloudflare preflight、live deploy authorization gate、rollback matrix、
proposal-only writeback gate 和 cleanup guard 固定为后续发布实现的阻断门槛。

新增产物：

- `docs/product/memory_atlas_release_rollback_contract.md`
- `docs/acceptance/memory_atlas_release_rollback_acceptance.md`
- `validate:v1.1.6-stage8-phase1`

验收边界：

- 运行时 manifest 指向旧 commit、本地 app 服务旧数据、release artifact 包含
  raw/private/cookie/session/secret、未授权 Cloudflare deploy、未授权 Access policy
  change、缺少 Memory Starfield/Memory River rollback path、proposal-only 边界被削弱、
  临时产物无 cleanup 证据或 GitHub upload 先于 final validation，均为未来实现失败条件。
- Stage 8 Phase 1 通过不表示 production build、local app install、Cloudflare live
  deploy、Access policy change、浏览器截图或真实 release audit 已完成。
- 不实现运行时 UI，不修改 CSS，不运行 installer，不执行 production build，不部署
  Cloudflare，不修改 Access policy，不读取 raw/private 数据，不直接写长期记忆，不执行
  agent apply，不进入 Stage 8 整体复审，不进入 Stage 9-10，不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload; No live deploy.

下一步：

- 进入 Stage 8 整体复审，补 review artifact 和 stage-level validator，并解决复审暴露的问题。
- Stage 8 整体复审未执行前，不上传 GitHub main。

### Stage 8 整体复审

Stage 8 复审状态：`stage_8_review_passed_pending_github_main_upload`。

任务 ID：`MA-V116-S8-REVIEW`。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage8_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage8.cjs`
- `validate:v1.1.6-stage8`

复审结论：

- Phase 8.1 Release Rollback Contract、验收、validator 和记录一致。
- Stage 8 缺少 deterministic whole-stage validator 与 review artifact 的缺口已修复。
- Stage 8 已通过整体复审，等待 GitHub main upload gate。

复审边界：

- No runtime UI。
- No CSS change。
- No browser screenshot run。
- No production build。
- No installer run。
- No local app install or rebuild。
- No app bundle or runtime cache mutation。
- No Cloudflare live deploy。
- No Access policy change。
- No raw/private data read。
- No direct writeback。
- No GitHub main upload。

下一 gate：

- 先执行 final remote checks、`validate:v1.1.6-stage8-phase1`、
  `validate:v1.1.6-stage8`、项目级 acceptance audit 和 diff check。
- 再上传 canonical GitHub main tree。

### Stage 9 Phase 1：Memory Starfield C3 Spike

Stage 9 Phase 1 状态：`phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review`。

任务 ID：`MA-V116-S9P01`。

本 phase 是 v1.1.6 修补包进入 C3 隔离原型的第一轮，只固定
`memory-starfield-spike` 作为记忆星系的独立原型证据，不替换 production Galaxy，
不导入 experiment，不进入 Stage 9 整体复审。

新增产物：

- `docs/product/memory_starfield_c3_spike_contract.md`
- `docs/acceptance/memory_starfield_c3_spike_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase1.cjs`
- `validate:v1.1.6-stage9-phase1`

验收边界：

- spike 必须保留 Three.js canvas、particle LOD、nebula dust、Flow Field、
  gravitational disk、Black Hole marker、Proto-Star marker、Memory Terrain
  cluster、hover card、reduced-motion control 和 smoke status hook。
- `fixture.ts` 必须保持 raw/private、plaintext secrets 和 local absolute path
  标志为 false。
- production `src` 不得 import 或 reference `memory-starfield-spike`。
- 本 phase 不 production integration、不 build、不运行浏览器截图、不安装本地 app、
  不部署 Cloudflare、不修改 Access policy、不读取 raw/private、不直接写长期记忆、
  不上传 GitHub main。

Machine-readable boundary summary: No production integration; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- Stage 9 Phase 2 应进入 Memory River C3 Spike 或下一个 Roadmap v2 C3 原型。
- Stage 9 整体复审未执行前，不上传 GitHub main。

### Stage 6 整体复审

Stage 6 状态：`stage_6_review_passed_pending_github_main_upload`。

任务 ID：`MA-V116-S6-REVIEW`。

本复审覆盖 v1.1.6 Stage 6 Phase 1 Memory River Rebuild Contract，只确认
`memory_river_rebuild_contract` 合同、验收、validator、review artifact、
package script 和治理记录一致。不实现运行时 UI、不修改 CSS、不实现 Memory
River runtime、不读取 raw/private 数据、不直接写长期记忆、不执行 agent
apply、不进入 Stage 7、不在 review artifact 中执行 GitHub main 上传。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage6_review.md`
- `validate:v1.1.6-stage6`

验收边界：

- Stage 6 复审通过不表示 runtime Memory River、浏览器截图、真实 zoom/brush
  交互或 agent apply 已完成。
- Stage 7 必须在 Stage 6 上传校验通过后另起 bounded run。
- 不 commit `.DS_Store`。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 继续 Stage 3 的下一个 phase，补 proposal-only 工作区的持久化/队列或复审前收敛检查。
- Stage 3 整体复审未执行前，不进入 Stage 4，不上传 GitHub main。

### Stage 3 Phase 2：Proposal Queue Persistence Contract

Stage 3 Phase 2 状态：`phase_3_2_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S3P02`。

本 phase 是 v1.1.6 修补包 proposal-only 调整层的第二轮，只定义 proposal queue 持久化与版本链合同，不实现运行时 UI、不修改 CSS、不启动浏览器、不写 localStorage、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply。

新增产物：

- `docs/product/proposal_queue_persistence_contract.md`
- `docs/acceptance/proposal_queue_persistence_acceptance.md`
- `validate:v1.1.6-stage3-phase2`

本 phase 解决的缺口：

- Stage 3 Phase 1 定义了工作区，但没有固定本地 proposal queue 的持久化键、追加策略和版本链。
- proposal queue 必须固定为 `memory-atlas.writeback.proposals.v1`，范围为 `browser_local_only`，变更策略为 `append_only`。
- 每个 proposal_record 必须保留 proposal_id、revision、parent_proposal_id、supersedes_proposal_id、rollback_to_proposal_id、parent_snapshot_id、target_ref、target_type、target_id、field、old_value_ref、proposed_value、diff_summary、reason、evidence_refs、status、created_at、updated_at、requires_conflict_check、requires_agent_or_human_apply 和 rollback_hint。
- proposal_history 必须记录状态变化、替代和 rollback_proposal，不能静默覆盖旧 proposal。
- stale_snapshot、schema_mismatch 和 forbidden_payload 必须作为阻断状态显式可见。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 3 Phase 2 的 proposal queue 持久化与版本链合同。
- agent apply、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 3 整体复审，补 review artifact 和 stage-level validator，并修复复审暴露的问题。
- Stage 3 整体复审未执行前，不进入 Stage 4，不上传 GitHub main。

### Stage 3 整体复审

Stage 3 整体复审状态：`stage_3_review_passed_pending_stage4`。

任务 ID：`MA-V116-S3-REVIEW`。

本复审覆盖 v1.1.6 Stage 3 Phase 1-2，只确认 proposal-only 调整工作区、proposal queue 持久化与版本链的合同、验收、validator、记录、review artifact 和进入 Stage 4 前边界一致，不实现运行时 UI、不修改 CSS、不写 localStorage、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage3_review.md`
- `validate:v1.1.6-stage3`

复审发现的问题：

- Phase 3.1-3.2 已有合同、验收和 phase validator，但缺少 Stage 3 整体 review artifact 和 deterministic stage-level validator。

修复：

- 新增 Stage 3 review artifact。
- 新增 `validate:v1.1.6-stage3`。
- 更新 delivery、model、feature、development、model parameter 和 changelog 记录，标记 Stage 3 复审通过并等待 Stage 4。

验收边界：

- Stage 3 复审通过不表示 runtime UI、浏览器截图、真实 localStorage queue、agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 2.0 已完成。
- Stage 4-5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 4 的第一个 bounded run。
- 若 Stage 3 文件后续变化，必须重新运行 `validate:v1.1.6-stage3`。

### Stage 4 Phase 1：Search 2.0 Workflow Contract

Stage 4 Phase 1 状态：`phase_4_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S4P01`。

本 phase 覆盖 v1.1.6 Search 2.0 工作流合同，只确认 `search_2_0_workflow`、query/filter、result list、`matched_reason`、`jump_to_starfield`、`jump_to_river`、`open_inspector`、session summary、zero-result recovery、proposal-only handoff、安全边界、validator 和记录一致，不实现运行时 UI、不修改 CSS、不建立真实搜索索引、不读取 raw/private 数据、不直接写长期记忆、不进入 Review / Summary / Iteration、不进入 Data Map 2.0、不上传 GitHub main。

新增产物：

- `docs/product/search_2_0_workflow_contract.md`
- `docs/acceptance/search_2_0_workflow_acceptance.md`
- `validate:v1.1.6-stage4-phase1`

验收边界：

- Stage 4 Phase 1 通过不表示 runtime Search 2.0、浏览器截图、Review / Summary / Iteration 或 Data Map 2.0 已完成。
- Stage 4 整体复审未执行。
- Stage 5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 4 Phase 2：Review / Summary / Iteration 合同。
- Stage 4 整体复审未执行前，不进入 Stage 5，不上传 GitHub main。

### Stage 4 Phase 2：Review / Summary / Iteration Workflow Contract

Stage 4 Phase 2 状态：`phase_4_2_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S4P02`。

本 phase 覆盖 v1.1.6 Review / Summary / Iteration 工作流合同，只确认 `review_summary_iteration_workflow`、八个复盘问题、theme_change_panel、opportunity_panel、low_value_loop_panel、decision_change_panel、next_action_panel、proposal_decision_panel、iteration_backlog、安全边界、validator 和记录一致，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply、不进入 Data Map 2.0、不上传 GitHub main。

新增产物：

- `docs/product/review_summary_iteration_workflow_contract.md`
- `docs/acceptance/review_summary_iteration_workflow_acceptance.md`
- `validate:v1.1.6-stage4-phase2`

验收边界：

- Stage 4 Phase 2 通过不表示 runtime Review / Summary / Iteration、浏览器截图、Data Map 2.0 或 Stage 4 整体复审已完成。
- Stage 4 整体复审未执行。
- Stage 5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 4 整体复审，补 review artifact 和 stage-level validator，并解决复审暴露的问题。
- Stage 4 整体复审未执行前，不进入 Stage 5，不上传 GitHub main。

### Stage 4 整体复审

Stage 4 整体复审状态：`stage_4_review_passed_pending_stage5`。

任务 ID：`MA-V116-S4-REVIEW`。

本复审覆盖 Stage 4 Phase 1 Search 2.0 Workflow Contract 和 Stage 4
Phase 2 Review / Summary / Iteration Workflow Contract，只确认合同、验收、
phase validator、review artifact、stage-level validator、记录一致性、改动
范围和安全边界。不实现运行时 UI、不修改 CSS、不建立真实搜索索引、不实现复盘
runtime、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply、不进入
Data Map 2.0 runtime、不进入 Stage 5、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage4_review.md`
- `validate:v1.1.6-stage4`

复审结论：

- Stage 4 Phase 1 Search 2.0 合同、验收、validator 和记录一致。
- Stage 4 Phase 2 Review / Summary / Iteration 合同、验收、validator 和记录一致。
- 复审发现的 deterministic stage-level validator/review artifact 缺口已修复。
- Stage 4 整体复审通过，进入 `stage_4_review_passed_pending_stage5`。

验收边界：

- Stage 4 复审通过不表示 runtime Search 2.0、runtime Review / Summary /
  Iteration、浏览器截图或 Data Map 2.0 已完成。
- Stage 5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 5 的第一个 bounded run。
- 若 Stage 4 文件后续变化，必须重新运行 `validate:v1.1.6-stage4`。

### Stage 5 Phase 1：Data Map 2.0 Workflow Contract

Stage 5 Phase 1 状态：`phase_5_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S5P01`。

本 phase 覆盖 v1.1.6 Data Map 2.0 工作流合同，只确认
`data_map_2_0_workflow`、source_layer、topic_layer、asset_layer、
action_layer、data_to_action_flow、source_to_topic_edges、topic_to_asset_edges、
asset_to_action_edges、map_card 字段、Inspector/Search/Review 跳转、
proposal-only handoff、安全边界、validator 和记录一致。不实现运行时 UI、
不修改 CSS、不实现 Data Map renderer、不读取 raw/private 数据、不直接写长期记忆、
不执行 agent apply、不进入 Stage 5 整体复审、不上传 GitHub main。

新增产物：

- `docs/product/data_map_2_0_workflow_contract.md`
- `docs/acceptance/data_map_2_0_workflow_acceptance.md`
- `validate:v1.1.6-stage5-phase1`

验收边界：

- Stage 5 Phase 1 通过不表示 runtime Data Map 2.0、浏览器截图或 Stage 5
  整体复审已完成。
- Stage 5 整体复审未执行。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 5 整体复审，补 review artifact 和 stage-level validator，并解决复审暴露的问题。
- Stage 5 整体复审未执行前，不上传 GitHub main。

### Stage 5 整体复审

Stage 5 状态：`stage_5_review_passed_pending_stage1_5_final_upload`。

任务 ID：`MA-V116-S5-REVIEW`。

本复审覆盖 v1.1.6 Stage 5 Phase 1 Data Map 2.0 Workflow Contract，只确认
`data_map_2_0_workflow` 合同、验收、validator、review artifact、package
script 和治理记录一致。不实现运行时 UI、不修改 CSS、不实现 Data Map
runtime、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply、不进入
Stage 6、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage5_review.md`
- `validate:v1.1.6-stage5`

验收边界：

- Stage 5 复审通过不表示 runtime Data Map 2.0、浏览器截图或 agent apply
  已完成。
- Stage 1-5 final upload 未执行。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 final upload gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

### Stage 6 Phase 1：Memory River Rebuild Contract

Stage 6 Phase 1 状态：`phase_6_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S6P01`。

本 phase 是 v1.1.6 修补包进入“记忆时间河重做”的第一轮，只定义
`memory_river_rebuild_contract` 合同、验收、validator 和治理记录一致性。
它把旧 Timeline 按 0 分处理，要求未来实现必须展示 `time_river`、
`theme_bands`、`event_pulses`、`decision_nodes`、`black_hole_band`、
`proto_star_marker` 和 `evidence_density_lane`，并支持 zoom、brush、
hover card、click Inspector、keyboard navigation 和 reduced motion。

新增产物：

- `docs/product/memory_river_rebuild_contract.md`
- `docs/acceptance/memory_river_rebuild_acceptance.md`
- `validate:v1.1.6-stage6-phase1`

验收边界：

- 默认日期列表、静态表格、普通 dots-and-lines timeline、缺少生命周期 marker、
  缺少 Inspector 交接或 reduced motion 被忽略，均为未来实现失败条件。
- Stage 6 Phase 1 通过不表示 runtime Memory River、浏览器截图或真实交互已完成。
- 不实现运行时 UI，不修改 CSS，不读取 raw/private 数据，不直接写长期记忆，
  不执行 agent apply，不进入 Stage 7-10，不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 执行 Stage 1-5 final upload gate：fetch/integrate、重跑 Stage 1-5 validators、
  可用 governance checks、确认 changed files、避免 staging `.DS_Store`。
- final upload gate 未通过前，不上传 GitHub main。

### Stage 7 Phase 1：Memory Starfield Rebuild Contract

Stage 7 Phase 1 状态：`phase_7_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S7P01`。

本 phase 是 v1.1.6 修补包进入“记忆星系重做”的第一轮，只定义
`memory_starfield_rebuild_contract` 合同、验收、validator 和治理记录一致性。
它把普通 dots-and-lines、node-link graph、Obsidian-like graph 或 chart-like
network 明确列为未来实现失败条件，要求未来实现必须展示
`memory_starfield`、`nebula_field`、`flow_field`、`trajectory_trails`、
`gravity_sources`、`black_hole_core`、`proto_star_cloud`、
`memory_terrain_layer`、`cluster_constellations` 和
`ambient_depth_particles`，并支持 orbit pan/zoom、hover card、click
Inspector、focus cluster、Search 2.0 跳转、Memory River 跳转、Presentation /
Analysis 模式、keyboard navigation 和 reduced motion。

新增产物：

- `docs/product/memory_starfield_rebuild_contract.md`
- `docs/acceptance/memory_starfield_rebuild_acceptance.md`
- `validate:v1.1.6-stage7-phase1`

验收边界：

- 默认只有点、只有边线、普通 Obsidian Graph、缺少星云、缺少流场、缺少轨迹、
  缺少引力源、缺少黑洞、缺少新生星云、缺少记忆地形层、缺少 Inspector 交接、
  WebGL/fallback 空白或 reduced motion 被忽略，均为未来实现失败条件。
- Stage 7 Phase 1 通过不表示 runtime Memory Starfield、浏览器截图或真实交互已完成。
- 不实现运行时 UI，不修改 CSS，不导入 experiment 目录，不切换 feature flag，
  不读取 raw/private 数据，不直接写长期记忆，不执行 agent apply，不进入 Stage 7
  整体复审，不进入 Stage 8-10，不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 7 整体复审，补 review artifact 和 stage-level validator，并解决复审暴露的问题。
- Stage 7 整体复审未执行前，不上传 GitHub main。

### Stage 7 整体复审

Stage 7 状态：`stage_7_review_passed_pending_github_main_upload`。

任务 ID：`MA-V116-S7-REVIEW`。

本复审覆盖 v1.1.6 Stage 7 Phase 1 Memory Starfield Rebuild Contract，只确认
`memory_starfield_rebuild_contract` 合同、验收、validator、review artifact、
package script 和治理记录一致。不实现运行时 UI、不修改 CSS、不实现 Memory
Starfield runtime、不导入 experiment 目录、不切换 feature flag、不读取
raw/private 数据、不直接写长期记忆、不执行 agent apply、不进入 Stage 8、不上传
GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage7_review.md`
- `validate:v1.1.6-stage7`

验收边界：

- Stage 7 复审通过不表示 runtime Memory Starfield、浏览器截图、WebGL/fallback
  canvas、真实 Search/River focus handoff 或 agent apply 已完成。
- Stage 8 未进入。
- GitHub main upload 只在 final remote checks 通过后执行。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.
