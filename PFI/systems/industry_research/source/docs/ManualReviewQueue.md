# AI-Research-System Manual Review Queue

## Purpose

Manual Review Queue converts weak, conflicting, missing, or high-risk evidence into a concrete queue.

It answers:

> What exactly needs to be reviewed before the system can use these artifacts for formal decision support?

The queue is read-only. It does not refresh OpenD, open moomoo, parse new Alipay uploads, edit reports, submit ResearchBus requests, or execute trades.

## Command

```bash
python3 -m src.cli manual-review-audit --date 2026-06-06
python3 -m src.cli manual-review-audit --date 2026-06-06 --json
```

Run order:

```bash
python3 -m src.cli data-trust-audit --date 2026-06-06
python3 -m src.cli reconciliation-audit --date 2026-06-06
python3 -m src.cli manual-review-audit --date 2026-06-06
```

## Outputs

Outputs are written to:

```text
data/report_artifacts/system_audit/
```

Files:

- `manual_review_queue_YYYY-MM-DD.json`
- `manual_review_queue_YYYY-MM-DD.csv`
- `manual_review_queue_YYYY-MM-DD.md`
- `manual_review_queue_YYYY-MM-DD.pdf`

The PDF is the formal review queue report. JSON and CSV are machine-readable inputs for later dashboard, ticketing, or ResearchBus integration.

## Queue Fields

| Field | Meaning |
| --- | --- |
| `review_id` | Stable local identifier for the queue item. |
| `queue_status` | Current queue state. v1 emits `Open`. |
| `priority` | `P0`, `P1`, or `P2`. |
| `source_layer` | Origin layer, usually `DataTrust` or `Reconciliation`. |
| `source_domain` | Domain such as `csv_artifact`, `data_trust`, `report_chain`, `pfi_os_bridge`, or `automation`. |
| `item_name` | File name, check name, or review item name. |
| `item_status` | Original status such as `NEEDS_REVIEW`, `REJECTED`, `fail`, or `warn`. |
| `evidence_classification` | `FACT`, `OBSERVATION`, `INFERENCE`, or `OPINION`. |
| `decision_grade` | `Actionable`, `Watch`, `Observe`, or `Reject`. |
| `user_confirmation_required` | Whether the user must confirm account, holding, video, or pending-order evidence. |
| `blocker_scope` | What downstream use is blocked or downgraded. |
| `issue` | Concrete issue found by previous audit layers. |
| `next_action` | Next practical action. |
| `owner` | `User` or `System`. |
| `source_paths` | Files proving the issue. |

## Priority Rules

| Priority | Meaning | Action |
| --- | --- | --- |
| `P0` | Blocks executable trading support. | Fix first or keep reports as research-only context. |
| `P1` | Requires review before formal decision support. | Review, confirm, repair source chain, or downgrade. |
| `P2` | Workflow/documentation quality issue. | Fix in Codex Workflow Layer or later hardening run. |

## User Confirmation Rules

The queue marks `user_confirmation_required=true` when the evidence relates to:

- Alipay / 支付宝
- Current positions / 持仓
- Pending orders / 待确认
- Video-visible or screen-recorded evidence
- Account evidence / 账户证据

These items must not be promoted into account facts, holding facts, or executable decision support until the user confirms them or provides stronger official-export evidence.

## Validation

Recommended validation:

```bash
PYTHONPATH=. python3 -m pytest tests/test_manual_review.py -q
PYTHONPATH=. python3 -m pytest tests/test_manual_review.py tests/test_reconciliation.py tests/test_data_trust.py tests/test_quality_gate.py tests/test_research_bus_bridge.py -q
python3 -m src.cli manual-review-audit --date 2026-06-06 --json
```

Use the Codex bundled Python runtime for tests when system Python lacks `pytest`. Use system Python for CLI generation if bundled Python lacks `certifi`.
