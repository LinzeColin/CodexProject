# 路线图 V0.2 — 阶段 / 环节 / 任务（交付制）

## 交付制三原则（防止「一个 bug 反复修、死活不能交付」）

1. **每周五交付制**：每周五给 Owner 一个能亲手操作 10 分钟的可用版本 + 一页「本周你能看到什么」。验收物永远是 Owner 眼见的结果，不是技术报告、不是测试通过数。
2. **两次修复上限**：同一问题最多修 2 次，每次限半天。第 3 次自动触发换方案：回滚 / 砍掉该功能降级交付 / 换成熟组件替代。问题台账里每个问题最多两行修复记录。
3. **颗粒度法则**：一个任务 = 一次开发会话干完（改动 ≤5 文件、上下文 ≤100 KB、有一条可运行的验收断言）；一个环节 ≤1 天；一个阶段以真实使用验收。任何任务若需要新增治理文档，直接判失败。

## R0｜决策冻结与漂移修复（8 任务 · 约 1 周）

目标：仓库只有一个真相；治理上下文压到 100 KB 以内。

| 任务 | 内容 | 你会看到 |
|---|---|---|
| R0-1 | 25 项决策表填完归档 | 一页你签过字的决策清单 |
| R0-2 | 阈值注册表登记为待生效版本 | 34 个参数一页看全 |
| R0-3 | 清除旧配置自动启用与「五封信」残留 | 配置改前/改后对照 |
| R0-4 | 三处版本指针对齐 | 抽查三处答案一致 |
| R0-5 | 运行记录加人话字段（正常/降级/弃权/失败/未运行） | 系统页三色运行行 |
| R0-6 | 巨型文档冻结入 archive/（只读不删除） | 会话成本前后对比 |
| R0-7 | 每阶段一页状态文件模板 | R0 自己用它收尾 |
| R0-8 | 工作合同重写为一页 | 一页你能看懂的语言 |

## R1｜最小学习闭环（11 任务 · 约 2 周）★ 核心

目标：一条命令跑通「抓取→排序→讲义→回忆→复习」。

| 任务 | 内容 | 你会看到 |
|---|---|---|
| R1-1 | 5 个资格硬门 | 30 天回放的拦截清单，每条一句原因 |
| R1-2 | 8 特征加权 + 弃权 + 双向解释 | 每天「为什么选它/为什么不是第二名」 |
| R1-3 | 30 天历史回放对照 | 新旧头名对照表，你抽查合理性 |
| R1-4 | 深度讲义生成（人话→脉络→机制→证据→边界→连接）| 一篇像原型那样的讲义 |
| R1-5 | 逐句溯源校验 | 随机点一句能跳到出处 |
| R1-6 | 接入 FSRS（评分→下次复习） | 四档评分给出不同间隔 |
| R1-7 | 学会/发送分离保护 | 演示：发邮件不改变任何学习状态 |
| R1-8 | 网页「今天学什么」+「学习队列」两页 | 亲手完成一次回忆 |
| R1-9 | 手动状态编辑（可撤销、单独记账） | 亲手改状态并撤销 |
| R1-10 | 单命令串联五环节 + 运行记录 | 一条命令 5 分钟内跑完全程 |
| R1-11 | 连续 5 个真实日期运行 | 系统页 5 行绿色「正常」 |

## R2｜证据与纠错（6 任务 · 约 1 周）

目标：每句话可追溯；证据变了自动找回受影响知识。
任务：元数据增强（OpenAlex/Semantic Scholar，失败不阻塞）；声明落库可检索（任意声明三步到原文）；版本/撤稿检测→影响图→重开知识项；纠错强提醒；旧发送记录/历史评分只存档不复算（两项迁移）。
**你会看到**：证据等级从「摘要级」升「全文级」；现场注入一次论文改版，系统自动重开知识项并提醒你。

## R3｜交付通道与雷达（5 任务 · 约 1 周）

目标：邮件成为幂等镜像；周雷达与应用闭环上线。
任务：新邮件模板上线（与网页同源渲染）；发送授权凭证（可过期可撤销）；每周雷达+知识债务；迁移练习与结果记录；本机定时器+睡眠补跑。
**你会看到**：收到新样式邮件；同日重发被拒并给出原因；周五第一份真实周报；合上电脑第二天照常有讲义。

## R4｜四周交付制试运行（4 个周五 · 与日常使用并行）★ 替代旧的 30 天试点

目标：每周五交付可用版本；参数用你的真实数据校准；到点决策不拖延。

| 周五 | 交付物 | 你会看到 |
|---|---|---|
| 第 1 周 | 可用版本 + 影子记录开启 | 10 分钟亲手验收 + 问题台账（每问题≤2 行修复记录） |
| 第 2 周 | 影子对照上线 | 「如果换个参数会怎样」对照页 |
| 第 3 周 | 首次参数校准（提案→预览→应用） | 你的 7 天记忆曲线 + 调参回执 |
| 第 4 周 | 试运行报告 + 持久运行决策 | 一页报告当场拍板：批准 / 退回 / 降级——不存在「再修一周」 |

## R5｜有目的的来源扩展（按需 · 每源 3 任务）

每源固定三步：覆盖缺口分析+启用提案（一页「为什么是它」）→ 统一订阅面接入+两周影子（零干扰报表）→ 上板评审+权重提案（预览→你点应用→回执）。板块二（顶级期刊）或生物预印本任选先行。

## R6｜部署上线（可选 · Cloudflare 混合 · R4 通过后 · 3 任务 · 约 1 周）

目标：手机随时随地打开你的系统；重活留本地，云端做门面与镜像（全部免费额度内）。

| 任务 | 内容 | 你会看到 |
|---|---|---|
| R6-1 | 前端上线 Cloudflare Pages + Access 私有访问 | 手机打开 home.linzezhang.com 即是你的系统，仅你可登录 |
| R6-2 | 数据镜像：本地 SQLite → D1（同为 SQLite 语法）+ R2 每周快照 | 云端数据页与本机一致，永不丢失 |
| R6-3 | Worker 定时轻任务：复习提醒 + 镜像刷新（失败不重试→本机心跳兜底） | 到点收到提醒；云端故障不影响本机闭环 |

## 机器可读摘要

```yaml
roadmap_version: v0.2-delivery
delivery_contract:
  cadence: weekly_friday_usable_build
  fix_attempt_limit: 2
  on_third_failure: [rollback, degrade_feature, adopt_mature_component]
  acceptance_language: owner_visible_outcomes_only
granularity: {task_max_files: 5, task_max_context_kb: 100, phase_max_days: 1}
stages:
  - {id: R0, tasks: 8,  weeks: 1, gate: repo_single_truth}
  - {id: R1, tasks: 11, weeks: 2, gate: five_real_days_loop}
  - {id: R2, tasks: 6,  weeks: 1, gate: correction_reopens_knowledge}
  - {id: R3, tasks: 5,  weeks: 1, gate: idempotent_mirror_and_radar}
  - {id: R4, fridays: 4, gate: pilot_report_signed_on_4th_friday}
  - {id: R5, tasks_per_source: 3, gate: per_source_promotion}
  - {id: R6, tasks: 3, weeks: 1, optional: true, gate: phone_access_via_cloudflare_mirror}
weights_v0_3: {user_relevance: 22, knowledge_gap: 20, novelty_to_user: 14, transfer_potential: 12, forgetting_pressure: 8, urgency: 6, evidence_quality: 5, diversity: 17}
self_iteration: {weekly: weight_proposal_owner_confirms, monthly: profile_update, fsrs_personalize_after: 100_reviews}
stop_lines: [no_new_governance_docs, no_parallel_current, fail_closed_without_authorization, stop_on_missing_p0_decision, no_endless_fix_loops]
```
