name: fund-weekly-analysis-skill
description: Use when operating, reviewing, automating, modifying, or handing off KMFA fund weekly/monthly analysis, DingTalk finance screenshot evidence, cash-flow净化, tax/loan/project-cost risk analysis, company-bank account matrix, Excel fund dashboard generation, local Codex automation, or GitHub main governance under LinzeColin/CodexProject/KMFA.

# KMFA Fund Weekly Analysis Skill

## Use First

This skill is the portable operating entry for KMFA资金与税费管理自动化. Use it only with a clone of `LinzeColin/CodexProject` and start from `main`.

Canonical GitHub path:

    KMFA/fund-weekly-analysis-skill/

Before acting, read these files in order:

1. `references/runbook.md`
2. `references/configuration.md`
3. `references/operating_contract.md`
4. `references/source_of_truth_contract.md`
5. `references/validation_checks.md`
6. `references/owner_review_handoff.md` when exporting, validating, or handing off OCR owner review workbooks
7. `templates/excel_sheet_spec.yaml`
8. `templates/fund_weekly_analysis_config.yaml`
9. `KMFA/HANDOFF.md` if present
10. The exact source files you will touch or process

## No simulation / no synthetic financial data

No simulation: production reports must be generated only from real source files, real DingTalk finance screenshots, real bank exports, real tax/payment/deposit/project ledgers, or explicitly reviewed manual corrections. Missing values remain blank or enter the exception queue.

## Hard Boundaries

* Do not create branches, PRs, issues, forks, or worktrees unless the user explicitly changes this rule in the current thread.
* Work on `main` only. If not on `main`, stop and report.
* Any change to this skill, its automation prompt, validator, template, or governance file must be committed and pushed to GitHub `main` in the same run after validation passes.
* Local Codex automation state is not Git by itself. The canonical automation prompt must be mirrored under `automation/` in this folder before the local automation is updated.
* Do not commit raw screenshots, raw bank exports, raw DingTalk archives, full bank account numbers, passwords, tokens, webhook URLs, app secrets, employee private plaintext, payroll raw data, or non-redacted report bodies to public GitHub.
* Do not use sample, test, synthetic, fake, demo, or estimated financial data in production reports. If a field cannot be extracted from real source evidence, leave it blank and send it to the review queue.
* Do not silently correct amount/date/counterparty discrepancies. Put all mismatches into the exception queue with source references.
* Do not count internal transfers as operating income or operating expense.
* Do not treat票据、电子承兑、理财、保证金、应收账款 as T0 cash. Always separate liquidity tiers.
* Do not let low-confidence OCR/vision extraction enter the final facts table without human review.
* Do not show full account numbers, ID numbers, personal phone numbers, passwords, employee-sensitive details, or private raw screenshots on management dashboards.

## Current Automation Rules

* Automation name: `KMFA资金周报自动化`.
* Timezone: `Australia/Sydney`.
* Scheduled run time: every Monday and Saturday at 11:00 local Sydney time.
* `Australia/Sydney` local time is the scheduler source of truth. Beijing time must not be used as the scheduler timezone.
* Input directory:

      /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群

* Public metadata/config root:

      KMFA/metadata/fund_weekly_analysis/

* Private runtime root, gitignored by default:

      KMFA/metadata/fund_weekly_analysis/private_runtime/

* Skill root:

      KMFA/fund-weekly-analysis-skill/

## Three-Layer Analytical Contract

The analysis must follow this order every time:

1. **净化层：钱是不是真的经营现金流？**
   * Build evidence index first.
   * Classify and pair internal transfers.
   * Separate operating cash flow, financing, investing/cash management, tax, deposits, guarantees, bills, loans, and unclassified net movement.
   * Output `待归类/内部调拨净额` separately. Never merge it into operating cash flow.

2. **定位层：钱在哪里，钱怎么变动？**
   * Build daily balance continuity ledger.
   * Preserve company, bank, account alias, liquidity tier, source evidence, and review status.
   * Generate company-bank matrix for every company and every bank/account alias found in real source data.
   * Show T0 bank cash,票据/电子汇票,理财,保证金, and total funds separately.

3. **预测层：钱什么时候可用，现在和将来够不够，有没有风险？**
   * Roll up daily, weekly, monthly, quarterly, half-year, and yearly views when enough real data exists.
   * Use only known real data for forecast inputs: taxes, payroll if supplied, project cost, customer receipts, deposit refunds, loan repayment, wealth-management redemption, bills maturity, and approved transfers.
   * Unconfirmed future items remain risk/opportunity lines, not fact values.

## Required Excel Output

The final workbook must be `.xlsx`, native Excel, editable, and compatible with Microsoft Excel and WPS.

Visible sheets, in this exact order:

1. `01_首页总览`
2. `02_资金趋势预测`
3. `03_三层净流余额`
4. `04_税费融资风险`
5. `05_公司银行矩阵`
6. `06_CodexSkill流程`

Hidden sheets, in this exact order after visible sheets:

* `H01_资金事实主表`
* `H02_异常任务池`
* `H03_钉钉证据索引`
* `H04_客户合同辅助`
* `H05_复审检查`
* `H06_配置规则`

Excel visual rules:

* Font: `Microsoft YaHei`; fallback to system sans-serif when unavailable.
* Title fill: `#0F172A`; title font white, bold.
* Positive/normal: green family `#DCFCE7` / `#15803D`.
* Warning: amber family `#FEF3C7` / `#D97706`.
* High risk: red family `#FEE2E2` / `#DC2626`.
* Table header blue/teal: `#1D4ED8` or `#0F766E`.
* All charts must be native Excel charts, not images.
* 首页 and trend charts must be line charts unless the user explicitly changes the chart type.
* No chart may exceed width 18 inches or height 9 inches. Treat this as max 1728 x 864 px at 96 dpi.
* Charts must not overlap tables or other charts.
* Sheet elements must be native cells, tables, charts, conditional formatting, or sparklines. Do not paste screenshots as report elements.
* Visible sheets must be legible for non-finance C-level/board users.

## Minimum Outputs Per Run

Write outputs under:

    KMFA/metadata/fund_weekly_analysis/private_runtime/runs/<run_id>/

Required files:

* `资金与税费管理母版_<run_id>.xlsx`
* `资金与税费管理报告_<run_id>.pdf`
* `run_manifest.json`
* `evidence_index.csv`
* `fund_ledger.csv`
* `net_flow_ledger.csv`
* `company_bank_matrix.csv`
* `tax_loan_risk.csv`
* `funding_forecast.csv`
* `cashflow_validation.csv`
* `screenshot_ocr_coverage.csv`
* `ocr_text_candidates.csv`
* `ocr_value_candidates.csv`
* `ocr_financial_fact_candidates.csv`
* `ocr_fact_cross_review.csv`
* `ocr_fact_ledger_staging_preview.csv`
* `ocr_fact_review_apply_gate.csv`
* `ocr_fact_review_authorization_template.json`
* `ocr_fact_review_authorization_preview.csv`
* `chat_text_candidates.csv`
* `chat_value_candidates.csv`
* `chat_evidence_links.csv`
* `attachment_evidence_reconciliation.csv`
* `attachment_reconciliation_remediation.csv`
* `attachment_remediation_dry_run.csv`
* `attachment_repair_plan.csv`
* `attachment_repair_apply_gate.csv`
* `attachment_repair_authorization_template.json`
* `attachment_repair_authorization_preview.csv`
* `workbook_quality_checks.csv`
* `kmfa_metadata_signals.csv`
* `automation_readiness.csv`
* `goal_completion_audit.csv`
* `management_conclusion_gate.csv`
* `owner_action_queue.csv`
* `fact_promotion_review_packet.csv`
* `fact_promotion_owner_review_batch.csv`
* `fact_promotion_authorization_template.json`
* `fact_promotion_authorization_preview.csv`
* `fact_promotion_execution_gate.csv`
* `fact_promotion_execution_dry_run.csv`
* `fact_promotion_execution_plan.csv`
* `fact_promotion_execution_authorization_template.json`
* `fact_promotion_execution_authorization_preview.csv`
* `fact_promotion_execution_apply_gate.csv`
* `exception_tasks.csv`
* `cross_review.json`
* `audit_log.json`
* `run_summary.md`

The Excel workbook and `资金与税费管理报告_<run_id>.pdf` are the user-facing deliverables for a successful run. Internal audit CSV/JSON files, OCR text, logs, private authorization manifests, and sidecar files are private validation material only and must stay under ignored private runtime unless a separate owner-approved handoff says otherwise.

Current deterministic runner status contract:

* Run `tools/check_source_readiness.py` before each scheduled extraction. It is a fast preflight that does not hash/read file bodies and returns `READY`, `SOURCE_MISSING`, or `SOURCE_UNREADABLE`.
* Missing configured folder returns `SOURCE_MISSING`, writes fail-closed artifacts, and may list private source candidates such as sibling `DWS_Outputs.zip` or `DWS_Archive/<group>` for explicit materialization. It must not silently switch to those candidates.
* Existing configured folder with unreadable or macOS/OneDrive `dataless` files returns `SOURCE_UNREADABLE`, writes fail-closed artifacts, and must not generate an Excel package.
* Existing configured folder returns `INDEXED_PENDING_EXTRACTION`, hashes real files, copies the current native Excel mother template into the private run folder, writes the required CSV/JSON package, and creates exception tasks for every evidence item that still needs OCR/table extraction or human review.
* Public-safe KMFA metadata signals from fund pressure, project-cost fact layer, report grade, and scope reconciliation metadata are copied into `kmfa_metadata_signals.csv` and workbook pending-review areas. These signals never create amounts, forecasts, or management conclusions.
* Every screenshot evidence row is audited in `screenshot_ocr_coverage.csv` before OCR value extraction. Missing sidecars stay `ocr_text_sidecar_missing`, create review tasks, and never create ledger amounts or management conclusions.
* Scheduled local runs reuse matching, non-empty private OCR sidecars from ignored private runtime before generating new OCR. If coverage is still missing, they call `tools/generate_screenshot_ocr_sidecars.py --engine vision --apply` after the runner to produce `screenshot_ocr_sidecar_generation_plan.csv`, `screenshot_ocr_sidecar_generation_summary.json`, `screenshot_ocr_sidecar_generation_progress.jsonl`, and non-empty local Vision OCR text sidecars under private runtime only. The generation plan is append/resume safe: successful private sidecar rows are preserved, new batches continue with the next `OCRGEN-*` id, and scheduled runs rerun the same `run_id` once after new sidecars are written so the workbook package includes the new pending-review OCR candidates. For controlled validation only, `KMFA_FUND_RUN_ID` may pin the runner `run_id`, `KMFA_FUND_VISION_LIMIT` may pass a small `--limit` to the OCR generator for bounded same-run checks, and `KMFA_SKIP_CODEX_EXEC=1` may skip the final Codex CLI handoff without changing default automation behavior. The tool itself remains dry-run by default for manual use; scheduled `--apply` still never writes OCR text to Git-tracked paths, never modifies OneDrive source files, and never promotes financial facts. Vision OCR runs through `tools/ocr_with_vision.swift` in bounded batches using `--vision-batch-size` and per-batch `--timeout-seconds`; scheduled runs retry timeout rows with `--retry-timeout-seconds 30 --retry-batch-size 1 --retry-max-rows 64` by default, controlled by `KMFA_FUND_VISION_RETRY_TIMEOUT_SECONDS`, `KMFA_FUND_VISION_RETRY_BATCH_SIZE`, and `KMFA_FUND_VISION_RETRY_MAX_ROWS`. Rows beyond the retry budget stay `ocr_retry_deferred_due_retry_budget` for future runs instead of blocking the whole scheduled entrypoint.
* Adjacent real OCR text sidecars for screenshots, such as `<image>.ocr.txt` or `<stem>.ocr.txt`, and private Vision OCR sidecars listed in the current or historical private `screenshot_ocr_sidecar_generation_plan.csv` are indexed into `ocr_text_candidates.csv` and exception tasks as pending review. Historical private sidecars are accepted only from ignored private runtime, must be non-empty, must keep `financial_fact_promoted=false`, and must match the recorded text hash when present. Date/amount candidates detected in that text are written to `ocr_value_candidates.csv`; conservative company/category/bank/amount rows are written to `ocr_financial_fact_candidates.csv` as `ocr_financial_fact_candidate_pending_review`. The runner also emits `ocr_fact_cross_review.csv`, `ocr_fact_owner_review_batch.csv`, `ocr_fact_ledger_staging_preview.csv`, `ocr_fact_review_apply_gate.csv`, `ocr_fact_review_authorization_template.json`, and `ocr_fact_review_authorization_preview.csv`; the cross-review file summarizes OCR fact candidates by metric for human review only, the owner review batch converts those metric groups into P0/P1 owner scan batches, the staging preview maps candidates into ledger-like review rows but keeps `fund_ledger_write_allowed=false`, the template defaults every row to `authorized=false`, and even a valid private `ocr_fact_review_authorizations/<run_id>.json` manifest is validation-only with `authorization_scope=ocr_financial_fact_review_validation_only` and cannot write `fund_ledger.csv`. OCR candidates never create ledger amounts or management conclusions without human/cross review.
* Every successful output package emits `ocr_fact_candidate_owner_decision_progress_summary.csv` after `ocr_fact_candidate_owner_decision_preview.csv`. It summarizes all OCR fact owner decisions plus per-metric counts for candidates, ready rows, blockers, missing owner decision manifests, pending/approved/correction/rejected decisions, missing company/bank values, and authorization-update readiness. It is owner-facing progress evidence only; every row must keep `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `owner_decision_readiness_gate.csv` after the owner decision preview. It compresses the current owner decision manifest blocker into one run-level gate, including candidate, ready, blocking, missing-manifest, pending-review, approved, correction, rejected, missing company, and missing bank counts. It may reach `ready_for_private_ocr_fact_authorization_update_no_write` only when all decision preview rows are ready; otherwise it must expose statuses such as `blocked_missing_owner_decision_manifest` and keep `owner_decision_manifest_write_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* `tools/export_owner_decision_review_csv.py` may export a small owner-facing `ocr_fact_candidate_owner_decision_review_batch.csv` and, with `--xlsx`, a native `ocr_fact_candidate_owner_decision_review_batch.xlsx` workbook from `ocr_fact_candidate_owner_worklist.csv`, filtered by metric and per-metric limit. The export may include a short `source_ocr_text_excerpt` copied only from repo-local private OCR sidecars to help owner review; the excerpt should prefer lines around the candidate amount or business date and fall back to the file start only when no match exists. The paired `source_ocr_excerpt_focus_status` must label whether the excerpt is `focused_amount`, `focused_business_date`, `fallback_file_start`, `missing_ocr_path`, `missing_ocr_sidecar`, `empty_ocr_sidecar`, or `unreadable_ocr_sidecar`; `source_ocr_excerpt_line_range`, `source_ocr_excerpt_focus_line_number`, and `source_ocr_excerpt_match_value` must preserve physical OCR sidecar line references and the matched amount/date token when a focused match exists. The XLSX workbook includes a sheet-protected `Owner Review` sheet with unlocked owner input columns for `owner_authorization_decision`, `owner_corrected_company`, `owner_corrected_bank`, and `owner_note`, plus formula-backed `owner_review_completion_status` and `missing_owner_fields_current` using `TEXTJOIN` so the owner can see row-level blockers update after editing; it also includes a sheet-protected read-only `Review Summary` sheet summarizing the exported batch by `all`, `candidate_metric`, and `source_ocr_excerpt_focus_status`. Run `tools/validate_owner_review_workbook.py --workbook-path <xlsx>` before owner intake; it must return `OWNER_REVIEW_WORKBOOK_READY`, `owner_input_cells_unlocked=true`, protected sheets, owner decision validation present, locked evidence/status cells, and no-write flags before the workbook is treated as ready. It is only an editable review workbook for `tools/install_owner_decision_manifest.py --draft-csv-path` or `--draft-xlsx-path`; every exported row must start as `owner_authorization_decision=pending_owner_review` and keep `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* When `ocr_fact_candidate_owner_worklist.csv` has rows, the runner must automatically emit the full private review packet `ocr_fact_candidate_owner_decision_review_all.csv` and `ocr_fact_candidate_owner_decision_review_all.xlsx` for all candidate worklist rows. These files reuse the same owner review export workbook rules, must pass `OWNER_REVIEW_WORKBOOK_READY` before intake, and remain private runtime only. `cross_review.json` must include `ocr_fact_candidate_owner_decision_review_all_count`, ready count, blocking count, and XLSX-ready status. The automatic all packet is no-write/no-promote/no-conclusion and does not write `ocr_fact_candidate_owner_decisions/<run_id>.json`; it only removes the manual export step before owner fills unlocked review columns.
* Every successful output package emits `ocr_fact_owner_decision_correction_evidence_packet.csv` for rows in `ocr_fact_owner_decision_correction_queue.csv`. The packet links each missing company/bank blocker to the real fact candidate, evidence id, source image path, OCR text path, candidate line excerpt, amount/date, required owner fields, and a no-write owner decision JSON fragment. It may reach `ready_for_owner_field_review_no_write`, but every row keeps `owner_decision_manifest_write_allowed=false`, `fund_ledger_write_allowed=false`, `formal_fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `ocr_fact_owner_decision_correction_ocr_line_context.csv` for correction evidence packets when OCR text sidecar context is available. It reads real OCR sidecar text within `ocr_line_context_radius=3` around the target `candidate_line_number`, preserving line offsets and excerpts for owner review. It may reach `ready_ocr_line_context_no_write`, but it must keep `owner_field_autofill_allowed=false`, `owner_decision_manifest_write_allowed=false`, `fund_ledger_write_allowed=false`, `formal_fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `ocr_fact_owner_decision_correction_chat_context.csv` for correction evidence packets when manifest/chat context is available. It links the source image to `_manifest/manifest.csv` and `chat_records/chat_records.csv` by message id, exposing message time, sender, resource status, chat excerpt, and quoted excerpt for owner review. It may reach `ready_chat_context_no_write`, but it must keep `owner_field_autofill_allowed=false`, `owner_decision_manifest_write_allowed=false`, `fund_ledger_write_allowed=false`, `formal_fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `ocr_fact_owner_decision_correction_chat_neighbor_context.csv` for ready correction chat context rows. It reads real `chat_records/chat_records.csv` rows within `neighbor_context_radius=2` around the target `chat_record_row_number`, preserving neighbor offsets and excerpts for owner review. It may reach `ready_neighbor_context_no_write`, but it must keep `owner_field_autofill_allowed=false`, `owner_decision_manifest_write_allowed=false`, `fund_ledger_write_allowed=false`, `formal_fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `ocr_fact_owner_decision_correction_owner_review_packet.csv` to consolidate correction evidence, OCR line context, chat context, and neighbor chat context into one owner-facing review row per correction evidence packet. It may reach `ready_for_owner_field_decision_no_write`, but it must keep `owner_field_autofill_allowed=false`, `owner_decision_manifest_write_allowed=false`, `fund_ledger_write_allowed=false`, `formal_fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `ocr_fact_owner_decision_correction_manifest_readiness.csv` after the owner review packet. It validates whether the private `ocr_fact_candidate_owner_decisions/<run_id>.json` manifest exists, contains the matching fact candidate, uses `approve_for_review_authorization`, and fills all `required_owner_fields`. It may reach `ready_for_owner_decision_manifest_validation_no_write`, but missing manifests remain `blocked_missing_owner_decision_manifest`, incomplete required values remain blocked, and every row keeps `owner_decision_manifest_write_allowed=false`, `source_mutation_allowed=false`, `fund_ledger_write_allowed=false`, `formal_fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* `tools/install_owner_decision_manifest.py` is the only packaged helper for validating reviewed owner correction decisions from `ocr_fact_owner_decision_correction_draft.json`, the pending-review `ocr_fact_candidate_owner_decision_template.json` when the correction draft is empty, a spreadsheet-edited CSV supplied with `--draft-csv-path`, or a native owner review workbook supplied with `--draft-xlsx-path`, into the private `ocr_fact_candidate_owner_decisions/<run_id>.json` path. XLSX intake is normalized as `owner_decision_xlsx_intake` before the same validation gates run. Every validated draft writes private `ocr_fact_candidate_owner_decision_intake_validation_report.csv` rows such as `blocked_missing_owner_values` or `ready_for_private_owner_decision_manifest_no_write`, preserving owner-fill context columns including `source_evidence_id`, `source_ocr_text_relative_path`, `source_ocr_text_excerpt`, `source_ocr_excerpt_focus_status`, `source_ocr_excerpt_line_range`, `source_ocr_excerpt_focus_line_number`, `source_ocr_excerpt_match_value`, `business_date`, `amount`, and `currency`, with every write/promote/conclusion flag false. It also writes private `ocr_fact_candidate_owner_decision_intake_summary.csv`, summarizing all rows, each `candidate_metric`, and each `source_ocr_excerpt_focus_status` with `candidate_count`, `ready_count`, `blocking_count`, missing-owner-values, not-approved, missing-field, and top recommended-action counts; the summary is owner guidance only and keeps every write/promote/conclusion flag false. It is dry-run by default; `--apply --acknowledge-owner-reviewed-values` is required to write, and it must return `BLOCKED_OWNER_VALUES_MISSING` when required owner values are blank. The installed manifest remains validation-only with `financial_fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, and `management_conclusion_allowed=false`; it must not write ledger rows, promote OCR facts, mutate source files, or produce management conclusions.
* Every successful output package emits `ocr_fact_owner_decision_correction_roundtrip_audit.csv` after `ocr_fact_owner_decision_correction_apply_preview.csv`. It audits whether owner-corrected company/bank values from the private owner decision manifest have reached the controlled ledger apply gate. Statuses include `owner_correction_resolved_apply_gate_ready_no_write`, `owner_correction_present_apply_gate_still_blocked`, `no_owner_correction_required_apply_gate_ready_no_write`, and `blocked_owner_correction_required`. Every row keeps `owner_decision_manifest_write_allowed=false`, `fund_ledger_write_allowed=false`, `formal_fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Real DingTalk `chat_records/chat_records.csv` content and quoted_content fields are indexed into `chat_text_candidates.csv` when they carry finance signals. Date/amount candidates detected in that text are written to `chat_value_candidates.csv` as `chat_value_candidate_pending_review`. They never create ledger amounts or management conclusions without human/cross review.
* Real DingTalk `_manifest/manifest.csv` resource rows are used to link chat text/value candidates to attachment evidence in `chat_evidence_links.csv`. Links remain `linked_pending_review` and never create ledger amounts or management conclusions without human/cross review.
* Every real DingTalk `_manifest/manifest.csv` resource row is reconciled against the evidence index in `attachment_evidence_reconciliation.csv`. Missing output paths, missing evidence files, or SHA mismatches create blocking exception tasks and never create ledger amounts or management conclusions.
* Attachment reconciliation blockers are converted into `attachment_reconciliation_remediation.csv` operator actions. These rows are not automation-safe, do not modify source files, and never create ledger amounts or management conclusions.
* Attachment remediation rows are assessed into `attachment_remediation_dry_run.csv` as dry-run-only actions. `safe_to_apply=false` and `apply_performed=false` must remain true until an explicit future controlled repair run is approved.
* Attachment dry-run rows are converted into `attachment_repair_plan.csv` plan-only steps. `operator_confirmation_required=true`, `source_mutation_allowed=false`, and `apply_performed=false` must remain true until a separate approved repair run.
* Attachment repair plan rows are gated by `attachment_repair_apply_gate.csv`. Without a separate private operator authorization manifest, every row must keep `operator_authorization_present=false`, `apply_allowed=false`, `source_mutation_allowed=false`, and `apply_performed=false`.
* Optional private authorization manifests live under `KMFA/metadata/fund_weekly_analysis/private_runtime/attachment_repair_authorizations/<run_id>.json`. The only accepted public-safe schema is `authorization_manifest_version=1`, matching `run_id`, `authorization_scope=attachment_repair_plan_validation_only`, `source_mutation_allowed=false`, `apply_execution_allowed=false`, and row-level `repair_plan_authorizations`. A valid manifest may set `authorization_validation_status=valid_manifest_validation_only`, but this runner still keeps `apply_allowed=false` and performs no repair.
* The runner emits `attachment_repair_authorization_template.json` in the run directory as a private draft only. All row entries default to `authorized=false`; the template is not read as authorization unless an operator edits and saves a confirmed copy to `attachment_repair_authorizations/<run_id>.json`.
* The runner emits `attachment_repair_authorization_preview.csv` to show authorization coverage impact from the apply gate. Rows with valid authorization may reach `ready_for_operator_review_no_apply`, but still keep `apply_allowed=false`, `source_mutation_allowed=false`, and `formal_fact_allowed=false`.
* CSV files with the exact structured columns `date, company, bank, account_alias, liquidity_tier, inflow, outflow, ending_balance, flow_type` are extracted into `fund_ledger.csv`, `net_flow_ledger.csv`, `company_bank_matrix.csv`, and `tax_loan_risk.csv` as `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW`.
* When structured CSV rows include real `due_date` risk/opportunity lines for tax, deposit, loan, or project-cost flows, the runner writes `funding_forecast.csv` and `02_资金趋势预测` with known due-date projections only. These remain `structured_csv_forecast_pending_review`, and they are not a management conclusion.
* When structured CSV facts exist, the runner writes `cashflow_validation.csv`: balance continuity, operating cashflow effect, and internal-transfer exclusion are checked per ledger row. Continuity failures create exception tasks and block management conclusions.
* Every generated workbook is inspected into `workbook_quality_checks.csv`: sheet order, hidden audit sheets, visible row 2 cleanup, homepage 15-day/30-day native line chart semantics, native chart dimensions, formula error markers, and visible sensitive-value patterns. Any failing workbook quality check blocks management conclusions.
* Every generated workbook writes a hidden `H06_配置规则` runtime rules table before workbook quality inspection. The table must include `run_id`, `source_input_dir`, local timezone, `schedule_rrule`, `schedule_ready`, `no_hallucinated_data_policy`, `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `management_conclusion_allowed=false`, and the private-runtime governance policy.
* Every successful output package emits `automation_readiness.csv`: a read-only Codex automation readiness sidecar comparing the tracked contract and local automation state. It must verify `Australia/Sydney` plus the current Monday/Saturday 11:00 local schedule, set `schedule_ready=true` only when the local schedule matches, keep `management_conclusion_allowed=false`, and mark schedule readiness as evidence only, not as financial fact promotion.
* `tools/check_codex_app_automation.py` must also validate the tracked contract itself. If the contract drifts from Monday/Saturday 11:00 `Australia/Sydney`, the weekly Monday/Saturday 11:00 prompt, the governed OneDrive input path, the source readiness gate, or `main_only_no_branch_no_pr_no_worktree`, it must return `CODEX_AUTOMATION_CONTRACT_INVALID` even when the live local automation matches the bad contract.
* `tools/check_delivery_acceptance.py --run-id <run_id>` is the repeatable final delivery checker for the taskpack. It verifies git main/origin/remote parity, public-safe zip contents, tracked schedule/source contract, live automation readiness, source readiness, native Excel sheet/chart structure, human-readable PDF presence, OCR reuse/candidate counts, no hallucinated generated amounts, owner review all-packet readiness, and fail-closed owner blockers. When engineering delivery is ready but owner values/manifest are still missing, it returns `DELIVERY_ACCEPTANCE_READY_WITH_OWNER_BLOCKERS` and keeps `owner_blockers_fail_closed` as an expected blocker rather than releasing formal ledger rows or management conclusions.
* Every successful output package emits `goal_completion_audit.csv`: requirement-level evidence for source readiness, native workbook, C-level native chart size/15-day/30-day semantics, KMFA metadata signal transform, company-bank matrix, internal-transfer netting, cashflow validation, known due-date forecasting, cross-checks, no-hallucination, raw/private runtime boundary, formal fact promotion, management conclusions, automation schedule external verification, and the main-only runtime contract. This is a final-objective audit, not a success badge: missing reviewed company-bank facts, missing real internal-transfer rows, missing cashflow validation rows, and missing known due-date forecast rows must remain `blocking=true` until real reviewed evidence exists. This audit does not grant promotion or conclusion authority.
* Every successful output package emits `management_conclusion_gate.csv`: a fail-closed C-level conclusion gate that combines source readiness, workbook quality, formal fact promotion execution, formal ledger population, cashflow validation, evidence cross-review, automation external check status, and final management-conclusion release authorization. `formal_fund_ledger.csv` rows may move the formal execution and ledger population gates to ready, but the final authorization gate still keeps `management_conclusion_allowed=false` until a separate release approval exists.
* Every successful output package emits `owner_action_queue.csv`: a fail-closed owner-facing queue derived only from blocking or external-check management gates. Rows are `pending_owner_action` or external checks only. Every row keeps `automation_safe=false`, `source_mutation_allowed=false`, `fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, and `management_conclusion_allowed=false`; it describes next actions but does not authorize or execute them.
* Every successful output package emits `fact_promotion_review_packet.csv`: a public-safe summary of structured facts, screenshot OCR coverage, OCR ledger staging, chat value candidates, attachment evidence integrity, workbook quality, and goal audit rows for owner review. The `screenshot_ocr_coverage` row is appended after the original six review areas so existing owner authorization packet IDs remain stable; it is evidence readiness only, keeps `authorization_required=false`, and never promotes facts. Every row keeps `fund_ledger_write_allowed=false` and `financial_fact_promoted=false`.
* Every successful output package emits `fact_promotion_owner_review_batch.csv`: an owner-facing batch view derived from `fact_promotion_review_packet.csv`. It groups the same six review areas with candidate/ready/blocker counts, `owner_review_status` values such as `ready_for_owner_review_no_promotion`, and recommended owner action while keeping `financial_fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`; it is not authorization and it never promotes facts.
* Every successful output package emits `fact_promotion_authorization_template.json` as a draft owner-review manifest derived from `fact_promotion_review_packet.csv`. It defaults every review row to `authorized=false`, uses `authorization_scope=fact_promotion_review_packet_validation_only`, and keeps `financial_fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, and `management_conclusion_allowed=false`; the draft is not consumed as authorization until a separate controlled validation run is approved.
* Optional private fact-promotion authorization manifests live under `KMFA/metadata/fund_weekly_analysis/private_runtime/fact_promotion_authorizations/<run_id>.json`. The runner emits `fact_promotion_authorization_preview.csv` to validate coverage only. Valid rows may reach `ready_for_owner_review_no_fact_promotion`, but still keep `financial_fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `fact_promotion_execution_gate.csv` as the final fail-closed gate before any future formal fact-promotion execution. It combines owner authorization coverage with remaining review blockers. Review areas where `authorization_required=false` must become explicit `authorization_not_required` preview rows and `not_required_*` no-op execution rows such as `not_required_no_candidate_facts` or `not_required_review_area_ready`, and must not inflate blocked counts. Ready rows may reach `ready_for_controlled_fact_promotion_execution`, but this runner still keeps `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `fact_promotion_execution_dry_run.csv` as a no-write impact preview derived from `fact_promotion_execution_gate.csv`. Ready rows may show `ready_for_controlled_execution_preview_no_write` and a `dry_run_impact_count`, but every row still keeps `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `fact_promotion_execution_plan.csv` as the owner-facing execution plan derived from the dry-run preview. Ready rows may reach `ready_for_owner_execution_authorization_no_write` and declare `required_authorization_scope=controlled_fact_promotion_execution`, but every row still keeps `source_mutation_allowed=false`, `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `fact_promotion_execution_authorization_template.json` and `fact_promotion_execution_authorization_preview.csv`. The template defaults every execution plan row to `authorized=false` and points to private `fact_promotion_execution_authorizations/<run_id>.json`; the preview may mark valid rows as `ready_for_controlled_execution_run_no_write` only when every `ready_for_owner_execution_authorization_no_write` plan row is explicitly authorized. Partial coverage must emit `blocked_incomplete_execution_authorization_coverage`, and every row still keeps `source_mutation_allowed=false`, `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `fact_promotion_execution_apply_gate.csv` as the final no-write gate before any future formal fact-promotion write path. Rows may reach `ready_for_controlled_execution_apply_no_write` and report `planned_apply_count`, but still keep `source_mutation_allowed=false`, `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* Every successful output package emits `fact_promotion_execution_result.csv` and `formal_fund_ledger.csv`. Only `structured_csv_facts` rows with valid review authorization, valid execution authorization, and `ready_for_controlled_execution_apply_no_write` may materialize into `formal_fund_ledger.csv`; OCR, chat, and attachment review areas never materialize. This sidecar does not mutate OneDrive sources, does not mutate `fund_ledger.csv`, and does not unlock management conclusions.
* When structured CSV facts exist, the runner patches the native `.xlsx` workbook directly: `01_首页总览` 4+4 cards, `02_资金趋势预测`, `03_三层净流余额`, `04_税费融资风险`, `05_公司银行矩阵`, and hidden `H01/H02/H03/H05` receive the same traced pending-review facts while preserving the existing native chart parts.
* `INDEXED_PENDING_EXTRACTION` is not a management conclusion. It means no amount was generated, inferred, forecast, or promoted into facts yet.
* `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW` is also not a management conclusion. The amounts came from real structured CSV rows, but they remain pending cross-review and must not become final C-level KPIs until gates pass.

Explicit source materialization:

* Use `tools/materialize_fund_source.py` when the configured `DWS_Outputs/付款请示群` folder is missing but a verified private candidate such as `DWS_Archive/付款请示群` or `DWS_Outputs.zip` exists.
* Dry-run is default. `--apply` is required before any files are copied.
* For directory candidates, pass `--source-dir`. For zip candidates, pass `--source-zip` and `--zip-prefix 付款请示群`; only files under that group prefix are eligible.
* ZIP candidates may contain either `付款请示群/...` directly or `DWS_Outputs/付款请示群/...` under a standard container root; the operator still passes `--zip-prefix 付款请示群`, and other groups remain out of scope.
* The tool copies only missing files, skips identical files, fails on target hash conflicts, detects OneDrive/macOS `dataless` source files as `SOURCE_UNREADABLE`, treats unreadable/bad zip files as `SOURCE_UNREADABLE`, and writes `source_materialization_manifest.json` plus `source_materialization_files.csv` under ignored private runtime.
* Do not materialize from unverified zip/archive contents silently during scheduled runner execution.

The shipped editable workbook template is:

      templates/资金与税费管理母版_真实数据预览_v2.xlsx

It is the current mother template. It keeps `01_首页总览` first, clears visible report-page row 2 explanatory text, shows the requested 4+4 homepage KPI card order, and contains exactly two homepage native line charts for the latest 15 and 30 daily snapshots. Generated production outputs still belong under private runtime and must not be committed.

Track only public-safe manifests/configs in Git unless the user gives explicit current-run authorization and the repo/privacy boundary permits raw data.

## Data Quality Gates

Stop before producing a management conclusion if any blocking gate fails:

1. Formula error scan finds Excel errors.
2. Any generated amount comes from non-real data.
3. Daily balance continuity gap exceeds 0.01 and is not explicitly sent to exceptions.
4. Internal transfer pairing rules were not applied.
5. T0 cash and total funds are not separated.
6. Tax version conflict is not flagged.
7. Raw sensitive data is visible on management sheets.
8. Required sheet order or sheet names are wrong.
9. Hidden audit/review sheets are not hidden.
10. GitHub main sync is required but validation failed.

## Agent Behavior

When uncertain, do not guess. Use `待识别`, `待复核`, or `需人工确认` and write a task into `exception_tasks.csv`. Every decision must leave a source trail: source file path, sheet/image name, evidence_id, row number when available, extraction confidence, and reviewer status.
