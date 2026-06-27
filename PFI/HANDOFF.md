# PFI Handoff

Last updated: 2026-06-27 Australia/Sydney

## Current Goal

PFI v0.2.1 前端优化 Stage 2 已完成：全局用户可见文案中文化，清理 `运行边界` 类 UI 文案，移除手机演示框/预览框风险，动态证据抽屉和 Stage 5/6 卡片不再暴露英文交付噪音或机器证据字段。

## Current Status

- Correct and only active PFI project root is `PFI/`.
- QBVS is independent top-level system `QBVS/`; PFI does not own or cover QBVS.
- Active QBVS runtime path is `QBVS/qbvs`.
- User raw-data archive root is `MetaDatabase/`; current PFI Alipay raw and processed data are under `MetaDatabase/PFI/alipay_daily/`.
- Former app shell source has been moved into `PFI/src/pfi_os`,
  `PFI/scripts`, `PFI/macos`, `PFI/assets`, `PFI/web`, `PFI/shared`, and
  `PFI/systems`.
- Installed app target is now `PFI.app`, bound by `PFI_PROJECT_ROOT`.
- Installed app entries in `/Applications`, `~/Downloads`, and `~/Desktop`
  resolve to this checkout.
- Local runtime data home is now `~/.pfi` or explicit `$PFI_DATA_HOME`.
- Current app URL after migration verification: `http://localhost:8501`.
- Stage 1 contracts remain in `src/pfi_v02/stage1_ia.py`, `src/pfi_v02/core_models.py`, and `src/pfi_v02/classification_rules.py`.
- Stage 2 registry is implemented in `src/pfi_v02/stage2_registry.py`.
- Stage 2 import pipeline is implemented in `src/pfi_v02/stage2_import.py`.
- Stage 2 non-CSV and reconciliation contracts are implemented in `src/pfi_v02/stage2_contracts.py`.
- Stage 2 record is `docs/pfi_v02/STAGE2_DATA_SYNC_MVP.md`.
- Stage 2 acceptance audit is `docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`.
- Stage 2 local contract acceptance is complete for phases 2A-2H.
- Stage 3 read-model is implemented in `src/pfi_v02/stage3_read_mvp.py`.
- Stage 3 record is `docs/pfi_v02/STAGE3_READABLE_MVP.md`.
- Stage 3 local readable MVP acceptance is complete for phases 3A-3D.
- Stage 4 analysis read-model is implemented in `src/pfi_v02/stage4_analysis_mvp.py`.
- Stage 4 record is `docs/pfi_v02/STAGE4_ANALYSIS_MVP.md`.
- Stage 4 local analysis MVP acceptance is complete for phases 4A-4B.
- Stage 5 advice/report/export model is implemented in `src/pfi_v02/stage5_advice_report_alpha.py`.
- Stage 5 record is `docs/pfi_v02/STAGE5_ADVICE_REPORT_ALPHA_EXPORT.md`.
- Stage 5 local advice/report/Alpha-read-only export acceptance is complete for phases 5A-5C.
- Stage 6 E2E stabilization model is implemented in `src/pfi_v02/stage6_e2e_stabilization.py`.
- Stage 6 record is `docs/pfi_v02/STAGE6_E2E_STABILIZATION.md`.
- Stage 6 local synthetic E2E, regression governance, delivery rollback, 20 gate audit, and ACC-* taskpack audit acceptance is complete for phases 6A-6C.
- Stage 0 preparation audit is `docs/pfi_v02/STAGE0_PREPARATION_AUDIT_20260627.md`.
- Stage 1-5 acceptance audit is `docs/pfi_v02/STAGE1_5_ACCEPTANCE_AUDIT_20260627.md`.
- v0.2.1 前端优化记录是 `docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md`。
- v0.2.1 Stage 0/1 合同是 `src/pfi_v02/stage_v021_frontend_contract.py`，测试是 `tests/test_v021_stage0_frontend_contract.py` 和 `tests/test_v021_stage1_navigation_contract.py`。
- v0.2.1 Stage 2 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage2_contract()`，测试是 `tests/test_v021_stage2_copy_cleanup_contract.py`。
- v0.2.1 UI 货币基准已锁定为 CNY；所有页面顶部右上角必须显示 `CNY/AUD=4.70（YYYYMMDD--HH:MM）`，读取当日 06:00 Australia/Sydney 汇率快照。
- v0.2.1 正式前端目标是 `PFI/web` HTML Web Shell；多模态反馈、触感、声音、视觉、通知和运行反馈控制台后续必须收敛到设置页。
- Web shell default homepage consumes Stage 6 closeout status and now shows one unified 15-entry navigation list: 首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、首页、市场、研究、持仓、策略实验室、数据与系统、设置.
- 2026-06-27验收退回纠偏：默认 8501 顶部已新增 PFI 本机数据上传；真实支付宝导出 CSV parser 已支持说明区/中间表头/GB18030/尾随空列；旧支付宝原始账单 4 份已导入 `~/.pfi/runtime/imports/alipay_daily`，覆盖 `2022-06-06` 至 `2026-06-03`，`8815` 条标准化流水，`406` 条待复核；Web Shell 动态英文状态已中文化，8 个一级入口浏览器点击验证通过。
- 2026-06-27二次纠偏：QBVS 已从 `PFI/` 内部分离为顶层 `QBVS/`；PFI 合同改为 `qbvs_independent_system=true`；Web Shell 补回 V0.1 六入口；`MetaDatabase/` 保存支付宝原始 CSV、manifest 和标准化流水，供 GitHub 验收。
- 当前 GitHub 分支 `codex/pfi-stage6-meta-qbvs-sync` 已推送 commit `d0d0a4b8f50231e2c63293396a1fee8e03de7fda`；PFI/QBVS/MetaDatabase 相关工作区在该 commit 后干净。
- 2026-06-27 Stage 1-5 acceptance audit：根 `README.md` 和 `governance/projects.yaml` 已登记 `QBVS` 和 `MetaDatabase`；`MetaDatabase` 补三基和最小治理；PFI Stage 1-5 contracts `Ran 89 tests / OK`；QBVS smoke `Ran 1 test / OK`；PFI/QBVS/MetaDatabase governance `errors 0 / warnings 0`；Web Shell Chrome 点击验收 `14/14`、console errors `0`。
- 2026-06-27 v0.2.1 Stage 1：HTML Web Shell 左侧导航已改为 15 个统一入口；`数据与系统` 映射设置页；策略实验室旧入口和投资管理卡片都打开投资管理下的策略实验室状态；新增 `docs/pfi_v02/LEDGER_CLASSIFICATION_STANDARD.md`；三基文件已明确功能目录、开发日志、参数依据三种定位。
- 2026-06-27 v0.2.1 Stage 2：HTML Web Shell 与动态首页摘要完成中文可读文案清理；`Review lifecycle`、`PFI Context Export`、`Synthetic E2E`、`Rollback plan`、`Follow-up list`、`Top N`、`tradeoff`、`owner gate`、`parser / raw / batch` 等旧英文/机器文案被移出用户可见面；`运行边界`、`查看边界`、`验收边界`、`安全边界` 和英文 `Boundary` 被合同测试禁止；未新增 iframe、手机演示框或预览框。

## Decisions

- Do not re-embed `QBVS/qbvs` inside `PFI/`.
- Any future QBVS change must happen under `CodexProject/QBVS`.
- Put new shared PFI V0.2 contracts at the `PFI/` root.
- Keep PFI strategy backtesting, 盘感训练 and 大数据模拟器 under PFI `投资管理`.
- Keep V0.1 compatibility entries visible as aliases in the same navigation list: 首页、市场、研究、持仓、策略实验室、数据与系统.
- Do not recreate a separate `strategy` product workspace; PFI strategy backtesting, 盘感训练 and simulator stay under `投资管理`.
- Do not recreate visible new/old navigation group titles.
- Keep PFI research-only: no trading password, no automatic real-money orders.
- Non-CSV sources are first-class: 支付宝基金、中国大陆券商、ABC Bullion do not rely on CSV as the primary contract.
- Low-confidence OCR/screenshot/recording input is candidate-only and must enter review before acceptance.
- Stage 3 `sync_all_plan` is a plan/preview only. It does not log in, submit payments, submit broker orders, or mutate real accounts.
- Stage 3 FX values are deterministic local fixtures for UI/test readability, not live exchange rates.
- Stage 4 attribution values are deterministic local estimates. If evidence is insufficient, PFI must show `estimate/需要复核` rather than precise conclusions.
- Stage 4 consumption analysis excludes transfers and investment records from living consumption.
- Stage 4 cashflow forecast separates life cash from investment cash.
- Stage 5 recommendations are review queue items. They are not orders, payment actions, or automatic real-money decisions.
- Stage 5 Alpha export is only `pfi_context_snapshot_v1`; it does not add Alpha/Ralpha/System first-level entries and does not modify the Alpha repository.
- Stage 5 context constraints keep `trading_password_available=false` and `live_trade_submission_authorized=false`.
- Stage 6 is synthetic/read-only E2E only. It proves local V0.2 can run, verify, and rollback; it does not prove real account production connectivity.
- Stage 6 follow-ups are separate gates: external Alpha context consumer, real account data connection, PDF/ZIP package, CDR/Open Banking, and production release evidence.

## Validation Commands

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp tests.test_stage5_advice_report_alpha tests.test_stage6_e2e_stabilization -q
cd ../QBVS && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pfi_os.examples.macos_app_acceptance_lite --project-root . --summary-json
node --check web/app/shell.js
git diff --check
```

Latest Stage 2 target result: `Ran 22 tests / OK`.
Latest closeout result: Stage 1+2 contracts `Ran 45 tests / OK`; legacy QBVS smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; PFI.app resolves to `CodexProject/PFI`; port 8501 is served by canonical PFI `.venv`; no PFI LaunchAgent found.
Latest Stage 3 closeout result: Stage 1+2+3 contracts `Ran 59 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Python compile `OK`; Web shell syntax `OK`.
Latest Stage 4 closeout result: Stage 1+2+3+4 contracts `Ran 71 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 4 contract `Ran 12 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`.
Latest Stage 5 closeout result: Stage 1+2+3+4+5 contracts `Ran 85 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 5 contract `Ran 14 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; browser validation screenshot `/tmp/pfi-stage5-browser-verified.png`.
Latest Stage 6 closeout result: Stage 1+2+3+4+5+6 contracts `Ran 95 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 6 contract `Ran 10 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; browser validation screenshot `/tmp/pfi-stage6-browser-verified.png`.
Latest验收退回纠偏 result: `tests.test_stage2_alipay_import` `Ran 7 tests / OK`; Stage 1 classification + Stage 2 targeted contracts `Ran 32 tests / OK`; Python compile `OK`; Web shell syntax `OK`; real old Alipay import `4/4 files`, `8815` records, `406` review; browser validation `upload panel true`, `private ledger true`, `file input 1`, `navCount 8`, all primary entry clicks OK, no raw `ready`/`Synthetic E2E`; screenshot `/tmp/pfi-alipay-upload-verified-v2.png`.
Latest v0.2.1 Stage 1 target result: Stage 1 target contracts `Ran 22 tests / OK`; full PFI unittest discover `Ran 112 tests / OK`; `node --check web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop clicked `15/15` entries with screenshot `/tmp/pfi-v021-stage1-nav-verified.png`; Chrome headless mobile 390x844 validated `数据源与上传` and `策略实验室` with screenshot `/tmp/pfi-v021-stage1-mobile-verified.png`.
Latest v0.2.1 Stage 2 target result: Stage 2 contract `Ran 4 tests / OK`; Stage 0/1/2 frontend contracts `Ran 16 tests / OK`; Stage 4/5/6 regression contracts `Ran 36 tests / OK`; full PFI unittest discover `Ran 116 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop clicked `15/15` entries and validated `复盘生命周期`、`PFI 上下文导出`、`策略实验室`, console errors `0`, screenshot `/tmp/pfi-v021-stage2-copy-desktop-verified.png`; Chrome headless mobile 390x844 validated `15` entries and `数据源与上传`, screenshot `/tmp/pfi-v021-stage2-copy-mobile-verified.png`.

## Next

1. Finish current Stage 2 full verification and push the resulting commit to GitHub `main`.
2. Next v0.2.1 pursuing goal should start with `P3 / S3 设置页`：设置页独立路由、运行反馈控制台移入设置页。
3. Do not jump to graphing, upload center, or position persistence until the corresponding stage is opened by the user.
