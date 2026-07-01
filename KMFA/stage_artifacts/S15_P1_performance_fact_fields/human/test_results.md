# KMFA S15-P1 测试结果

更新时间: 2026-07-01

## TDD Red

命令:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_fact_fields.py
```

结果:

```text
ModuleNotFoundError: No module named 'KMFA.tools.performance_fact_fields'
```

说明: 测试先写入 canonical KMFA worktree 后运行，因实现尚未存在而失败，符合 TDD red 阶段预期。

## TDD Green

命令:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_fact_fields.py
```

结果:

```text
.....
Ran 5 tests in 0.015s
OK
```

## Artifact Generator

命令:

```bash
PYTHONPATH=. python3 KMFA/tools/performance_fact_fields.py --generated-at 2026-07-01T23:30:00+10:00
```

结果:

```text
PASS: KMFA S15-P1 performance fact field artifacts generated (fields=6, bindings=6, manual_reviews=4, project_cost_records=4, collection_items=4, performance_fact_table=false, salary_calculation=false, bonus_approval=false, s15_p2_scope=false, stage15_review=false, github_upload=false)
```

## Phase Validator

命令:

```bash
PYTHONPATH=. python3 KMFA/tools/check_s15_p1_performance_fact_fields.py
```

结果:

```text
PASS: KMFA S15-P1 performance fact field check passed (fields=6, bindings=6, manual_reviews=4, performance_fact_table=false, salary_calculation=false, bonus_approval=false, payroll_export=false, s15_p2_scope=false, s15_p3_scope=false, stage15_review=false, github_upload=false)
```

## Final Verification

命令:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_fact_fields.py
PYTHONPATH=. python3 KMFA/tools/check_s15_p1_performance_fact_fields.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p); puts "YAML_OK #{p}" }' KMFA/docs/governance/roadmap.yaml KMFA/docs/governance/project.yaml KMFA/docs/governance/VERSION_MATRIX.yaml KMFA/docs/governance/model_registry.yaml KMFA/docs/governance/ASSURANCE_STATUS.yaml KMFA/metadata/project/project.yaml KMFA/metadata/model_registry.yaml
python3 - <<'PY'
from pathlib import Path
import csv, json
for p in [
    'KMFA/metadata/reports/performance_fact_fields_manifest.json',
    'KMFA/stage_artifacts/S15_P1_performance_fact_fields/machine/s15_p1_manifest.json',
]:
    json.loads(Path(p).read_text(encoding='utf-8'))
for p in [
    'KMFA/metadata/reports/performance_fact_field_definitions.jsonl',
    'KMFA/metadata/reports/performance_fact_field_bindings.jsonl',
    'KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl',
    'KMFA/docs/governance/events.jsonl',
    'KMFA/docs/governance/development_events.jsonl',
    'KMFA/metadata/stage_status.jsonl',
]:
    for line in Path(p).read_text(encoding='utf-8').splitlines():
        if line.strip():
            json.loads(line)
with open('KMFA/docs/governance/parameter_registry.csv', newline='', encoding='utf-8') as f:
    rows = list(csv.reader(f))
    assert rows and all(len(row) == len(rows[0]) for row in rows)
print('JSON_JSONL_CSV_PARSE_OK')
PY
disallowed_binary_file_scan_over_KMFA_tree
sensitive_pattern_scan_over_s15_p1_public_safe_outputs
git diff --check -- KMFA
```

结果:

```text
PASS: targeted S15-P1 test suite ran 5 tests, OK.
PASS: KMFA S15-P1 performance fact field check passed (fields=6, bindings=6, manual_reviews=4, performance_fact_table=false, salary_calculation=false, bonus_approval=false, payroll_export=false, s15_p2_scope=false, s15_p3_scope=false, stage15_review=false, github_upload=false).
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=469, tasks=162, v1.2_html=45+).
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
PASS: governance validators returned errors=0 / warnings=0.
PASS: JSON/JSONL/CSV parse checks passed; parameter_registry.csv rows=177 cols=34.
PASS: YAML parse checks passed with Ruby YAML parser. The local python3 environment did not have PyYAML installed, so YAML parsing was verified with Ruby.
PASS: raw/secret scan found no committed disallowed binary/private data files and no forbidden S15-P1 public-safe output patterns.
PASS: git diff --check -- KMFA returned clean.
```
