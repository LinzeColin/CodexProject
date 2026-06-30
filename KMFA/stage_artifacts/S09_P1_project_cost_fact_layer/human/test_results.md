# S09-P1 Test Results

- project_id: `KMFA`
- stage_phase: `S09-P1`
- evidence_time: `2026-06-30T23:30:00+10:00`
- status: `phase_validated_local_only`
- github_upload_performed: `false`

## TDD Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_cost_fact_layer -q
```

Initial expected failure before implementation:

```text
ModuleNotFoundError: No module named 'KMFA.tools.project_cost_fact_layer'
FAILED (errors=1)
```

Passing result after implementation:

```text
Ran 4 tests in 0.011s
OK
```

## Phase Artifact Generation

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/project_cost_fact_layer.py --generated-at 2026-06-30T23:30:00+10:00
PASS: KMFA S09-P1 project cost fact layer artifacts written (fact_records=4, cost_categories=9, unallocated_pool=9, formal_report_allowed=false, github_upload_allowed=false)
```

## Phase Validator

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py
PASS: KMFA S09-P1 project cost fact layer check passed (fact_records=4, cost_categories=9, unallocated_pool=9, manual_review_queue=3, unresolved_differences=1, s09_p2_scope=false, s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false)
```

## Final Verification After Rebase

- verified_base_head: `a85145939375a850dd7cdf780bb3c493319ad2e0`
- branch: `codex/kmfa`
- remote: `origin git@github.com:LinzeColin/CodexProject.git`

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py
PASS: KMFA S09-P1 project cost fact layer check passed (fact_records=4, cost_categories=9, unallocated_pool=9, manual_review_queue=3, unresolved_differences=1, s09_p2_scope=false, s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
Ran 92 tests in 1.664s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
CodexProject governance validation
root: checked
projects checked: KMFA
errors: 0
warnings: 0
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
CodexProject governance validation
root: checked
projects checked: KMFA
errors: 0
warnings: 0
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=357, tasks=162, v1.2_html=45+)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PASS: no KMFA Python float money usage found
```

```text
KMFA JSON/JSONL/CSV parse scan
PASS: KMFA parse checks passed (json=79, jsonl=41, csv=24)
```

```text
KMFA raw/private binary scan
PASS: no raw zip/Excel/PDF/sqlite/db files under KMFA
```

```text
KMFA secret scan
PASS: KMFA secret scan found no credential-like patterns
```

```text
git diff --check -- README.md governance/projects.yaml KMFA
PASS: no whitespace errors reported
```

## Scope Boundary

- S09-P1 only.
- S09-P2 and S09-P3 are not executed.
- Stage 9 review is not executed.
- GitHub upload is not executed.
- Raw/private business artifacts are not committed.
