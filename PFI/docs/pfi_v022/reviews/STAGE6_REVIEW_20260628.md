# PFI v0.2.2 Stage 6 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 6；不复审 Stage 7-13，不做整体项目复审，不重装 app 入口，不同步 GitHub。

复审结论：Stage 6 标签系统与自定义视图合同通过；验收测试已从构造财务记录改为真实 `MetaDatabase` 支付宝流水。
上线阻塞项：1

剩余阻塞项是全局 legacy 测试/样例/模拟数据审计仍未关闭；Stage 6 本轮已不再用虚构交易作为验收依据。

## 复审范围

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S6-P1-T1` | `pfi_tags` 标签注册表包含 ID、中文名、范围、类型、系统默认、可编辑、启用状态。 | 通过 |
| `S6-P1-T2` | `pfi_tag_assignments` 支持一笔交易、经济事件、持仓或账户拥有多个标签。 | 通过 |
| `S6-P1-T3` | `pfi_tag_rules` 支持金额、时间、分类、事件类型、账户角色自动打标签。 | 通过 |
| `S6-P2-T1` | 默认标签库覆盖通用、消费、投资、数据质量、现金流、复盘。 | 通过 |
| `S6-P2-T2` | 自定义标签支持新增、重命名、停用、删除；系统默认标签不可物理删除。 | 通过 |
| `S6-P2-T3` | `pfi_tag_history` 记录旧值、新值、时间、影响对象和原因。 | 通过 |
| `S6-P3-T1` | 标签组合可筛选账本。 | 通过 |
| `S6-P3-T2` | 标签驱动报告可按标签聚合消费、投资、异常和复盘项。 | 通过 |
| `S6-P3-T3` | `pfi_custom_views` 和本地 HTML 可保存并展示自定义标签视图。 | 通过 |

## 发现与修复

修复 1：Stage 6 验收不再依赖构造财务交易。

- 问题：`tests/test_v022_stage6_tags_views.py` 使用 `txn_001`、`txn_night_large` 等构造交易验证规则和报告。这与用户最新约束冲突：PFI 正式交付和验收不应使用 demo/sample/synthetic/fixture/mock/fake/测试样例或虚构财务事实。
- 修复：新增 `load_stage6_alipay_records_from_metadatabase()`，从 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` 读取真实支付宝标准化流水，转换成 Stage 6 标签规则可消费的记录形态；没有真实文件时返回空列表，不制造 fallback 数据。
- 验证：Stage 6 目标测试现在使用真实 `txn_alipay_*` transaction_id，并拒绝旧构造 transaction id。

修复 2：真实流水可进入标签规则、标签筛选和标签报告。

- 数据源：`MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`。
- 转换后记录数：`7247`。
- 真实事件类型覆盖：`ordinary_consumption`、`investment_return`、`investment_deposit`、`investment_buy`、`refund`。
- 标签规则示例：真实大额消费按 `CNY >= 2000` 命中 `tag_consumption_large`；真实投资记录可进入投资标签报告。
- 报告边界：标签报告只聚合真实记录，不改变原始流水、净资产、投资收益或现金流金额。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 标签不能持久化 | 未触发；`Stage6TagViewStore` 建立 SQLite 表并支持重启后读取。 |
| 一笔记录只能有一个标签 | 未触发；`pfi_tag_assignments` 支持同一真实 transaction_id 多标签。 |
| 标签只能手动添加 | 未触发；`pfi_tag_rules` 对真实 MetaDatabase 流水自动打标签。 |
| 默认标签缺失关键分析维度 | 未触发；默认标签覆盖通用、消费、投资、数据质量、现金流、复盘。 |
| 自定义标签无法修改 | 未触发；自定义标签支持新增、重命名、停用、软删除。 |
| 标签历史不可追踪 | 未触发；`pfi_tag_history` 记录旧值、新值、影响对象和原因。 |
| 标签无法筛选账本 | 未触发；`filter_ledger_by_tags()` 支持真实 transaction_id 标签筛选。 |
| 标签不参与报告 | 未触发；`build_tag_report()` 按真实记录标签聚合 CNY 金额。 |
| 自定义视图不能保存 | 未触发；`pfi_custom_views` 和 HTML 输出可保存并展示视图。 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Stage 6 模块 | `PFI/src/pfi_v02/stage_v022_tags_views.py` |
| 原 Stage 6 合同测试 | `PFI/tests/test_v022_stage6_tags_views.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage6.py` |
| Stage 6 验收报告 | `PFI/docs/pfi_v022/STAGE6_TAGS_CUSTOM_VIEWS.md` |
| Roadmap lock | `PFI/docs/pfi_v022/ROADMAP_LOCK.md` |
| 真实标准化流水 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage6_tags_views.py tests/test_v022_review_stage6.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_review_stage6.py -q -p no:cacheprovider
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## 最新验证结果

- Stage 6 目标 + 复审测试：`9 passed, 139 subtests passed`。
- Stage 0-6 v0.2.2 相关回归：`54 passed, 243 subtests passed`。
- Web shell 语法：`node --check PFI/web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- 空白检查：`git diff --check -- PFI` 通过。
- 8501 health：`ok`。
- 真实浏览器矩阵：`/tmp/pfi_stage6_review_recheck/summary.json` 通过；桌面 15 个一级入口、7 个首页功能按钮、全局搜索 `8815/406`、策略实验室同路由、业务页反馈隔离、禁用词扫描、console errors 均通过；移动端 5 个底部入口可见，水平溢出 `0px`。截图为 `/tmp/pfi_stage6_review_recheck/desktop.png` 和 `/tmp/pfi_stage6_review_recheck/mobile.png`。

## 剩余风险

- 本轮只证明 Stage 6 已按真实 MetaDatabase 流水完成复审；不能自动证明 Stage 7-13 或整体项目复审完成。
- PFI 仓库仍存在 legacy `demo/sample/synthetic/fixture/mock/fake/测试样例` 命中；后续不能只用完整 pytest 作为产品验收依据。
- 本轮不重装 app 入口；整体 pursuing goal 完成后再统一刷新 app 入口。
- 本轮不同步 GitHub；当前 worktree 存在 side thread 和历史混合改动，后续同步前必须先做 PFI-only diff review。
