# Owner Review Handoff

Purpose: preserve the no-write owner review path after OCR fact candidates are generated. This file is public-safe. It records commands, gates, and stop conditions, not OCR text, screenshots, bank details, or private owner values.

## Current Gate

OCR fact candidates are not financial facts. They are review candidates until a private owner decision manifest is validated. The runner must keep:

```text
fund_ledger_write_allowed=false
financial_fact_promoted=false
management_conclusion_allowed=false
```

for every owner review export, intake report, intake summary, authorization preview, ledger staging preview, and management gate row unless a separate authorized execution path explicitly changes that state.

## Export Owner Review Workbook

Use the latest run id with OCR coverage. For a full workbook, do not pass `--metrics` and set `--limit-per-metric 0`.

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/export_owner_decision_review_csv.py \
  --repo-root /Users/linzezhang/CodexProject \
  --run-id <run_id> \
  --limit-per-metric 0 \
  --xlsx \
  --output-name ocr_fact_candidate_owner_decision_review_all.csv \
  --xlsx-output-name ocr_fact_candidate_owner_decision_review_all.xlsx
```

The generated CSV/XLSX must remain in:

```text
KMFA/metadata/fund_weekly_analysis/private_runtime/runs/<run_id>/
```

Do not commit these review files to Git.

## Required Workbook Shape

Validate the XLSX before handoff:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/validate_owner_review_workbook.py \
  --workbook-path /Users/linzezhang/CodexProject/KMFA/metadata/fund_weekly_analysis/private_runtime/runs/<run_id>/ocr_fact_candidate_owner_decision_review_all.xlsx
```

Required ready status:

```text
OWNER_REVIEW_WORKBOOK_READY
```

The workbook must have:

* `Owner Review` sheet with one row per selected OCR fact candidate.
* `Review Summary` sheet with `all`, per `candidate_metric`, and per `source_ocr_excerpt_focus_status` summary rows.
* Both sheets protected.
* Only owner input cells unlocked: `owner_authorization_decision`, `owner_corrected_company`, `owner_corrected_bank`, `owner_note`.
* Evidence, formula, status, and write-flag cells locked.
* Owner decision dropdown present.
* All write/promotion/conclusion flags false.

## Owner Fill Rules

Owner may edit only the unlocked input columns:

```text
owner_authorization_decision
owner_corrected_company
owner_corrected_bank
owner_note
```

Allowed decisions:

```text
pending_owner_review
approve_for_review_authorization
needs_correction
reject_candidate
```

Rows are intake-ready only when required owner fields are filled and the decision is `approve_for_review_authorization`. A row with missing company or bank must remain blocked. Do not infer company or bank from adjacent chat text, filenames, or OCR context without owner input.

## Intake Dry-Run

After the owner saves the reviewed workbook, run dry-run intake first:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/install_owner_decision_manifest.py \
  --repo-root /Users/linzezhang/CodexProject \
  --run-id <run_id> \
  --draft-xlsx-path /Users/linzezhang/CodexProject/KMFA/metadata/fund_weekly_analysis/private_runtime/runs/<run_id>/ocr_fact_candidate_owner_decision_review_all.xlsx
```

Expected blocked status before owner values are complete:

```text
BLOCKED_OWNER_VALUES_MISSING
```

The dry-run writes private validation evidence only:

```text
ocr_fact_candidate_owner_decision_intake_validation_report.csv
ocr_fact_candidate_owner_decision_intake_summary.csv
```

It must not write the private owner decision manifest unless `--apply --acknowledge-owner-reviewed-values` is used after all required values are present.

## Apply Gate

Only after the dry-run is ready may an operator intentionally run:

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/install_owner_decision_manifest.py \
  --repo-root /Users/linzezhang/CodexProject \
  --run-id <run_id> \
  --draft-xlsx-path /Users/linzezhang/CodexProject/KMFA/metadata/fund_weekly_analysis/private_runtime/runs/<run_id>/ocr_fact_candidate_owner_decision_review_all.xlsx \
  --apply \
  --acknowledge-owner-reviewed-values
```

This still remains validation-only. It does not promote financial facts, write ledgers, mutate source files, or release management conclusions.

## Stop Conditions

Stop and report instead of proceeding when any of these occur:

* Workbook validator does not return `OWNER_REVIEW_WORKBOOK_READY`.
* Intake summary has `ready_count=0` and `blocking_count>0`.
* Required owner fields are missing.
* Target private owner decision manifest exists but does not match the run id or schema.
* Any write/promotion/conclusion flag is true before a separately approved controlled execution path.
* Any OCR text, screenshot content, bank account detail, or private owner value is about to enter Git.
