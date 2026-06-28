# 2026-06-28 M1-M4 补发执行证据

- 服务日期: `2026-06-28`
- 执行时间: `2026-06-28 11:26:41 Australia/Sydney`
- 运行入口: `local-runner daily --daily-input-report`
- 输入来源: 复用同日 `/Users/linzezhang/.adp/arxiv-daily-push/runs/20260628/adp-daily-input-report.json`
- 运行结果: `pass`
- 今日已发送 / 总应发送: `4 / 4`

## 邮件产品结果

| 邮件产品 | 状态 | 发送方式 | 证据 |
|---|---|---|---|
| M1 | 已发送 | 历史已发送记录，未重复发送 | `smtp-delivery:87f268d29a31288d` |
| M2 | 已发送 | 本次真实 SMTP 补发 | `smtp-delivery:c72ffcd03a277e1d` |
| M3 | 已发送 | 本次真实 SMTP 补发 | `smtp-delivery:590b7230463ff9f7` |
| M4 | 已发送 | 本次真实 SMTP 补发 | `smtp-delivery:7f815186af789297` |

## 边界

- 本记录证明 2026-06-28 的 M1-M4 邮件发送缺口已补齐。
- 本记录不表示 Stage 2 正式生产验收通过。
- 本记录不表示 scheduler、Release、CURRENT、V7 合同、公共 schema、来源板块或排序公式发生变化。
- 本记录不替代后续每日自动运行的验收；后续每日运行仍必须产生自己的发送记录和用户中心同步。

## 验证

- `adp-local-runner-report.json`: `status=pass`
- `daily_input_source`: `existing_report`
- `real_smtp_sent`: `true`
- `production_evidence_ready`: `true`
- `mail_delivery_summary.sent_mail_count`: `4`
- `mail_delivery_summary.newly_sent_mail_products`: `M2, M3, M4`
- `mail_delivery_summary.historical_sent_mail_products`: `M1`
