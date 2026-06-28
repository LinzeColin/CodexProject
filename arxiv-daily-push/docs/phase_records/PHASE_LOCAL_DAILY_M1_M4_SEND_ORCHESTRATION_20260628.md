# Local Daily M1-M4 Send Orchestration

更新时间：2026-06-28 10:26:53 Australia/Sydney

## 结论

- 本轮把本机 daily runner 从单 M1 实发路径升级为 M1-M4 四产品统一发送路径。
- `EMAIL_LEARNING_V1` 模板合同不变，`M1_M4_MAIL_PRODUCTS` 不变，公共 schema 不变。
- 真实 daily runner 现在会为 `M1, M2, M3, M4` 分别生成 `delivery_package`、email preview 和 SMTP delivery report。
- `real_smtp_sent` 只有四个产品全部 `sent` 才为 true。
- 用户中心邮件状态页在真实发送链路中按实际成功封数同步 `今日已发送 / 总应发送`。
- 同一服务日期重跑时，runner 会读取内容账本中的已发送产品，已发送产品不重复调用 SMTP，只补发缺失产品。

## 改动范围

| 文件 | 改动 |
|---|---|
| `src/arxiv_daily_push/local_runner.py` | 新增 M1-M4 delivery package 构建、逐产品 SMTP 边界、同日已发送产品跳过、聚合报告、逐产品预览/报告文件、用户中心已发送计数同步。 |
| `tests/test_local_runner.py` | 覆盖 dry-run 四产品、fake SMTP 四封实发、用户中心 `4 / 4`、用户中心阻断时四产品均 blocked。 |
| `功能清单.md` | 增加本轮功能记录。 |
| `开发记录.md` | 增加本轮开发记录、回滚方式和参数口径。 |
| `模型参数文件.md` | 明确本轮不改评分参数，只落实既有 M1-M4 发送合同。 |

## 验收标准

| 验收项 | 结果 |
|---|---|
| dry-run 不伪造已发送 | 通过，四个产品均为 `dry_run`，`sent_mail_count=0`。 |
| fake SMTP 真实发送四封 | 通过，`M1, M2, M3, M4` 均为 `sent`，`sent_mail_count=4`。 |
| 用户中心计数同步 | 通过，fake SMTP 路径写入 `4 / 4`。 |
| 用户中心同步缺失时不得发信 | 通过，四个产品均 blocked，fake SMTP 未收到邮件。 |
| 六因子明细缺失时不得发信 | 通过，四个产品均 blocked，fake SMTP 未收到邮件。 |
| 同日缺口补发不重复已发送产品 | 通过，历史 M1 已发送时 fake SMTP 只收到 M2-M4 三封，汇总仍为 `4 / 4`。 |

## 已运行验证

- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_local_runner.py -q`
- 结果：9 tests OK
- `PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`
- 结果：641 tests OK after rebase

## 风险与下一步

- 本轮代码已具备按产品缺口补发保护。
- 是否实际执行今日 M2-M4 真实补发，取决于本机 SMTP 环境和用户中心同步门是否在运行时通过；运行证据必须追加到用户中心历史发送记录。
