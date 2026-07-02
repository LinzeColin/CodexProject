# S04-P3 Tool Function Test Report

- Project: `KMFA`
- Stage/Phase: `S04/S04-P3`
- Status: `PASS`
- Raw business data used: `false`

## Case Summary

| Total | Passed | Failed |
|---:|---:|---:|
| 22 | 22 | 0 |

## Coverage

- amount decimals
- amount negatives
- amount ten-thousand-yuan unit
- amount abnormal characters
- Chinese dates
- year-month periods
- nullish date and period values

## Boundary Cases

| Case | Category | Outcome |
|---|---|---|
| `S4PCT01-AMOUNT-DECIMAL-CENT` | `amount_decimal` | `PASS` |
| `S4PCT01-AMOUNT-DECIMAL-LARGE` | `amount_decimal` | `PASS` |
| `S4PCT01-AMOUNT-DECIMAL-OBJECT` | `amount_decimal` | `PASS` |
| `S4PCT01-AMOUNT-FRACTIONAL-CENT` | `amount_decimal` | `PASS` |
| `S4PCT01-AMOUNT-NEGATIVE-MINUS` | `amount_negative` | `PASS` |
| `S4PCT01-AMOUNT-NEGATIVE-PARENTHESES` | `amount_negative` | `PASS` |
| `S4PCT01-AMOUNT-NEGATIVE-UNICODE` | `amount_negative` | `PASS` |
| `S4PCT01-AMOUNT-WAN-MIN-CENT` | `amount_wan_yuan` | `PASS` |
| `S4PCT01-AMOUNT-WAN-NEGATIVE` | `amount_wan_yuan` | `PASS` |
| `S4PCT01-AMOUNT-ABNORMAL-HASH` | `amount_abnormal_characters` | `PASS` |
| `S4PCT01-AMOUNT-ABNORMAL-PENDING` | `amount_abnormal_characters` | `PASS` |
| `S4PCT02-DATE-CHINESE` | `date_chinese` | `PASS` |
| `S4PCT02-DATE-COMPACT` | `date_compact` | `PASS` |
| `S4PCT02-DATE-SLASH` | `date_separator` | `PASS` |
| `S4PCT02-PERIOD-CHINESE-YEARMONTH` | `period_chinese_year_month` | `PASS` |
| `S4PCT02-PERIOD-COMPACT` | `period_compact` | `PASS` |
| `S4PCT02-PERIOD-FROM-CHINESE-DATE` | `period_from_date` | `PASS` |
| `S4PCT02-DATE-NONE` | `date_nullish` | `PASS` |
| `S4PCT02-PERIOD-BLANK` | `period_nullish` | `PASS` |
| `S4PCT02-DATE-HASH` | `date_nullish` | `PASS` |
| `S4PCT02-DATE-NA` | `date_nullish` | `PASS` |
| `S4PCT02-DATE-INVALID-MONTH` | `date_invalid` | `PASS` |
