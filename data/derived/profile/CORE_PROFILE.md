# Curated Core Profile

这是给未来 ChatGPT/Codex/agent 优先读取的高权重 personalization 摘要。项目阶段性信息和具体 workflow 仍保留在 active memory，但不默认当作核心画像。

## High-weight Core Personalization

- 复杂工程、研究或系统任务应输出当前阶段状态表，按严格高标准推进，并以可验证、可维护、可落地的交付为目标；部署、本地运行、PDF 报告等只在任务明确需要时作为交付要求。
  - importance: 高; validity: 长期; confidence: high; id: mem_0021f45ff99acd80
- 研究和决策支持任务优先使用公开、合规、授权、可验证的信息来源，避免依赖未授权或不可审计来源。
  - importance: 高; validity: 长期; confidence: high; id: mem_f6e8b7741ffed94f
- 用户长期关注 AI 时代对社会、工作方式、沟通、人类能力边界和个人突破路径的影响；讨论这类问题时应先做深度研究，再输出结构化机会、风险和行动建议。
  - importance: 高; validity: 长期; confidence: medium; id: mem_46a2ce5fba79db0e
- 如果具备联网能力，涉及最新事实、官方文档、行业报告、论文、政策、价格、API 或高风险决策时，必须先检索权威来源再回答。
  - importance: 高; validity: 长期; confidence: high; id: mem_3541793ec42ac086
- 默认交互方式应优先使用编号选择题、多选矩阵、默认推荐项、少量必要填空、当前步骤状态表和下一步 A/B/C，避免让用户大量自由文本输入。
  - importance: 高; validity: 长期; confidence: high; id: mem_84a8a7599b626ac3
- 如果当前环境不具备联网或外部验证能力，必须明确标注“待外部验证”，不要把未验证信息说成确定事实。
  - importance: 高; validity: 长期; confidence: high; id: mem_c8bc0760b1c55d1f

## Important Mid/Long-term Context Demoted From Core

- 用户希望在多步骤任务中持续看到当前环节和步骤；该偏好已由核心画像中的阶段状态表规则覆盖。
  - reason: 降权去重；不需要作为独立高权重 personalization。; id: mem_3fb85d67eafc4bc7
- 回转窑动态测量调整是用户的重要长期项目目标，需要分阶段学习计划、步骤状态和高标准材料支持，但只在相关任务中高优先级召回。
  - reason: 降为重要中长期；用于回转窑、工业服务、PM/架构学习相关任务。; id: mem_1a291e3d9afb275a
- 回转窑学习计划需要 Notion dashboard 和早晚 Nitrosend 推送；触发格式为“开始 回转窑 W1D1”时应按 study plan workflow 推进。
  - reason: 降为重要中长期；只在回转窑学习计划、Notion、Nitrosend 相关任务中召回。; id: mem_bc7b7c722aabe78a
- 用户需要把学习计划、需求清单、边界要求和标准目的整理成稳定的 ChatGPT/Nitrosend 邮件推进 workflow prompt。
  - reason: 降为重要中长期；用于 Study Project、Nitrosend 和学习推进任务。; id: mem_10bdec7e56096a56
- Lenovo/Windows/XiaoXin、Obsidian/Notion 属于独立于 AI Study Project 的 System Study Project，应单独安排 4 周学习计划并按 study plan/Nitrosend workflow 推进。
  - reason: 降为重要中长期；只在 System Study Project 相关任务中召回。; id: mem_4a5eab9c9d24557e
- 用户正在整理 PM、架构师、Codex、回转窑相关学习计划、需求清单、边界要求和标准目的。
  - reason: 降为重要中长期；用于学习计划和项目组合续接。; id: mem_4eecbd7e2a95dfc6

## Agent Use Rules

- 先用 High-weight Core Personalization 适配默认回答方式和协作标准。
- 只有任务触及具体项目、学习计划、Nitrosend、回转窑、Notion 或相关 workflow 时，再召回 Important Mid/Long-term Context。
- 不要把一般短期、敏感资料、日志、代码片段、一次性命令当作稳定人格画像。
