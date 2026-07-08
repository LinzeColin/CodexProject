# Taskpack: fund-weekly-analysis-skill

Deliverables:

1. Optimized Excel template: `templates/资金与税费管理母版_真实数据预览_v2.xlsx`
2. Skill instructions: `SKILL.md`
3. Automation prompt: `automation/weekly_mon_sat_1100_sydney.prompt.md`
4. macOS launchd template: `automation/launchd/com.kmfa.fund-weekly-analysis.plist`
5. Deterministic runner, source readiness gate, source materializer, and validators under `tools/`
6. Governance references under `references/`
7. Owner review checklist: `references/excel_master_review_checklist.md`

Install:

```bash
export KMFA_REPO_ROOT=/path/to/CodexProject
bash tools/install_to_kmfa_main.sh
```

After install, replace `__REPO_ROOT__` in the launchd plist with the actual repo path, copy it to `~/Library/LaunchAgents/`, then run:

```bash
launchctl load ~/Library/LaunchAgents/com.kmfa.fund-weekly-analysis.plist
```

The installer does not commit raw financial evidence. It tracks only skill/governance/config files and a gitignored metadata private_runtime boundary.

Runtime package rule: `ocr_fact_candidate_owner_decision_progress_summary.csv` is emitted from owner decision preview status for all OCR fact candidates and per metric. It is progress evidence only; it must keep `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.

Owner decision intake rule: `tools/install_owner_decision_manifest.py --draft-csv-path <reviewed.csv>` or `--draft-xlsx-path <reviewed.xlsx>` may validate spreadsheet-edited owner decisions, but it remains dry-run by default and never promotes facts, writes ledgers, mutates source files, or releases management conclusions.

Owner decision validation report rule: every valid JSON/CSV/XLSX intake writes private `ocr_fact_candidate_owner_decision_intake_validation_report.csv` with row-level missing-field or ready statuses plus owner-fill context such as evidence id, OCR text path, OCR excerpt, focus status, sidecar line range/focus line/match value, business date, amount, and currency. It is review guidance only and keeps every write/promotion/conclusion flag false.

Owner decision intake summary rule: every valid JSON/CSV/XLSX intake also writes private `ocr_fact_candidate_owner_decision_intake_summary.csv` with one `all` row, one row per `candidate_metric`, and one row per `source_ocr_excerpt_focus_status`, summarizing candidate count, ready count, blocking count, missing owner values, not-approved rows, missing fields, and top recommended owner action. It is summary guidance only and keeps every write/promotion/conclusion flag false.

Owner review export rule: `tools/export_owner_decision_review_csv.py` may export a small `ocr_fact_candidate_owner_decision_review_batch.csv` and, with `--xlsx`, a native `ocr_fact_candidate_owner_decision_review_batch.xlsx` from the private owner worklist for spreadsheet review. It may include `source_ocr_text_excerpt` copied from repo-local private OCR sidecars, preferring lines around the candidate amount or business date, and must include `source_ocr_excerpt_focus_status` so reviewers can distinguish amount hits, business-date hits, file-start fallback, missing OCR path/sidecar, empty sidecar, and unreadable sidecar. It must also include `source_ocr_excerpt_line_range`, `source_ocr_excerpt_focus_line_number`, and `source_ocr_excerpt_match_value` for sidecar-level traceability. The review sheet must include formula-backed row-level `owner_review_completion_status` and `missing_owner_fields_current` guidance. It only prepares pending-review review files and must keep every write/promotion/conclusion flag false.
