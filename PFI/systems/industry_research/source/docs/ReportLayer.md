# AI-Research-System Report Layer

## Purpose

Report Layer turns upstream evidence audits into a formal report-quality gate.

It does not create new market evidence, refresh data, or repair upstream blockers. Its role is to decide how far a formal report is allowed to go:

- `EvidenceChainReady`: no system-level blocker was found in the audit chain.
- `ObservationOnly`: weak evidence exists and must stay clearly labeled as observation or evidence gap.
- `ResearchOnlyBlocked`: P0 or Reject evidence exists; formal reports may be used only for research review and gap tracking.
- `NoFormalResearchUse`: the Evidence Decision Matrix is missing or unreadable.

This layer improves report safety, traceability, and downgrade discipline.

## Inputs

Primary input:

```text
data/report_artifacts/system_audit/evidence_decision_matrix_YYYY-MM-DD.json
```

The matrix is authoritative for:

- Evidence classification: `FACT`, `INFERENCE`, `OPINION`, `OBSERVATION`.
- Decision grade: `Actionable`, `Watch`, `Observe`, `Reject`.
- Priority: `P0`, `P1`, `P2`.
- Blocker count, weak-evidence count, and user-confirmation requirements.

## Command

```bash
python3 -m src.cli report-layer-audit --date 2026-06-06
python3 -m src.cli report-layer-audit --date 2026-06-06 --json
```

Full audit stack:

```bash
make audit-stack DATE=2026-06-06
```

## Outputs

```text
data/report_artifacts/system_audit/report_layer_audit_YYYY-MM-DD.json
data/report_artifacts/system_audit/report_layer_audit_YYYY-MM-DD.csv
data/report_artifacts/system_audit/report_layer_audit_YYYY-MM-DD.md
data/report_artifacts/system_audit/report_layer_audit_YYYY-MM-DD.pdf
```

The JSON is the machine-readable source. The PDF is the formal audit output.

## Quality Gate Behavior

`src.reporting.quality_gate.run_report_quality_gate()` now includes Report Layer issues.

Priority order:

1. If `report_layer_audit_YYYY-MM-DD.json` exists, use its `quality_gate_issues`.
2. Otherwise, if `evidence_decision_matrix_YYYY-MM-DD.json` exists, derive Report Layer issues from the matrix.
3. If neither exists for an older date, do not invent a blocker.

Fail-closed rules:

- `P0`, `Reject`, or `blocker_count > 0` forces `ResearchOnlyBlocked`.
- `Watch`, `OBSERVATION`, or `OPINION` forces review language and weak-evidence labeling.
- Missing matrix forces `NoFormalResearchUse`.

## Required Report Language

When blocked:

```text
当前报告仅可作为研究复盘和证据缺口清单，不能作为交易执行依据。
```

When review is required:

```text
当前结论需要更多证据或人工复核后才能提高置信等级。
```

When passed:

```text
当前审计层未发现系统级阻断；仍需单份报告质量门禁通过。
```

## Current 2026-06-06 Result

- Status: `Blocked`
- Conclusion ceiling: `ResearchOnlyBlocked`
- Gate rows: 4
- Status counts: `Blocked=2`, `Review=2`
- Decision counts: `Reject=2`, `Watch=2`
- Priority counts: `P0=2`, `P1=2`
- Upstream matrix rows: 763
- Quality gate issues: 2

Interpretation:

- Formal reports remain usable for research review, evidence-gap tracking, and post-run audit.
- They must not be presented as executable trading support while upstream P0 / Reject blockers remain.
- Weak rows must stay labeled as observation or evidence gap.

## Tests

Relevant tests:

```bash
python3 -m pytest tests/test_report_layer.py -q
make test-monitoring
make audit-stack DATE=2026-06-06
```

The current implementation is intentionally conservative. It downgrades conclusions rather than hiding or repairing weak evidence.
