# KMFA v0.1.3 S01-P1 Test Results

生成时间: 2026-07-02T14:43:03+10:00

## 当前已通过

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s01_p1_preflight.py`
  - PASS: version_file=`0.1.0-post-s18-final-no-go-backup-upload`，governance_version=`0.1.3-s01p1-current-state-preflight`，actual_lineage_rows=0，pending_reconciliation=12，grade_D=2，delivery_allowed=false。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s01_p1_preflight -q`
  - PASS: 1 test passed。

## 最终复跑

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_lineage_report_gate.py`
  - PASS: reports=2，grade_D=2，pending_reconciliation=12，actual_lineage_rows=0，delivery_allowed=false。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_lineage_completeness.py`
  - PASS: lineage completeness gate remains safely blocked。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_report_grade_gate.py`
  - PASS: release_gate=blocked_by_missing_evidence。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
  - PASS: 280 tests passed。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - PASS: errors 0 / warnings 0。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - PASS: errors 0 / warnings 0。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
  - PASS: errors 0 / warnings 0。
- Structured parse check
  - PASS: json=2，jsonl=1，csv=2。
- Raw/private path scan
  - PASS: changed_or_untracked=45，无 raw/private path、zip、Excel workbook、PDF、sqlite/db 或未批准 CSV。
- High-signal secret scan
  - PASS: scanned_files=22，无 private key、OpenAI key、GitHub token 或 AWS key pattern。
- `git diff --check -- KMFA scripts`
  - PASS: no output。

## 结论

S01-P1 当前状态复核通过，且只证明当前阻塞状态可追踪。它不修复任何 blocker，不授权 S01-P2、Stage 1 review、GitHub upload、正式报告、经营决策依据、live connector 或业务执行。本文件只记录 public-safe 命令与结论，不包含 raw business data、字段明文、zip、Excel workbook、PDF、private CSV、sqlite/db、credentials、银行流水、合同、薪资或税务申报材料。
