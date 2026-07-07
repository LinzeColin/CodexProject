# S19 Test Results

## Commands

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_dingtalk_attendance -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/check_s19_dingtalk_attendance.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/validate_no_sensitive_git.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type morning --timezone Asia/Shanghai`
- `dws attendance record get --user 01256723246324629191 --date 2026-07-07 --format json`
- `dws attendance summary --user 01256723246324629191 --date "2026-07-07 18:15:00" --stats-type month --format json`
- `dws attendance record get --user 01425158064862 --date 2026-07-07 --format json`
- `dws attendance summary --user 01425158064862 --date "2026-07-07 18:15:00" --stats-type month --format json`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai`
- `git diff --check --cached`
- open PR query returned `0`
- open issue query returned `0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover KMFA/tests -q`

## Result

- S19 unit tests: PASS
- S19 file contract: PASS
- config-only healthcheck: returned `CONFIG_MISSING` without sample data
- KMFA-only tracked-file sensitive scan: PASS
- pre-DWS baseline run without live OpenAPI configuration: returned `CONFIG_MISSING`; superseded by current DWS live backend validation below.
- DWS record/summary validation: PASS for 张霖泽 and 林全意; both returned success with empty `recordList` and zero attendance summary.
- DWS live S19 evening run: PASS; status `COMPLETED`, backend `dws`, member_count `44`, record_success_count `44`, summary_success_count `44`, record_nonempty_count `42`, known_no_record_names `张霖泽, 林全意`, unexpected_empty_record_count `0`.
- DWS live raw archive: `/Users/linzezhang/OneDrive/dingtalk_attendance/202607/s19_evening_20260707_095119.raw.jsonl.gz`, sha256 `aabfb6415d95f55d76890d74ef60d3430785f404210679631be470eb47f3a811`.
- diff whitespace check: PASS
- full KMFA unittest discover: not a valid S19 gate in this independent main checkout; it returned 38 environment errors from legacy v0.1.3 tests that require `codex/kmfa`, the old canonical local app path, and private raw inventory files.
