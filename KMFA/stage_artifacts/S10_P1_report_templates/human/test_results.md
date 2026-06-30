# S10-P1 Test Results

更新时间: 2026-06-30

## TDD Red

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_report_templates -q
```

Result:

```text
FAILED (errors=1)
ModuleNotFoundError: No module named 'KMFA.tools.report_templates'
```

## S10-P1 Unit Tests

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_report_templates -q
```

Result:

```text
Ran 4 tests in 0.002s
OK
```

## Artifact Generation

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/report_templates.py
```

Result:

```text
PASS: KMFA S10-P1 report template artifacts generated (templates=2, sections=11, project_cost_sections=4, business_overview_sections=7, formal_report_allowed=false, s10_p2_scope=false, s10_p3_scope=false, ui_scope=false)
```

## Validator

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p1_report_templates.py
```

Result:

```text
PASS: KMFA S10-P1 report template check passed (templates=2, sections=11, project_cost_sections=4, business_overview_sections=7, formal_report_allowed=false, trusted_grade_assignment_allowed=false, s10_p2_scope=false, s10_p3_scope=false, ui_scope=false, lineage_full_check_scope=false, external_connector_scope=false)
```

## Full KMFA Tests

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
```

Result:

```text
Ran 104 tests in 1.803s
OK
```

## Governance Validators

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
```

Result:

```text
errors: 0
warnings: 0
```

## KMFA Boundary Validators

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
```

Result:

```text
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=374, tasks=162, v1.2_html=45+)
PASS: no KMFA Python float money usage found
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
```

## Parse And Safety Scans

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import csv, json, pathlib
root = pathlib.Path('KMFA')
for path in sorted(root.rglob('*.json')):
    json.loads(path.read_text(encoding='utf-8'))
for path in sorted(root.rglob('*.jsonl')):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            json.loads(line)
for path in sorted(root.rglob('*.csv')):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        list(csv.reader(f))
print('PASS: KMFA JSON/JSONL/CSV parse checks passed')
PY
ruby -ryaml -e 'Dir.glob("KMFA/**/*.yaml").sort.each { |p| YAML.load_file(p) }; puts "PASS: KMFA YAML parse checks passed"'
find KMFA -type f \( -name '*.zip' -o -name '*.xlsx' -o -name '*.xls' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' \)
rg -n "sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|AIza[0-9A-Za-z_-]{35}|xox[baprs]-[0-9A-Za-z-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}" KMFA
git diff --check -- KMFA
```

Result:

```text
PASS: KMFA JSON/JSONL/CSV parse checks passed
PASS: KMFA YAML parse checks passed
raw/private extension scan: no matches
high-signal secret scan: no matches
git diff --check: PASS
```

Note: Python `yaml` was unavailable in this environment, so YAML parsing was verified with Ruby/Psych.
