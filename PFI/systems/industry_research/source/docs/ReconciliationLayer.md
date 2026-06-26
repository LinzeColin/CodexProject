# AI-Research-System Reconciliation Layer

## Purpose

Reconciliation Layer is the read-only file-to-file audit layer for AI-Research-System.

It answers:

> Do the local files that support research reports actually agree with each other?

The layer compares local artifacts only. It does not refresh OpenD, open moomoo, parse new Alipay uploads, generate reports, submit ResearchBus requests, or change report content.

## Command

```bash
python3 -m src.cli reconciliation-audit --date 2026-06-06
python3 -m src.cli reconciliation-audit --date 2026-06-06 --json
```

## Outputs

Outputs are written to:

```text
data/report_artifacts/system_audit/
```

Files:

- `reconciliation_audit_YYYY-MM-DD.json`
- `reconciliation_audit_YYYY-MM-DD.csv`
- `reconciliation_audit_YYYY-MM-DD.md`
- `reconciliation_audit_YYYY-MM-DD.pdf`

The PDF is the formal audit report. JSON and CSV are machine-readable evidence for automation and cross-system coordination.

## Checked Domains

Current v1 checks:

- Data Trust audit exists.
- Data Trust `record_count` matches actual `records`.
- Data Trust `status_counts` matches row statuses.
- Data Trust JSON/CSV/Markdown/PDF output bundle exists.
- Data Trust CSV rows match JSON records.
- Data Trust source file hashes still match current local files.
- Active `REJECTED` Data Trust rows are surfaced as fail-closed blockers.
- Source logs are covered by Data Trust.
- Source logs have matching internal Markdown artifacts.
- Source logs have matching formal PDF reports.
- ResearchBus bridge export files exist and use `ResearchBusV1`.
- PFIOS bridge rows with `Review`, `Blocked`, `NeedsMoreEvidence`, `DataQualityReview`, or `DoNotUse` are downgraded.
- Policy bridge status files have matching event CSV files when matched events exist.
- Current-date automation health files exist and do not contain `fail`.
- `HANDOFF.md` and `README.md` record the current evidence layer.

## Status Meaning

| Status | Meaning | Decision Impact |
| --- | --- | --- |
| `pass` | Files agree for this check. | Can proceed to next audit layer. |
| `warn` | Evidence exists but is incomplete, weak, cached, or needs review. | Use for observation only. |
| `fail` | Evidence chain is broken or actively rejected. | Blocks executable trading support. |

## Severity

| Severity | Meaning |
| --- | --- |
| `P0` | Must block executable use until fixed. |
| `P1` | Must be reviewed before formal decision support. |
| `P2` | Workflow/documentation or lower-risk quality issue. |

## Fail-Closed Rules

- Any Data Trust `REJECTED` row creates a Reconciliation `fail`.
- If a source log lacks a formal PDF or internal Markdown companion, it cannot prove a formal report.
- If current-date automation health fails, related reports cannot support executable trading actions.
- If PFIOS bridge rows are weak or blocked, they can only support observation or further validation.
- Missing ResearchBus bridge files means cross-system state should not be treated as synchronized.

## Validation

Recommended validation after changes:

```bash
PYTHONPATH=. python3 -m pytest tests/test_reconciliation.py -q
PYTHONPATH=. python3 -m pytest tests/test_reconciliation.py tests/test_data_trust.py tests/test_quality_gate.py tests/test_research_bus_bridge.py -q
python3 -m src.cli reconciliation-audit --date 2026-06-06 --json
```

Use the Codex bundled Python runtime for tests when system Python lacks `pytest`. Use system Python for CLI generation if bundled Python lacks `certifi`.
