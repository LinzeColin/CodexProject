# KMFA S02-P2 Test Results

run_id: `KMFA-S02-P2-20260629`

## Commands

```bash
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
    Path('KMFA/metadata/imports/raw_manifest_schema.json'),
    Path('KMFA/stage_artifacts/S02_P2_immutability_policy/machine/s02_p2_manifest.json'),
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
for path in json_files:
    with path.open('r', encoding='utf-8') as f:
        json.load(f)
records = 0
for path in jsonl_files:
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                json.loads(line)
                records += 1
print(f'PASS: JSON files parsed={len(json_files)}; JSONL files parsed={len(jsonl_files)}; records={records}')
PY
find KMFA -type f \( -name '*.zip' -o -name '*.xlsx' -o -name '*.xls' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*token*' -o -name '*secret*' -o -name '*password*' \) -print
rg -n --pcre2 "<secret-patterns>" KMFA
python3 -m py_compile KMFA/tools/immutability_policy_check.py KMFA/tools/metadata_protocol_check.py KMFA/tools/no_omission_check.py
```

## Actual Results

| Command | Result |
|---|---|
| `python3 KMFA/tools/immutability_policy_check.py` | PASS: raw manifest append-only, derived versions append-only, control events no raw writes |
| `python3 KMFA/tools/metadata_protocol_check.py` | PASS: S02-P1 metadata protocol still valid |
| `python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=234, tasks=162 |
| `python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `git diff --check -- KMFA` | PASS |
| JSON/JSONL parse check | PASS: JSON files parsed=2; JSONL files parsed=15; records=256 |
| Sensitive file suffix scan | PASS: no `.zip`, `.xlsx`, `.xls`, `.pdf`, `.sqlite`, `.db`, `*token*`, `*secret*`, or `*password*` files under `KMFA/` |
| Secret regex scan | PASS: no high-signal API key/private-key patterns matched under `KMFA/` |
| `python3 -m py_compile ...` | PASS |

## Boundary

S02-P2 is complete as a protocol and governance phase only. It does not import raw business data, does not calculate project cost, does not create formal reports, does not complete S02-P3, and does not upload GitHub.
