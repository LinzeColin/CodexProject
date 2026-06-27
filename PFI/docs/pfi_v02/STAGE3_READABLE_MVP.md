# PFI V0.2 Stage 3 Readable MVP

更新时间：2026-06-27 Australia/Sydney

## 目标

Stage 3 将 PFI 从“有数据合同”推进到“打开后能读懂并操作”的本地只读 MVP。Owner 在首页能看到财务状态、账户地图、账本流水、待复核、今日建议，并能进入四个主动作：

1. 同步全部
2. 处理待复核
3. 查看建议
4. 生成报告

## 范围

- 新增本地 read-model：`src/pfi_v02/stage3_read_mvp.py`。
- 新增合同测试：`tests/test_stage3_readable_mvp.py`。
- Web shell 默认首页接入 Stage 3 read-model。
- Web shell 一级入口显示 PFI V0.2 的 8 个目标入口。
- 保留 PFI 旧策略回测、盘感训练和大数据模拟器；QBVS 作为 `CodexProject/QBVS` 顶层独立系统验证，不作为 PFI 所属入口。

## 非范围

- 不接入真实凭证。
- 不执行真实同步、登录、支付或券商提交。
- 不读取或迁移其它项目数据。
- 不声明生产联通或实盘可用。

## Phase / Task 验收矩阵

| Task ID | Phase | 任务 | Acceptance Criteria | Stop Condition | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| S3PAT01 | 3A | 今日财务状态卡 | 净资产、现金、投资资产、本月支出、数据健康可展示 | 首页依赖真实账户才可运行 | synthetic summary test | `build_stage3_read_model()` |
| S3PAT02 | 3A | 账户地图 | 支付宝、基金、Moomoo、中国券商、ABC、CBA、微信状态可展示 | 缺核心账户 | account map test | `account_map` |
| S3PAT03 | 3A | 投资/消费/现金流快照 | 三类摘要可进入详情并带证据 | 摘要数据无来源 | summary trace test | `home.snapshots` |
| S3PAT04 | 3A | 今日建议 Top N | 建议有证据、动作、状态、效果、tradeoff | 首页建议无证据 | recommendation test | `recommendations` |
| S3PBT01 | 3B | 全部账户列表 | 支持投资、日常、现金、资产、负债账户 | 数据源和账户混用 | account test | `accounts` |
| S3PBT02 | 3B | 跨币种视图 | AUD/CNY/USD/HKD 可折算展示 | 币种混算 | FX fixture test | `fx_view` |
| S3PBT03 | 3B | 账户对账 | 平台余额 vs PFI 账本余额有状态 | 差异不可见 | reconciliation test | `reconciliation` |
| S3PCT01 | 3C | 全部流水 | 可查看 normalized transactions | 无法追溯来源 | ledger view test | `ledger` |
| S3PCT02 | 3C | 待分类流水 | 低置信度记录进入复核 | unknown 静默入账 | review test | `review_queue` |
| S3PCT03 | 3C | 转账匹配 | 转账可确认、拒绝、修改 | 转账进入消费统计 | transfer matching test | `transfer_match_decision()` |
| S3PCT04 | 3C | 原始证据链 | 每条流水可追溯 batch/raw/parser | 无证据链 | evidence test | `source_trace` |
| S3PDT01 | 3D | 同步全部 | 一键生成可用数据源同步/导入扫描计划 | 每个平台都要手动进入 | UX flow test | `sync_all_plan` |
| S3PDT02 | 3D | 待复核选择题 | 复核以 A/B/C/D 选择为主 | 大量自由文本输入 | owner checklist test | `build_owner_review_checklist()` |
| S3PDT03 | 3D | 简单状态语言 | 正常/需要同步/需要复核/有异常/有建议 | 技术状态暴露到首页 | UI copy review | `simple_status_language()` |
| S3PZT01 | 3Z | Stage 3 closeout | 合同、UI、治理、入口、缓存、GitHub 同步完成 | 未通过目标验证 | closeout validation | 本文件 + `HANDOFF.md` |

## Stop Condition Checks

| 检查项 | 结果 |
| --- | --- |
| 自动实盘下单 | PASS：未新增 |
| 交易密码 | PASS：未请求、未存储 |
| 支付或券商提交动作 | PASS：`sync_all_plan` 只生成计划，`does_not_execute=true` |
| 真实账户生产联通声明 | PASS：仍标记为独立后续 gate |
| QBVS 被 PFI 覆盖或重新内嵌 | PASS：未内嵌；`QBVS/qbvs` 保持 `CodexProject/QBVS` 顶层独立系统 |
| Alpha 一级入口 | PASS：未新增 |
| 8 个 PFI V0.2 一级入口 | PASS：Web shell 左侧入口显示目标 8 入口 |

## Validation

目标验证命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp -q
cd ../QBVS && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
python3 -B -m unittest tests.governance.test_human_entry_markdown_contract -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pfi_os.examples.macos_app_acceptance_lite --project-root . --summary-json
git diff --check -- PFI
```

当前本地结果：

- Stage 1+2+3 contracts：`Ran 59 tests / OK`
- Top-level QBVS lifecycle smoke：`Ran 1 test / OK`
- Project governance validation：`errors 0 / warnings 0`
- Human-entry Markdown contract：`Ran 2 tests / OK`
- Stage 3 contract：`Ran 13 tests / OK`
- Python compile：`OK`
- Web shell syntax：`node --check OK`

## 当前边界

Stage 3 完成的是 owner-readable 本地只读 MVP，不是生产联通。真实数据、真实账户、凭证、自动调度、支付提交、券商下单、报告正式发布仍需后续单独 gate。
