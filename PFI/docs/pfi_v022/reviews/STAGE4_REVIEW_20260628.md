# PFI v0.2.2 Stage 4 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 4；不复审 Stage 5-13，不做整体项目复审，不重装 app 入口。

复审结论：通过  
上线阻塞项：0

## 复审范围

Stage 4：Economic Event 与 Interconnection 逻辑。

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S4-P1-T1` | 新增并使用 `economic_event_id`，多来源记录可归并为一个真实经济事件。 | 已修复并通过 |
| `S4-P1-T2` | 新增并使用 `interconnection_group_id`，银行转 Moomoo、支付宝基金申购、退款、信用卡还款可形成关联组。 | 已修复并通过 |
| `S4-P1-T3` | 每个 event_type 写清首页、消费、投资、现金流和报告处理方式；同一事件可多处展示但同一口径只计算一次。 | 通过 |
| `S4-P2-T1` | `docs/pfi_v02/INTERCONNECTION_MATRIX.md` 覆盖普通消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、信用卡还款、内部转账、收入、费用、汇率兑换。 | 通过 |
| `S4-P2-T2` | Interconnection Matrix 写明是否计入消费总流出、生活消费、投资、净资产、现金流。 | 已修复并通过 |
| `S4-P2-T3` | 退款抵消原消费；信用卡还款不重复计入生活消费；投资入金计入消费总流出但不计入生活消费。 | 通过 |

## 发现与修复

修复 1：按 interconnection_group_id 防止重复核心计量。

- 问题：原实现主要按 `economic_event_id` 去重。如果银行侧出金和券商侧入金已经匹配到同一 `interconnection_group_id`，但来源侧临时生成了不同 `economic_event_id`，核心指标会把同一笔投资入金算两次。
- 风险：CBA -> Moomoo、支付宝基金申购、黄金申购、内部转账和汇率兑换等双侧记录会污染消费总流出、投资现金、现金流和报告。
- 修复：`aggregate_core_metrics()` 现在优先按 `interconnection_group_id + event_type` 去重；缺少关联组时再按 `economic_event_id + event_type` 兜底。`ordinary_consumption` 与 `consumption` 在核心去重中按同一普通消费口径处理。
- 验证：`tests/test_v022_review_stage4.py` 构造同一 `interconnection_group_id`、两个不同 `economic_event_id` 的银行到 Moomoo 入金，要求 `deduped_core_event_count=1`、`total_consumption_outflow_cny=1000.00`、`investment_cash_cny=1000.00`。

修复 2：补齐现金流依赖图的投资与费用事件。

- 问题：原 `Metric Dependency Graph` 的 `cashflow` 只列收入、退款、信用卡还款、内部转账和汇率兑换，漏掉投资入金、基金申购、黄金申购、投资买入、投资卖出和费用。
- 风险：现金流页、首页摘要和报告可能看不到投资动作与费用对现金压力的影响。
- 修复：`src/pfi_v02/stage_v022_interconnection.py` 与 `config/pfi_parameters.yaml` 的 `cashflow` 依赖图已补齐投资与费用事件。
- 验证：`tests/test_v022_review_stage4.py` 同时读取代码合同和机器参数源，确认现金流依赖事件完整。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 多条来源记录被当成多次经济影响时停止 | 未触发；复审测试覆盖双来源入金，核心金额只算一次。 |
| 关联组缺失导致重复计算时停止 | 未触发；`interconnection_group_id + event_type` 已成为核心去重优先键。 |
| 同一事件在同一口径重复计算时停止 | 未触发；同一关联组同一事件类型只进入核心指标一次。 |
| 核心资金流缺失时停止 | 未触发；现金流依赖图已补齐投资入金、基金申购、黄金申购、投资买入、投资卖出和费用。 |
| 任一事件口径模糊时停止 | 未触发；Interconnection Matrix 写明消费总流出、生活消费、投资、净资产、现金流和抵消规则。 |
| 抵消逻辑不清时停止 | 未触发；退款抵消原消费，信用卡还款不重复生活消费，投资入金进入消费总流出但不进入生活消费。 |
| 同一 interconnection_group 因重复来源记录导致核心金额重复计算 | 未触发；新测试直接覆盖该场景。 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Stage 4 模块 | `PFI/src/pfi_v02/stage_v022_interconnection.py` |
| 参数源 | `PFI/config/pfi_parameters.yaml` |
| Interconnection Matrix | `PFI/docs/pfi_v02/INTERCONNECTION_MATRIX.md` |
| Stage 4 验收报告 | `PFI/docs/pfi_v022/STAGE4_INTERCONNECTION.md` |
| 原 no-double-count 合同测试 | `PFI/tests/test_v022_interconnection_no_double_count.py` |
| 原消费/投资流出测试 | `PFI/tests/test_v022_consumption_investment_outflow.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage4.py` |
| 三基文件 | `PFI/模型参数文件.md`、`PFI/功能清单.md`、`PFI/开发记录.md` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_review_stage4.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_review_stage4.py tests/test_v022_review_stage3.py tests/test_pfi_parameters_consistency.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

本机验证结果：

- Stage 4 复审目标测试：`4 passed, 26 subtests passed`。
- Stage 4 相关回归：`24 passed, 79 subtests passed`。
- 完整 PFI 测试：`270 passed, 251 subtests passed`。
- Web Shell 语法：`node --check PFI/web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- `git diff --check -- PFI`：通过。
- 参数 JSON 解析：`python3 -m json.tool PFI/config/pfi_parameters.yaml` 通过。
- macOS app 轻量验收：`Blocked, pass=22, fail=7, info=2`；运行服务健康，8501 正常，阻塞项为 `/Users/linzezhang/Desktop/PFI.app` 缺失。按当前 goal 约束，本轮不重装 app 入口，整体复审完成后统一刷新入口。

## 剩余风险

- 本轮只证明 Stage 4 的 Economic Event 与 Interconnection 复审问题已解决；Stage 5-13 的复审解决仍未在本 run 中执行。
- 本轮不重装 app 入口；按当前 pursuing goal 约束，整体项目复审解决完成后再刷新 app 入口。
- 真实导入数据的模糊匹配、低置信关联候选和人工确认队列属于后续 Stage 8-13 与整体复审范围；本轮锁定核心计算不能重复入账。
