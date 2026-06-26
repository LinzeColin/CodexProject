# PFI V0.2 Stage 0 Compatibility Audit

更新时间：2026-06-27 Australia/Sydney

## Single Acceptance Target

Stage 0 只关闭“兼容审计与边界锁定”：确认本地 PFI 真实入口、现有一级入口、owner entry、active runtime、测试命令和 v0.2 目标 8 入口映射，并用合同测试防止后续 Stage 删除旧入口、引入排除项或移动 active runtime。

本阶段不把 Web Shell 从当前 6 入口改成 8 入口；8 入口是 v0.2 目标态，当前 6 入口是兼容壳，Stage 1 后再做可点击 IA 迁移。

## Read-Only Audit Summary

| 项 | 结论 |
| --- | --- |
| Current local PFI project root | `CodexProject/PFI_OS` |
| Repository root evidence | 当前 checkout 的仓库根有 `AGENTS.md`、`README.md` 和 `governance/projects.yaml`；`PFI_OS/` 已登记为 PFI 路径，changed-scope check 已写入根治理。 |
| PFI current entry files | `PFI_OS/AGENTS.md`、`README.md`、`HANDOFF.md`、`功能清单`、`开发记录`、`模型参数文件` 存在。 |
| Public assumption mismatch | TaskPack 公开假设中的 `PFI/大数据模拟器` 与 `qbvs/` 在当前本地 checkout 不存在；本地等价能力在 `PFI_OS` 的策略实验室、模拟实验、回测、盘感训练和 `src/pfi_os` runtime 中。 |
| Current UI/routes | 当前 PFI 有 Web Shell、Streamlit launcher、同屏中文功能面板和 legacy query 兼容入口，不是 CLI-only/docs-only。 |
| Local PFI OS / ledger system | 已存在：`src/pfi_os/application/operational_store.py`、业务/消费/策略/报告/数据模块、合同测试和 Web Shell。 |
| Active runtime paths not to move | `src/pfi_os/`、`web/`、`scripts/`、`tests/`、`$PFI_OS_DATA_HOME/private/operational/pfi.sqlite`。 |

## Existing Owner-Facing Entries

当前 Web Shell 一级入口仍保持 6 个兼容入口：

1. 首页
2. 市场
3. 研究
4. 持仓
5. 策略实验室
6. 数据与系统

当前 Streamlit owner-facing views：

| Current view | v0.2 target location | Compatibility action |
| --- | --- | --- |
| 首页｜总控驾驶舱 | 首页总览 | 保留当前入口；迁移为首页总览默认视图。 |
| 市场｜热点分析 | 投资管理 > 市场观察 | 保留当前入口；作为投资管理市场观察视图。 |
| 市场｜情绪分析 | 投资管理 > 市场观察 | 保留当前入口；作为市场情绪视图。 |
| 研究｜政策雷达 | 报告与洞察 > 政策证据 | 保留当前入口；作为证据和报告能力。 |
| 研究｜报告中心 | 报告与洞察 | 保留当前入口；作为报告与洞察主视图。 |
| 持仓｜持仓复核 | 投资管理 > 持仓复核 | 保留当前入口；只读复核，不自动下单。 |
| 持仓｜个人画像 | 建议与复盘 > 行为画像 | 保留当前入口；作为复盘输入。 |
| 策略实验室｜单标的回测 | 投资管理 > 策略实验室 / 回测 | 保留当前入口；策略回测保持核心化。 |
| 策略实验室｜参数扫描 | 投资管理 > 策略实验室 / 参数扫描 | 保留当前入口；作为策略实验室视图。 |
| 策略实验室｜盘感训练 | 投资管理 > 策略实验室 / 盘感训练 | 保留当前入口；隐藏未来答案并只做训练。 |
| 策略实验室｜策略库 | 投资管理 > 策略实验室 / 策略库 | 保留当前入口；策略注册保持人工复核。 |
| 数据与系统｜模拟实验 | 投资管理 > 策略实验室 / 大数据模拟器 | 保留当前入口；大数据模拟器归入策略实验室。 |
| 数据与系统｜数据中心 | 数据源与同步 | 保留当前入口；作为数据源与同步兼容入口。 |

## V0.2 Target IA

v0.2 目标一级入口固定为 8 个：

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与同步
7. 建议与复盘
8. 报告与洞察

## Compatibility Matrix

| Existing local/public entry | Keep accessible | New PFI V0.2 location | Compatibility action |
| --- | ---: | --- | --- |
| 首页 | Yes | 首页总览 | 当前 Web Shell 按钮保留；Stage 1 后作为别名或跳转。 |
| 市场 | Yes | 投资管理 > 市场观察 | 当前 Web Shell 按钮保留；归入投资管理下的市场观察能力。 |
| 研究 | Yes | 报告与洞察 | 当前 Web Shell 按钮保留；研究证据和报告清单归入报告与洞察。 |
| 持仓 | Yes | 账户与资产 / 投资管理 | 当前 Web Shell 按钮保留；账户事实归入账户与资产，投资复核归入投资管理。 |
| 策略实验室 | Yes | 投资管理 > 策略实验室 | 当前 Web Shell 按钮保留；作为投资管理下的核心兼容入口。 |
| 数据与系统 | Yes | 数据源与同步 | 当前 Web Shell 按钮保留；系统诊断只作为内部状态，不作为产品一级入口。 |
| PFI/大数据模拟器 | Yes | 投资管理 > 策略实验室 / 大数据模拟器 | 公开假设路径若在其他 checkout 存在必须保留；当前本地用 PFI_OS 模拟实验兼容。 |
| qbvs/ active runtime | Yes | 投资管理 > 策略实验室 / 大数据模拟器 | 当前本地未发现该目录；若在其他 checkout 存在，禁止移动、改名或宽重构。 |
| 功能清单 | Yes | Owner entry / current + v0.2 summary | 保留为 owner 可读入口，补充 v0.2 Stage 0 状态。 |
| 开发记录 | Yes | Development record | 保留为开发记录，写入 Stage 0 交付与验证命令。 |
| 模型参数文件 | Yes | Model/parameter owner entry | 保留当前回测/盘感参数，并增加 v0.2 IA 和边界参数。 |

## Boundary Lock

| Boundary | Stage 0 decision |
| --- | --- |
| Alpha as PFI product L1 | Not allowed. Alpha remains independent and can only consume PFI context read-only in later stages. |
| R-prefixed Alpha variant | Not part of product, docs, schema, tests, or routes. |
| system/development product L1 | Not allowed as PFI product navigation; diagnostics can remain internal under data/source/status areas. |
| Excluded external payment project | Not read, migrated, reused, or depended on for this Stage 0 run. |
| Real trading | No automatic real-money order submission, no broker-order execution, no trading password. |
| Owner data | Non-trading credentials and owner-provided personal financial data can be used only under local/private data boundaries in later implementation stages. |

## Test Availability Report

Existing usable commands:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' .venv/bin/python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/contract/test_pfi005_gate2_shell_acceptance.py tests/contract/test_pfi012_mvp_release_gate.py -q
scripts/devReadyCheck.sh --summary-json
```

Stage 0 focused command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' .venv/bin/python -m pytest tests/contract/test_pfi_v02_stage0_compatibility.py tests/test_pfi_product_contracts.py -q
```

Observed validation on 2026-06-27:

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' .venv/bin/python -m pytest tests/contract/test_pfi_v02_stage0_compatibility.py tests/test_pfi_product_contracts.py -q` | `17 passed` |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' .venv/bin/python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/contract/test_pfi005_gate2_shell_acceptance.py tests/contract/test_pfi012_mvp_release_gate.py -q` | `25 passed`, 2 deprecation warnings |
| `scripts/devReadyCheck.sh --summary-json` | `status=Pass`, pass 40, fail 0, info 1 |
| `scripts/secretScan.sh` | Pass |
| `git diff --check` | Pass, no output |
| Excluded-literal grep scoped to Stage 0 and root governance touched files | Pass, no output |

## Proposed / Modified Files

| File | Purpose |
| --- | --- |
| `src/pfi_os/ui_contracts/pfi_v02_stage0.py` | Machine-readable Stage 0 target IA and compatibility contract. |
| `docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md` | Read-only audit, compatibility matrix, boundaries, stop review and validation commands. |
| `tests/contract/test_pfi_v02_stage0_compatibility.py` | Contract tests for Stage 0 acceptance criteria. |
| `docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md` | Reframe old 6 workspaces as compatibility shell and v0.2 8 entries as target IA. |
| `README.md`、`PLANS.md`、`功能清单`、`开发记录`、`模型参数文件`、`HANDOFF.md` | Owner-facing status and next-step records. |
| Repository root `AGENTS.md`、`README.md`、`governance/projects.yaml` | Root governance, PFI registration path and changed-scope check required by Stage 0A. |

## Stop Condition Review

| Stop condition | Result |
| --- | --- |
| Local structure unclear | Not triggered; local root is `PFI_OS`. |
| Requires moving active runtime | Not triggered; runtime paths are not moved. |
| Cannot preserve aliases | Not triggered; all current entries are mapped. |
| Modify external independent repo | Not triggered. |
| Add excluded variant/module | Not triggered. |
| Read or depend on excluded external payment project | Not triggered. |
| Require trading password | Not triggered. |
| Automatic real-money trade | Not triggered. |
| Existing smoke unavailable | Not triggered; focused tests are available and runnable. |
| No single acceptance target | Not triggered; acceptance target is this Stage 0 contract. |

## Rollback Plan

1. Remove `docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md`.
2. Remove `src/pfi_os/ui_contracts/pfi_v02_stage0.py`.
3. Remove `tests/contract/test_pfi_v02_stage0_compatibility.py`.
4. Revert owner-entry updates in `README.md`、`PLANS.md`、`功能清单`、`开发记录`、`模型参数文件`、`HANDOFF.md` and the IA addendum.

## Acceptance Criteria Closure

| Phase | Status | Evidence |
| --- | --- | --- |
| Phase 0A | Closed by contract | Current root, PFI entry files, active runtime paths and test commands are recorded above. |
| Phase 0B | Closed by contract | Every current first-level entry and owner-facing view maps to a v0.2 target location. |
| Phase 0C | Closed by contract | Excluded boundaries are locked, and target IA has no excluded product L1. |
