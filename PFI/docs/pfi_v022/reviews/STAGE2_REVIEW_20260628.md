# PFI v0.2.2 Stage 2 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 2；不复审 Stage 3-13，不做整体项目复审，不重装 app 入口。

复审结论：通过  
上线阻塞项：0

## 复审范围

Stage 2：CNY 基准与汇率规则。

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S2-P1-T1` | 首页、投资、消费、现金流、报告主显示均为 CNY。 | 已修复并通过 |
| `S2-P1-T2` | 保留原币辅助显示，例如 `¥2,405.00 / 约 500.00 AUD / AUD/CNY=4.81`。 | 通过 |
| `S2-P1-T3` | 金额字段必须具备原始金额、原始币种、CNY 金额和汇率快照 ID。 | 已修复并通过 |
| `S2-P2-T1` | 06:00 有效日规则：03:00 使用昨日，06:00 后使用当日。 | 通过 |
| `S2-P2-T2` | 普通运行不得默认联网抓汇率。 | 通过 |
| `S2-P2-T3` | 汇率快照必须包含来源、读取时间、币种对和 hash。 | 通过 |

## 发现与修复

修复 1：补齐 `currency.base_currency` 的现金流影响面。

- 问题：`PFI/config/pfi_parameters.yaml` 的 `currency.base_currency.impact_surfaces` 已覆盖首页、投资、消费、报告，但漏掉 Stage 2 明确要求的 `现金流`。
- 风险：现金流页面可能被误判为不属于 CNY 主显示验收面。
- 修复：将 `现金流` 加入 `currency.base_currency.impact_surfaces`。
- 验收：`tests/test_v022_review_stage2.py` 直接读取参数文件并断言首页、投资、消费、现金流、报告全部在影响面内。

修复 2：账本金额字段增加中文标签映射。

- 问题：`ledger_amount_fields()` 已返回 `original_amount`、`original_currency`、`amount_cny`、`fx_snapshot_id`，但缺少与用户验收语言一致的中文字段标签。
- 风险：机器字段可用但三基文件和用户验收难以确认 `原始金额`、`原始币种`、`CNY金额`、`汇率快照ID` 的对应关系。
- 修复：新增 `FX_LEDGER_AMOUNT_FIELD_LABELS_ZH`，并在 `ledger_amount_fields()` 与 Stage 2 合同的 `ledger_amount_schema` 中返回 `field_labels_zh`。
- 验收：`tests/test_v022_review_stage2.py` 断言机器字段保持不变，并断言中文标签映射完整。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 任一核心板块仍以 AUD 为主显示时停止 | 未触发；`currency.base_currency` 影响面已包含首页、投资、消费、现金流、报告。 |
| 原币丢失或汇率不显示时停止 | 未触发；`amount_display_label()` 保留 CNY 主金额、原币金额和 `AUD/CNY` 汇率。 |
| 金额无法追溯汇率时停止 | 未触发；账本字段保留 `fx_snapshot_id`，并新增中文标签映射。 |
| 03:00 错用当天汇率时停止 | 未触发；`effective_fx_date()` 对 03:00 返回前一日。 |
| 每次运行触发网络抓取时停止 | 未触发；普通读取只读本地快照，显式刷新必须 `--allow-network`。 |
| 汇率无快照或无法追溯时停止 | 未触发；当前快照含来源、读取时间、pair 和 hash。 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| 参数源 | `PFI/config/pfi_parameters.yaml` |
| 汇率与账本字段模块 | `PFI/src/pfi_v02/stage_v022_fx.py` |
| Stage 2 合同 | `PFI/src/pfi_v02/stage_v022_database_governance.py` |
| 真实汇率快照 | `PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json` |
| 原 Stage 2 合同测试 | `PFI/tests/test_v022_fx_effective_date.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage2.py` |
| Stage 2 验收报告 | `PFI/docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_review_stage2.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_fx_effective_date.py tests/test_pfi_parameters_consistency.py tests/test_v022_stage0_database_governance.py tests/test_v022_stage13_post_review.py tests/test_v022_review_stage1.py tests/test_v022_review_stage2.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pfi_v02.stage_v022_fx read
node --check web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

本机验证结果：

- Stage 2 复审目标测试：`4 passed`。
- Stage 2 相关回归：`37 passed, 35 subtests passed`。
- 完整 PFI 测试：`262 passed, 225 subtests passed`。
- 本地汇率快照读取：读取 `fx_AUD_CNY_20260628`，`rate=4.6874`，`ordinary_runtime_network_refresh=false`。
- Web Shell 语法：`node --check web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- `git diff --check -- PFI`：通过。
- macOS app 轻量验收：`Blocked, pass=22, fail=7, info=2`；失败均来自 `/Users/linzezhang/Desktop/PFI.app` 不存在，`/Applications/PFI.app` 和 `~/Downloads/PFI.app` 均绑定 canonical PFI，8501 健康运行。按当前 goal 约束，app 入口重装留到整体复审解决完成后执行。

## 剩余风险

- 本轮只证明 Stage 2 的 CNY/Fx 治理复审问题已解决；Stage 3-13 的复审解决仍未在本 run 中执行。
- 本轮不重装 app 入口；按当前 pursuing goal 约束，整体项目复审解决完成后再刷新 app 入口。
- `PFI/.venv/bin/python` 当前不存在，本轮使用系统 `python3` 完成验证；后续刷新 app 入口时建议同时恢复项目虚拟环境或固定 `PFI_PYTHON`。
