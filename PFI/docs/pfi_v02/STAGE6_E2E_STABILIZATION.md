# PFI V0.2 Stage 6 E2E Stabilization

更新时间：2026-06-27

## 目标

Stage 6 将 PFI V0.2 从“本地 MVP 功能已建立”推进到“可运行、可验证、可回滚、可继续迭代”。本阶段只使用 synthetic/read-only 合同与 fixture，不接真实账户、不读取交易密码、不提交支付或券商订单。

## 最小范围

- `src/pfi_v02/stage6_e2e_stabilization.py`
- `tests/test_stage6_e2e_stabilization.py`
- `src/pfi_os/application/homepage_summary.py`
- `web/index.html`
- `web/app/shell.js`
- `PFI` owner 三基文件和 `docs/governance`
- `QBVS/` 顶层独立系统引用
- `MetaDatabase/` 原始数据备份

QBVS 已独立为 `CodexProject/QBVS` 顶层系统；PFI 不覆盖 QBVS，不修改外部 Alpha repo，不新增 Alpha/Ralpha/System/Development 产品一级入口。

## Phase 6A：Synthetic E2E Scenario

| Task | Acceptance Criteria | Stop Condition | Validation | Evidence |
| --- | --- | --- | --- | --- |
| S6PAT01 多数据源合成样例 | 支付宝、支付宝基金、Moomoo AU、中国大陆券商、ABC Bullion、CBA、微信均有 fixture 或 contract | 任一核心源缺失 | Stage 6 focused contract test | `source_fixture_matrix` |
| S6PAT02 首页闭环 | 首页展示账户、投资、消费、数据健康、建议 | 首页不可读或无结果 | Homepage snapshot contract | `homepage_loop` |
| S6PAT03 账本闭环 | 转账、投资买入、消费、退款、费用、估值、基金赎回、贵金属买入、信用卡还款分类正确 | 分类错误或无 raw/parser trace | Ledger E2E contract | `ledger_loop` |
| S6PAT04 建议闭环 | 建议生成、Top N 展示、accept/reject/snooze/review/effect measurement 可复盘 | 无证据建议进入队列 | Recommendation E2E contract | `recommendation_loop` |

## Phase 6B：Regression / Governance

| Task | Acceptance Criteria | Stop Condition | Validation | Evidence |
| --- | --- | --- | --- | --- |
| S6PBT01 Existing smoke | 顶层 QBVS lifecycle smoke 继续通过 | 外部策略验证系统破坏 | `tests.test_s3pct02_lifecycle` | `phase_6b.existing_smoke` |
| S6PBT02 New focused tests | Stage 6 focused tests 通过 | 新合同不可运行 | `tests.test_stage6_e2e_stabilization` | `phase_6b.new_focused_tests` |
| S6PBT03 Changed-scope governance | governed files changed 时跑 changed-only governance | governance 失败 | `scripts/lean_governance.py ci --changed-only --base-ref origin/main` | `phase_6b.changed_scope_governance` |
| S6PBT04 No broad refactor | diff 只在 PFI Stage 6 选定范围内 | 宽重构、目录迁移、runtime 移动 | diff review + tests | `phase_6b.no_broad_refactor` |

## Phase 6C：Delivery / Rollback

| Task | Acceptance Criteria | Stop Condition | Validation | Evidence |
| --- | --- | --- | --- | --- |
| S6PCT01 Owner docs | 首页、同步、复核、建议、报告、回滚和后续任务 owner 可读 | 三基缺失或过期 | Governance validation | 三基文件 |
| S6PCT02 Diff summary | 改动能对应代码、测试、文档、Web、治理 | 无法复审变更 | Stage 6 record | `phase_6c.diff_summary` |
| S6PCT03 Rollback plan | 至少 6 步可回滚，不涉及私有数据迁移 | 无回滚路径 | Stage 6 focused test | `phase_6c.rollback_plan` |
| S6PCT04 Follow-up list | Alpha consumer、真实数据、PDF/ZIP、CDR/Open Banking、发布证据独立排期 | 后续任务混入 Stage 6 | Stage 6 focused test | `phase_6c.follow_up_list` |

## 20 Gate Audit

`build_stage6_e2e_stabilization_model().total_acceptance_gate` 固化 20 个 Gate，覆盖：

- PFI 现有入口未删除，V0.2 IA 优先。
- QBVS 独立于 PFI 投资管理；PFI 只保留自身策略回测、盘感训练和大数据模拟器。
- V0.1 六入口：首页、市场、研究、持仓、策略实验室、数据与系统继续可访问。
- 七个核心数据源覆盖；支付宝基金、中国大陆券商、ABC Bullion 不假设 CSV。
- CBA CSV P0 仍稳定。
- 非交易凭证/个人数据只读，交易密码排除。
- 不新增 Ralpha/Alpha/System/Development 一级入口。
- 转账、投资买入、基金申购/赎回、ABC 贵金属买卖、信用卡还款分类正确。
- 首页可读、建议有证据和复盘、报告和 Context Export 有 schema/fixture/test。
- Existing smoke + focused tests + rollback gate 可验证。

## ACC-* Audit

`taskpack_acceptance_audit` 覆盖 `ACC-COMPAT-*`、`ACC-IA-*`、`ACC-DS-*`、`ACC-LEDGER-*`、`ACC-UX-*`、`ACC-REC-*`、`ACC-ALPHA-*`。所有 acceptance 都必须为 `PASS`，否则 Stage 6 不得 closeout。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage6_e2e_stabilization -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp tests.test_stage5_advice_report_alpha tests.test_stage6_e2e_stabilization -q
(cd ../QBVS && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q)
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
python3 -B -m unittest ../tests.governance.test_human_entry_markdown_contract -q
python3 ../scripts/lean_governance.py ci --changed-only --base-ref origin/main
```

当前 closeout 验证结果：

- Stage 1-6 contracts：`Ran 95 tests / OK`
- Stage 6 focused contract：`Ran 10 tests / OK`
- QBVS lifecycle smoke：`Ran 1 test / OK`
- Project governance validation：`errors 0 / warnings 0`
- Human-entry Markdown contract：`Ran 2 tests / OK`
- Python compile：`OK`
- Web shell syntax：`OK`
- macOS app acceptance lite：`29 pass / 0 fail / 2 info`
- Browser validation：Stage 6 六个功能按钮可打开，8 个一级入口可切换，console error `0`，截图 `/tmp/pfi-stage6-browser-verified.png`
- `git diff --check -- PFI`：`OK`
- `lean_governance.py ci --changed-only --base-ref origin/main`：在 GitHub clean clone 中 `decision=SHIP`，`changed_file_count=28`，`selected_project_count=1`，`validation_checked_project_count=1`

当前 active checkout 仍有 EEI/ADP/Alpha 等非 PFI 脏变更；最终提交使用 GitHub clean clone / PFI-only diff，避免跨项目状态污染。

## 回滚计划

1. Revert `src/pfi_v02/stage6_e2e_stabilization.py`。
2. Revert `tests/test_stage6_e2e_stabilization.py`。
3. Revert `docs/pfi_v02/STAGE6_E2E_STABILIZATION.md`。
4. Revert `homepage_summary.py` 的 Stage 6 payload 和 evidence drawer。
5. Revert `web/index.html`、`web/app/shell.js` 的 Stage 6 Web 接入。
6. Revert owner 三基和 `docs/governance` 的 Stage 6 记录。
7. 若需回滚 QBVS 顶层独立，必须单独 revert 本次分离提交，不能在 PFI 内重新嵌入 QBVS。
8. 不需要生产数据库、私有账本或真实凭证迁移回滚。

## 后续任务

- 外部 Alpha 仓库实现只读 context consumer。
- 真实账户数据接入需单独 owner gate。
- PDF/ZIP 交付包需单独 task。
- CDR/Open Banking 集成需单独 task。
- Production release evidence gate 需真实运行证据后再开。
