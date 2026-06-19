# Codex 行为与记忆同步报告

- 生成时间：2026-06-17T21:18:55Z
- 数据来源：真实本地 Codex session 派生摘要，不包含原始全文和 plaintext secret。
- 覆盖范围：2026-06-03 至 2026-06-17，317 个 session，48461 条消息，168761 次工具调用。

## 主要话题
- Codex 本地数据 / agent 工作流：3052
- 高质量交付 / 验证 / CI：2459
- 安全边界 / secret / 权限：2446
- GitHub 备份 / durable state：1456
- 前端交互 / Three.js / Dashboard：1134
- 金融 / trading / 风险边界：1072
- 长期记忆数据库 / RAG：533
- Memory Atlas / 记忆可视化：426

## Memory（给 ChatGPT / Codex Personalization）
### 新增
- 暂无

### 修改
- OpenAIDatabase 是 durable memory source：GitHub 上的 OpenAIDatabase 应作为任意 agent 可读取的长期记忆、画像、偏好和历史上下文数据库。（证据 1077）
- 真实数据优先：用户明确要求使用真实 Codex / ChatGPT / GitHub 数据，不接受 mock、伪进度或只给概念演示。（证据 1021）
- 任意 agent personalization：所有 agent 访问后都应能生成适配用户的 profile、preference、project context、rules 和 history summary。（证据 793）
- 默认中文输出：用户长期偏好中文输出；代码、API、库名、错误信息和专业术语可保留英文。（证据 757）
- 报告面向人类 ROI 和成长：处理记忆或行为数据后，应输出人能直接使用的话题、行动、建议、机会、ROI、能力成长和风险提醒。（证据 460）

### 删除/降级建议
- 暂无

## Meta Data（给 ChatGPT / Codex Agents.md）
### 新增
- 暂无

### 修改
- GitHub secret 边界：GitHub 备份中不得提交 plaintext high-risk secrets；金融/交易 agent 使用 secret_ref 和受控本地 resolver。（证据 2236）
- 授权边界：用户说先不开始时必须先澄清需求；用户授权开始后应持续推进到可验证结果。（证据 1274）

### 删除/降级建议
- 暂无

## 需要做什么
- 把新增 Memory / Meta Data 建议在人审后同步到长期记忆和 AGENTS.md 规则。
- 每周自动运行本脚本，更新 Codex 行为数据和 Memory Atlas 快照。

## 风险
- 原始 Codex transcript 不进入 GitHub；需要深度原文分析时应由授权本地 agent 临时读取。
- plaintext secret 只允许存为 secret_ref 元数据，不提交到仓库。
