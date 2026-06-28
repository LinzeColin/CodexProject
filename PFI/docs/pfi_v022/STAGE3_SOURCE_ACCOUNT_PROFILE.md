# PFI v0.2.2 Stage 3 数据源、账户角色与可扩展结构

交付日期：2026-06-28 Australia/Sydney
任务名称：`PFI v0.2.2 E2E 逻辑优化`
验收门禁：`PFI-V022-S3-SOURCE-ACCOUNT-PROFILE-GATE`

## 结论

Stage 3 - 数据源、账户角色与可扩展结构 已完成。PFI 不再把“支付宝=消费、Moomoo=投资、银行卡=现金”作为计算规则；当前合同改为 source profile + capabilities + account role assignment + role effective date。

本轮不实现 Stage 4 的 `economic_event_id` 或 `interconnection_group_id`，不改 v0.2.1 HTML Web Shell 交互架构，不做真实交易、自动投资、支付或券商提交。

## Task 复核

| Task ID | 交付物 | 验收结论 |
| --- | --- | --- |
| `S3-P1-T1` | 通用数据源 Profile Schema | 通过，支持 `wallet`、`bank`、`broker`、`fund_platform`、`bullion_platform`、`payment_platform`、`manual_snapshot`、`other`。 |
| `S3-P1-T2` | capabilities source profile | 通过，能力覆盖现金流水、投资交易、基金交易、黄金交易、余额快照、费用、退款、转账。 |
| `S3-P1-T3` | 未来新增数据源模板 | 通过，提供 `other_source_template`，新增 source 可用 profile 扩展，不需要修改核心计算代码。 |
| `S3-P2-T1` | 账户角色 Schema | 通过，一个账户可同时是主钱包、消费账户、投资入金来源、收入接收账户、储蓄账户和外部对手方。 |
| `S3-P2-T2` | 角色生效时间 | 通过，角色字段包含 `role_effective_from` 和 `role_effective_to`。 |
| `S3-P2-T3` | 按角色和事件类型计算 | 通过，消费计算按 `affects_consumption=true` 和 active `consumption_account` role，不按 source 名称硬编码。 |

## Source Profile Schema

| 字段 | 中文说明 |
| --- | --- |
| `source_id` | 数据源 ID。 |
| `source_label_zh` | 数据源中文名称。 |
| `source_type` | 数据源类型。 |
| `supported_file_types` | 支持文件类型。 |
| `capabilities` | 数据源能力。 |
| `account_roles_allowed` | 允许绑定的账户角色。 |
| `parser_version` | 解析器或 profile 版本。 |
| `role_effective_date_required` | 是否强制账户角色有生效日期；当前必须为 `true`。 |

支持的 `source_type`：

```text
wallet, bank, broker, fund_platform, bullion_platform, payment_platform, manual_snapshot, other
```

支持的 `capabilities`：

```text
cash_ledger=现金流水
investment_trade=投资交易
fund_trade=基金交易
bullion_trade=黄金交易
balance_snapshot=余额快照
fee=费用
refund=退款
transfer=转账
```

## other_source_template

`other_source_template` 是未来新增数据源模板，默认字段如下：

| 字段 | 值 |
| --- | --- |
| `source_id` | `other_source_template` |
| `source_type` | `other` |
| `supported_file_types` | `csv`, `xlsx`, `json`, `pdf`, `manual` |
| `capabilities` | `cash_ledger`, `balance_snapshot`, `fee`, `refund`, `transfer` |
| `account_roles_allowed` | `main_wallet`, `consumption_account`, `income_account`, `investment_funding_source` |
| `parser_version` | `profile-template-v1` |
| `role_effective_date_required` | `true` |

新增数据源流程：

1. 新建 source profile。
2. 选择 `source_type`。
3. 声明 `capabilities`。
4. 声明允许的 `account_roles_allowed`。
5. 给账户绑定 role，并填写 `role_effective_from` / `role_effective_to`。
6. 指标计算读取 role 和 event flags，不读取 source 名称。

## 账户角色 Schema

账户角色字段：

```text
account_id
source_id
role
role_effective_from
role_effective_to
```

支持角色：

```text
main_wallet=主钱包
consumption_account=消费账户
investment_funding_source=投资入金来源
income_account=收入接收账户
investment_account=投资账户
asset_custody=资产托管账户
liability_account=负债账户
savings_account=储蓄账户
external_counterparty=外部对手方
```

示例：`acct_cba_main` 可以同时具备：

- `main_wallet`
- `consumption_account`
- `investment_funding_source`
- `income_account`

当某个账户角色变化时，不覆盖历史角色，而是新增或关闭一条 role assignment。历史账本按交易日期匹配当日有效 role。

## 计算规则

当前 Stage 3 锁定原则：

```text
metric_basis = role_and_event_type
forbid_source_name_hardcode = true
```

消费金额示例规则：

```text
消费金额 = 所有 affects_consumption=true 且账户在事件日期拥有 consumption_account 角色的 ledger event 之和
```

该规则不允许写成：

```text
消费金额 = 支付宝 + 微信 + 银行卡
```

未知 role、未知 source_type、未知 capability 进入复核队列，不直接进入正式计算。

## 交付文件

| 文件 | 用途 |
| --- | --- |
| `src/pfi_v02/stage_v022_source_profile.py` | Stage 3 source profile、capability、account role、生效期和 role-aware 计算合同。 |
| `tests/test_v022_stage3_source_account_profiles.py` | Stage 3 合同测试。 |
| `config/pfi_parameters.yaml` | Stage 3 机器可读参数源。 |
| `config/parameter_changelog.md` | Stage 3 参数变更记录。 |
| `模型参数文件.md` | Stage 3 中文参数解释。 |
| `功能清单.md` | Stage 3 用户可检查能力目录。 |
| `开发记录.md` | Stage 3 开发记录和验收结果。 |

## Stop Condition 复核

| Stop Condition | 结论 |
| --- | --- |
| 新增数据源必须改核心代码 | 未触发，`build_custom_source_profile()` 和 `other_source_template` 可扩展新 source。 |
| capabilities 写死在 source 名称里 | 未触发，source 能力由 `capabilities` 字段声明。 |
| 无法添加新 source | 未触发，测试已加入 `new_super_wallet` custom profile。 |
| 一个账户只能有一个角色 | 未触发，`acct_cba_main` 同时有四个 role。 |
| 角色历史无法追踪 | 未触发，role assignment 包含 `role_effective_from` 和 `role_effective_to`。 |
| 公式按 source 名称写死 | 未触发，消费计算只读取 `affects_consumption` 和 `consumption_account` role。 |

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage3_source_account_profiles -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date PFI.tests.test_v022_stage3_source_account_profiles -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## 本次验证结果

| 命令 | 结果 |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage3_source_account_profiles -q` | `Ran 7 tests / OK` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date PFI.tests.test_v022_stage3_source_account_profiles -q` | `Ran 32 tests / OK` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q` | `Ran 179 tests / OK` |
| `python3 scripts/validate_project_governance.py --project PFI` | `errors: 0`, `warnings: 0` |
| `node --check PFI/web/app/shell.js` | 通过 |
| `git diff --check -- PFI` | 通过 |
| `python3 -m json.tool PFI/config/pfi_parameters.yaml` | 通过 |
| `git diff --name-only -- PFI/web` | 无输出，确认本轮不修改 Web Shell 前端入口 |
