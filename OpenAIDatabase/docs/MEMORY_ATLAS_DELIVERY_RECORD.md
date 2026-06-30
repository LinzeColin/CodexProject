# Memory Atlas Delivery Record

更新时间：2026-06-19

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
- 所有板块共享筛选状态、数据源选择、主题/层级/分类筛选和右侧详情同步。
- 所有页面默认可视化程度目标 80%+；列表只能作为 drill-down，不能成为主体验。
- 人类版输出优先：话题、需要做什么、记得做什么、建议做什么、机会、风险、ROI、能力成长，不只显示 agent 内部字段。
- 所有派生数据上传 GitHub 备份；本地临时缓存、构建缓存、`.DS_Store`、Python cache 尽量清理。

导航板块：

- Galaxy：主视觉为银河星云/宇宙天体形态，不是简单光点。按重要性、关联性、层级、主题形成核心、旋臂、星云、天体、邻域层级。支持 hover、点击聚焦、相机飞近、局部邻域分层、折叠高连接主题边线。
- 数据导图：应使用框架导图格式展示来源、画像、项目决策和行动机会，不是普通列表。
- ROI Dashboard：显示 leverage score、推荐动作、层级、主题、增量信号；用于 ROI 排序和决策。
- Obsidian Graph：支持 global/local graph、图谱设置折叠、Focus - Connectivity、节点显示名 `层级 · 主题 · 关键词`，并同步 Inspector。
- Timeline：必须是真实动态可交互 Timeline。支持真实日期轴、动态窗口、缩放、播放游标、密度轨、密度背景、hover 详情、点击同步 Inspector。
- Contribution Grid：支持日/周/月/年和年份选择。日/周共享 7 行 x 52-54 列全年坐标，周模式以一整列自然周为对象；月/年共享两年 24 列，年视图纵向展示。
- Word Cloud：Heatmap、Bubble Chart、Word Cloud 三层都可点击并同步右侧详情。
- Search/Review：搜索与复盘必须输出人能直接用的结论和行动，不只给数据库字段。
- Summary & Iteration：包含给 ChatGPT/Codex 使用的建议 `Personalization / Memory`、`Agents.md / 执行规则`、`config.toml`、`Memory`，显示更新时间，标明新增/修改/降权含义。

Writeback：

- 前端允许生成长期记忆写回 proposal，但不能直接修改 active memory。
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
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 3.1 默认首页实现；`记忆总览` 成为启动板块，左侧导航保留，首页显示 Memory Weather、Universe State 状态卡、Black Hole / Proto-Star 信号和 proposal-only 行动建议；Galaxy 与 Timeline 仍未替换。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 3.2 首页预览组件；首页新增轻量 `Mini Starfield`、近期主题变化 `River Pulse` 和 `Inspector Deep Link`，点击前同步当前焦点再进入 Galaxy、Timeline 或详情检索；Stage 3 整体复审通过，仍未替换 Galaxy/Timeline、未直接写回长期记忆、未读取 raw/private 数据。

近期提交参考：

- `3e50dd2` / `8e25c80` / `12d7a70`：Contribution Grid 趋势渐变与布局优化。
- `f1ec3f9`：Obsidian Graph 重做。
- `ef23323`：Memory Atlas runtime cleanup and visual density。
- 本轮后续提交：Timeline 动态交互、writeback rollback、模型参数/交付记录、Application Support source workspace 启动刷新。

## 6. 待开发清单

高优先级：

- Timeline 增加刷选区间、多阶段聚类摘要、相邻时间段差异解释。
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
