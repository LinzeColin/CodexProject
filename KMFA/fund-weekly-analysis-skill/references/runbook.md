# Runbook

## Monday/Saturday 11:00 Australia/Sydney run

The local scheduler uses Sydney local time. Monday/Saturday 11:00 Australia/Sydney is the operational schedule. Beijing 09:00 is reference wording only for the current UTC+10 offset; during Sydney daylight saving time the Beijing reference is 08:00. Beijing time must not be used as the scheduler timezone.
For controlled validation only, `KMFA_FUND_RUN_ID=<run_id>` pins the runner output directory and `KMFA_SKIP_CODEX_EXEC=1` skips the final Codex CLI handoff. Default automation runs leave both unset.

1. Confirm local repo is on `main` and clean enough to run.
2. Pull latest `origin/main` with fast-forward only.
3. Read `SKILL.md` and all references/templates.
4. Run `tools/check_source_readiness.py` as a fast preflight.
5. Continue only when readiness is `READY`.
6. Scan input directory recursively.
7. Build file manifest with SHA256 and size.
8. If the configured folder is missing, write `SOURCE_MISSING` plus private source candidates; do not silently fall back to zip/archive sources.
9. If the configured folder exists but contains unreadable/cloud-only files, write `SOURCE_UNREADABLE`; do not generate a partial Excel package.
10. If a private directory or zip candidate is verified and the operator intends to populate the configured folder, run `tools/materialize_fund_source.py` first without `--apply`, inspect the manifest, then rerun with `--apply`.
11. Build evidence index for screenshots and finance files.
12. Write the `INDEXED_PENDING_EXTRACTION` no-hallucination output package first: current native Excel template copy, fact ledgers, funding forecast sidecar, cashflow validation sidecar, screenshot OCR coverage sidecar, OCR text/value/financial-fact candidate sidecars, OCR fact cross-review sidecar, OCR fact ledger staging preview sidecar, OCR fact review gate/template/preview sidecars, chat text/value candidate sidecars, chat-evidence link sidecar, attachment-evidence reconciliation sidecar, attachment remediation sidecar, attachment remediation dry-run sidecar, attachment repair plan sidecar, attachment repair apply gate sidecar, attachment repair authorization template, attachment repair authorization preview sidecar, workbook quality checks, metadata signals, automation readiness sidecar, goal completion audit, fact-promotion review packet, fact-promotion owner review batch, fact-promotion authorization/gate/dry-run/plan/execution-authorization/apply-gate sidecars, exception tasks, cross-review JSON, audit log, and run summary.
13. Carry public-safe KMFA metadata signals from fund pressure, project-cost fact layer, report grade, and scope reconciliation metadata into `kmfa_metadata_signals.csv` plus workbook pending-review cells. These signals support review routing only; they do not create amounts, forecasts, or conclusions.
14. Extract only real values with source trace. CSV files may be auto-extracted only when they contain the exact structured columns `date, company, bank, account_alias, liquidity_tier, inflow, outflow, ending_balance, flow_type`; those rows become `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW`, not management conclusions.
15. Build known due-date funding projections only from real structured CSV `due_date` risk/opportunity rows, including tax, deposit, loan, and project-cost flows; write `funding_forecast.csv` and `02_资金趋势预测` as `structured_csv_forecast_pending_review`.
16. When structured CSV facts exist, patch the copied native `.xlsx` workbook with the same traced facts in homepage KPI cards, `02_资金趋势预测`, visible flow/risk/matrix sheets, and hidden `H01/H02/H03`; preserve native chart parts and keep all values pending review.
17. Audit every screenshot evidence row in `screenshot_ocr_coverage.csv`, then put adjacent/private OCR text sidecars into `ocr_text_candidates.csv`, put detected date/amount candidates into `ocr_value_candidates.csv`, put conservative company/category/bank/amount OCR rows into `ocr_financial_fact_candidates.csv`, summarize OCR fact candidates by metric in `ocr_fact_cross_review.csv`, map OCR fact candidates into ledger-like no-write rows in `ocr_fact_ledger_staging_preview.csv`, gate OCR fact candidates through `ocr_fact_review_apply_gate.csv`, emit a private draft `ocr_fact_review_authorization_template.json`, preview authorization coverage in `ocr_fact_review_authorization_preview.csv`, write `ocr_fact_candidate_owner_decision_progress_summary.csv` from owner decision preview status for all-candidate and per-metric progress, index real DingTalk `chat_records.csv` finance text into `chat_text_candidates.csv`, put detected date/amount candidates into `chat_value_candidates.csv`, link chat candidates to `_manifest/manifest.csv` attachment evidence in `chat_evidence_links.csv`, reconcile every manifest attachment row against evidence in `attachment_evidence_reconciliation.csv`, convert blockers into `attachment_reconciliation_remediation.csv`, emit dry-run-only checks in `attachment_remediation_dry_run.csv`, convert dry-run rows into `attachment_repair_plan.csv`, gate every repair plan row in `attachment_repair_apply_gate.csv`, and create pending-review/blocking exception tasks; do not promote OCR/chat text, value candidates, financial-fact candidates, cross-review rows, staging preview rows, review gates, links, attachment reconciliation rows, remediation rows, dry-run rows, repair plan rows, or apply gate rows into ledger amounts until human/cross review passes.
18. Write `ocr_fact_review_authorization_template.json` in the run directory as a private draft only. Every row must default to `authorized=false`; an operator must edit and save a confirmed copy to `ocr_fact_review_authorizations/<run_id>.json` before it can be validated. The only accepted schema is validation-only: `authorization_scope=ocr_financial_fact_review_validation_only`, `financial_fact_promotion_allowed=false`, and `fund_ledger_write_allowed=false`.
18a. When owner correction values are reviewed outside the runner, optionally use `tools/export_owner_decision_review_csv.py --run-id <run_id> --metrics <metric,...> --limit-per-metric <n> --xlsx` to prepare a small no-write `ocr_fact_candidate_owner_decision_review_batch.csv` plus native `ocr_fact_candidate_owner_decision_review_batch.xlsx` for spreadsheet review. The export may include short `source_ocr_text_excerpt` values copied only from repo-local private OCR sidecars, preferring lines around the candidate amount or business date, and must include `source_ocr_excerpt_focus_status` so reviewers can tell whether the excerpt is amount-focused, business-date-focused, a file-start fallback, or an OCR path/sidecar problem. The paired `source_ocr_excerpt_line_range`, `source_ocr_excerpt_focus_line_number`, and `source_ocr_excerpt_match_value` identify the physical OCR sidecar lines and matched token for traceable review. The XLSX workbook must include a sheet-protected `Owner Review` sheet with only owner input columns unlocked, dropdown `owner_authorization_decision`, formula-backed row-level `owner_review_completion_status` and `missing_owner_fields_current` guidance, plus a sheet-protected read-only `Review Summary` sheet that summarizes the exported batch by `all`, `candidate_metric`, and `source_ocr_excerpt_focus_status`; every sheet keeps write/promotion/conclusion flags false. Before intake, run `tools/validate_owner_review_workbook.py --workbook-path <review.xlsx>` and require `OWNER_REVIEW_WORKBOOK_READY`. Then use `tools/install_owner_decision_manifest.py --run-id <run_id>` first as a dry-run. It validates `ocr_fact_owner_decision_correction_draft.json`, defaults to the pending-review `ocr_fact_candidate_owner_decision_template.json` when the correction draft is empty, accepts a spreadsheet-edited CSV via `--draft-csv-path <reviewed.csv>`, or accepts the native review workbook via `--draft-xlsx-path <reviewed.xlsx>`. Every valid intake writes private `ocr_fact_candidate_owner_decision_intake_validation_report.csv` with row-level statuses such as `blocked_missing_owner_values` or `ready_for_private_owner_decision_manifest_no_write`, plus context columns such as `source_evidence_id`, `source_ocr_text_relative_path`, `source_ocr_text_excerpt`, `source_ocr_excerpt_focus_status`, sidecar line locator fields, `business_date`, `amount`, and `currency`; every valid intake also writes private `ocr_fact_candidate_owner_decision_intake_summary.csv` with `all`, per-metric, and per-OCR-focus-status counts for owner action planning. Every report and summary row keeps write/promote/conclusion flags false. It may write the private `ocr_fact_candidate_owner_decisions/<run_id>.json` manifest only with `--apply --acknowledge-owner-reviewed-values`, only when every `required_owner_fields` value is filled and every owner decision is `approve_for_review_authorization`. Missing values must return `BLOCKED_OWNER_VALUES_MISSING`; pending review values must return `BLOCKED_OWNER_DECISION_NOT_APPROVED`; successful writes remain validation-only and do not write ledgers, promote facts, mutate sources, or release management conclusions.
19. After a successful scheduled runner invocation, run `tools/generate_screenshot_ocr_sidecars.py --engine vision --apply --run-dir <run_dir>` to write `screenshot_ocr_sidecar_generation_plan.csv`, `screenshot_ocr_sidecar_generation_summary.json`, and non-empty local Vision OCR text sidecars under private runtime. Existing successful plan rows must be preserved and new OCR batches must append with the next generation id. If the summary reports newly generated sidecars, rerun `tools/run_fund_weekly_analysis.py` once with the same `run_id` so private OCR sidecars are indexed into `ocr_text_candidates.csv`, `ocr_value_candidates.csv`, and OCR fact review outputs as pending-review candidates. Manual use stays dry-run unless `--apply` is explicit. OCR text must remain private runtime only, empty OCR output must not be written, and generated OCR must not be promoted into ledger amounts without review. Use bounded batches with `--vision-batch-size` and per-batch `--timeout-seconds` so a slow Vision batch cannot hang the whole run; scheduled runs additionally retry timed-out rows with `--retry-timeout-seconds 30 --retry-batch-size 1`.
20. Write `attachment_repair_authorization_template.json` in the run directory as a draft only. Every row must default to `authorized=false`; the operator must edit and save a confirmed copy to `attachment_repair_authorizations/<run_id>.json` before it can be validated.
21. If a private `attachment_repair_authorizations/<run_id>.json` file exists, validate only the schema and row coverage: `authorization_manifest_version=1`, matching `run_id`, `authorization_scope=attachment_repair_plan_validation_only`, `source_mutation_allowed=false`, `apply_execution_allowed=false`, and explicit row-level `repair_plan_authorizations`. A valid authorization manifest may be counted in cross-review, but this runner still does not execute repairs or allow source mutation.
22. Write `attachment_repair_authorization_preview.csv` from `attachment_repair_apply_gate.csv` to show coverage impact only. Valid rows may be marked `ready_for_operator_review_no_apply`; all rows still keep `apply_allowed=false`, `source_mutation_allowed=false`, `apply_performed=false`, and `formal_fact_allowed=false`.
23. Build funds ledger and net-flow ledger.
24. Apply internal-transfer pairing before management rollups.
25. Build `cashflow_validation.csv`: validate balance continuity at 0.01 tolerance, compute operating cashflow effect, and confirm internal transfers are excluded from operating cashflow. Any continuity failure enters exception tasks and blocks management conclusions.
26. Build `automation_readiness.csv`: compare the tracked Codex automation contract with the local automation TOML; require `Australia/Sydney` and the current weekly Monday/Saturday 11:00 local schedule for `schedule_ready=true`; keep `management_conclusion_allowed=false`.
27. Patch hidden `H06_配置规则`: write the runtime rules table with `run_id`, `source_input_dir`, local timezone, `schedule_rrule`, no-hallucination policy, fact-promotion/ledger/management fail-closed flags, and private-runtime governance.
28. Build `workbook_quality_checks.csv`: verify generated workbook sheet order, hidden sheets, visible row 2 cleanup, native chart size limits, formula error markers, and visible sensitive-value patterns after the H06 patch.
29. Build `goal_completion_audit.csv`: record final-objective requirement status and evidence, including C-level chart quality, KMFA metadata transform, private runtime boundary, and main-only runtime contract, without granting formal promotion or conclusion authority.
30. Build `management_conclusion_gate.csv`: combine source readiness, workbook quality, formal fact promotion execution, formal ledger population, cashflow validation, evidence cross-review, and automation readiness status; keep `management_conclusion_allowed=false` until all gates pass.
31. Build `owner_action_queue.csv`: derive owner-facing next actions only from blocking or external-check management gates; every row must keep `automation_safe=false`, `source_mutation_allowed=false`, `fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, and `management_conclusion_allowed=false`.
32. Build `fact_promotion_review_packet.csv`: summarize structured facts, OCR staging, chat value candidates, attachment evidence integrity, workbook quality, and goal audit rows for owner review; keep all rows no-write/no-promote.
33. Build `fact_promotion_owner_review_batch.csv`: derive one row per review packet area, record candidate/ready/blocker counts, `owner_review_status`, `priority`, and recommended owner action; keep `financial_fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
34. Build `fact_promotion_authorization_template.json`: derive one draft row per fact promotion review packet row, default every `authorized=false`, and keep `authorization_scope=fact_promotion_review_packet_validation_only`, `financial_fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, and `management_conclusion_allowed=false`.
35. Build `fact_promotion_authorization_preview.csv`: validate private `fact_promotion_authorizations/<run_id>.json` coverage only, mark valid rows as `ready_for_owner_review_no_fact_promotion`, and keep no-write/no-promote/no-conclusion flags false.
36. Build `fact_promotion_execution_gate.csv`: combine authorization coverage and unresolved review blockers into a fail-closed execution gate. Review areas with `authorization_required=false` become explicit `not_required_*` no-op rows and do not count as blocked. Ready rows may reach `ready_for_controlled_fact_promotion_execution`, but `fact_promotion_execution_allowed=false` must remain until a separate approved execution path is introduced.
37. Build `fact_promotion_execution_dry_run.csv`: derive a no-write impact preview from `fact_promotion_execution_gate.csv`. Rows may show `ready_for_controlled_execution_preview_no_write` and nonzero `dry_run_impact_count` only when the execution gate is ready, but every row must keep `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
38. Build `fact_promotion_execution_plan.csv`: derive an owner-facing execution plan from the dry-run rows. Rows may reach `ready_for_owner_execution_authorization_no_write` only when dry-run is ready; record `required_authorization_scope=controlled_fact_promotion_execution`, but keep `source_mutation_allowed=false`, `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
39. Build `fact_promotion_execution_authorization_template.json` and `fact_promotion_execution_authorization_preview.csv`: create a private execution authorization draft under `fact_promotion_execution_authorizations/<run_id>.json` and validate coverage only. Valid rows may reach `ready_for_controlled_execution_run_no_write`, but every row must keep `source_mutation_allowed=false`, `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
40. Build `fact_promotion_execution_apply_gate.csv`: derive the final no-write apply gate from execution authorization preview rows. Valid rows may reach `ready_for_controlled_execution_apply_no_write`, but every row must keep `source_mutation_allowed=false`, `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
41. Build daily balance continuity and company-bank matrix.
42. Build tax/loan/project-cost/wealth-management/deposit risk tables.
43. Promote reviewed facts into Excel with exact sheet order and style spec.
44. Hide audit/review sheets.
45. Run validation checks.
46. Write run summary.
47. Commit/push skill or automation changes to GitHub main only after validation passes.

## Source materialization command

Dry-run:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py \
  --repo-root /Users/linzezhang/CodexProject \
  --source-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Archive/付款请示群 \
  --target-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群
```

Apply after checking the dry-run manifest:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py \
  --repo-root /Users/linzezhang/CodexProject \
  --source-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Archive/付款请示群 \
  --target-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群 \
  --apply
```

If dry-run returns `SOURCE_UNREADABLE`, do not apply. First make the OneDrive
source files available offline, then rerun dry-run and confirm
`unreadable_count=0`.

ZIP dry-run:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py \
  --repo-root /Users/linzezhang/CodexProject \
  --source-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip \
  --zip-prefix 付款请示群 \
  --target-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群
```

ZIP apply after checking the dry-run manifest:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py \
  --repo-root /Users/linzezhang/CodexProject \
  --source-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip \
  --zip-prefix 付款请示群 \
  --target-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群 \
  --apply
```

ZIP materialization is explicit only. The scheduled runner still must not silently
read or extract `DWS_Outputs.zip` when the configured hot folder is missing.
If the zip was produced with a top-level `DWS_Outputs/` folder, still pass
`--zip-prefix 付款请示群`; the materializer strips the standard container root
and remains group-scoped.

## Manual work expected from user

The user should only need to place files in the input folder and review high-risk exception tasks. The agent must not ask the user to manually rename files or hand-type data unless a blocking data ambiguity cannot be resolved from evidence.
