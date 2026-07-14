# Test Results

- PASS: v0.1.3 S07-P1 replay generator wrote manifest and human evidence.
- PASS: v0.1.3 S07-P1 replay validator and focused unit confirmed categories=9, field_candidates=45, field_reports=9, q5_allowed=0, stage7_review=false, github_upload=false.
- PASS: legacy S07-P1 finance adapter validator and legacy unit tests passed.
- PASS: v0.1.3 Stage 6 review dependency validator passed with phases=3, findings_open=0, q5_allowed=0, quality=Q4, report=D, release=blocked, github_upload=false.
- PASS: full KMFA unittest discovery passed with 309 tests.
- PASS: no-float, no-omission, project governance, lean governance, governance sync, structured parse, parameter registry shape, raw/private artifact path scan, S07-P1 public-safe evidence scan, high-signal secret scan and diff check passed.
- PASS: raw data inbox was not read, listed, modified, deleted, moved, renamed, overwritten, or written. S07-P2, S07-P3, Stage 7 review, GitHub upload, raw value matching, lineage full check, formal report, live connector and business execution were not performed.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s07_p1_finance_file_adapter_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s07_p1_finance_file_adapter_replay -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p1_finance_file_adapter.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_finance_file_adapter -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_stage_review.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync
# structured JSONL CSV parse and parameter registry shape check via Python one-shot
# structured YAML parse check via ruby -ryaml
# changed/untracked raw/private artifact path scan via Python one-shot
# S07-P1 public-safe evidence scan via Python one-shot
# changed/untracked high-signal secret scan via Python one-shot
git diff --check -- KMFA scripts
```

- manifest: `KMFA/stage_artifacts/V013_S07_P1_FINANCE_FILE_ADAPTER_REPLAY/machine/finance_file_adapter_replay_manifest.json`
- report: `KMFA/stage_artifacts/V013_S07_P1_FINANCE_FILE_ADAPTER_REPLAY/human/finance_file_adapter_replay_report.md`
- status: `completed_validated_local_only_no_go_upload_deferred_finance_file_adapter_replayed`
