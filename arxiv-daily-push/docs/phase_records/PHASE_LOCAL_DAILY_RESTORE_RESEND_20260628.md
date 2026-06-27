# 2026-06-28 本地运行恢复与补发证据

服务日期：`2026-06-28`

更新时间：`2026-06-28 09:09:13 AEST +1000`

## 结论

| 项目 | 结果 |
|---|---|
| 今日补发 | 已完成 |
| SMTP 真实发送 | 已发送 |
| 用户中心同步门 | 通过 |
| 今日已发送 / 总应发送 | 1 / 4 |
| 自动运行恢复 | daily、health、watchdog 三个 LaunchAgent 已启用 |
| 是否记录 SMTP secret | 否 |
| 是否记录邮件正文 | 否 |

## 补发邮件

| 字段 | 值 |
|---|---|
| 主内容 | [arXiv:2606.26919](https://arxiv.org/abs/2606.26919)，The parental parsimony problem on binary, tree-child phylogenetic networks |
| 邮件产品 | M1 |
| 模板 | Email V1 |
| 实际发送时间 | 2026-06-28 09:05:00 AEST +1000 |
| 发送证据 | `smtp-delivery:87f268d29a31288d` |
| local runner 状态 | `status=pass` |
| SMTP 状态 | `notification_status=sent` |
| message_id | 已存在；不在 GitHub 明文展示 |

## 过程阻断

| 时间 | 结果 | 直接原因 |
|---|---|---|
| 2026-06-28 08:49:00 AEST +1000 | 阻断，未发送 | daily 未显式传入 `--project-root`，用户中心路径解析到错误目录 |
| 2026-06-28 08:50:04 AEST +1000 | 阻断，未发送 | 旧候选队列中存在旧版评分权重，六因子明细同步门拒绝通过 |
| 2026-06-28 08:53:36 AEST +1000 | 阻断，未发送 | `stage2_s2pjt02_review_schedule_report.json` 与 `stage2_s2pjt03_action_asset_roi_ledger_report.json` 缺失 |
| 2026-06-28 09:05:00 AEST +1000 | 已发送，补发 | 用户中心同步门通过，SMTP 发送成功 |

## 已修复项

| 修复项 | 证据 |
|---|---|
| 旧候选队列评分迁移到 `adp-roi-semantic-rubric-v2` | `global_scan.normalize_candidate_queue` 刷新旧队列项的六因子评分明细 |
| launchd daily 命令显式传入项目根 | `local-runner daily --project-root .../CodexProject/arxiv-daily-push` |
| 今日复习快照写入用户中心 | [复习行动与收益](../../用户中心/复习行动与收益.md) |
| 今日邮件发送记录写入用户中心 | [邮件发送与队列状态](../../用户中心/邮件发送与队列状态.md) |
| 本机自动运行恢复 | `com.linze.adp.local.daily`、`com.linze.adp.local.health`、`com.linze.adp.local.watchdog` 均为 enabled |

## 验证

| 验证 | 结果 |
|---|---|
| `python3 -m unittest arxiv-daily-push/tests/test_global_scan.py -q` | 13 tests OK |
| `python3 -m unittest arxiv-daily-push/tests/test_local_runner.py -q` | 8 tests OK |
| S2PIT02 runtime dashboard report | pass |
| S2PJT01 lifecycle state report | pass |
| S2PJT02 review schedule report | pass |
| S2PJT03 action ROI report | pass |
| local runner final send | pass；`real_smtp_sent=True` |
| launchd health kickstart | exit code 0；`latest-preflight.json status=pass` |
| launchd watchdog kickstart | exit code 0；`latest-readiness.json status=pass` |

## 边界

本次恢复没有记录 SMTP 密码、SMTP username、邮件正文或 message_id 原文。`S2PJT01` 是本地生命周期模型覆盖证据，不表示今天已经掌握某篇论文；今日用户可读数量只来自 S2PJT02/S2PJT03 当日报告。
