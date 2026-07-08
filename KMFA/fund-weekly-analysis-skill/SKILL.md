name: fund-weekly-analysis-skill
description: Use when operating, reviewing, automating, modifying, or handing off KMFA fund weekly/monthly analysis, DingTalk finance screenshot evidence, cash-flow净化, tax/loan risk analysis, company-bank account matrix, Excel fund dashboard generation, local Codex automation, or GitHub main governance under LinzeColin/CodexProject/KMFA.

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
6. `templates/excel_sheet_spec.yaml`
7. `templates/fund_weekly_analysis_config.yaml`
8. `KMFA/HANDOFF.md` if present
9. The exact source files you will touch or process

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
* Reference only: 11:00 Australia/Sydney equals 09:00 Asia/Shanghai during the current UTC+10 offset. The local scheduler must use Sydney local time, not Beijing time.
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
* `exception_tasks.csv`
* `cross_review.json`
* `audit_log.json`
* `run_summary.md`

Current deterministic runner status contract:

* Run `tools/check_source_readiness.py` before each scheduled extraction. It is a fast preflight that does not hash/read file bodies and returns `READY`, `SOURCE_MISSING`, or `SOURCE_UNREADABLE`.
* Missing configured folder returns `SOURCE_MISSING`, writes fail-closed artifacts, and may list private source candidates such as sibling `DWS_Outputs.zip` or `DWS_Archive/<group>` for explicit materialization. It must not silently switch to those candidates.
* Existing configured folder with unreadable or macOS/OneDrive `dataless` files returns `SOURCE_UNREADABLE`, writes fail-closed artifacts, and must not generate an Excel package.
* Existing configured folder returns `INDEXED_PENDING_EXTRACTION`, hashes real files, copies the current native Excel mother template into the private run folder, writes the required CSV/JSON package, and creates exception tasks for every evidence item that still needs OCR/table extraction or human review.
* Public-safe KMFA metadata signals from fund pressure, project-cost fact layer, report grade, and scope reconciliation metadata are copied into `kmfa_metadata_signals.csv` and workbook pending-review areas. These signals never create amounts, forecasts, or management conclusions.
* Every screenshot evidence row is audited in `screenshot_ocr_coverage.csv` before OCR value extraction. Missing sidecars stay `ocr_text_sidecar_missing`, create review tasks, and never create ledger amounts or management conclusions.
* Scheduled local runs call `tools/generate_screenshot_ocr_sidecars.py --engine vision --apply` after the runner to produce `screenshot_ocr_sidecar_generation_plan.csv`, `screenshot_ocr_sidecar_generation_summary.json`, and non-empty local Vision OCR text sidecars under private runtime only. The generation plan is append/resume safe: successful private sidecar rows are preserved, new batches continue with the next `OCRGEN-*` id, and scheduled runs rerun the same `run_id` once after new sidecars are written so the workbook package includes the new pending-review OCR candidates. The tool itself remains dry-run by default for manual use; scheduled `--apply` still never writes OCR text to Git-tracked paths, never modifies OneDrive source files, and never promotes financial facts. Vision OCR runs through `tools/ocr_with_vision.swift` in bounded batches using `--vision-batch-size` and per-batch `--timeout-seconds`.
* Adjacent real OCR text sidecars for screenshots, such as `<image>.ocr.txt` or `<stem>.ocr.txt`, and private Vision OCR sidecars listed in `screenshot_ocr_sidecar_generation_plan.csv` are indexed into `ocr_text_candidates.csv` and exception tasks as pending review. Date/amount candidates detected in that text are written to `ocr_value_candidates.csv`; conservative company/category/bank/amount rows are written to `ocr_financial_fact_candidates.csv` as `ocr_financial_fact_candidate_pending_review`. They never create ledger amounts or management conclusions without human/cross review.
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
* When structured CSV rows include real `due_date` risk/opportunity lines, the runner writes `funding_forecast.csv` and `02_资金趋势预测` with known due-date projections only. These remain `structured_csv_forecast_pending_review`, and they are not a management conclusion.
* When structured CSV facts exist, the runner writes `cashflow_validation.csv`: balance continuity, operating cashflow effect, and internal-transfer exclusion are checked per ledger row. Continuity failures create exception tasks and block management conclusions.
* Every generated workbook is inspected into `workbook_quality_checks.csv`: sheet order, hidden audit sheets, visible row 2 cleanup, native chart dimensions, formula error markers, and visible sensitive-value patterns. Any failing workbook quality check blocks management conclusions.
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
