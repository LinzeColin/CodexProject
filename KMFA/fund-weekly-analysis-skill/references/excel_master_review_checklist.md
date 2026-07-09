# Excel Master Review Checklist

Purpose: this checklist is the owner-facing review surface before any future authorized task-pack execution. It records what Codex understands as the current latest mother workbook and what functions are in scope.

Current evidence snapshot from the latest mother workbook:

| Item | Observed State |
|---|---|
| Workbook | `资金与税费管理母版_真实数据预览_v2.xlsx` |
| Sheet count and order | 12 sheets; `01_首页总览` first, `02_资金趋势预测` second |
| Visible row 2 | Blank on visible report sheets `01` through `06` |
| Hidden audit row 2 | Preserved on hidden `H01` through `H06`; hidden rows may contain data/header values and are not cleared by the visible-report rule |
| Sheet 01 top card band | Rows 4-7 are the first KPI band, with labels anchored at `B4`, `E4`, `H4`, `K4` |
| Sheet 01 second card band | Rows 8-11 are the second KPI band, with labels anchored at `B8`, `E8`, `H8`, `K8` |
| Sheet 01 charts | Exactly two native line charts: latest 15 days and latest 30 days |
| Schedule | Current active schedule is Monday/Saturday at 11:00 `Australia/Sydney` |

## Rule Checklist

| Rule | Required State | Evidence |
|---|---|---|
| Latest mother workbook | `templates/资金与税费管理母版_真实数据预览_v2.xlsx` is the authoritative editable native Excel template | `validate_taskpack.py` and workbook template inspection |
| Visible sheet row 2 | Row 2 on every visible report sheet is blank; hidden audit/data sheets keep their row 2 data unless separately authorized | `workbook_quality_checks.csv` and template validator |
| Sheet order | `01_首页总览` is first and `02_资金趋势预测` is second | Template validator and workbook quality gate |
| Hidden audit sheets | `H01` through `H06` stay hidden | Template validator and workbook quality gate |
| Sheet 01 rows 4-7 cards | Rows 4-7 form the first KPI band; labels are `可用现金占比`, `银行存款`, `票据/电子汇票`, `期末总资金` anchored at row 4 | Template validator |
| Sheet 01 rows 8-11 cards | Rows 8-11 form the second KPI band; labels are `保证金可释放`, `外部净流出`, `内部调拨净额`, `资金缺口` anchored at row 8 | Template validator |
| Homepage charts | `01_首页总览` has exactly two native line charts: latest 15 days and latest 30 days | Template validator and `WQ-HOMEPAGE-CHART-SEMANTICS` check chart titles, series, and point counts |
| Chart size | Each native chart is at most 18 in x 9 in | `WQ-HOMEPAGE-CHART-SIZE` workbook quality gate |
| Native Excel only | Report elements remain editable cells, tables, formulas, and native charts, not pasted screenshots | Skill contract and template validation |
| Real data only | No simulated amount, forecast, or management conclusion is generated | Runner cross-review and audit log |
| OCR and chat values | OCR/chat extracted amounts remain candidates until human review | Candidate sidecars keep `financial_fact_promoted=false` |
| Ledger writes | OCR fact previews do not write `fund_ledger.csv` | `fund_ledger_write_allowed=false` gates |
| Automation schedule | Local Codex automation runs Monday/Saturday at 11:00 in `Australia/Sydney` | `check_codex_app_automation.py` |
| Stale schedule conflict | Any daily 11:30 wording is stale unless explicitly re-approved in a later owner instruction | Current repo contract and local automation drift check |
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
| Workbook quality gates | Active | Sheet order, hidden sheets, row 2, homepage 15-day/30-day line chart semantics, chart dimensions, formulas, sensitive visible values |
| Goal completion audit | Active | `goal_completion_audit.csv` records requirement-level status, including C-level chart quality, KMFA metadata transform, private runtime boundary, main-only runtime contract, and remaining blockers |
| Management conclusion gate | Active | `management_conclusion_gate.csv` blocks C-level conclusions until formal facts and all review gates pass |
| Final management conclusion authorization | Active | `management_conclusion_final_authorization` stays blocked until a separate release approval exists, even when `formal_fund_ledger.csv` has rows |
| Owner action queue | Active | `owner_action_queue.csv` lists pending owner/external-check actions while keeping automation/source/fact/ledger/conclusion execution disabled |
| Fact promotion review packet | Active | `fact_promotion_review_packet.csv` summarizes owner-review areas while keeping no-write/no-promote |
| Fact promotion authorization template | Active | `fact_promotion_authorization_template.json` drafts one default-deny authorization row per review packet row |
| Fact promotion authorization preview | Active | `fact_promotion_authorization_preview.csv` validates owner manifest coverage without promotion, ledger write, or management conclusion |
| Fact promotion execution gate | Active | `fact_promotion_execution_gate.csv` blocks formal promotion until authorization is valid and review blockers are clear |
| Fact promotion execution dry-run | Active | `fact_promotion_execution_dry_run.csv` previews impact with no write, no promotion, and no conclusion |
| Fact promotion execution plan | Active | `fact_promotion_execution_plan.csv` defines owner execution authorization requirements without applying them |
| Fact promotion execution authorization preview | Active | `fact_promotion_execution_authorization_preview.csv` validates private execution authorization coverage for every ready execution plan row before any no-write apply gate can proceed |
| Fact promotion execution apply gate | Active | `fact_promotion_execution_apply_gate.csv` shows final no-write readiness and planned apply counts before any future formal ledger write |
| Fact promotion execution result | Active | `fact_promotion_execution_result.csv` records controlled execution results; only authorized structured CSV facts may write a formal ledger sidecar |
| Formal fund ledger sidecar | Active | `formal_fund_ledger.csv` materializes authorized structured CSV rows without mutating source files or `fund_ledger.csv`; OCR/chat/attachment areas remain excluded |
| Automation drift check | Active | Repo contract must match local Codex automation before claiming ready |

## Authorization Boundary

This checklist is not an authorization to promote OCR/chat candidates, repair source files, write final ledger facts, or produce management conclusions. Those actions require a separate controlled run with explicit owner authorization and fresh validation.
