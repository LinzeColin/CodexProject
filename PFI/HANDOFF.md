# PFI Handoff

Last updated: 2026-06-27 Australia/Sydney

## Current Goal

PFI root unification and app-entry migration after PFI V0.2 Stage 2.

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

## Decisions

- Do not move or broadly refactor `PFI/modules/qbvs_lab/qbvs` again without a
  dedicated migration gate and backup.
- Put new shared PFI V0.2 contracts at the `PFI/` root.
- Keep strategy backtesting and 大数据模拟器 under `投资管理 > 策略实验室 / 大数据模拟器`.
- Keep PFI research-only: no trading password, no automatic real-money orders.
- Non-CSV sources are first-class: 支付宝基金、中国大陆券商、ABC Bullion do not rely on CSV as the primary contract.
- Low-confidence OCR/screenshot/recording input is candidate-only and must enter review before acceptance.

## Validation Commands

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts -q
cd modules/qbvs_lab && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pfi_os.examples.macos_app_acceptance_lite --project-root . --summary-json
git diff --check
```

Latest Stage 2 target result: `Ran 22 tests / OK`.
Latest closeout result: Stage 1+2 contracts `Ran 45 tests / OK`; legacy QBVS smoke `Ran 1 test / OK`; macOS app lite acceptance `29 pass / 0 fail`; manual browser navigation acceptance `Pass`; app process cwd is `CodexProject/PFI`.

## Next

1. Re-run full Stage 1+2 contract tests plus legacy QBVS smoke before closeout.
2. Stage 3 can build owner-readable homepage/account/ledger MVP on these contracts.
