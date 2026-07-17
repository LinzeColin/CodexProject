---
name: gongzi-fafang-biaozhun
description: Use when Codex is asked to整理、生成、校验或复核工资/薪资/发放表 Excel，尤其是当月原始发放文件按上月模板生成最终发放版、ABExcel 校验、差异报告、金额分校验、B公司/报销路由或密码 123 打开校验。
---

# 工资发放标准

## Core Rule

Treat every工资发放表 task as financial production work. Do not claim correctness unless source rows, amounts in cents, routing, formulas, styles, ABExcel, password-open, save-reopen, and mutation tests all pass.

Before doing any workbook action, read `references/工资发放标准.md` completely and follow it as the business source of truth. Use the spreadsheet workflow/tooling available in the current environment for `.xlsx` authoring and verification.

## Input Sufficiency Gate

If any required input is missing or ambiguous, stop before implementation and ask for the missing items with a numbered checklist.

Required inputs:

| Item | Requirement | Default |
|---|---|---|
| 当月原始 Excel | Must be the unique data source; user must identify it clearly | none |
| 模板 Excel / 上月最终正确版 | Provides only structure, style, formulas, Sheet order, sections | none |
| 文件角色 | Which file is raw and which file is template | none |
| 文件密码 | Opening password for protected workbooks | `123` |
| 目标月份 | Used in workbook title and output filenames, e.g. `2026.05月发放` | none |
| 发给 Agent 的日期 | `YYYYMMDD` used in output filenames | current date only if user accepts |
| 输出位置 | Where deliverables should be written | current task output directory |
| 特殊规则/例外 | Only if user wants rules beyond the standard | none |

Necessary and sufficient condition to proceed: raw file + template file + file-role mapping + target month + output date + readable password. If these are not satisfied, do not infer from filenames when doing so could change money, routing, or deliverable names.

## Execution Contract

Start every non-trivial run with a compact contract:

1. Goal.
2. Minimal file scope.
3. Files/directories to inspect.
4. Files that may be written.
5. Verification commands/checks.
6. Risks and rollback.
7. Stop conditions.

Only write outputs to the declared output directory. Never modify input workbooks.

## Mandatory Workflow

Follow this order:

1. Read-only: inspect raw/template Sheet order, used ranges, headers, formulas, styles, merged cells, key fields, row counts, and anomalies.
2. Plan: list files, output names, handled Sheets, routing rules, tests, rollback.
3. Implement: build Canonical Ledger from raw; generate final workbook from template structure; generate independent Oracle/B workbook; generate ABExcel.
4. Verify: run 2 rounds x 6 checks, 20 tests, password-open/save-reopen, formula-error scan, style fingerprint, and mutation tests.
5. Deliver: use conditional delivery rules from the reference standard.

## Accuracy Requirements

- Convert money to exact integer cents for validation; do not use binary float as the final truth.
- Reject or report source amounts with more than two decimals; do not silently round.
- Keep amount cells numeric; keep identifiers such as bank card numbers and line numbers as text.
- Do not reuse template people, old amounts, or old remarks.
- Do not use historical person names, historical month cases, or hardcoded row fixes as business rules.
- Do not treat matching totals as sufficient. Row-level, section-level, routing-level, formula-level, style-level, and file-level checks must also pass.

## Routing Hard Stops

Use `references/工资发放标准.md` section 7 exactly.

Critical distinction:

| Text form | Meaning |
|---|---|
| `公司名称/报销` | Slash form; may split B-company payment and invoice routing depending on whether B-company amount exists |
| `公司名称报销` | Direct form; invoice routes to that company |

Never merge these two forms. Never override `B公司/报销` using 社保公司. Unknown combinations must enter the difference report.

## Conditional Delivery

No-difference delivery only when all are true:

- 2 rounds x 6 checks pass.
- ABExcel passes.
- 20 tests pass.
- Mutation test proves validator catches deliberate errors.
- No differences or unknown items.
- Final file opens with password `123`.

Deliver only:

- `{目标月份}-{YYYYMMDD}_最终发放.xlsx`
- `{目标月份}-{YYYYMMDD}_校验ABExcel检查.xlsx`

If any difference, failed check, unknown item, password uncertainty, formula uncertainty, source uncertainty, or mutation-test failure exists, deliver:

- `{目标月份}-{YYYYMMDD}_最终发放.xlsx`
- `{目标月份}-{YYYYMMDD}_校验ABExcel检查.xlsx`
- `{目标月份}-{YYYYMMDD}_差异报告.md`
- `{目标月份}-{YYYYMMDD}_差异明细.xlsx`

Do not say “准确无误”, “最终正确”, or “无差异通过” unless the reference standard’s final acceptance criteria all pass with evidence.

## Insufficient Input Response Template

When input is insufficient, respond in Chinese:

```text
ACTION: ESCALATE
缺少完成工资发放表任务的必要充分条件：
1. ...
默认值：文件密码按 123 处理。
在补齐以上信息前，我不会生成或修改正式发放文件。
```

Keep the list minimal and concrete. Ask only for missing items that block correctness.
