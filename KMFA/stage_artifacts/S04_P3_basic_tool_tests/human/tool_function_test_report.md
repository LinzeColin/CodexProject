# S04-P3 工具函数测试报告

生成时间: 2026-06-29T23:05:00+10:00

## 摘要

- project_id: `KMFA`
- stage_phase: `S04-P3`
- status: `PASS`
- raw_business_data_used: `false`
- case_summary: `22 total / 22 passed / 0 failed`

## 覆盖范围

| Task | 覆盖 | 结果 |
|---|---|---|
| `S4PCT01` | 金额小数、负数、Unicode 负号、括号负数、万元、异常字符、非整分拒绝 | PASS |
| `S4PCT02` | 中文日期、紧凑日期、斜杠日期、中文年月、紧凑期间、中文完整日期转期间、空值和无效日期 | PASS |
| `S4PCT03` | `KMFA/tools/generate_tool_test_report.py --format json/markdown` | PASS |

## 生成命令

```bash
python3 KMFA/tools/generate_tool_test_report.py --format json
python3 KMFA/tools/generate_tool_test_report.py --format markdown
```

## 边界用例清单

| Case | Category | Outcome |
|---|---|---|
| `S4PCT01-AMOUNT-DECIMAL-CENT` | `amount_decimal` | PASS |
| `S4PCT01-AMOUNT-DECIMAL-LARGE` | `amount_decimal` | PASS |
| `S4PCT01-AMOUNT-DECIMAL-OBJECT` | `amount_decimal` | PASS |
| `S4PCT01-AMOUNT-FRACTIONAL-CENT` | `amount_decimal` | PASS |
| `S4PCT01-AMOUNT-NEGATIVE-MINUS` | `amount_negative` | PASS |
| `S4PCT01-AMOUNT-NEGATIVE-PARENTHESES` | `amount_negative` | PASS |
| `S4PCT01-AMOUNT-NEGATIVE-UNICODE` | `amount_negative` | PASS |
| `S4PCT01-AMOUNT-WAN-MIN-CENT` | `amount_wan_yuan` | PASS |
| `S4PCT01-AMOUNT-WAN-NEGATIVE` | `amount_wan_yuan` | PASS |
| `S4PCT01-AMOUNT-ABNORMAL-HASH` | `amount_abnormal_characters` | PASS |
| `S4PCT01-AMOUNT-ABNORMAL-PENDING` | `amount_abnormal_characters` | PASS |
| `S4PCT02-DATE-CHINESE` | `date_chinese` | PASS |
| `S4PCT02-DATE-COMPACT` | `date_compact` | PASS |
| `S4PCT02-DATE-SLASH` | `date_separator` | PASS |
| `S4PCT02-PERIOD-CHINESE-YEARMONTH` | `period_chinese_year_month` | PASS |
| `S4PCT02-PERIOD-COMPACT` | `period_compact` | PASS |
| `S4PCT02-PERIOD-FROM-CHINESE-DATE` | `period_from_date` | PASS |
| `S4PCT02-DATE-NONE` | `date_nullish` | PASS |
| `S4PCT02-PERIOD-BLANK` | `period_nullish` | PASS |
| `S4PCT02-DATE-HASH` | `date_nullish` | PASS |
| `S4PCT02-DATE-NA` | `date_nullish` | PASS |
| `S4PCT02-DATE-INVALID-MONTH` | `date_invalid` | PASS |

## 非范围确认

- 未使用真实业务源数据。
- 未生成经营报告。
- 未执行 A0、zero-delta、事实层、UI、外部接口或 GitHub 上传。
