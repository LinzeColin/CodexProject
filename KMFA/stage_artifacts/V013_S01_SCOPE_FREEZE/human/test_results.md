# KMFA v0.1.3 S01-P2 Test Results

生成时间: 2026-07-02T14:52:38+10:00

## RED 证据

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s01_p2_scope_freeze -q`
  - RED: `ModuleNotFoundError: No module named 'KMFA.tools.check_v013_s01_p2_scope_freeze'`。

## GREEN 证据

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s01_p2_scope_freeze.py`
  - PASS: actual_lineage_rows=0，pending_reconciliation=12，grade_D=2，delivery_allowed=false，stage_review=false，github_upload=false。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s01_p2_scope_freeze -q`
  - PASS: 1 test passed。

## 最终复跑

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s01_p1_preflight.py`
  - PASS: S01-P1 inherited NO_GO blockers unchanged。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_lineage_report_gate.py`
  - PASS: reports=2，grade_D=2，pending_reconciliation=12，actual_lineage_rows=0，delivery_allowed=false。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_report_grade_gate.py`
  - PASS: release_gate=blocked_by_missing_evidence。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
  - PASS: 281 tests passed。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - PASS: errors 0 / warnings 0。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - PASS: errors 0 / warnings 0。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
  - PASS: errors 0 / warnings 0。

## 结论

S01-P2 范围冻结通过，且只证明 public-safe scope、非范围、停止线和本机 raw boundary 已登记。它不修复 blocker，不授权 S01-P3、Stage 1 review、GitHub upload、正式报告、经营决策依据、live connector 或业务执行。
