# PFI v0.2.2 Stage 3 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 3；不复审 Stage 4-13，不做整体项目复审，不重装 app 入口。

复审结论：通过  
上线阻塞项：0

## 复审范围

Stage 3：数据源、账户角色与可扩展结构。

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S3-P1-T1` | 建立通用数据源 Profile Schema，支持 wallet、bank、broker、fund_platform、bullion_platform、payment_platform、manual_snapshot、other。 | 通过 |
| `S3-P1-T2` | 数据源能力由 capabilities 描述，覆盖现金流水、投资交易、基金交易、黄金交易、余额快照、费用、退款、转账。 | 通过 |
| `S3-P1-T3` | 支持未来新增数据源，至少提供 `other_source_template`。 | 已修复并通过 |
| `S3-P2-T1` | 账户角色 schema 支持一个账户同时是主钱包、消费账户、投资入金来源、收入接收账户等。 | 已修复并通过 |
| `S3-P2-T2` | 角色字段包含 `role_effective_from` 和 `role_effective_to`，历史可追踪。 | 通过 |
| `S3-P2-T3` | 指标计算按角色和事件类型，不按 source 名称硬编码。 | 通过 |

## 发现与修复

修复 1：补齐 taskpack 默认账户角色。

- 问题：taskpack 默认角色包含 `主钱包`、`消费账户`、`投资入金来源`、`投资账户`、`收入接收账户`、`负债账户`、`储蓄账户`、`外部对手方`；当前实现缺少 `储蓄账户` 和 `外部对手方`，且 `income_account` 中文标签写为 `收入账户`。
- 风险：未来新增储蓄账户、外部收付款对手方或家庭转账对手方时会被错误归为未知角色，进入复核或要求改核心代码。
- 修复：新增 `savings_account=储蓄账户`、`external_counterparty=外部对手方`；将 `income_account` 中文标签改为 `收入接收账户`；参数源增加 `role_labels_zh`。
- 保留：`asset_custody=资产托管账户` 继续保留为 PFI 扩展角色，用于基金、券商和贵金属托管。

修复 2：新增 source profile 角色扩展示例。

- 问题：`other_source_template` 只能覆盖主钱包、消费账户、收入和投资入金来源，不能直接表达储蓄账户或外部对手方。
- 风险：新增 source 虽然有模板，但 role 维度不完整，仍可能要求改核心枚举或绕过 schema。
- 修复：`other_source_template` 增加 `savings_account` 和 `external_counterparty`；`build_custom_source_profile()` 可接受这两个 role；示例账户 `acct_cba_savings`、`acct_external_counterparty` 可按日期读取有效角色。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 新增数据源必须改核心代码时停止 | 未触发；`build_custom_source_profile()` 可创建带储蓄账户和外部对手方角色的 `other` source。 |
| 数据源能力写死在名称里时停止 | 未触发；source 能力仍由 `capabilities` 声明。 |
| 无法添加新 source 时停止 | 未触发；复审测试新增 `family_savings_and_counterparty` 自定义 source。 |
| 一个账户只能有一个角色时停止 | 未触发；一个账户仍可多角色，新增角色没有破坏多角色 schema。 |
| 角色历史无法追踪时停止 | 未触发；新增角色仍走 `role_effective_from` / `role_effective_to`。 |
| 公式按 source 名称写死时停止 | 未触发；消费计算仍按 `affects_consumption` 和 active role，不按支付宝、微信、银行卡等名称。 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Stage 3 模块 | `PFI/src/pfi_v02/stage_v022_source_profile.py` |
| 参数源 | `PFI/config/pfi_parameters.yaml` |
| Stage 3 验收报告 | `PFI/docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` |
| 原 Stage 3 合同测试 | `PFI/tests/test_v022_stage3_source_account_profiles.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage3.py` |
| 三基文件 | `PFI/模型参数文件.md`、`PFI/功能清单.md`、`PFI/开发记录.md` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_review_stage3.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage3_source_account_profiles.py tests/test_v022_review_stage3.py tests/test_v022_review_stage2.py tests/test_pfi_parameters_consistency.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

本机验证结果：

- Stage 3 复审目标测试：`4 passed`。
- 原 Stage 3 合同测试：`7 passed, 13 subtests passed`。
- Stage 0-3/复审回归：`48 passed, 48 subtests passed`。
- 完整 PFI 测试：`266 passed, 225 subtests passed`。
- Web Shell 语法：`node --check PFI/web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- `git diff --check -- PFI`：通过。
- 参数 JSON：`python3 -m json.tool PFI/config/pfi_parameters.yaml` 通过。
- macOS app 轻量验收：`Blocked, pass=22, fail=7, info=2`；失败均来自 `/Users/linzezhang/Desktop/PFI.app` 不存在，8501 健康运行，按当前 goal 约束留到整体复审完成后统一重装入口。

## 剩余风险

- 本轮只证明 Stage 3 的 source/account profile 复审问题已解决；Stage 4-13 的复审解决仍未在本 run 中执行。
- 本轮不重装 app 入口；按当前 pursuing goal 约束，整体项目复审解决完成后再刷新 app 入口。
- 当前角色 schema 已允许外部对手方，但真实对手方匹配、Interconnection 归并和双计量防护属于 Stage 4 及后续复审范围。
