# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py --require-private-refresh`
  - PASS: KMFA v0.1.4 raw candidate fingerprint evidence refresh artifacts validated.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py`
  - PASS: 5 focused tests passed in 43.232s.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py`
  - PASS: static compilation completed without output.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
  - PASS: errors=0, warnings=0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --changed-only --base-ref HEAD --enforce-sync`
  - PASS: errors=0, warnings=0.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --changed-only --base-ref HEAD --enforce-sync`
  - PASS: errors=0, warnings=0.
- `git diff --check -- KMFA`
  - PASS: no whitespace errors.
- raw/private/secret scans
  - PASS: no forbidden raw/private/binary-like filenames in tracked candidate set.
  - PASS: no raw inbox path or high-confidence secret pattern in unstaged diff.
  - PASS: private refresh outputs are ignored by `KMFA/.gitignore` and no private runtime file is tracked.

Expected matrix result: 15/15 PASS.
