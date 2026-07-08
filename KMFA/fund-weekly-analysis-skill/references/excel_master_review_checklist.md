# Excel Master Review Checklist

Purpose: this checklist is the owner-facing review surface before any future authorized task-pack execution. It records what Codex understands as the current latest mother workbook and what functions are in scope.

## Rule Checklist

| Rule | Required State | Evidence |
|---|---|---|
| Latest mother workbook | `templates/资金与税费管理母版_真实数据预览_v2.xlsx` is the authoritative editable native Excel template | `validate_taskpack.py` and workbook template inspection |
| Visible sheet row 2 | Row 2 on every visible report sheet is blank | `workbook_quality_checks.csv` and template validator |
| Sheet order | `01_首页总览` is first and `02_资金趋势预测` is second | Template validator and workbook quality gate |
| Hidden audit sheets | `H01` through `H06` stay hidden | Template validator and workbook quality gate |
| Sheet 01 row 4 cards | Row 4 shows `可用现金占比`, `银行存款`, `票据/电子汇票`, `期末总资金` | Template validator |
| Sheet 01 row 8 cards | Row 8 shows `保证金可释放`, `外部净流出`, `内部调拨净额`, `资金缺口` | Template validator |
| Homepage charts | `01_首页总览` has exactly two native line charts: latest 15 days and latest 30 days | Template validator checks chart titles, series, and point counts |
| Chart size | Each native chart is at most 18 in x 9 in | Workbook quality gate |
| Native Excel only | Report elements remain editable cells, tables, formulas, and native charts, not pasted screenshots | Skill contract and template validation |
| Real data only | No simulated amount, forecast, or management conclusion is generated | Runner cross-review and audit log |
| OCR and chat values | OCR/chat extracted amounts remain candidates until human review | Candidate sidecars keep `financial_fact_promoted=false` |
| Ledger writes | OCR fact previews do not write `fund_ledger.csv` | `fund_ledger_write_allowed=false` gates |
| Automation schedule | Local Codex automation runs Monday and Saturday at 11:00 in `Australia/Sydney` | `check_codex_app_automation.py` |
| GitHub sync | Skill, automation prompt, validators, and public-safe governance changes are committed to GitHub `main` | Post-push parity check |

## Function Checklist

| Function | Current Status | Output / Gate |
|---|---|---|
| Source readiness | Active | `READY`, `SOURCE_MISSING`, or `SOURCE_UNREADABLE`; non-ready stops runner |
| Explicit source materialization | Active | Dry-run by default; `--apply` copies only verified `付款请示群` files |
| Evidence index | Active | Source files are indexed without generating financial conclusions |
| Screenshot OCR coverage | Active | `screenshot_ocr_coverage.csv` marks missing/present OCR sidecars |
| Private Vision OCR sidecars | Active | Optional private sidecars under ignored runtime, never committed |
| OCR text/value candidates | Active | `ocr_text_candidates.csv`, `ocr_value_candidates.csv` |
| OCR financial fact candidates | Active | `ocr_financial_fact_candidates.csv`; no fact promotion |
| OCR cross-review | Active | `ocr_fact_cross_review.csv` groups candidate metrics for review |
| OCR ledger staging preview | Active | `ocr_fact_ledger_staging_preview.csv`; no ledger write |
| Chat text/value candidates | Active | `chat_text_candidates.csv`, `chat_value_candidates.csv` |
| Chat evidence links | Active | `chat_evidence_links.csv` links chat rows to attachment evidence |
| Attachment reconciliation | Active | `attachment_evidence_reconciliation.csv` flags missing/conflicting evidence |
| Attachment remediation queue | Active | Plan/dry-run/apply-gate sidecars remain fail-closed |
| Structured CSV fact extraction | Active | Real structured CSV rows can create pending-review ledgers |
| Internal-transfer netting | Active | Internal transfers are separated from operating cash flow |
| Cashflow validation | Active | Balance continuity and operating cashflow effects are checked |
| Funding forecast | Active | Known due-date tax/deposit/loan/project-cost items only; no evidence-free forecast |
| Company-bank matrix | Active | Company, bank, account alias, liquidity tier, and risk matrix |
| Workbook generation | Active | Native Excel copy patched without rewriting chart packages |
| Workbook quality gates | Active | Sheet order, hidden sheets, row 2, charts, formulas, sensitive visible values |
| Automation drift check | Active | Repo contract must match local Codex automation before claiming ready |

## Authorization Boundary

This checklist is not an authorization to promote OCR/chat candidates, repair source files, write final ledger facts, or produce management conclusions. Those actions require a separate controlled run with explicit owner authorization and fresh validation.
