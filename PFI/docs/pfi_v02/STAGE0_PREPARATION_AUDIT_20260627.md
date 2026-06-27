# PFI V0.2 Stage 0 准备审计

日期：2026-06-27 Australia/Sydney

## 本轮目标

本轮只做 Stage 0 准备、验收口径对齐和事实审计，不扩展新功能，不移动根目录，不清理其它项目，不修改 EEI、ADP、Alpha、Serenity。

## 权威输入

| 来源 | 当前结论 |
| --- | --- |
| 根 `AGENTS.md` | 必须使用 canonical checkout；GitHub 是验收事实源；三基文件必须中文可读；改动前要明确范围、验证和停止条件。 |
| 根 `README.md` | 当前 canonical root 是 `CodexProject`；PFI 已列为项目；QBVS 和 MetaDatabase 尚未登记为根项目。 |
| 根 `governance/projects.yaml` | PFI 已登记；QBVS 和 MetaDatabase 尚未登记。是否登记需要用户确认，因为登记后会触发 Lean v2 项目治理义务。 |
| `PFI/HANDOFF.md` | PFI 当前根为 `PFI/`；QBVS 已是顶层 `QBVS/`；MetaDatabase 是顶层用户原始数据归档。 |
| `PFI/功能清单.md` | 已中文说明 V0.2 八入口、V0.1 六入口、消费账户分类、PFI 投资管理边界、QBVS 独立边界。 |
| `PFI/开发记录.md` | 已记录 Stage 1-6 和 2026-06-27 两轮验收退回纠偏。 |
| `PFI/模型参数文件.md` | 已中文说明分类规则、阈值、人工复核条件和当前阈值依据。 |
| `/Users/linzezhang/Downloads/PFI_V0.2_Roadmap.md` | Stage 0 要求读取治理、确认旧入口兼容矩阵、锁定边界，并保证新八入口优先、旧入口保留。 |
| `/Users/linzezhang/Downloads/PFI_V0.2_修复Roadmap_含PursuingGoal和Prompt.md` | 修复模式要求不再扩功能，先修中文可读、入口可用、验证可复现。 |
| `/Users/linzezhang/Downloads/PFI_V0.2_Codex_TaskPack.md` | 当前本机 Downloads 未发现该文件；现有依据来自 Roadmap 和修复 Roadmap。 |

## Stage 0 验收矩阵

| Stage 0 项 | 验收要求 | 当前状态 | 证据 |
| --- | --- | --- | --- |
| 0A-1 根治理读取 | 确认仓库治理规则、PFI 路径、changed-scope 方法 | 已完成 | `AGENTS.md`、`README.md`、`governance/projects.yaml`；changed-scope 命令为 `python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main` |
| 0A-2 当前 PFI 结构报告 | 确认 PFI 根、Web Shell、Streamlit、三基、Stage 文档 | 已完成 | `PFI/HANDOFF.md`、`PFI/README.md`、`PFI/docs/pfi_v02/`、`PFI/web/`、`PFI/src/` |
| 0A-3 测试可用性报告 | 找到并运行最小验收测试 | 已完成 | Stage 1-6 focused contracts、QBVS smoke、Web shell syntax、浏览器点击验收已记录 |
| 0B-1 旧入口兼容矩阵 | 旧入口不能删除，必须映射到 V0.2 | 已完成 | Web Shell 保留 V0.1 六入口：`首页/市场/研究/持仓/策略实验室/数据与系统` |
| 0B-2 新入口优先 | V0.2 八入口优先显示 | 已完成 | Web Shell `data-primary-entry=true` 共 8 个 |
| 0B-3 旧功能保留 | 盘感训练、策略回测、大数据模拟器保留 | 已完成 | PFI 投资管理内保留策略实验室、盘感训练、参数扫描和大数据模拟器能力 |
| 0C-1 Alpha 边界 | PFI 不新增 Alpha 一级入口、不修改 Alpha | 已完成 | Stage 5 仅保留 read-only context export；本轮未改 Alpha |
| 0C-2 Ralpha 边界 | 不新增 Ralpha | 已完成 | 当前 PFI 入口不包含 Ralpha |
| 0C-3 System/Development 边界 | 不把系统/开发入口暴露为产品一级入口 | 已完成 | Web Shell V0.2 八入口和 V0.1 六入口均为用户产品入口 |
| 0C-4 Serenity-Alipay 排除 | 本轮不修改 Serenity-Alipay | 已完成 | 本轮 PFI 范围不包含 Serenity-Alipay；本地 runtime DB/WAL 不提交 |

## V0.1 到 V0.2 入口兼容矩阵

| V0.1 一级入口 | V0.2 归宿 | 当前处理 |
| --- | --- | --- |
| 首页 | 首页总览 | 保留为兼容入口，可点击跳转。 |
| 市场 | 投资管理 / 市场观察 | 保留为兼容入口，可点击跳转。 |
| 研究 | 报告与洞察 | 保留为兼容入口，可点击跳转。 |
| 持仓 | 账户与资产 / 投资管理 | 保留为兼容入口，可点击跳转。 |
| 策略实验室 | 投资管理 / 策略实验室 | 保留为兼容入口；PFI 自身策略回测、盘感训练、参数扫描、大数据模拟器在这里。 |
| 数据与系统 | 数据源与同步 | 保留为兼容入口，可点击跳转。 |

## QBVS 冲突和当前裁定

下载版 Roadmap 旧口径写过“现有 PFI/大数据模拟器 / QBVS 保留为：投资管理 > 策略实验室 / 大数据模拟器”。用户最新口径已明确改为：

> 投资管理不需要覆盖 QBVS，把 QBVS 从 PFI 独立出来，这是两个系统，GitHub 上也要独立出来。

当前执行以最新用户指令为准：

- QBVS 已从 `PFI/` 移出，成为 `CodexProject/QBVS` 顶层独立系统。
- PFI 不再拥有、覆盖或伪装 QBVS。
- PFI 仍保留自己的策略回测、盘感训练、参数扫描和大数据模拟器能力。
- 是否把 `QBVS` 写入根 `README.md` 项目表和 `governance/projects.yaml`，需要用户确认，因为这会让 QBVS 承担独立项目治理文件、CI 和三基文件要求。

## MetaDatabase 边界

当前按用户要求新增顶层 `MetaDatabase/`，用途是保存用户上传或已交接的原始数据及派生处理件。

当前已落地：

- `MetaDatabase/PFI/alipay_daily/raw/`：保存 4 份支付宝原始 CSV。
- `MetaDatabase/PFI/alipay_daily/processed/`：保存导入 manifest 和标准化流水。
- PFI 本地私有运行目录仍是 `~/.pfi/`；GitHub 可验收归档为 `MetaDatabase/`。

当前裁定：

- `MetaDatabase` 已登记为 CodexProject 顶层 Lean v2 数据归档项目。
- 当前已补三基文件、最小治理文件、manifest 和数据边界说明。
- 后续新增数据仍需要单独确认授权、manifest、校验和、数据字典和隐私分级。

## 当前 GitHub 同步事实

| 项 | 状态 |
| --- | --- |
| 分支 | `codex/pfi-stage6-meta-qbvs-sync` |
| 已推送 commit | `d0d0a4b8f50231e2c63293396a1fee8e03de7fda` |
| 分支用途 | PFI/QBVS/MetaDatabase Stage 6 纠偏和 Stage 0 准备验收 |
| GitHub 可见范围 | `PFI/`、`QBVS/`、`MetaDatabase/` 在该分支可见 |
| 未纳入本轮 | EEI、ADP、Alpha、Serenity 的本地脏文件和 runtime state |

## 已有验证证据

本轮 Stage 0 准备审计复验：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage2_alipay_import tests.test_stage6_e2e_stabilization -q
```

结果：`Ran 25 tests / OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
```

结果：`Ran 1 test / OK`。

```bash
node --check PFI/web/app/shell.js
git diff --check -- PFI QBVS MetaDatabase
```

结果：均通过。

前一轮 Stage 6 纠偏完整验收：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp tests.test_stage5_advice_report_alpha tests.test_stage6_e2e_stabilization -q
```

结果：`Ran 99 tests / OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
```

结果：`Ran 1 test / OK`。

```bash
node --check PFI/web/app/shell.js
git diff --check -- PFI QBVS MetaDatabase
```

结果：均通过。

浏览器验收：

- Web Shell：8 个 V0.2 一级入口、6 个 V0.1 兼容入口均可点击；截图 `/tmp/pfi-v01-v02-entry-verified.png`。
- Streamlit：上传面板、私有账本、MetaDatabase 提示、8815 条支付宝流水可见；截图 `/tmp/pfi-streamlit-metadb-verified.png`。

## 当前未确认项

1. 是否将 `codex/pfi-stage6-meta-qbvs-sync` 合并到 `main`，让 GitHub 默认分支直接显示 Stage 6 和 Stage 0/1-5 交付物。
2. 是否需要把下载版 Roadmap 旧口径同步修订为“QBVS 独立，不再映射进 PFI 投资管理”。

## Stage 0 停止条件状态

| 停止条件 | 状态 |
| --- | --- |
| 已读取 governance / PFI / Roadmap 权威文件 | 满足 |
| 已形成旧入口兼容矩阵 | 满足 |
| 已锁定 Alpha/Ralpha/System/Serenity 边界 | 满足 |
| 已记录 QBVS 新旧口径冲突 | 满足 |
| 已确认 PFI 保留盘感训练、策略回测、大数据模拟器 | 满足 |
| 已确认 MetaDatabase 当前数据边界 | 满足 |
| 已列出需要用户确认的治理登记问题 | 满足 |
