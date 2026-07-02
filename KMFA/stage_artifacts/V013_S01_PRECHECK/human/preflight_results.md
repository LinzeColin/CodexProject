# KMFA v0.1.3 S01-P1 Preflight Results

生成时间: 2026-07-02T14:41:04+10:00

## 命令结果

- `git status --short --branch`
  - `## codex/kmfa...origin/main [ahead 1, behind 6]`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_lineage_report_gate.py`
  - PASS: reports=2, grade_D=2, pending_reconciliation=12, actual_lineage_rows=0, delivery_allowed=false。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_lineage_completeness.py`
  - PASS: lineage completeness gate is safely blocked，field=1、metric=1、report=1、rerun_steps=8、delivery_allowed=false。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_report_grade_gate.py`
  - PASS: quality_grades=Q0-Q5，report_grades=A-D，release_gate=blocked_by_missing_evidence。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - PASS: errors 0 / warnings 0。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - PASS: errors 0 / warnings 0。

## 结论

S01-P1 当前状态复核通过，且只证明当前阻塞状态可追踪。它不修复任何 blocker，不授权 Stage 1 review、GitHub upload、正式报告、经营决策依据、live connector 或业务执行。
