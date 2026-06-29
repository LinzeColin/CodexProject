# KMFA S02-P3 Test Results

run_id: `KMFA-S02-P3-20260629`

## Commands

```bash
python3 KMFA/tools/check_report_grade_gate.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 KMFA/tools/no_omission_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- KMFA
python3 - <<'PY'
import json
from pathlib import Path
json_files = [
    Path('KMFA/metadata/protocol/directory_manifest.json'),
    Path('KMFA/metadata/imports/raw_manifest_schema.json'),
    Path('KMFA/stage_artifacts/S02_P2_immutability_policy/machine/s02_p2_manifest.json'),
    Path('KMFA/stage_artifacts/S02_P3_quality_gate/machine/s02_p3_manifest.json'),
]
json_subset_files = [
    Path('KMFA/metadata/quality/quality_grade_policy.yaml'),
    Path('KMFA/metadata/reports/report_grade_policy.yaml'),
    Path('KMFA/metadata/reports/report_release_gate.yaml'),
    Path('KMFA/metadata/imports/raw_manifest_policy.yaml'),
    Path('KMFA/metadata/lineage/derived_data_policy.yaml'),
    Path('KMFA/metadata/approvals/control_event_policy.yaml'),
]
jsonl_files = [
    Path('KMFA/docs/governance/events.jsonl'),
    Path('KMFA/docs/governance/development_events.jsonl'),
    Path('KMFA/metadata/stage_status.jsonl'),
    Path('KMFA/metadata/imports/import_runs.jsonl'),
    Path('KMFA/metadata/imports/raw_file_manifest.jsonl'),
    Path('KMFA/metadata/quality/data_quality_results.jsonl'),
    Path('KMFA/metadata/quality/zero_delta_results.jsonl'),
    Path('KMFA/metadata/lineage/field_lineage.jsonl'),
    Path('KMFA/metadata/lineage/metric_lineage.jsonl'),
    Path('KMFA/metadata/lineage/report_lineage.jsonl'),
    Path('KMFA/metadata/lineage/derived_data_versions.jsonl'),
    Path('KMFA/metadata/approvals/resolution_events.jsonl'),
    Path('KMFA/metadata/approvals/human_signoff_log.jsonl'),
    Path('KMFA/metadata/approvals/control_events.jsonl'),
    Path('KMFA/metadata/reports/report_manifest.jsonl'),
]
for path in json_files + json_subset_files:
    with path.open('r', encoding='utf-8') as f:
        json.load(f)
records = 0
for path in jsonl_files:
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                json.loads(line)
                records += 1
print(f'PASS: JSON files parsed={len(json_files)}; JSON-subset YAML parsed={len(json_subset_files)}; JSONL files parsed={len(jsonl_files)}; records={records}')
PY
find KMFA -type f \( -name '*.zip' -o -name '*.xlsx' -o -name '*.xls' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*token*' -o -name '*secret*' -o -name '*password*' \) -print
rg -n --pcre2 "<secret-patterns>" KMFA
python3 -m py_compile KMFA/tools/check_report_grade_gate.py KMFA/tools/immutability_policy_check.py KMFA/tools/metadata_protocol_check.py KMFA/tools/no_omission_check.py
```

## Actual Results

| Command | Result |
|---|---|
| `python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `python3 KMFA/tools/immutability_policy_check.py` | PASS: raw manifest append-only, derived versions append-only, control events no raw writes |
| `python3 KMFA/tools/metadata_protocol_check.py` | PASS: S02-P1 metadata protocol still valid |
| `python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=234, tasks=162 |
| `python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `git diff --check -- KMFA` | PASS |
| JSON/JSONL parse check | PASS: JSON files parsed=4; JSON-subset YAML parsed=6; JSONL files parsed=15; records=258 |
| Sensitive file suffix scan | PASS: no `.zip`, `.xlsx`, `.xls`, `.pdf`, `.sqlite`, `.db`, `*token*`, `*secret*`, or `*password*` files under `KMFA/` |
| Secret regex scan | PASS: no high-signal API key/private-key patterns matched under `KMFA/` |
| `python3 -m py_compile ...` | PASS |

## Boundary

S02-P3 is complete as a protocol and governance phase only. It does not import raw business data, run real zero-delta comparisons, complete lineage validation, generate reports, review Stage 2, or upload GitHub.
