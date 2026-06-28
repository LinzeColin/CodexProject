# PFI v0.2.2 Stage 6 - 标签系统与自定义视图

## 目标

本轮完成 Stage 6：在 Stage 5 的单一主分类体系之外，新增可持久化、多标签、可规则自动赋值、可追踪历史、可筛选账本、可进入报告和可保存自定义视图的标签系统。

本轮不实现 Stage 7 现金流评分、Stage 8 Runtime Diff、Stage 9 参数中心或 Stage 12 逻辑审查页；不新增真实交易、自动投资、支付或券商提交能力。

## Task 验收

| Task ID | 交付物 | 验收标准 | 状态 |
|---|---|---|---|
| `S6-P1-T1` | `pfi_tags` | 标签包含 ID、中文名、范围、类型、是否系统默认、是否可编辑、是否启用 | 完成 |
| `S6-P1-T2` | `pfi_tag_assignments` | 一笔交易、经济事件、持仓或账户可有多个标签 | 完成 |
| `S6-P1-T3` | `pfi_tag_rules` | 支持按金额、时间、分类、事件类型、账户角色自动打标签 | 完成 |
| `S6-P2-T1` | 默认标签库 | 覆盖通用、消费、投资、数据质量、现金流、复盘标签 | 完成 |
| `S6-P2-T2` | 自定义标签生命周期 | 支持新增、重命名、停用、删除自定义标签；系统默认标签不可物理删除 | 完成 |
| `S6-P2-T3` | `pfi_tag_history` | 标签变更记录旧值、新值、时间、影响对象和原因 | 完成 |
| `S6-P3-T1` | 标签筛选账本 | 可按标签组合筛选，例如夜间 + 大额 + 计划外 | 完成 |
| `S6-P3-T2` | 标签驱动报告 | 报告能按标签聚合消费、投资、异常和复盘项 | 完成 |
| `S6-P3-T3` | `pfi_custom_views` / 本地 HTML | 可保存 `订阅检查`、`投资追涨复盘`、`夜间大额复盘` 等常用视图 | 完成 |

## 持久化表

| 表 | 用途 |
|---|---|
| `pfi_tags` | 标签注册表，包含默认标签和用户自定义标签。 |
| `pfi_tag_assignments` | 标签赋值表，支持同一对象拥有多个标签。 |
| `pfi_tag_rules` | 自动打标签规则表。 |
| `pfi_tag_history` | 标签新增、重命名、停用、删除的历史记录。 |
| `pfi_custom_views` | 保存自定义视图名称、标签组合和目标入口。 |

## 默认标签库

默认标签组为：通用、消费、投资、数据质量、现金流、复盘。

关键默认标签包括：计划内、计划外、周期性、人工已复核、夜间消费、大额消费、订阅扣费、投资入金、买入交易、追涨候选、低置信、未匹配转账、现金流压力、需要复核、行动候选。

系统默认标签用于历史追溯，不允许物理删除；用户自定义标签支持新增、重命名、停用和软删除。

## 标签规则

当前默认规则覆盖：

- 金额：`amount_cny >= 2000` 自动打 `大额消费`。
- 时间：`22:00-06:00` 自动打 `夜间消费`。
- 分类：`订阅服务` 自动打 `订阅扣费`。
- 事件类型：`investment_deposit` 自动打 `投资入金`。
- 事件类型：`investment_buy` 自动打 `买入交易`。
- 账户角色：`investment_funding_source` 自动打 `投资挤压现金`。

## 自定义视图

本地 HTML 验收页：`PFI/web/pfi_v022_tag_views.html`。

默认示例：

- `订阅检查`：筛选订阅扣费 + 周期性。
- `投资追涨复盘`：筛选买入交易 + 追涨候选。
- `夜间大额复盘`：筛选夜间消费 + 大额消费。

自定义视图只保存筛选条件，不改变原始账本、净资产、投资收益或现金流金额。

## Stop Condition 复核

| Stop Condition | 处理 |
|---|---|
| 标签不能持久化 | `Stage6TagViewStore` 建立 SQLite 表并支持重启后读取。 |
| 一笔记录只能有一个标签 | `pfi_tag_assignments` 支持同一对象多个标签。 |
| 标签只能手动添加 | `pfi_tag_rules` 支持金额、时间、分类、事件类型、账户角色自动打标签。 |
| 默认标签缺失关键分析维度 | 默认标签覆盖通用、消费、投资、数据质量、现金流、复盘。 |
| 自定义标签无法修改 | 自定义标签支持新增、重命名、停用、删除。 |
| 标签历史不可追踪 | `pfi_tag_history` 记录旧值、新值、时间、影响对象和原因。 |
| 标签无法筛选账本 | `filter_ledger_by_tags()` 支持标签组合筛选。 |
| 标签不参与报告 | `build_tag_report()` 按标签聚合记录数量和 CNY 金额。 |
| 视图不能保存 | `save_custom_view()` 写入 `pfi_custom_views`，`render_custom_views_html()` 可渲染本地 HTML。 |

## Agent 交叉复审

- Agent 4：标签体系复核通过；分类保持单一主分类，标签承担多维分析、建议、视图和复盘。
- Agent 5：视图与报告复核通过；标签筛选不改变原始账本金额，自定义视图只保存筛选条件。

## Validation

```bash
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage6_tags_views.py -q
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py -q
PYTHONPATH=src .venv/bin/python -B -m pytest -q
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前本地 closeout 结果：

- Stage 6 目标测试：`6 passed`。
- Stage 0-6 v0.2.2 回归：`51 passed`。
- 完整 PFI pytest：`209 passed`。
- 项目治理：`errors 0 / warnings 0`。
- Web Shell 语法和 `git diff --check -- PFI`：通过。
- macOS app acceptance lite：`29 pass / 0 fail / 2 info`。
- 真实 8501 浏览器：上方工作台 iframe 包含 8 个一级入口，父页面和工作台禁用词扫描 0 命中，console errors `0`，截图 `/tmp/pfi-v022-stage6-app-verified.png`。
- Stage 6 HTML 浏览器：9 个任务 ID、5 张表、6 个默认标签组、3 个自定义视图全部可见，禁用词扫描 0 命中，console errors `0`，截图 `/tmp/pfi-v022-stage6-tag-views-verified.png`。
