# KMFA v0.1.4 S04-P3 Test Results

- status: `PASS`
- phase: `S04-P3`
- task_id: `KMFA-V014-S04-P3-BASIC-TOOL-REPORT-20260704`
- scope: `basic tool report only`
- raw_root_read_list_hash_mutation: `false`
- github_upload_performed: `false`
- stage4_review_performed: `false`
- s05_started: `false`

## Validation Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s04_p3_basic_tool_report.py KMFA/tools/check_v014_s04_p3_basic_tool_report.py KMFA/tests/test_v014_s04_p3_basic_tool_report.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s04_p3_basic_tool_report.py` | PASS: cases `22/22`, amount cases `11`, date/period cases `11`, raw_read `false`, github_upload `false` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p1_amount_precision.py` | PASS: amount dependency valid |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p2_field_standardization.py` | PASS: field standardization dependency valid |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p3_basic_tool_report.py` | PASS: S04-P3 evidence validator valid |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p3_basic_tool_report -q` | PASS: `Ran 1 test` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q` | PASS: `Ran 4 tests` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/generate_tool_test_report.py --format json` | PASS: public-safe JSON report render |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/generate_tool_test_report.py --format markdown` | PASS: public-safe Markdown report render |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` | PASS: requirements `20`, P0 `9`, P1 `8`, status records `604`, tasks `162`, v1.2_html `45+` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors `0`, warnings `0` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors `0`, warnings `0` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors `0`, warnings `0` |
| `ruby -e 'require "yaml"; ARGV.each { \|p\| YAML.load_file(p) }; puts "PASS: YAML parse"' ...` | PASS |
| `structured JSON/JSONL/CSV parse check` | PASS: JSON `2`, JSONL records `909`, CSV `2` |
| `changed/untracked raw-private artifact path scan` | PASS: files `31` |
| `changed/untracked high-signal secret scan` | PASS: files `31` |
| `git diff --check -- KMFA scripts` | PASS |

## Boundary Confirmation

- S04-P3 used synthetic public-safe boundary cases only.
- No raw business data, ZIP, Excel, PDF, private CSV, SQLite/database, credentials, raw filenames, raw hashes, raw field/header plaintext, sheet names, ZIP member names, row values or business values were committed by this phase.
- The next allowed run is `v0.1.4 Stage 4 overall review`. GitHub upload remains deferred until v1.4 Stage 1-18 complete overall review and all findings are fixed.
