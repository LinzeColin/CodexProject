# 复习行动ROI

更新时间：2026-06-26 16:27:41 Australia/Sydney

本页把复习、行动、能力资产和 ROI 的状态讲清楚：哪些已经有证据，哪些只是本地证据，哪些还没有变成 GitHub 用户中心每天可见的真实数量。

## 当前结论

| 领域 | 当前状态 | owner 能直接看到的数量 |
|---|---|---:|
| 复习计划 | `S2PJT02` 本地复习计划证据已完成 | 每日 GitHub due 数量未自动接入 |
| 行动和能力资产 | `S2PJT03` 本地行动/资产/ROI 证据已完成 | 每日 GitHub action/asset 数量未自动接入 |
| 内容到 ROI 账本 | `S2PIT04` 本地内容-邮件-复习-行动-ROI reconciliation 证据已完成 | GitHub 用户中心只显示状态，不显示逐日自动刷新数量 |
| 周报/月报 | `S2PJT04`、`S2PJT05` 本地证据已完成 | 未作为生产周报/月报自动发布 |

## 复习

| 项目 | 状态 |
|---|---|
| 复习间隔 | `1/3/7/14/30/90` 天 |
| due buckets | 本地报告会计算 due today、next 7 days、overdue、completed |
| 当前 GitHub 用户中心 due 数量 | 未接入自动刷新 |
| 不能误判 | 不能把本地复习计划证据当成生产 scheduler 或每日 due 面板 |

## 行动、能力资产、ROI

| 项目 | 状态 |
|---|---|
| 行动窗口 | `15m / 2h / 7d / 30d` 本地证据已覆盖 |
| 预计 ROI | 需要 assumptions 和 confidence |
| 实际 ROI | 只有成本、收益和证据引用可验证时才允许计算 |
| 当前 GitHub 用户中心行动数量 | 未接入自动刷新 |
| 当前 GitHub 用户中心转化数量 | 未接入自动刷新 |
| 不能误判 | 不能把 expected ROI 写成确定收益承诺 |

## 缺口清单

| 缺口 | 为什么重要 | 默认下一步 |
|---|---|---|
| 每日复习到期数量没有自动写入 GitHub 用户中心 | V7.1/V7.2 要求 owner 能看到复习到期数量 | 增加每日 status snapshot 写入 GitHub 用户中心 |
| 每日行动/资产/转化数量没有自动写入 GitHub 用户中心 | V7.1/V7.2 要求 owner 能看到行动和转化数量 | 增加 action/asset/ROI count snapshot |
| 周报/月报未作为 GitHub 用户中心固定入口展示 | 周报/月报是正式 Roadmap 和验收要求 | 在用户中心增加周报/月报入口页 |

## 证据入口

| 证据 | 文件 |
|---|---|
| 复习计划证据 | `docs/phase_records/PHASE_S2PJT02_REVIEW_SCHEDULE.md` |
| 行动资产 ROI 证据 | `docs/phase_records/PHASE_S2PJT03_ACTION_ASSET_ROI.md` |
| 内容到 ROI 账本证据 | `docs/phase_records/PHASE_S2PIT04_CONTENT_LEDGER.md` |
| 周报证据 | `docs/phase_records/PHASE_S2PJT04_WEEKLY_REPORT.md` |
| 月报证据 | `docs/phase_records/PHASE_S2PJT05_MONTHLY_REPORT.md` |

