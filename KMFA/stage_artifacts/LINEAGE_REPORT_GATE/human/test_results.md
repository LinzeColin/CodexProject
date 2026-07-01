# KMFA Lineage / Report Gate Test Results

更新时间: 2026-07-02T09:34:55+10:00

本轮只验证 Lineage / Report Gate 的公开安全阻断状态。结论不是 release 或 delivery 放行；当前仍为 `NO_GO`，`delivery_allowed=false`。

## Final Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_lineage_report_gate.py`
  - PASS: reports=2, grade_D=2, pending_reconciliation=12, actual_lineage_rows=0, delivery_allowed=false.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_lineage_report_gate -q`
  - PASS: 1 test.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_lineage_completeness.py`
  - PASS: lineage completeness gate remains safely blocked.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_whole_project_final_review.py`
  - PASS: whole-project final review gate remains local-only with delivery NO_GO.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_report_grade_gate.py`
  - PASS: report release gate remains blocked by missing evidence.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
  - PASS: 277 tests.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - PASS after fixing VERSION_MATRIX and DEVELOPMENT_LEDGER product version synchronization.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - PASS after fixing VERSION_MATRIX and DEVELOPMENT_LEDGER product version synchronization.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
  - PASS.
- structured changed-file parse check
  - PASS: JSON, JSONL, YAML and CSV changed files parsed.
- changed-file raw/private path and high-signal secret scan
  - PASS: no raw archive, spreadsheet, PDF, sqlite/db, unauthorized CSV or high-signal credential pattern in changed files.
- `git diff --check -- KMFA`
  - PASS.

## Findings Fixed

- `VERSION_MATRIX.yaml` initially still declared `0.1.0-post-s18-whole-project-review-local`; updated product version, status and version file value to `0.1.0-post-s18-lineage-report-gate-local`.
- `DEVELOPMENT_LEDGER.md` initially did not mention the new product version; updated ledger current version, phase, task and status.
