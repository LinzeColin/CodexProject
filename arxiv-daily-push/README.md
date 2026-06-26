# arXiv 日报推送

## 先读这里

| 你要找什么 | GitHub 中文入口 |
|---|---|
| 今天总体状态 | [用户中心](./用户中心/README.md) |
| 一屏判断和三项检查 | [一看三查](./用户中心/一看三查.md) |
| 已发送、未发送、排队、已讲解 | [邮件发送与队列状态](./用户中心/邮件发送与队列状态.md) |
| 各板块数据源和启用状态 | [数据源与板块健康](./用户中心/数据源与板块健康.md) |
| 复习、行动、能力资产、收益 | [复习行动与收益](./用户中心/复习行动与收益.md) |
| 当前路线图和停止门 | [路线图与停止门](./用户中心/路线图与停止门.md) |

不要要求用户去本机 `.adp` 目录、原始 JSON、LaunchAgent 或深层 `docs/owner` 目录里找状态。用户主阅读面就是 GitHub 浅层中文用户中心。

## 项目定位

`arXiv 日报推送` 是一个证据优先的中文学习邮件系统，不是浅层论文新闻摘要。它的目标是每天把一篇或一组高价值研究转成中文讲解、复习计划、行动建议和可追踪的学习收益。

当前事实：

| 事项 | 状态 |
|---|---|
| Stage 1 arXiv 单源 | 已验收并维持 |
| 本机运行策略 | 本机加本地 Codex 运行器 |
| GitHub 角色 | 代码、PR、证据、状态和备份 |
| GitHub 云端每日生产 | 未启用 |
| Stage 2 多来源正式生产 | 未通过 |
| Email V1 | 已作为 M1 到 M4 后续邮件模板合同 |

30 天级别证据指 30 个独立日期的真实数据回放、覆盖检查和证据产物；不等于必须等待 30 个自然日。

## 当前范围

已经具备的基础能力：

- 命令行和本地运行基础：版本检查、健康检查、邮件渲染、通知发送、记录校验。
- arXiv 来源接入：构造 arXiv 请求、解析 Atom 元数据、获取最新论文、维护来源注册。
- 确定性排序、证据门、中文讲解、发布门、干运行流水线、交接包和验收校验。
- 用户控制配置和中文用户中心。
- Stage 1 文档和事件存储模型。
- Stage 1 来源注册，目前正式来源只有 arXiv。
- Stage 1 候选排序、确定性队列和内容账本。
- Stage 1 B1 报告和邮件预览、30 个历史预览、本机恢复、迁移包和迁移后启动证据。
- Stage 1 本机运行准备，包括预检查、日常运行和计划任务草案。

保留但当前不作为验收目标的能力：

- 历史语音、分镜、视频命令。
- 历史 GitHub Release 媒体交付路径。
- 早期全 arXiv、收益、手工交付实验。

已完成的 Stage 1 验收证据：

- 30 个独立历史 B1 报告和邮件预览。
- 两次受控 Gmail SMTP 发送引用。
- PR #82 的真实 arXiv 云端干运行证据。

尚未启用：

- GitHub 云端计划任务生产运行。
- 未经用户本机环境和密钥设置验证的真实本地 SMTP 生产发送。
- 真实安装 launchd。
- Stage 2 来源正式生产推广。

## 目标基线

当前长期目标基线锁定在：

```text
docs/pursuing_goal/BASELINE_LOCK.md
docs/pursuing_goal/START_HERE_MASTER_TASK_PACK_TWO_STAGE_TEXT_DELIVERY_V5.md
docs/pursuing_goal/FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt
docs/pursuing_goal/ARXIV_DAILY_PUSH_TWO_STAGE_ROADMAP_V6.md
```

V4 和 Phase 1 到 12 文件只保留为历史上下文。当前目标中，Stage 1 只覆盖 B1/arXiv 单源；Stage 2 可以在后续门禁通过后推广其他板块和来源。

V6 任务编号规则：每次完成报告必须写明当前任务编号。历史当前任务曾是 `S2P1T01`，即 bioRxiv 和 medRxiv 来源推广。现在 Stage 1 arXiv 已验收，本机生产和迁移准备已完成；Stage 2 正式生产仍未通过。

V5 到 V6 的 Stage 1 任务连续性：

- `S1-01-READONLY-AUDIT-001`：只读任务包和仓库审计。
- `S1-02-V5-BASELINE-GOVERNANCE-CALIBRATION-001`：V5 基线锁和治理校准。
- `S1-03-OWNER-CONTROLS-001`：用户控制项和用户可读视图。
- `S1-04-SQLITE-DATA-MODEL-001`：统一本地文档和事件存储。
- `S1-05-ARXIV-CONNECTOR-CONTRACT-001`：arXiv 来源注册合同。
- `S1-06-SCORING-QUEUE-LEDGER-001`：研究评分、队列行为和内容账本。
- `S1-07-B1_REPORT_EMAIL_TEXT-001`：B1 教学报告、证据声明和邮件文本预览。
- `S1-08-LOCAL_RUNTIME_RECOVERY-001`：心跳、看门狗、备份、恢复、运行审计和计划任务控制。
- `S1-09-MIGRATION_PACKAGE-001`：低资源迁移包。
- `S1-10-POST_MIGRATION_BOOTSTRAP-001`：迁移后目标机器或 GitHub 托管运行器启动。
- `S1-11-HISTORICAL_B1_PREVIEWS-001`：完成 30 个独立历史 B1 报告和邮件预览。
- `S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001`：通过 PR #82 的加速真实 arXiv 验收产物和已有受控 SMTP 引用完成。
- `S1P5T03-R`：完成 30 个真实历史 arXiv 日期回放和内容账本对账。
- `S1P5T04`：完成受控 Gmail SMTP test10 和 Stage 1 arXiv 验收证据。
- `ADP-S1P5T05-LOCAL-PRODUCTION-AND-MIGRATION-PREP`：完成本机运行器和 2026-06-30 迁移准备；未安装 launchd，也未启用 GitHub 云端计划生产。

## 本地验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --project arxiv-daily-push
git diff --check
```

## 资源和安全边界

禁止提交媒体文件、模型权重、声音样本、凭证、Codex 认证信息、GitHub 令牌、SMTP 密钥、渲染缓存或依赖目录。本机生产必须把密钥保留在用户控制的环境或 Keychain 支持的设置中。禁止批量下载 PDF，禁止下载大模型或语音模型，禁止未受控真实 SMTP 发送，禁止上传 Release，禁止启用 GitHub 云端生产计划任务，禁止在来源门禁通过前推广 Stage 2 来源。
