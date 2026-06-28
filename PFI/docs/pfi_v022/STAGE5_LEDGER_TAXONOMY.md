# PFI v0.2.2 Stage 5 - 统一账本事件、消费双口径与分类体系

## 目标

本轮完成 Stage 5：在 Stage 4 的 `economic_event_id`、`interconnection_group_id` 和 no-double-count 事实层之上，锁定统一账本事件类型表、消费总流出 / 生活消费双口径，以及 12 大类 / 50 中类的消费分类 taxonomy。

本轮不实现 Stage 6 标签持久化，不修改 v0.2.1 Web Shell UIUX 基线，不新增真实交易、自动投资、支付或券商提交能力。

2026-06-28 复审并解决更新：分类验证已从静态声明升级为真实校验，每个 L1 的 `primary_category_per_transaction` 必须等于 `1`；同时新增 `future_merge_target_max_l1=10`、`future_merge_l1_count`、`future_merge_groups` 和 `multi_dimensional_analysis_uses_tags=true`，证明默认 12 大类可压缩到 10 类或更少，多维分析交给 Stage 6 标签系统。

## Task 验收

| Task ID | 交付物 | 验收标准 | 状态 |
|---|---|---|---|
| `S5-P1-T1` | `build_stage5_ledger_event_type_table()` | 包含消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、费用、信用卡还款、内部转账、收入、估值、汇率兑换 | 完成 |
| `S5-P1-T2` | Stage 5 event type policy | 每个事件写明是否影响消费总流出、生活消费、投资、净资产、现金流 | 完成 |
| `S5-P2-T1` | `消费总流出金额` 公式 | 包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用，退款抵消 | 完成 |
| `S5-P2-T2` | `生活消费金额` 公式 | 只包含普通生活消费，排除投资入金、基金申购、黄金申购、投资买入、内部转账、信用卡还款 | 完成 |
| `S5-P2-T3` | 双口径展示模板 | 首页、消费页、报告同时展示 `消费总流出` 与 `生活消费`，并解释差异 | 完成 |
| `S5-P3-T1` | L1 分类参数 | L1 ≤ 12 | 完成 |
| `S5-P3-T2` | L2 分类参数 | 每个 L1 的 L2 ≤ 5 | 完成 |
| `S5-P3-T3` | 分类约束测试 | L2 ≤ 50 | 完成 |
| `S5-P3-T4` | `future_merge_to` / `merge_candidate` | 每个 L1 都预留后续压缩字段 | 完成 |

## 双消费口径

- `消费总流出`：生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消。
- `生活消费`：普通生活消费 - 退款抵消。
- 首页、消费页和报告必须同时展示两个数字，不能只展示一个消费数字。
- 两个数字必须来自同一事实层和同一 `aggregate_core_metrics()` 读模型，不能各自硬编码。

## 默认分类 taxonomy

| L1 大类 | L2 中类 | 后续合并字段 |
|---|---|---|
| 餐饮食品 | 外出就餐、外卖、咖啡饮品、超市食品、零食饮料 | 生活必要 |
| 居住家庭 | 房租房贷、水电燃气、网络通讯、家居维修 | 生活必要 |
| 交通出行 | 公共交通、打车网约、车辆油电、停车路桥、长途交通 | 出行与成长 |
| 购物用品 | 日用百货、服饰鞋包、数码家电、美妆个护、家居用品 | 可选消费 |
| 医疗健康 | 门诊药品、保险保障、健身运动、牙科眼科 | 生活必要 |
| 教育成长 | 课程培训、书籍资料、考试认证、学习工具 | 出行与成长 |
| 娱乐社交 | 影视游戏、活动票务、社交聚餐、礼物红包、休闲旅行 | 可选消费 |
| 订阅服务 | 影音会员、软件工具、云服务、平台会员 | 可选消费 |
| 金融费用 | 银行费用、支付手续费、汇兑成本、贷款利息、税费罚款 | 金融成本 |
| 投资资金流出 | 证券入金、基金申购、黄金申购、其他投资入金 | 投资资金流 |
| 家庭责任 | 家庭支持、人情往来、报销垫付 | 家庭责任 |
| 调整其他 | 退款抵扣、未分类其他 | 调整其他 |

约束结果：`L1 ≤ 12`，每类 `L2 ≤ 5`，总 `L2 ≤ 50`，每笔交易主分类数量为 `1`。当前 `future_merge_to` 分组为 7 类，满足后续压缩到 10 类或更少的要求。

## Stop Condition 复核

| Stop Condition | 处理 |
|---|---|
| 事件类型不足以表达真实资金流 | Stage 5 事件表覆盖 13 类事件，包含估值和汇率兑换。 |
| 事件影响口径缺失 | 每个事件都有五个 affects flags。 |
| 投资入金未计入消费总流出 | `investment_deposit.affects_total_consumption_outflow=true`，测试覆盖。 |
| 生活消费被投资入金污染 | `investment_deposit.affects_living_consumption=false`，测试覆盖。 |
| 只显示一个消费数字导致误解 | 首页、消费页、报告模板同时返回两个口径和中文差异解释。 |
| 分类超过限制 | `validate_stage5_taxonomy_constraints()` 校验 `L1 ≤ 12`、每类 `L2 ≤ 5`、总 `L2 ≤ 50`。 |
| 每笔交易主分类数量不是 1 | `validate_stage5_taxonomy_constraints()` 会返回 `status=失败`，并在 `violations` 中记录 `primary_category_per_transaction`。 |
| 后续无法合并分类 | 每个 L1 都有 `future_merge_to` 和 `merge_candidate`，且当前 future merge 分组为 7 类，低于 `future_merge_target_max_l1=10`。 |

## Agent 交叉复审

- Agent 1：双消费口径复核通过；投资入金、基金申购、黄金申购、投资买入和费用进入消费总流出，但不进入生活消费。
- Agent 3：分类参数复核通过；12 大类 / 每类 5 中类 / 总中类 50，分类与 Stage 6 标签系统分离。

## 复审修复

- 修复 1：分类验证真正检查每笔交易只有一个主分类。错误 taxonomy 中任一 L1 的 `primary_category_per_transaction` 不等于 `1` 时，验证返回失败。
- 修复 2：补齐后续压缩到 10 类以内的机器验收字段。默认 12 个 L1 当前可通过 `future_merge_to` 收敛为 7 个分组。
- 本轮复审报告：`docs/pfi_v022/reviews/STAGE5_REVIEW_20260628.md`。
- 本轮复审测试：`tests/test_v022_review_stage5.py`。

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_review_stage5.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_review_stage5.py tests/test_v022_review_stage4.py tests/test_pfi_parameters_consistency.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests -q -p no:cacheprovider
python3 scripts/validate_project_governance.py --project PFI
node --check web/app/shell.js
git diff --check -- PFI
```

本轮实际结果：

- Stage 5 复审目标测试：`4 passed, 27 subtests passed`。
- Stage 5 相关回归：`21 passed, 126 subtests passed`。
- 完整 PFI 测试：`274 passed, 278 subtests passed`。
- 项目治理：`errors 0 / warnings 0`。
- Web shell 语法、`git diff --check -- PFI`、参数 JSON 解析：通过。
- macOS app 轻量验收：`Blocked, pass=22, fail=7, info=2`；运行服务健康，8501 正常，阻塞项为 `/Users/linzezhang/Desktop/PFI.app` 缺失。按当前 goal 约束，本轮不重装 app 入口。
