# ADP V0.1 · PRECEDENCE（权威顺序与冲突裁决规则）

> 任务 `ADP-S0-P01-T001` 交付物。任何冲突材料按本顺序自动裁决，0 个 P0 指令缺失。

## 权威顺序（高 → 低）

```text
1. Owner 本轮最新明确指令
2. 当前线上与 Cloudflare 私有只读事实
3. 当前 Git commit 与机器 Manifest
4. 本最终包（ADP_V0.1_FINAL_...）的机器合同、Roadmap 和任务合同
5. 2026-07-15 Reconciled 包中的 canonical specs
6. 其他历史线程、Codex 输出和旧交接包（仅补细节，不得覆盖 1–5）
```

裁决原则：低层级材料只能在不与任何高层级冲突时补充细节；一旦冲突，以更高层级为准并记入 CONFLICT_LEDGER（T002 建立）。

## 冲突处理规则（本轮固定裁决）

| # | 冲突主题 | 旧材料主张 | 本轮裁决 | 理由 |
|---|---|---|---|---|
| 1 | 多租户/安全/认证 | 通用 SaaS 需要 | **SUPERSEDED**，不进入本轮 | DIR-001（Owner 明确不做） |
| 2 | TAM/定价/商业套餐 | 商业化优先 | **SUPERSEDED** | DIR-001 |
| 3 | UI 原型 | 多套替代 UI/导航重做 | **SUPERSEDED**；只保留现有线上六主题+高级动效 | DIR-003 |
| 4 | 中国来源层级 | A0–A4/B/C/D | **仅 A0/A1/A2** | DIR-002 |
| 5 | 171 个来源 | 已上线声明 | **候选 Seed**，按 cohort 晋级 | 09_ANTI_BLACK_HOLE，S4 |
| 6 | 20TB / 10M 文档 / 30M 版本 | 需求量/采购 | **容量压测包络**，非当前需求 | FACT-016 |
| 7 | Workflows | 强制编排依赖 | **候选**，先与 Cron+Queues 基准比较 | 09_ANTI_BLACK_HOLE |
| 8 | 向量数据库 | 先上向量检索 | **延后**，精确/结构化/FTS 不足后再基准 | 09_ANTI_BLACK_HOLE |
| 9 | “竞品都有我也有” | 复制全部页面/按钮 | **同等或更好的用户收益**，按收益缺口优先级 | 02_CANONICAL_SCOPE |
| 10 | “最终交付” | 产品代码已完成 | **最终执行基线**，代码未完成，逐 Stage 推进 | 01_FINAL_READINESS |

## 事实分类（不得混用）

`VERIFIED_PUBLIC` / `OWNER_DIRECTIVE` = 输入事实；
`UNVERIFIED_PRIVATE` = 未知，禁止猜测填充或直接生成 schema/需求（S0-P02 补齐）；
`ASSUMPTION` = 假设，须显式标注；`SUPERSEDED` = 归档不执行。
