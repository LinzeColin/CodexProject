# KMFA Stage 1 v1.2 重放验证结果

运行时间: `2026-06-29T18:42:29+10:00`

| 命令 | 结果 |
|---|---|
| `python3 KMFA/tools/check_required_html.py` | `PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).` |
| `python3 KMFA/tools/no_omission_check.py` | `PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=235, tasks=162, v1.2_html=45+)` |
| `python3 -m json.tool KMFA/metadata/baseline/source_package_v1_2.json` | `PASS_JSON_MANIFESTS` |
| `python3 -m json.tool KMFA/metadata/baseline/html_acceptance_samples_v1_2.json` | `PASS_JSON_MANIFESTS` |
| `python3 KMFA/tools/check_report_grade_gate.py` | `PASS: KMFA report grade gate check passed (quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence)` |
| `python3 KMFA/tools/immutability_policy_check.py` | `PASS: KMFA immutability policy check passed (raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes)` |
| `python3 KMFA/tools/metadata_protocol_check.py` | `PASS: KMFA metadata protocol check passed (dirs=8, files=16, identifiers=5)` |
| `python3 scripts/lean_governance.py validate --project KMFA` | `PASS: errors 0 / warnings 0` |
| `python3 scripts/validate_project_governance.py --project KMFA` | `PASS: errors 0 / warnings 0` |
| `git diff --check -- KMFA` | `PASS` |
| `find KMFA -type f ... forbidden raw/binary scan` | `PASS: no forbidden files found` |

## 验证边界

这些验证只证明 v1.2 任务包、HTML 样板、私有源边界和 Stage 1 治理基线已承接。它们不证明 S03 文件导入、金额计算、zero-delta、lineage 或报告生成已经实现。
