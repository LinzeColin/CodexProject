# AI-Research-System Data Trust Layer

## Purpose

Data Trust Layer is the read-only evidence audit layer for AI-Research-System.

It answers one operational question:

> Which local files can support research conclusions, which files are only candidates, and which files must be manually reviewed before they affect reports or decisions?

This layer does not refresh market data, call OpenD, open moomoo, parse new Alipay uploads, generate trading instructions, or change existing report production logic.

## Command

```bash
python3 -m src.cli data-trust-audit --date 2026-06-06
python3 -m src.cli data-trust-audit --date 2026-06-06 --json
```

## Outputs

Outputs are written to:

```text
data/report_artifacts/system_audit/
```

Files:

- `data_trust_audit_YYYY-MM-DD.json`
- `data_trust_audit_YYYY-MM-DD.csv`
- `data_trust_audit_YYYY-MM-DD.md`
- `data_trust_audit_YYYY-MM-DD.pdf`

The PDF is the formal human-readable audit report. JSON and CSV are machine-readable evidence for later automation and cross-system integration.

## Audited Sources

Current v1 checks:

- Report source logs under `data/report_artifacts/**/_source_logs/*.json`
- Matching internal Markdown reports under `data/report_artifacts/**/_markdown/`
- Matching formal PDFs under `~/Downloads/行研报告/`
- Local sample/watchlist CSV files
- Private Alipay positions, candidates, pending orders, trade ledger, import log, and raw transaction files
- Automation health JSON files
- Policy bridge status files
- ResearchBus bridge JSON files
- PFIOS bridge JSON files
- PFIOS validation summaries

## Status Definitions

| Status | Meaning | Allowed Use |
| --- | --- | --- |
| `RAW_IMPORTED` | Raw imported evidence kept for traceability. | Trace only; not enough for action conclusion. |
| `PARSED_CANDIDATE` | Parsed evidence candidate. | Research context only. |
| `NEEDS_REVIEW` | Needs manual review or stronger source confirmation. | Downgrade conclusion; no action upgrade. |
| `USER_CONFIRMED` | User-confirmed or official-export evidence. | Account and holding fact layer. |
| `RECONCILED` | Has required companion evidence for this audit. | Can enter report evidence chain. |
| `ARCHIVED` | Historical archived evidence. | Background only. |
| `REJECTED` | Failed, conflicting, or unusable evidence. | Blocks corresponding conclusion. |

## Decision Grades

| Grade | Meaning |
| --- | --- |
| `Actionable` | The artifact can support a report fact or operational check. It still does not authorize live trading. |
| `Watch` | The artifact has value but needs manual review, stronger source confirmation, or companion evidence. |
| `Observe` | The artifact can provide background context only. |
| `Reject` | The artifact must not support conclusions until fixed. |

## Fail-Closed Rules

- `NEEDS_REVIEW` or `REJECTED` artifacts must not increase buy/sell confidence, Volume, or suggested amount.
- Video-visible Alipay holdings remain review evidence unless confirmed by official export or explicit user confirmation.
- Cached policy bridge results remain candidate evidence until original source URL, crawler request, report path, and operation impact are verified.
- PFIOS rows marked `Review`, `Blocked`, `NeedsMoreEvidence`, `DataQualityReview`, or `DoNotUse` must downgrade research conclusions.
- Automation health `warn` or `fail` must be surfaced before report outputs are used for decision support.

## Validation

Recommended validation after changes:

```bash
PYTHONPATH=. python3 -m pytest tests/test_data_trust.py -q
PYTHONPATH=. python3 -m pytest tests/test_data_trust.py tests/test_quality_gate.py tests/test_research_bus_bridge.py -q
python3 -m src.cli data-trust-audit --date 2026-06-06 --json
```

Use the Codex bundled Python runtime when system Python lacks `pytest`.
