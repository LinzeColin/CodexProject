# Agent Context Pack

固定入口：给任意 ChatGPT / Codex / future agent 启动时读取。

- 生成时间：2026-07-01T05:50:06Z
- 数据来源：OpenAIDatabase redacted derived memory surfaces
- 覆盖 Codex：2026-06-29 至 2026-07-01，16 个 session，11661 条消息，53580 次工具调用。
- Memory Atlas：340 个节点，1771 条边。
- 数据源注册表：memory_atlas_data_source_registry.v1，当前 2 个 active，3 个 planned。

## Agent 启动规则

- 新 agent 启动后先读取本文件、CORE_PROFILE 和 Memory Atlas，再生成适配用户的 profile、preference、project context、rules 和 history summary；不要依赖聊天上下文猜测。
- 默认中文输出；代码、API、库名、错误信息和专业术语可保留英文。
- 使用真实数据和可验证证据；不要使用 mock、伪进度或只给概念演示。
- 新增微信、小红书、抖音等平台数据时，先按数据源注册表输出脱敏派生事件；未接入真实数据前只能显示计划来源，不能生成假节点。
- 写回长期记忆只能走 proposal / 人审 / agent apply / git rollback 流程。

## Profile / Core Personalization

- 复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。
- 研究和决策支持任务优先使用公开、合规、授权、可验证的信息来源，避免依赖未授权或不可审计来源。
- 用户长期关注 AI 时代对社会、工作方式、沟通、人类能力边界和个人突破路径的影响；讨论这类问题时应先做深度研究，再输出结构化机会、风险和行动建议。
- 如果具备联网能力，涉及最新事实、官方文档、行业报告、论文、政策、价格、API 或高风险决策时，必须先检索权威来源再回答。
- 默认交互方式应优先使用编号选择题、多选矩阵、默认推荐项、少量必要填空、当前步骤状态表和下一步 A/B/C，避免让用户大量自由文本输入。
- 如果当前环境不具备联网或外部验证能力，必须明确标注“待外部验证”，不要把未验证信息说成确定事实。

## Memory（给 ChatGPT / Codex Personalization）

- OpenAIDatabase 是 durable memory source：GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。（证据 272，置信度 high）
- 任意 agent personalization：所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。（证据 51，置信度 high）
- 默认中文输出：用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。（证据 19，置信度 high）
- 真实数据优先：用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。（证据 19，置信度 high）
- 报告面向人类 ROI 和成长：处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。（证据 12，置信度 high）

## Meta Data（给 ChatGPT / Codex Agents.md）

- GitHub secret 边界：GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。（证据 275，置信度 high）
- 授权边界：用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。（证据 46，置信度 high）

## Top Topics

- Codex 本地数据 / agent 工作流：324
- GitHub 备份 / durable state：289
- 安全边界 / secret / 权限：283
- 高质量交付 / 验证 / CI：273
- Memory Atlas / 记忆可视化：30
- 长期记忆数据库 / RAG：11
- 前端交互 / Three.js / Dashboard：7
- 金融 / trading / 风险边界：5

## Data Sources

Active:
- ChatGPT（memory_atlas / openai_export_derived_memory）：active_redacted_derived_data
- Codex（codex / codex_local_derived_behavior）：active_real_local_redacted_summary
Planned:
- 微信数据（计划接入）（wechat / wechat）：planned_no_real_data
- 小红书数据（计划接入）（xiaohongshu / xiaohongshu）：planned_no_real_data
- 抖音数据（计划接入）（douyin / douyin）：planned_no_real_data

## Read Order

- `data/derived/agent_context/AGENT_CONTEXT.md`
- `data/derived/agent_context/agent_context_pack.json`
- `data/derived/profile/CORE_PROFILE.md`
- `data/derived/codex/codex_agent_recommendations.json`
- `data/derived/visualization/memory_atlas.json`
- `config/data_sources/source_registry.json`

## Safety

- 不包含原始 transcript、plaintext high-risk secrets、本地绝对路径。
- 需要深度原文分析时，由授权本地 agent 临时读取原始数据；不要把原始数据提交到 GitHub。
