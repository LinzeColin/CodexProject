# PFI V0.2 Stage 2 Acceptance Audit

Updated: 2026-06-27 Australia/Sydney

## Conclusion

Stage 2 local contract delivery is complete. The implementation proves the
data-source registry, low-operation import contracts, non-CSV contracts,
review-queue boundaries, reconciliation contracts, and legacy QBVS compatibility
in the current `CodexProject/PFI` root.

This is not production readiness. Real account credentials, live platform
connectivity, automatic trading, payment submission, and broker order
submission remain out of scope and unverified.

## Acceptance Matrix

| Phase | Task | Acceptance status | Evidence | Validation |
| --- | --- | --- | --- | --- |
| 2A | Register all core data sources | PASS | `src/pfi_v02/stage2_registry.py` includes `alipay_daily`, `alipay_fund`, `moomoo_au`, `cn_broker`, `abc_bullion`, `cba_bank`, `wechat_pay`, `other_connector` | `tests.test_stage2_data_source_registry` |
| 2A | Declare acquisition modes, credential needs, freshness target | PASS | `Stage2SourceProfile` requires acquisition, credentials, freshness, parser contracts, ledger boundaries | `tests.test_stage2_data_source_registry` |
| 2A | New platform extension contract | PASS | `build_connector_profile()` creates plugin profiles without core-ledger rewrite | `tests.test_stage2_data_source_registry` |
| 2B | CBA CSV parser | PASS | `parse_cba_csv_bytes()` normalizes date, description, account, amount direction, hashes, parser version | `tests.test_stage2_cba_csv_import` |
| 2B | CBA watch folder and dedupe | PASS | `detect_cba_watch_folder_files()` and duplicate-content suppression are tested | `tests.test_stage2_cba_csv_import` |
| 2B | CBA transfer matching | PASS | Broker deposit, credit-card repayment, and bullion payment are not ordinary consumption | `tests.test_stage2_cba_csv_import` |
| 2C | Alipay ZIP/CSV parser | PASS | `parse_alipay_bill_bytes()` supports CSV and ZIP inner CSV | `tests.test_stage2_alipay_import` |
| 2C | Fund subscription/redemption classification | PASS | Alipay fund subscription/redemption emit `FUND` events, not consumption or ordinary income | `tests.test_stage2_alipay_import` |
| 2C | Low-confidence review queue | PASS | Unknown/low-confidence records become review choices and are not silently accepted | `tests.test_stage2_alipay_import` |
| 2D | Alipay fund transaction line | PASS | `build_alipay_fund_non_csv_contract()` defines subscription, redemption, cash arrival, fee lines | `tests.test_stage2_non_csv_contracts` |
| 2D | Alipay fund holding line | PASS | Contract supports page read, app-assisted read, manual holding snapshot | `tests.test_stage2_non_csv_contracts` |
| 2D | Alipay fund NAV line | PASS | Contract supports external NAV source and existing QBVS NAV capability | `tests.test_stage2_non_csv_contracts` |
| 2D | Fund triangle reconciliation | PASS | Missing or mismatched inputs return review/mismatch, not false success | `tests.test_stage2_non_csv_contracts` |
| 2E | Moomoo OpenD/API read-only probe | PASS | `probe_moomoo_opend_contract()` reports unavailable without fabricated data | `tests.test_stage2_non_csv_contracts` |
| 2E | Moomoo account/funds/positions/orders/fills contract | PASS | `build_moomoo_read_only_contract()` records read contracts and ledger outputs | `tests.test_stage2_non_csv_contracts` |
| 2E | No trading password or live order submission | PASS | Registry and contract boundaries require read-only and no trading password | Stage 2 registry and non-CSV tests |
| 2E | Existing QBVS reuse | PASS | Contract references `PFI/modules/qbvs_lab/qbvs/datasources.py` and `moomoo_batch.py` | `tests.test_stage2_data_source_registry`, `tests.test_stage2_non_csv_contracts` |
| 2F | China broker non-CSV profile | PASS | QMT, PTrade, terminal, HTML, PDF, Excel, browser/manual snapshot modes are represented | `tests.test_stage2_non_csv_contracts` |
| 2F | Holdings/trades/fees/taxes model | PASS | Account, position, trade, commission, stamp tax, transfer fee fields are represented | `tests.test_stage2_non_csv_contracts` |
| 2F | Acquisition mode selection | PASS | `select_cn_broker_acquisition()` selects modes from profile capability | `tests.test_stage2_non_csv_contracts` |
| 2G | ABC Bullion non-CSV read contract | PASS | Page read, statement HTML/PDF, browser-assisted read, holding snapshot, optional CSV are represented | `tests.test_stage2_non_csv_contracts` |
| 2G | Bullion event model | PASS | Gold/silver buy and sell are investment asset events with units, quantity, fees, valuation | `tests.test_stage2_non_csv_contracts` |
| 2G | ABC triangle reconciliation | PASS | Statement, bank payment, and valuation inputs are required before matched status | `tests.test_stage2_non_csv_contracts` |
| 2H | WeChat ZIP/CSV/XLS/XLSX contract | PASS | Email ZIP, CSV, XLS, XLSX, and watch folder file contracts are represented | `tests.test_stage2_non_csv_contracts` |
| 2H | WeChat payment/transfer/red-packet/refund rules | PASS | Transfer and refund are not ordinary consumption; unknown/low-confidence records go to review | `tests.test_stage2_non_csv_contracts` |

## Stop Conditions Checked

| Stop condition | Result |
| --- | --- |
| Trading password required | PASS - excluded by registry and contracts |
| Automatic real-money order submission | PASS - explicitly forbidden |
| Payment or broker-order submission | PASS - out of scope |
| QBVS runtime move/rename/broad refactor | PASS - active runtime remains `PFI/modules/qbvs_lab/qbvs` |
| Alpha as PFI first-level entry | PASS - forbidden and tested |
| Rejected Alpha variant product entry | PASS - forbidden label only, no product entry |
| Technical development product entry | PASS - forbidden label only, no product entry |
| Excluded external project dependency | PASS - no Stage 2 implementation dependency |
| Low-confidence records accepted silently | PASS - review queue required |
| Non-CSV sources forced into CSV-only model | PASS - Alipay Fund, China Broker, ABC Bullion are non-CSV first-class contracts |

## Validation Evidence

```text
Stage 1+2 contracts:
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts -q
Ran 45 tests in 0.141s
OK

Legacy QBVS smoke:
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
Ran 1 test in 11.883s
OK

Governance:
python3 scripts/validate_project_governance.py --project PFI
errors: 0
warnings: 0

Human entry Markdown contract:
python3 -B -m unittest tests.governance.test_human_entry_markdown_contract -q
Ran 2 tests in 0.011s
OK
```

## Local Entry Evidence

- `/Applications/PFI.app/Contents/Resources/PFI_PROJECT_ROOT` points to
  `CodexProject/PFI`.
- Port `8501` is served by `PFI/.venv/bin/python -m streamlit ...`.
- The PFI listening process command resolves to the canonical checkout.
- No PFI LaunchAgent was found under `~/Library/LaunchAgents`.

## Cleanup Evidence

PFI Python bytecode and cache artifacts under `PFI/` were removed after
validation. Follow-up validation must continue to use `PYTHONDONTWRITEBYTECODE=1`
or `-B` to avoid recreating bytecode before closeout.
