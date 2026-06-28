# PFI v0.2.2 Stage 2 CNY 与汇率治理验收报告

日期：2026-06-28 Australia/Sydney

阶段：`Stage 2 - CNY 基准与汇率规则`

本轮目标：把 PFI 当前口径推进为 CNY 主显示，并建立真实、可追溯、默认离线的 `AUD/CNY` 汇率快照读取规则。UIUX 仍以 v0.2.1 HTML Web Shell 为基线，本轮只更新必要汇率徽标与金额主口径。

## 交付摘要

| 项 | 当前值 |
| --- | --- |
| 主货币 | `CNY` |
| 当前汇率对 | `AUD/CNY` |
| 当前徽标示例 | `AUD/CNY=4.69（20260628--06:00）` |
| 快照含义 | `1 AUD = 4.6874 CNY` |
| 快照 ID | `fx_AUD_CNY_20260628` |
| 快照文件 | `PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json` |
| 来源 | `Frankfurter v2 public API` |
| 来源 URL | `https://api.frankfurter.dev/v2/rate/AUD/CNY?date=2026-06-28` |
| 本地读取模块 | `PFI/src/pfi_v02/stage_v022_fx.py` |
| 合同测试 | `PFI/tests/test_v022_fx_effective_date.py` |
| 快照 hash | `2e0d770f16f07543bfe03f9189f1be923b2ef4518a346c79788655600040018b` |

## Phase 2.1 CNY 主显示

| Task ID | 要求 | 当前实现 | 验收状态 |
| --- | --- | --- | --- |
| `S2-P1-T1` | 首页、投资、消费、现金流、报告主显示 CNY | `PFI/web/index.html` 初始主金额使用 `CNY`；`PFI/web/app/shell.js` 用 `FX_TO_CNY` 和 `rateAudToCny=4.6874` 把动态 AUD 摘要、建议节省目标和持仓汇总折成 CNY 后显示。 | 通过 |
| `S2-P1-T2` | 保留原币辅助显示 | `amount_display_label()` 输出 `CNY ... / 原币 AUD ... / AUD/CNY=...`；Web Shell 文案提示“原币辅助显示”。 | 通过 |
| `S2-P1-T3` | 账本金额字段 | `ledger_amount_fields()` 输出 `原始金额`、`原始币种`、`CNY金额`、`汇率快照ID`。 | 通过 |

## Phase 2.2 每日汇率快照

| Task ID | 要求 | 当前实现 | 验收状态 |
| --- | --- | --- | --- |
| `S2-P2-T1` | 06:00 有效日规则 | `effective_fx_date()`：Sydney 时间 06:00 前用前一日，06:00 及之后用当天。 | 通过 |
| `S2-P2-T2` | 普通运行不默认联网 | `refresh_daily_fx_snapshot()` 默认 `allow_network=False` 会拒绝联网；`read_effective_fx_snapshot()` 只读本地文件。 | 通过 |
| `S2-P2-T3` | 快照目录、来源、读取时间、pair、hash | `data/fx_snapshots/AUD_CNY/2026-06-28.json` 包含 `source_provider`、`source_url`、`fetched_at`、`pair_base`、`pair_quote`、`hash`。 | 通过 |

## 有效日规则

```text
timezone = Australia/Sydney
cutoff = 06:00

本地时间 < 06:00  => 使用前一自然日快照
本地时间 >= 06:00 => 使用当天快照
```

测试覆盖：

- `2026-06-28 03:00 Australia/Sydney` -> `2026-06-27`
- `2026-06-28 06:00 Australia/Sydney` -> `2026-06-28`
- `2026-06-28 08:00 Australia/Sydney` -> `2026-06-28`

## 真实快照读取

显式刷新命令：

```bash
PYTHONPATH=PFI/src python3 -B -m pfi_v02.stage_v022_fx refresh --allow-network
```

本地普通读取命令：

```bash
PYTHONPATH=PFI/src python3 -B -m pfi_v02.stage_v022_fx read
```

本机 Python 的系统 CA 在联网读取时出现过 `SSLCertVerificationError`。实现保留 Python 标准库读取路径，并在显式 `--allow-network` 刷新时降级使用系统 `curl -fsSL` 获取同一 URL；快照内记录 `fetch_transport=system_curl_fallback_after_SSLCertVerificationError`。普通运行仍不联网，不触发该降级路径。

## 缺失快照状态

当有效快照不存在时，系统返回：

```text
汇率数据待更新
```

该状态用于前端/报告 gate。PFI 不允许：

- 编造实时汇率。
- 用旧快照冒充当天有效快照。
- 在普通本地运行中强制联网刷新。
- 将缺失快照的报告标记为正式可验收报告。

## 非目标

- 不实现 Stage 3 数据源、账户角色和 capabilities 结构。
- 不新增参数中心 HTML 页面。
- 不改写 v0.2.1 UIUX 主架构。
- 不连接真实银行、券商或支付平台。
- 不提交真实交易、自动投资、付款或券商下单。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_fx_effective_date -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m pfi_v02.stage_v022_fx read
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## 停止条件检查

| 停止条件 | 当前结果 |
| --- | --- |
| CNY 主显示仍被 AUD 主显示覆盖 | 未触发 |
| 原始金额、原始币种、CNY金额、汇率快照ID 任一字段缺失 | 未触发 |
| 普通运行默认联网抓汇率 | 未触发 |
| 快照缺少来源、读取时间、pair 或 hash | 未触发 |
| 06:00 有效日边界不可测试 | 未触发 |

结论：Stage 2 可进入 closeout 验证；下一轮应从 Stage 3 开始，不提前实现 Stage 4-13。
