# PFI V0.2 Stage 4 Investment And Consumption Analysis MVP

更新时间：2026-06-27 Australia/Sydney

## 目标

Stage 4 将 PFI 从“能记录、能读懂”推进到“能分析”。投资侧覆盖收益质量、风险质量和行为质量；消费侧覆盖成本、预算、订阅、异常和现金流。

## 范围

- 新增本地分析 read-model：`src/pfi_v02/stage4_analysis_mvp.py`。
- 新增合同测试：`tests/test_stage4_analysis_mvp.py`。
- Web shell 首页、投资管理、消费管理接入 Stage 4 分析能力。
- 保留 Stage 3 首页、账户、账本 read-model 作为 Stage 4 输入。
- 保留 PFI 策略实验室、策略回测、盘感训练和大数据模拟器；QBVS 保持 `CodexProject/QBVS` 顶层独立系统。

## 非范围

- 不接入真实交易密码。
- 不提交券商订单。
- 不提交支付动作。
- 不声明投资建议自动执行。
- 不修改 Alpha、EEI、ADP、Serenity 或其它项目。

## Phase / Task 验收矩阵

| Task ID | Phase | 任务 | Acceptance Criteria | Stop Condition | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| S4PAT01 | 4A | 投资总览 | 总市值、盈亏、资产配置、现金仓位可算 | 投资/消费混算 | investment summary test | `investment_analysis.summary` |
| S4PAT02 | 4A | 收益归因 | 市场、主动决策、费用、汇率、现金拖累可分解 | 数据不足却给精确结论 | attribution test | `investment_analysis.attribution` |
| S4PAT03 | 4A | 风险分析 | 集中度、回撤、币种暴露、流动性可展示 | 无风险证据 | risk test | `investment_analysis.risk` |
| S4PAT04 | 4A | 行为复盘 | 追涨、杀跌、频繁交易、持有周期可识别 | 缺交易数据仍生成行为结论 | behavior test | `build_investment_behavior_review()` |
| S4PAT05 | 4A | QBVS 独立系统边界 | PFI 大数据模拟器保留在投资管理下，QBVS 独立于 PFI | QBVS 被 PFI 覆盖或内嵌 | compatibility smoke | `qbvs_compatibility` |
| S4PBT01 | 4B | 消费总览 | 本月支出、预算剩余、固定/弹性支出可算 | 转账计入消费 | spending summary test | `consumption_analysis.summary` |
| S4PBT02 | 4B | 分类分析 | 支付宝、微信、CBA 消费可分类 | 低置信度无复核 | classifier test | `consumption_analysis.classification` |
| S4PBT03 | 4B | 订阅检测 | 周期扣费和疑似订阅可识别 | 订阅无法复盘 | recurring test | `consumption_analysis.recurring` |
| S4PBT04 | 4B | 异常消费 | 大额、重复、夜间、节假日、冲动型消费可识别 | 异常无证据 | anomaly test | `consumption_analysis.anomalies` |
| S4PBT05 | 4B | 现金流预测 | 30/90/180 天支出、收入、可投资现金可预测 | 生活现金和投资现金混淆 | cashflow test | `consumption_analysis.cashflow_forecast` |
| S4PZT01 | 4Z | Stage 4 closeout | 合同、UI、治理、入口、缓存、GitHub 同步完成 | 未通过目标验证 | closeout validation | 本文件 + `HANDOFF.md` |

## Stop Condition Checks

| 检查项 | 结果 |
| --- | --- |
| 投资/消费混算 | PASS：投资总览只读取 investment positions；消费总览显式排除 transfer 和 investment records |
| 数据不足却给精确结论 | PASS：收益归因 `precision=estimate`，`precision_policy=insufficient_data_blocks_exact_conclusion` |
| 无风险证据 | PASS：集中度、回撤、币种暴露、流动性均带 evidence refs |
| 缺交易数据仍生成行为结论 | PASS：空交易输入返回待同步且 conclusions 为空 |
| QBVS 被 PFI 覆盖或内嵌 | PASS：`QBVS/qbvs` 保持 `CodexProject/QBVS` 顶层独立；PFI 只保留自己的策略实验室、大数据模拟器和盘感训练 |
| 转账计入消费 | PASS：`excluded_transfer_aud` 和 `excluded_investment_aud` 单独记录，不进入生活消费 |
| 低置信度无复核 | PASS：低于 0.70 的消费分类进入 review queue |
| 订阅无法复盘 | PASS：订阅候选带 review action |
| 异常无证据 | PASS：每条 anomaly 带 evidence ref |
| 生活现金和投资现金混淆 | PASS：cashflow forecast 分离 `life_cash_aud` 和 `investment_cash_aud` |
| 自动实盘下单、交易密码、支付或券商提交 | PASS：未新增，仍在 boundaries 中禁止 |

## Validation

目标验证命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp -q
cd ../QBVS && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
python3 -B -m unittest tests.governance.test_human_entry_markdown_contract -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pfi_os.examples.macos_app_acceptance_lite --project-root . --summary-json
git diff --check -- PFI
```

当前本地结果：

- Stage 1+2+3+4 contracts：`Ran 71 tests / OK`
- Top-level QBVS lifecycle smoke：`Ran 1 test / OK`
- Project governance validation：`errors 0 / warnings 0`
- Human-entry Markdown contract：`Ran 2 tests / OK`
- Stage 4 focused contract：`Ran 12 tests / OK`
- Python compile：`OK`
- Web shell syntax：`node --check OK`
- `git diff --check -- PFI`：`OK`

## 当前边界

Stage 4 完成的是本地只读智能分析 MVP。真实账户联通、真实凭证、自动调度、支付提交、券商下单、报告正式发布、Alpha 只读 context export 和生产运行仍需后续单独 gate。
