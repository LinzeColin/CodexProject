# Memory Atlas 竞品与架构矩阵

日期：2026-06-17

## 1. Executive Summary

Memory Atlas 应保持为一个合并运行的平台：同一个 Vite + React + Three.js
前端、同一个左侧导航、同一套筛选器、同一个派生可视化快照。不同来源数据
只作为 `source slice` 切换，不拆成多个 app、插件或页面体系。

本轮调研后的默认决策：

1. 继续采用 `统一平台 + 可选择数据来源 + 共享可视化视图`。
2. 当前优先数据源是 `Codex 本地数据` 和 `Memory Atlas / OpenAI Export 记忆库`。
3. Galaxy 是第一主视图，贡献网格是行为强度和增量分析入口，Recommendation 是给人和 agent 更新画像/规则的入口。
4. 前端允许生成长期记忆修改建议，但只能生成 versioned proposal；真实写回必须由受信任 agent 检查、提交、可回滚。
5. Cloudflare Pages + Access 只部署脱敏派生快照；本地原始数据、secret、raw transcript、SQLite 原始索引不进入部署产物。

## 2. 一手来源核对

| 来源 | 核心发现 | 对 Memory Atlas 的约束 |
| --- | --- | --- |
| Obsidian Graph View | 官方 Graph View 包含 global graph、local graph、filters、groups、force、link distance、time-lapse；local graph 支持 depth。Source: https://obsidian.md/help/plugins/graph | Obsidian Graph 只吸收“全局/局部图谱 + 深度 + 筛选”，不能变成文件 vault 插件。 |
| Notion database views | Notion 同一数据库可显示为 table/list/board/gallery/calendar/timeline，可增加多个 views，并支持 group/filter/sort。Source: https://www.notion.com/help/guides/using-database-views | Memory Atlas 的多个视图必须共享同一数据切片和筛选状态，不能变成卡片式 Notion clone。 |
| Notion Timeline | Timeline 用于观察项目在时间上的进展，可拖动时长、回到 today、显示左侧 table、显示/隐藏 properties。Source: https://www.notion.com/help/timelines | Timeline 应做成时间轴/泳道/事件地图，不退化为 table/list。 |
| GitHub Contributions | GitHub contribution graph 展示过去一年贡献；可点选某天，可按范围选取，右侧年份用于浏览旧活动；贡献按 UTC 计。Sources: https://docs.github.com/en/account-and-profile/concepts/contributions-on-your-profile, https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/viewing-contributions-on-your-profile | Contribution Grid 应作为行为强度和增量分析，不照搬 GitHub 的贡献定义；日/周/月/年必须有 hover 和点击详情。 |
| Neo4j Bloom | Bloom 是图数据探索应用，支持 Perspectives、search、scene interactions、property inspection、graph edit、graph data science integration。Sources: https://neo4j.com/docs/bloom-user-guide/current/, https://neo4j.com/docs/bloom-user-guide/current/about-bloom/ | 吸收 search-first 和 perspective 思路；禁止前端直接改底层记忆，所有写回走 proposal。 |
| Kumu | Kumu 支持系统/关系图，并可运行 Social Network Analysis metrics；被过滤掉的元素不参与指标计算。Source: https://docs.kumu.io/guides/metrics | ROI Dashboard 和图谱应显示 hub/connector/孤岛/高杠杆记忆，且指标必须受当前筛选影响。 |
| Gephi | Gephi 强项是网络导入、交互过滤、布局算法、属性样式、导出，以及 dynamic network timeline。Sources: https://gephi.org/, https://docs.gephi.org/desktop/User_Manual/Import_Dynamic_Data/ | Memory Atlas 可吸收布局和动态网络概念，但不应要求用户进入专业桌面分析工具。 |
| OpenAI Memory | ChatGPT Memory 可查看 summary、编辑、不要再提、删除；history 可恢复 prior versions；saved memory 不等于完整聊天历史。Source: https://help.openai.com/en/articles/8590148-memory-faq | Memory Atlas 的 Memory/Meta Data 建议必须标注新增、修改、删除/降权、当前项，并保留历史备份与版本回滚。 |

## 3. 竞品能力矩阵

| 产品/模式 | 成熟能力 | 适合吸收 | 不应复制 | Memory Atlas 决策 |
| --- | --- | --- | --- | --- |
| Obsidian Graph | 全局图、局部图、深度、分组、过滤、力导向调参 | Obsidian Graph 视图、局部上下文、连接强度、孤立点观察 | 文件夹 vault 心智、插件依赖、图内标签噪音 | 节点代表 memory/theme/project/decision/source；右侧 Inspector 同步。 |
| Notion Views | 同一数据多视图、filter/sort/group、timeline、chart | 左侧导航 + 共享筛选 + 多视图同步 | 重卡片、项目管理 clone、第三方依赖 | source 选择只改变数据，不改变平台结构。 |
| GitHub Contributions | 年度行为网格、hover、点击日期、年份浏览 | AI agent 使用强度、消息/tool call/记忆增量、异常信号 | GitHub 贡献规则、绿色单色热力、只能日粒度 | 日/周共享 7 行 x 52-54 列；月/年共享 24 列两年面板。 |
| Neo4j Bloom | 图搜索、perspective、scene action、属性检查、图算法 | search-first 探索、业务视角、关系洞察 | 前端直接编辑图数据库 | Recommendation/写回只生成 proposal；真实变更由 agent 审核提交。 |
| Kumu | 系统图、网络指标、hub/connector 发现、演示叙事 | ROI/high-leverage 节点、机会地图、弱连接发现 | 手工维护地图、协作编辑直接覆盖数据库 | 指标随筛选实时变化，输出建议优先服务 ROI 和成长。 |
| Gephi | 高级布局算法、动态网络、属性编码、导出 | 可借鉴动态图谱、timeline replay、社区结构 | 复杂桌面工作流、专家工具门槛 | 前端保持可用；高级分析留给未来导出/离线脚本。 |
| ActivityWatch 类本地采集 | local-first watcher、行为数据采集、隐私边界 | Codex 周期性同步、来源适配器、最小必要采集 | 全盘监控、上传 raw 行为日志 | 只采集 Codex/OpenAI 明确来源；提交脱敏摘要和派生指标。 |
| ChatGPT Memory | summary、source、edit、prioritize/deprioritize、history | Memory/Meta Data 建议、版本历史、personalization pack | 只依赖 Settings 里的 executive summary | GitHub 是 durable memory database；ChatGPT Memory 只是 compact output target。 |

## 4. 架构矩阵

| 层 | 职责 | 必须具备 | 明确不做 |
| --- | --- | --- | --- |
| Raw Sources | OpenAI export、Codex 本地 session/log、未来浏览器/Notion/finance 等来源 | source adapter、只读扫描、raw 本地保留或加密归档 | 上传 raw transcript、cookies、session、broker credential、plaintext secret |
| Source Normalization | 把不同来源转为统一事件、记忆候选、行为 bucket | `source_id`、timestamp、activity metrics、topic/profile/preference signals | 各来源各做一套前端 |
| Memory Database | active memory、candidate、profile、project index、decision log、timeline、secret_ref | GitHub-backed RAG/search/fetch；任意 agent 可读取画像/偏好/历史 | 依赖聊天上下文或 ChatGPT settings memory |
| Derived Analytics | `data/processed/*` 与 `data/derived/*` | 脱敏、可 diff、可重建、可审计 | 混入 raw 内容或本地绝对敏感路径 |
| Visualization Snapshot | `data/derived/visualization/memory_atlas.json` | 单文件快照、source selectable、公开部署安全 | 包含 raw source refs、record hashes、local secrets、SQLite |
| Frontend Shell | Galaxy、Notion Map、ROI、Obsidian、Timeline、Contribution、Search、Recommendation | 中文 UI、左侧导航、状态同步、页面不滚动、右侧 Inspector | 每个来源独立 app 或第三方插件 |
| Recommendation | Memory / Meta Data 两板块 | 新增、修改、删除/降权、当前项；人类可理解；agent 可写入 personalization/AGENTS.md | 只输出 agent 内部字段 |
| Writeback | 前端提交长期记忆修改建议 | versioned proposal、冲突检查、git commit、可回滚 | 静态前端直接改 active memory |
| Automation | Codex weekly sync、build atlas、commit/push | LaunchAgent、日志、失败可见、幂等 | 静默失败、无限缓存、未验证即标记完成 |
| Deployment | 本地 `.app`、Cloudflare Pages + Access、未来 Tauri | 本地优先；Cloudflare 只发布脱敏快照；Tauri 稳定后再考虑 | 未受保护公网部署；过早重写 native app |

## 5. 方案决策矩阵

| 方案 | ROI | 工程风险 | 长期可维护性 | 推荐结论 |
| --- | --- | --- | --- | --- |
| 统一 Memory Atlas 平台 + source slice | 高：一次开发，多数据源复用 | 中：数据契约要稳 | 高 | 默认方案。当前继续走这条。 |
| 每个来源独立 app | 低：重复 UI/部署/验收 | 高：碎片化 | 低 | 不采用。 |
| Obsidian/Notion 插件 | 中：借现成生态 | 高：权限、依赖、迁移受限 | 中低 | 不作为主交付，只借鉴交互。 |
| 纯 Dashboard/表格 | 中：实现快 | 低 | 中 | 只能做 ROI 子视图，不能承载记忆关系。 |
| Neo4j/Gephi 专业图工具 | 中：分析强 | 高：用户使用门槛高 | 中 | 可作为未来导出/高级分析，不作为默认运行方式。 |
| Tauri native app | 中高：体验更像本地软件 | 中高：打包、签名、更新复杂 | 中 | 稳定后再评估；当前不提前迁移。 |

## 6. 当前交付边界

本阶段必须完成：

1. `Memory Atlas.app` 在 Downloads 和 Applications 都有入口、图标、可启动。
2. 首页/全局筛选可选择 `全部来源`、`Memory Atlas / OpenAI Export 记忆库`、`Codex 本地数据`。
3. 选择来源后 Galaxy、Notion Map、ROI、Obsidian、Timeline、Contribution、Search、Recommendation 同步更新。
4. Codex 数据使用真实本地 Codex session/log 派生摘要，不使用 mock 数据。
5. Contribution Grid 的日/周/月/年和年份下拉只显示有历史的年份。
6. Recommendation 包含 `Memory（给 ChatGPT / Codex Personalization）` 与 `Meta Data（给 ChatGPT / Codex Agents.md）`，并标注新增、修改、删除/降权、当前项。
7. 所有派生数据、需求、架构、验收脚本、同步脚本都提交到 GitHub。
8. 本地缓存清理，保持电脑瘦身；不清理 raw source 和加密归档。

暂不算完成的外部 gate：

1. Cloudflare Pages live deploy。
2. Cloudflare Access 登录挑战验证。
3. Tauri 迁移。

## 7. 默认推荐

短期继续投入统一 Memory Atlas，而不是引入第三方插件或 native 重写。最有 ROI
的下一轮是：

1. 把 Codex 数据分析从“活动统计”升级到“行为习惯、执行质量、ROI、成长路径”。
2. 给 Contribution Grid 点击详情增加更强的人类解释和建议。
3. 给 Galaxy/Graph/Timeline 加同一套 selection intelligence：点击任何对象都能知道它说明什么、为什么重要、下一步怎么用。
4. Cloudflare Pages + Access 在获得用户明确授权后做 live deploy 验证。
5. 稳定 2-3 轮后再重新评估 Tauri。
