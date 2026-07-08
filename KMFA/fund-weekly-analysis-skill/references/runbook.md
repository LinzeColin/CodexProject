# Runbook

## Daily 11:30 Australia/Sydney run

The local scheduler uses Sydney local time. 11:30 Australia/Sydney is the operational replacement for the previous Beijing 09:30 wording during the current UTC+10 offset.

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
12. Write the `INDEXED_PENDING_EXTRACTION` no-hallucination output package first: current native Excel template copy, fact ledgers, funding forecast sidecar, cashflow validation sidecar, OCR text/value candidate sidecars, workbook quality checks, metadata signals, exception tasks, cross-review JSON, audit log, and run summary.
13. Carry public-safe KMFA metadata signals from fund pressure, project-cost fact layer, report grade, and scope reconciliation metadata into `kmfa_metadata_signals.csv` plus workbook pending-review cells. These signals support review routing only; they do not create amounts, forecasts, or conclusions.
14. Extract only real values with source trace. CSV files may be auto-extracted only when they contain the exact structured columns `date, company, bank, account_alias, liquidity_tier, inflow, outflow, ending_balance, flow_type`; those rows become `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW`, not management conclusions.
15. Build known due-date funding projections only from real structured CSV `due_date` risk/opportunity rows; write `funding_forecast.csv` and `02_资金趋势预测` as `structured_csv_forecast_pending_review`.
16. When structured CSV facts exist, patch the copied native `.xlsx` workbook with the same traced facts in homepage KPI cards, `02_资金趋势预测`, visible flow/risk/matrix sheets, and hidden `H01/H02/H03`; preserve native chart parts and keep all values pending review.
17. Put adjacent real OCR text sidecars into `ocr_text_candidates.csv`, put detected date/amount candidates into `ocr_value_candidates.csv`, and create pending-review exception tasks; do not promote OCR text or value candidates into ledger amounts until human/cross review passes.
18. Build funds ledger and net-flow ledger.
19. Apply internal-transfer pairing before management rollups.
20. Build `cashflow_validation.csv`: validate balance continuity at 0.01 tolerance, compute operating cashflow effect, and confirm internal transfers are excluded from operating cashflow. Any continuity failure enters exception tasks and blocks management conclusions.
21. Build `workbook_quality_checks.csv`: verify generated workbook sheet order, hidden sheets, visible row 2 cleanup, native chart size limits, formula error markers, and visible sensitive-value patterns.
22. Build daily balance continuity and company-bank matrix.
23. Build tax/loan/wealth-management/deposit risk tables.
24. Promote reviewed facts into Excel with exact sheet order and style spec.
25. Hide audit/review sheets.
26. Run validation checks.
27. Write run summary.
28. Commit/push skill or automation changes to GitHub main only after validation passes.

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

ZIP materialization is explicit only. The daily runner still must not silently
read or extract `DWS_Outputs.zip` when the configured hot folder is missing.
If the zip was produced with a top-level `DWS_Outputs/` folder, still pass
`--zip-prefix 付款请示群`; the materializer strips the standard container root
and remains group-scoped.

## Manual work expected from user

The user should only need to place files in the input folder and review high-risk exception tasks. The agent must not ask the user to manually rename files or hand-type data unless a blocking data ambiguity cannot be resolved from evidence.
