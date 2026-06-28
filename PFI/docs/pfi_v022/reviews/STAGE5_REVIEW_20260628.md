# PFI v0.2.2 Stage 5 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 5；不复审 Stage 6-13，不做整体项目复审，不重装 app 入口。

复审结论：Stage 5 后台合同修复通过；真实 8501 UIUX 入口阻断已复验关闭
上线阻塞项：1

最新纠偏：用户反馈正式入口 UIUX、二级入口、功能按钮和测试数据边界仍不满足交付要求。Stage 5 后台账本分类修复已通过；`UIUX_REAL_ENTRY_BLOCKER_20260628.md` 已用真实 8501 桌面/移动浏览器矩阵关闭。`TEST_DATA_AUDIT_STAGE5_20260628.md` 仍记录 PFI legacy 测试/样例/模拟数据全局审计风险，后续 Stage 不能只靠完整 pytest 作为产品验收依据。

## 复审范围

Stage 5：统一账本事件、消费双口径与分类体系。

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S5-P1-T1` | 建立统一账本事件类型表，覆盖消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、费用、信用卡还款、内部转账、收入、估值、汇率兑换。 | 通过 |
| `S5-P1-T2` | 每种事件绑定消费总流出、生活消费、投资、净资产、现金流五个影响口径。 | 通过 |
| `S5-P2-T1` | 新增 `消费总流出金额`，包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用，退款抵消。 | 通过 |
| `S5-P2-T2` | 保留 `生活消费金额`，只包含普通生活消费，排除投资入金、基金申购、黄金申购、投资买入、内部转账、信用卡还款。 | 通过 |
| `S5-P2-T3` | 首页、消费页、报告同时展示 `消费总流出` 与 `生活消费`，并解释差异。 | 通过 |
| `S5-P3-T1` | 建立 12 个以内 L1 大类。 | 通过 |
| `S5-P3-T2` | 每个 L1 最多 5 个 L2。 | 通过 |
| `S5-P3-T3` | 总 L2 不超过 50，并由自动测试覆盖。 | 通过 |
| `S5-P3-T4` | 每个 L1 有 `future_merge_to` 或 `merge_candidate`，后续可压缩到 10 类或更少。 | 已修复并通过 |

## 发现与修复

修复 1：分类验证真正检查每笔交易只有一个主分类。

- 问题：原 `validate_stage5_taxonomy_constraints()` 只返回静态 `primary_category_per_transaction=1`，没有检查传入 taxonomy 中每个 L1 是否仍保持该值。如果某个 L1 被改成 `2`，验证仍会通过。
- 风险：这会绕过 taskpack 的“每笔交易只有一个主分类”，让分类系统和 Stage 6 标签系统边界变模糊。
- 修复：验证函数现在检查每个 taxonomy row 的 `primary_category_per_transaction`；不等于 `1` 时返回 `status=失败`，并在 `violations` 中写入 `primary_category_per_transaction`。
- 验证：`tests/test_v022_review_stage5.py` 构造错误 taxonomy 并要求失败。

修复 2：补齐后续压缩到 10 类以内的机器验收字段。

- 问题：文档写明后续可压缩到 10 类或更少，但代码和参数源没有返回可直接验收的 `future_merge_target_max_l1`、`future_merge_l1_count`、`future_merge_groups`。
- 风险：GitHub 验收只能看文字，不能证明 12 个 L1 真的能按 `future_merge_to` 收敛到 10 类以内。
- 修复：验证函数、Stage 5 合同和 `config/pfi_parameters.yaml` 均新增 `future_merge_target_max_l1=10`、`future_merge_l1_count=7`、`future_merge_groups` 和 `multi_dimensional_analysis_uses_tags=true`。
- 验证：`tests/test_v022_review_stage5.py` 同时读取运行合同和机器参数源，确认压缩目标、实际分组和标签边界一致。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 事件类型不足以表达真实资金流时停止 | 未触发；统一账本事件类型表覆盖 13 类事件，包含估值和汇率兑换。 |
| 影响口径缺失时停止 | 未触发；每个事件都有消费总流出、生活消费、投资、净资产、现金流 flags。 |
| 投资入金未计入消费总流出时停止 | 未触发；投资入金、基金申购、黄金申购、投资买入和费用进入消费总流出。 |
| 生活消费被投资入金污染时停止 | 未触发；生活消费只包含普通生活消费并由退款抵消。 |
| 只显示一个消费数字导致误解时停止 | 未触发；首页、消费页、报告 payload 同时包含 `消费总流出` 与 `生活消费`。 |
| 分类超过限制时停止 | 未触发；当前 L1=12、单个 L2 最大=5、总 L2=50。 |
| 后续无法合并分类时停止 | 未触发；当前 future merge 分组为 7 类，低于 10 类目标。 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Stage 5 模块 | `PFI/src/pfi_v02/stage_v022_ledger_taxonomy.py` |
| Stage 5 合同 | `PFI/src/pfi_v02/stage_v022_database_governance.py` |
| 参数源 | `PFI/config/pfi_parameters.yaml` |
| Stage 5 验收报告 | `PFI/docs/pfi_v022/STAGE5_LEDGER_TAXONOMY.md` |
| 原 Stage 5 合同测试 | `PFI/tests/test_v022_stage5_ledger_taxonomy.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage5.py` |
| 三基文件 | `PFI/模型参数文件.md`、`PFI/功能清单.md`、`PFI/开发记录.md` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_review_stage5.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_review_stage5.py tests/test_v022_review_stage4.py tests/test_pfi_parameters_consistency.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests -q -p no:cacheprovider
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

本机验证结果：

- Stage 5 复审目标测试：`4 passed, 27 subtests passed`。
- Stage 5 相关回归：`21 passed, 126 subtests passed`。
- 完整 PFI 测试：`274 passed, 278 subtests passed`。
- Web Shell 语法：`node --check PFI/web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- `git diff --check -- PFI`：通过。
- 参数 JSON 解析：`python3 -m json.tool PFI/config/pfi_parameters.yaml` 通过。
- macOS app 轻量验收：`Blocked, pass=22, fail=7, info=2`；运行服务健康，8501 正常，阻塞项为 `/Users/linzezhang/Desktop/PFI.app` 缺失。按当前 goal 约束，本轮不重装 app 入口，整体复审完成后统一刷新入口。
- 真实 8501 UIUX 最终复验：`/tmp/pfi_uiux_recheck_stage5_fixed2/summary.json`；桌面和移动均为 iframe=1、15/15 一级入口可见且可点击、搜索 `8815/406` 命中真实支付宝流水、上传中心/导入中心可见、业务页反馈污染 0、设置页反馈控制可见、禁用可见词 0、console/page error 0；截图为 `/tmp/pfi_uiux_recheck_stage5_fixed2/desktop.png` 和 `/tmp/pfi_uiux_recheck_stage5_fixed2/mobile.png`。
- 搜索覆盖层回归：`input type=search` 首次 Escape 后搜索结果面板隐藏，随后可以点击 `数据源与上传` 并打开上传中心。

## 剩余风险

- 本轮只证明 Stage 5 的账本事件、双消费口径、消费分类后台问题和真实入口 UIUX 阻断已修复；不能自动证明 Stage 6-13 或整体项目复审完成。
- 真实 8501 UIUX 复验已通过，见 `PFI/docs/pfi_v022/reviews/UIUX_REAL_ENTRY_BLOCKER_20260628.md`。
- PFI 仓库仍存在大量 legacy `demo/sample/synthetic/fixture/mock/fake/测试样例` 命中；后续不能继续用完整 pytest 作为产品验收依据，见 `PFI/docs/pfi_v022/reviews/TEST_DATA_AUDIT_STAGE5_20260628.md`。
- 本轮不重装 app 入口；side thread 已处理前端入口、反馈污染、上传归位和阶段标签/小字清理；主线程只补充搜索覆盖层关闭兜底并完成真实浏览器矩阵复验。
