# KMFA S12-P2 Test Results

## TDD Red

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_manual_impact_preview -q
```

Expected failing result before implementation:

```text
ModuleNotFoundError: No module named 'KMFA.tools.manual_impact_preview'
```

## Phase Validators

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_manual_impact_preview -q
```

Result:

```text
Ran 6 tests in 0.007s
OK
```

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/manual_impact_preview.py --generated-at 2026-07-01T13:00:00+10:00
```

Result:

```text
PASS: KMFA S12-P2 manual impact preview artifacts generated (previews=5, projects=8, metrics=11, reports=5, high_risk=3, blocked_publish=3, rerun=false, formal_report=false, stage12_review=false, github_upload=false)
```

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s12_p2_manual_impact_preview.py
```

Result:

```text
PASS: KMFA S12-P2 manual impact preview passed (previews=5, projects=8, metrics=11, reports=5, high_risk=3, blocked_publish=3, rerun=false, formal_report=false, stage12_review=false, github_upload=false)
```

## Final Validation

Final post-governance validation was completed locally for S12-P2 only. S12-P3,
Stage 12 review, GitHub upload, formal report generation, lineage full check,
and external interfaces were not executed.

```text
PASS: KMFA S12-P2 manual impact preview artifacts generated (previews=5, projects=8, metrics=11, reports=5, high_risk=3, blocked_publish=3, rerun=false, formal_report=false, stage12_review=false, github_upload=false)
PASS: KMFA S12-P2 manual impact preview passed (previews=5, projects=8, metrics=11, reports=5, high_risk=3, blocked_publish=3, rerun=false, formal_report=false, stage12_review=false, github_upload=false)
Ran 144 tests in 1.974s
OK
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=417, tasks=162, v1.2_html=45+)
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
PASS: no KMFA Python float money usage found
PASS: KMFA metadata protocol check passed (dirs=8, files=19, identifiers=5)
PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)
PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)
CodexProject governance validation: errors=0, warnings=0
PASS: KMFA JSON/JSONL parse checks passed
PASS: KMFA YAML parse checks passed
PASS: KMFA CSV UTF-8 and row-length checks passed
PASS: no committed raw/private binary or document artifacts found under KMFA outside taskpack
PASS: no high-signal credential patterns found under KMFA
PASS: S12-P2 machine/html artifacts contain no private-source tokens or private file references
PASS: git diff --check
```
