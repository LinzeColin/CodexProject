# PFI V0.2 Stage 2 Data Source and Low-Operation Sync MVP

Updated: 2026-06-27 Australia/Sydney

## Goal

Reduce manual entry by establishing a shared, testable data-source registry,
file import path, low-confidence review queue, non-CSV source contracts, and
reconciliation contracts.

Stage 2 does not move or refactor the existing active QBVS runtime under
`PFI/modules/qbvs_lab/qbvs`.

## Phase Status

| Phase | Scope | Contract / code | Validation |
| --- | --- | --- | --- |
| 2A | DataSource Registry | `src/pfi_v02/stage2_registry.py` | `tests.test_stage2_data_source_registry` |
| 2B | CBA CSV P0 | `src/pfi_v02/stage2_import.py` | `tests.test_stage2_cba_csv_import` |
| 2C | Alipay daily bill P0 | `src/pfi_v02/stage2_import.py` | `tests.test_stage2_alipay_import` |
| 2D | Alipay Fund non-CSV contract | `src/pfi_v02/stage2_contracts.py` | `tests.test_stage2_non_csv_contracts` |
| 2E | Moomoo AU OpenD/API | `src/pfi_v02/stage2_contracts.py` | `tests.test_stage2_non_csv_contracts` |
| 2F | China broker plugin | `src/pfi_v02/stage2_contracts.py` | `tests.test_stage2_non_csv_contracts` |
| 2G | ABC Bullion non-CSV contract | `src/pfi_v02/stage2_contracts.py` | `tests.test_stage2_non_csv_contracts` |
| 2H | WeChat contract | `src/pfi_v02/stage2_contracts.py` | `tests.test_stage2_non_csv_contracts` |

## Data Source Registry

Required sources are registered as first-class profiles:

1. `alipay_daily` - 支付宝日常账单
2. `alipay_fund` - 支付宝基金
3. `moomoo_au` - Moomoo AU
4. `cn_broker` - 中国大陆券商
5. `abc_bullion` - ABC Bullion
6. `cba_bank` - CBA 银行
7. `wechat_pay` - 微信
8. `other_connector` - 后续其他平台

Each profile declares acquisition modes, credential requirements, freshness
target, parser contracts, ledger boundaries, and read-only/no-trading-password
constraints. New platforms extend through profile/plugin contracts and do not
rewrite the core ledger.

## Implemented P0 Parsers

### CBA CSV

`parse_cba_csv_bytes()` supports:

- date parsing
- description parsing
- debit/credit or signed amount normalization
- account field mapping
- import batch hash
- raw record hash
- parser version traceability
- CBA watch folder detection and duplicate-file suppression
- transfer matching for broker deposits, credit card repayment, and bullion payment

### Alipay Daily Bill

`parse_alipay_bill_bytes()` supports CSV and ZIP-with-inner-CSV input, and
recognizes:

- consumption
- refund
- transfer candidates
- fund subscription
- fund redemption
- unknown / low-confidence records for multiple-choice review

Fund subscription and redemption are emitted as fund investment events, not
ordinary living consumption or ordinary income.

## Non-CSV Contracts

### Alipay Fund

The contract explicitly does not assume CSV. It uses triangular verification:

1. transaction line from Alipay daily bill
2. holding line from page read, app-assisted read, or manual holding snapshot
3. NAV line from external NAV source and existing QBVS NAV capability

Missing or mismatched inputs produce review or mismatch status, not false
success.

### Moomoo AU

The contract is read-only and reuses existing QBVS references:

- `PFI/modules/qbvs_lab/qbvs/datasources.py`
- `PFI/modules/qbvs_lab/qbvs/moomoo_batch.py`

If OpenD or SDK is unavailable, the probe reports unavailable and does not
fabricate data.

### China Broker

The profile supports QMT, PTrade, terminal reads, HTML/PDF/Excel statements,
browser read, and manual snapshots. It covers account, position, trade, fee,
commission, stamp tax, transfer fee, and bank-to-broker transfer mapping.

### ABC Bullion

The contract does not require CSV. It supports account page reads, HTML/PDF
statements, browser-assisted reads, holding snapshots, optional CSV, and
low-trust OCR candidates. Gold/silver buys are investment asset events, not
shopping consumption.

### WeChat

The contract supports email ZIP, CSV, XLS, XLSX, watch folder recognition,
payment normalization, transfer/refund matching, red packets, and
low-confidence review queue.

## Validation

Target command:

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts -q
```

Observed current result:

```text
Ran 22 tests in 0.061s
OK
```

Closeout command also reruns Stage 1 contracts, old QBVS lifecycle smoke,
exclusion grep, and `git diff --check`.

Observed closeout result:

```text
Stage 1+2 contracts: Ran 45 tests / OK
Legacy QBVS lifecycle smoke: Ran 1 test / OK
Scoped exclusion grep: no output
git diff --check: no output
Local cache scan: no .pyc, __pycache__, .pytest_cache, .mypy_cache or .DS_Store found under PFI
```

## Stop Conditions

Stage 2 is complete only when:

- all required data sources exist in the registry
- Alipay Fund, China Broker, and ABC Bullion do not assume CSV
- CBA CSV parser and watch folder dedupe are tested
- Alipay daily CSV/ZIP parser and review queue are tested
- Moomoo read-only contract reuses existing QBVS references
- WeChat file contract is present
- transfers, asset purchases, fund events, bullion events, and credit card
  repayment stay out of ordinary consumption
- old QBVS lifecycle smoke still passes
- changes are pushed to GitHub
- Python bytecode/cache artifacts created by local validation are removed
