# ChatGPT Personalization Export

- generated_at: 2026-06-28T21:40:14Z
- source: OpenAIDatabase redacted derived context
- raw_private_data_included: false
- plaintext_secrets_included: false

## Core Profile

- 复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。
- 研究和决策支持任务优先使用公开、合规、授权、可验证的信息来源，避免依赖未授权或不可审计来源。
- 用户长期关注 AI 时代对社会、工作方式、沟通、人类能力边界和个人突破路径的影响；讨论这类问题时应先做深度研究，再输出结构化机会、风险和行动建议。
- 如果具备联网能力，涉及最新事实、官方文档、行业报告、论文、政策、价格、API 或高风险决策时，必须先检索权威来源再回答。
- 默认交互方式应优先使用编号选择题、多选矩阵、默认推荐项、少量必要填空、当前步骤状态表和下一步 A/B/C，避免让用户大量自由文本输入。
- 如果当前环境不具备联网或外部验证能力，必须明确标注“待外部验证”，不要把未验证信息说成确定事实。


## Preferences And Taste

- OpenAIDatabase 是 durable memory source: GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。 (confidence=high; evidence=6007)
- 任意 agent personalization: 所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。 (confidence=high; evidence=2645)
- 真实数据优先: 用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。 (confidence=high; evidence=2502)
- 默认中文输出: 用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。 (confidence=high; evidence=1331)
- 报告面向人类 ROI 和成长: 处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。 (confidence=high; evidence=839)

## History And Patterns

- Codex 本地数据 / agent 工作流: 13926
- 安全边界 / secret / 权限: 12393
- 高质量交付 / 验证 / CI: 10824
- GitHub 备份 / durable state: 8520
- 前端交互 / Three.js / Dashboard: 2800
- 长期记忆数据库 / RAG: 2291
- 金融 / trading / 风险边界: 2080
- Memory Atlas / 记忆可视化: 604


## Project And Decision Context

- Use `data/derived/project_index/PROJECT_INDEX.md` for project continuity.
- Use `data/derived/decision_log/DECISION_LOG.md` for durable decisions.
- Use `data/derived/timeline/TIMELINE.md` for chronological history.

## Future Agent Sync Rules

- If profile, preference, taste, history, or pattern changes, update the mapped source files first.
- Regenerate this export after every meaningful memory sync.
- Do not write raw transcripts, cookies, browser profiles, or plaintext secrets into GitHub.

## Meta Rules

- GitHub secret 边界: GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。 (confidence=high; evidence=12085)
- 授权边界: 用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。 (confidence=high; evidence=5393)
