# PFI V0.2 Stage 1-5 交付验收审计

日期：2026-06-27 Australia/Sydney

## 目标

本审计用于证明 Stage 1 到 Stage 5 的 phase、task、acceptance criteria、stop condition 和 validation 当前都有可追溯证据。范围只覆盖本地只读 PFI V0.2，不声明生产联通、实盘交易、支付提交、券商下单或 Alpha 仓库修改。

## 权威口径

| 项 | 当前口径 |
| --- | --- |
| PFI 根目录 | `CodexProject/PFI` |
| QBVS | 顶层独立系统 `CodexProject/QBVS`；PFI 不拥有、不覆盖 QBVS |
| PFI 投资管理 | 保留 PFI 自身策略回测、参数扫描、盘感训练和大数据模拟器 |
| MetaDatabase | 顶层数据归档项目 `CodexProject/MetaDatabase`；保存用户授权原始数据和 manifest |
| Alpha | 独立系统；PFI 只输出只读 `pfi_context_snapshot_v1` |
| 禁止动作 | 无交易密码、无自动实盘下单、无支付提交、无券商订单提交 |

## Stage 总览

| Stage | Pursuing Goal | 当前状态 | 核心证据 |
| --- | --- | --- | --- |
| Stage 1 | 信息架构与核心模型 | PASS | `stage1_ia.py`, `core_models.py`, `classification_rules.py`, Stage 1 tests |
| Stage 2 | 数据源与低操作同步 MVP | PASS | `stage2_registry.py`, `stage2_import.py`, `stage2_contracts.py`, Stage 2 tests |
| Stage 3 | 首页、账户、账本可读 MVP | PASS | `stage3_read_mvp.py`, Web Shell, Stage 3 tests |
| Stage 4 | 投资与消费智能分析 MVP | PASS | `stage4_analysis_mvp.py`, Web Shell, Stage 4 tests |
| Stage 5 | 建议、报告、Alpha 只读出口 | PASS | `stage5_advice_report_alpha.py`, Web Shell, Stage 5 tests |

## Phase / Task 验收矩阵

| Stage | Phase | Roadmap Acceptance | 当前证据 | Stop Condition 状态 |
| --- | --- | --- | --- | --- |
| 1 | 1A 8 个一级入口 Contract | 首页、账户、账本、投资、消费、同步、建议、报告 8 个一级入口 | `PFI/web/index.html` 8 个 `data-primary-entry=true`；Chrome 点击 8/8 | PASS：无 Alpha/Ralpha/System/Development 一级入口 |
| 1 | 1B 核心对象模型 | DataSource、Account、Asset、ImportBatch、RawRecord、LedgerEvent、Snapshot 可表达 | `tests.test_stage1_core_models` | PASS：数据源、账户、资产不混用 |
| 1 | 1C 分类规则 | 转账、基金、贵金属、信用卡还款不误算消费 | `tests.test_stage1_classification_rules` | PASS：投资买入、基金申购、还款不进入生活消费 |
| 2 | 2A DataSource Registry | 核心数据源齐全、acquisition mode、plugin 扩展 | `tests.test_stage2_data_source_registry` | PASS：非 CSV 和扩展 contract 存在 |
| 2 | 2B CBA CSV P0 | parser、watch folder、dedupe、transfer matching | `tests.test_stage2_cba_csv_import` | PASS：转账/入金/还款不计普通消费 |
| 2 | 2C 支付宝日常账单 P0 | CSV/ZIP parser、基金识别、低置信度复核 | `tests.test_stage2_alipay_import` | PASS：低置信度进入 review queue |
| 2 | 2D 支付宝基金 Non-CSV | 交易线、持仓线、净值线、三角校验 | `tests.test_stage2_non_csv_contracts` | PASS：不假设基金 CSV，不把净值替代交易 |
| 2 | 2E Moomoo AU OpenD/API | read-only probe、账户/资金/持仓/订单/成交 contract | `tests.test_stage2_non_csv_contracts` | PASS：无交易密码、无自动下单；QBVS 只作为外部独立引用 |
| 2 | 2F 中国大陆券商 Non-CSV | QMT/PTrade/HTML/PDF/Excel/terminal/manual snapshot profile | `tests.test_stage2_non_csv_contracts` | PASS：不写死单一券商或 CSV |
| 2 | 2G ABC Bullion Non-CSV | 页面/statement/PDF/HTML/browser-assisted/snapshot、贵金属事件、三角校验 | `tests.test_stage2_non_csv_contracts` | PASS：贵金属买卖为投资事件 |
| 2 | 2H 微信 Contract | ZIP/CSV/XLS/XLSX、支付/转账/红包/退款规则 | `tests.test_stage2_non_csv_contracts` | PASS：微信转账不全算消费 |
| 3 | 3A 首页总览 MVP | 财务状态、账户地图、投资/消费/现金流快照、今日建议 | `tests.test_stage3_readable_mvp`；Web Shell 首页 | PASS：首页不依赖真实账户才能运行 |
| 3 | 3B 账户与资产 MVP | 全部账户、跨币种、账户对账 | `tests.test_stage3_readable_mvp` | PASS：账户与数据源不混用，差异可见 |
| 3 | 3C 账本流水 MVP | 全部流水、待分类、转账匹配、原始证据链 | `tests.test_stage3_readable_mvp` | PASS：unknown 不静默入账 |
| 3 | 3D 低操作 UX | 同步全部、A/B/C/D 待复核、简单状态语言 | `tests.test_stage3_readable_mvp`；Web Shell 中文入口 | PASS：技术状态不作为首页主语言 |
| 4 | 4A 投资分析 | 总览、归因、风险、行为复盘、策略实验室保留 | `tests.test_stage4_analysis_mvp`；Web Shell 投资管理 | PASS：数据不足时显示 estimate/复核，不输出精确结论 |
| 4 | 4B 消费分析 | 总览、分类、订阅、异常、现金流预测 | `tests.test_stage4_analysis_mvp` | PASS：生活现金和投资现金分离，转账不计消费 |
| 5 | 5A 建议与复盘 | Recommendation model、review lifecycle、投资/消费建议、Top N | `tests.test_stage5_advice_report_alpha` | PASS：建议有证据、动作、tradeoff 和 owner decision |
| 5 | 5B 报告与洞察 | 月度、投资、消费、数据质量报告，导出中心 | `tests.test_stage5_advice_report_alpha` | PASS：报告带证据链和 reproducibility key |
| 5 | 5C Alpha 只读出口 | `pfi_context_snapshot_v1`、只读字段、Alpha 独立说明、约束字段 | `tests.test_stage5_advice_report_alpha` | PASS：不修改 Alpha，不新增 Alpha 一级入口，不授权实盘 |

## 入口和 UI 验证

Chrome headless 使用本机 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` 验证：

| 项 | 结果 |
| --- | --- |
| V0.2 一级入口数量 | 8 |
| V0.1 兼容入口数量 | 6 |
| 点击验证 | 14/14 成功 |
| console errors | 0 |
| 策略实验室证据标签 | `PFI 策略实验室` |
| 旧 QBVS-as-PFI 标签 | 未出现 |
| 截图 | `/tmp/pfi-stage1-5-webshell-verified.png` |

## 根治理修复

本轮 Stage 1-5 验收发现并修复两个治理阻塞：

1. `QBVS` 和 `MetaDatabase` 已是顶层目录但未登记，导致 `validate_project_governance.py --project PFI` 在 root 阶段失败。
2. `tests/governance/test_human_entry_markdown_contract.py` 仍查找旧 `PFI/modules/qbvs_lab`，与当前顶层独立 QBVS 事实冲突。

当前修复：

- `governance/projects.yaml` 登记 `QBVS` 和 `MetaDatabase`。
- 根 `README.md` 项目表加入 `QBVS` 和 `MetaDatabase`。
- `MetaDatabase` 补齐三基文件和最小 Lean v2 治理文件。
- human-entry 合同测试改为检查顶层 `QBVS`。

## 当前验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp tests.test_stage5_advice_report_alpha -q
```

结果：`Ran 89 tests / OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
```

结果：`Ran 1 test / OK`。

```bash
python3 scripts/validate_project_governance.py --project PFI
python3 scripts/validate_project_governance.py --project QBVS
python3 scripts/validate_project_governance.py --project MetaDatabase
python3 -B -m unittest tests.governance.test_human_entry_markdown_contract -q
node --check PFI/web/app/shell.js
```

结果：PFI/QBVS/MetaDatabase governance 均 `errors: 0 / warnings: 0`；human-entry contract `Ran 2 tests / OK`；Web shell syntax `OK`。

## 仍未完成

| 项 | 状态 | 原因 |
| --- | --- | --- |
| 合并到 `main` | 未完成 | 当前仍在 `codex/pfi-stage6-meta-qbvs-sync` 分支；需要单独 merge/push 才会出现在 GitHub 默认分支 |
| 真实账户生产联通 | 未完成 | Stage 1-5 明确非范围 |
| PDF/ZIP 正式交付包 | 未完成 | 后续独立 gate |
| Alpha 独立消费 PFI context | 未完成 | Stage 5 只定义 PFI 只读出口，不改 Alpha 仓库 |

## 停止条件结论

Stage 1-5 的本地只读 MVP、入口兼容、核心合同、数据源合同、可读 UI、投资/消费分析、建议/报告/Alpha 只读出口和安全边界均有当前验证证据。剩余项属于后续 release/production/merge gate，不阻止 Stage 1-5 本地验收通过。
