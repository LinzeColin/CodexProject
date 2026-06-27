# PFI Handoff

Last updated: 2026-06-27 Australia/Sydney

## Current Goal

PFI V0.2 Stage 3 readable MVP closeout and Stage 4 readiness.

## Current Status

- Correct and only active project root is `PFI/`.
- Former QBVS container path has been migrated to `PFI/modules/qbvs_lab`.
- Active QBVS runtime path is `PFI/modules/qbvs_lab/qbvs`.
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
- Web shell default homepage consumes Stage 3 read-model and shows the V0.2 8 first-level entries.

## Decisions

- Do not move or broadly refactor `PFI/modules/qbvs_lab/qbvs` again without a
  dedicated migration gate and backup.
- Put new shared PFI V0.2 contracts at the `PFI/` root.
- Keep strategy backtesting and 大数据模拟器 under `投资管理 > 策略实验室 / 大数据模拟器`.
- Keep PFI research-only: no trading password, no automatic real-money orders.
- Non-CSV sources are first-class: 支付宝基金、中国大陆券商、ABC Bullion do not rely on CSV as the primary contract.
- Low-confidence OCR/screenshot/recording input is candidate-only and must enter review before acceptance.
- Stage 3 `sync_all_plan` is a plan/preview only. It does not log in, submit payments, submit broker orders, or mutate real accounts.
- Stage 3 FX values are deterministic local fixtures for UI/test readability, not live exchange rates.

## Validation Commands

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp -q
cd modules/qbvs_lab && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pfi_os.examples.macos_app_acceptance_lite --project-root . --summary-json
node --check web/app/shell.js
git diff --check
```

Latest Stage 2 target result: `Ran 22 tests / OK`.
Latest closeout result: Stage 1+2 contracts `Ran 45 tests / OK`; legacy QBVS smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; PFI.app resolves to `CodexProject/PFI`; port 8501 is served by canonical PFI `.venv`; no PFI LaunchAgent found.
Latest Stage 3 closeout result: Stage 1+2+3 contracts `Ran 59 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Python compile `OK`; Web shell syntax `OK`.

## Next

1. Stage 4 can build investment and consumption intelligent analysis on top of Stage 3 account/ledger/readable MVP contracts.
2. Real account credentials, production sync, payment submission, broker order submission, and live trading remain separate gates.
