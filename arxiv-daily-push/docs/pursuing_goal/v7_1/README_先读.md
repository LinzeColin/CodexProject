# arXiv Daily Push V7.1 Codex Task Pack｜先读

## 最新状态

本包在 V7.0 基础上完成三条独立审查轨和整改设计：共 **53** 项（P0=8、P1=37、P2=8）；定向探针 19 项，通过 2、失败 17。

**生产 Gate 当前为 BLOCKED。** Stage2 来源 Shadow 开发可以继续；真实 SMTP、restore、自动 scheduler install 和 `DAILY_OPERATION` 必须等待 `S2PMT07`。

下一 Agent 的唯一入口：`HANDOFF/00_下一Agent先读.md`。

---

## 结论

这不是一份“建议备忘录”，而是一套要求 Codex 写入 GitHub、持续读取、自动校验并由你直接验收的 **V7.1 产品、审查与开发合同包**。

新基线：

> **多源采集 + 证据治理 + 深度理解 + 个人前沿情报 + 报告生成 + 中文人类界面 + 每日 3+1 邮件 + 复习 + 行动 + 能力资产 + ROI/经济转化 + 周报/月报，全部属于同一个系统。**

## 当前仓库核验快照（截至 2026-06-24）

| 事实 | 当前观察 | V7 处理 |
|---|---|---|
| 项目版本 | `0.23.0` | 合并后由 Codex 按版本规则决定是否提升，不在本包中伪造已发布版本 |
| 当前 Stage | `S2` | 继续，不暂停 |
| 当前任务 | legacy `S2P1T01` bioRxiv/medRxiv | canonical 映射为 `S2PBT01`，历史 ID 保留 |
| 当前邮件配置 | `five_independent_messages`，B1–B5 | 迁移为每日 `three_plus_one_messages`，M1–M4 |
| 当前 Owner 页面 | `OWNER_CONSOLE.md`、`MODEL_AND_QUEUE.md` 等英文名/英文正文 | 建立中文用户中心和四查面板；旧路径可暂时兼容 |
| 当前队列页面 | 主要展示最大容量和权重 | 改为同时展示数据库真实数量、最老等待、到期复习和转化状态 |
| 三基文件 | 已存在 `功能清单`、`开发记录`、`模型参数文件` | 保留，并要求完整显示 V7 契约、Roadmap、功能、参数、状态和证据 |

## 最新 Owner 决策

1. 四个数据源域继续建设，Stage 2 与 Stage 1+ 根本优化并行。
2. 阅读结构改为 **3 个主板块 + 3 个横切副板块**。
3. B2“工程与开源”和原 B3“产品与产业”合并为一个主板块。
4. 每日邮件改为 **三封主板块邮件 + 一封跨板块汇总邮件**。
5. 每周和每月总结是正式产品，不是可选附件。
6. 所有关键要求必须中文、人类可读地出现在 GitHub，能够直接对照功能、开发、参数、状态和验收。
7. 个人画像、邮箱等 Owner 信息允许公开，不作为本轮阻断；凭据、令牌和密码仍不属于“用户信息”，不得提交。

## Codex 最小读取顺序

每个线程不要把整个压缩包一次性塞入上下文。按以下顺序读取：

1. `HANDOFF/00_下一Agent先读.md`
2. `README_先读.md`
3. `09_并行审查/并行审查汇总与合并结论.md`
4. `00_系统总纲与不可漂移产品契约.md`
5. `ROADMAP/ARXIV_DAILY_PUSH_ROADMAP_V7_1_CN.md`
6. 当前唯一 Task 对应的 `08_首批任务卡/*.md`
7. 只有修改 Schema/配置/生成器时，才读取 `machine_readable/` 与 `templates/`

## 立即执行的两个并行线程

| 线程 | Task | 作用 | 合并约束 |
|---|---|---|---|
| 根合同/治理线程 | `S2PAT05` | 把 V7.1 三轨审查、合并政策、显式依赖和交接门写入仓库 | 必须先落库，才允许任何线程宣称按 V7.1 验收 |
| Stage 2 来源线程 | `S2PBT01`（legacy `S2P1T01`） | 继续 bioRxiv/medRxiv 限定范围实现 | 可以开发/测试，但必须遵守 EvidencePacket 和 D→B 解耦，不能直接生成最终邮件 |

## 建议写入仓库的位置

```text
arxiv-daily-push/
├── 00_用户中心/
│   ├── 00_开始这里.md
│   ├── 00_只改这里/
│   ├── 01_运行任务与真实队列总控台.md
│   ├── 02_数据源与阅读板块健康.md
│   ├── 03_模型评分参数与全量队列.md
│   ├── 04_内容邮件复习行动与ROI总账.md
│   └── 05_系统总纲开发要求与验收标准.md
├── 功能清单
├── 开发记录
├── 模型参数文件
└── docs/
    ├── governance/
    │   ├── product_contract.yaml
    │   ├── decision_log.yaml
    │   ├── requirements.yaml
    │   └── roadmap.yaml
    └── pursuing_goal/
        └── V7/
```

## 仓库事实核验来源

- `https://github.com/LinzeColin/CodexProject`
- `https://github.com/LinzeColin/CodexProject/blob/main/AGENTS.md`
- `https://github.com/LinzeColin/CodexProject/blob/main/docs/governance/STANDARD.md`
- `https://github.com/LinzeColin/CodexProject/tree/main/arxiv-daily-push`
- `https://github.com/LinzeColin/CodexProject/blob/main/arxiv-daily-push/AGENTS.md`
- `https://github.com/LinzeColin/CodexProject/blob/main/arxiv-daily-push/功能清单`
- `https://github.com/LinzeColin/CodexProject/blob/main/arxiv-daily-push/开发记录`
- `https://github.com/LinzeColin/CodexProject/blob/main/arxiv-daily-push/模型参数文件`
- `https://github.com/LinzeColin/CodexProject/blob/main/arxiv-daily-push/config/owner_controls.yaml`
- `https://github.com/LinzeColin/CodexProject/blob/main/arxiv-daily-push/docs/pursuing_goal/ARXIV_DAILY_PUSH_TWO_STAGE_ROADMAP_V6.md`

## 本包状态

- 合同版本：`ADP-PRODUCT-CONTRACT-V7.1`
- Roadmap 版本：`ADP-ROADMAP-V7.1`
- 状态：`parallel_audit_completed_remediation_required_before_production`
- 事实原则：现有仓库事实标记为观察事实；新结构是 Owner 已确认要求，但在 PR 合并前不得伪装成已实现。
