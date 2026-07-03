# Test Results

- PASS: legacy S07-P2 WPS adapter validator passed before replay.
- PASS: legacy S07-P2 unit tests passed before replay.
- PASS: v0.1.3 S06 Stage review dependency validator passed before replay.
- PASS: v0.1.3 S07-P1 dependency validator passed before replay.
- PASS: v0.1.3 S07-P2 replay generator wrote manifest and human evidence.
- PASS: v0.1.3 S07-P2 replay validator confirmed exports=4, field_mappings=20, conversion_guidance=4, q5_allowed=0, stage7_review=false, github_upload=false.
- PASS: focused S07-P2 replay unit test passed.
- PASS: full KMFA unittest discovery ran 310 tests.
- PASS: no-float, no-omission, project governance, lean governance, governance sync, structured parse, YAML parse, raw/private artifact path scan, public-safe evidence scan, strict high-signal secret scan, and diff check passed.
- PASS: S07-P3, Stage 7 review, GitHub upload, raw value matching, formal report, live connector, and business execution were not performed.
- PASS: raw data inbox was not read, listed, modified, deleted, moved, renamed, overwritten, or written.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p2_wps_file_adapter.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_wps_file_adapter -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_stage_review.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s07_p2_wps_file_adapter_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p2_wps_file_adapter_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s07_p2_wps_file_adapter_replay -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync
structured JSON/JSONL/CSV parse check
structured YAML parse check
changed/untracked raw/private artifact path scan
S07-P2 public-safe evidence scan
strict high-signal secret scan
git diff --check -- KMFA
```

- manifest: `KMFA/stage_artifacts/V013_S07_P2_WPS_FILE_ADAPTER_REPLAY/machine/wps_file_adapter_replay_manifest.json`
- report: `KMFA/stage_artifacts/V013_S07_P2_WPS_FILE_ADAPTER_REPLAY/human/wps_file_adapter_replay_report.md`
- status: `completed_validated_local_only_no_go_upload_deferred_wps_file_adapter_replayed`
