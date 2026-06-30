# S12-P1 Test Results

## Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_manual_resolution_events -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/manual_resolution_events.py --generated-at 2026-07-01T12:00:00+10:00
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s12_p1_manual_resolution_events.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
ruby JSON/JSONL/YAML/CSV UTF-8 parse checks
find/rg raw private artifact scan
rg high-signal secret scan
git diff --check
```

## Results

```text
Ran 6 tests in 0.007s
OK

PASS: KMFA S12-P1 manual resolution event artifacts generated (events=5, action_kinds=4, approved_events=1, reverse_events=1, raw_layer_write_allowed=false, approved_silent_update=false, impact_preview=false, rerun=false, formal_report_allowed=false, stage12_review=false, github_upload=false)

PASS: KMFA S12-P1 manual resolution events passed (events=5, action_kinds=4, approved_events=1, reverse_events=1, raw_layer_write_allowed=false, approved_silent_update=false, impact_preview=false, rerun=false, formal_report_allowed=false, stage12_review=false, github_upload=false)

Ran 138 tests in 1.875s
OK

PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=412, tasks=162, v1.2_html=45+)
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
PASS: no KMFA Python float money usage found
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)
PASS: lean governance validation errors=0 warnings=0
PASS: project governance validation errors=0 warnings=0
PASS: JSON OK 102, JSONL OK 53 files 922 rows, YAML OK 25, CSV UTF-8 OK 10 files 224 rows
PASS: raw/private artifact scan found no committed zip, Excel workbook, PDF, sqlite/db, private CSV, raw values or field plaintext in S12-P1 artifacts
PASS: high-signal secret scan found no API keys or private keys
PASS: git diff --check
```

## Notes

- Unit tests first failed with `ModuleNotFoundError` before the S12-P1 runtime existed, then passed after implementation.
- Ruby CSV parse without explicit encoding failed on local default US-ASCII; the same CSV parse with `encoding: "bom|utf-8"` passed and no CSV content fix was required.
- Final Stage 12 review and GitHub upload are intentionally out of scope for this phase.
