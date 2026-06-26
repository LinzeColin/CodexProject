# AI-Research-System Evidence Decision Matrix

## Purpose

Evidence Decision Matrix is the read-only evidence and decision-grade composition layer for AI-Research-System.

It answers:

> Which local conclusions are `FACT`, `INFERENCE`, `OPINION`, or `OBSERVATION`, and which rows are `Actionable`, `Watch`, `Observe`, or `Reject`?

The matrix combines existing local audit artifacts from:

- Data Trust Layer
- Reconciliation Layer
- Manual Review Queue
- Entity Registry
- Alias Map conflicts

It does not refresh market data, OpenD, moomoo, Alipay uploads, PFIOS, policy bridge, or ResearchBus.

## Command

Recommended run order:

```bash
python3 -m src.cli data-trust-audit --date 2026-06-06
python3 -m src.cli reconciliation-audit --date 2026-06-06
python3 -m src.cli manual-review-audit --date 2026-06-06
python3 -m src.cli entity-registry-audit --date 2026-06-06
python3 -m src.cli evidence-decision-audit --date 2026-06-06
```

JSON mode:

```bash
python3 -m src.cli evidence-decision-audit --date 2026-06-06 --json
```

## Outputs

Outputs are written to:

```text
data/report_artifacts/system_audit/
```

Files:

- `evidence_decision_matrix_YYYY-MM-DD.json`
- `evidence_decision_matrix_YYYY-MM-DD.csv`
- `evidence_decision_matrix_YYYY-MM-DD.md`
- `evidence_decision_matrix_YYYY-MM-DD.pdf`

The PDF is the formal audit report. JSON and CSV keep the full matrix for later dashboards, report gates, and cross-system integration.

## Evidence Classification

| Value | Meaning | Usage |
| --- | --- | --- |
| `FACT` | Directly supported by a local source artifact or audit result. | Strongest evidence class. |
| `INFERENCE` | Derived from multiple facts or rules. | Requires visible assumptions and source links. |
| `OPINION` | Subjective interpretation. | Must not be used as executable decision evidence. |
| `OBSERVATION` | Weak, partial, cached, user-visible, or candidate evidence. | Research context only until confirmed. |

## Decision Grades

| Value | Meaning | Usage |
| --- | --- | --- |
| `Actionable` | Structurally usable inside the research evidence chain. | Not a trading approval. Still needs report and risk gates. |
| `Watch` | Needs stronger evidence or manual review. | Observation or follow-up only. |
| `Observe` | Low-risk context or archived/reference information. | Does not drive action. |
| `Reject` | Failed, missing, conflicting, or unusable evidence. | Blocks executable trading support. |

## Status Logic

- `Blocked`: at least one row is `Reject`, `P0`, or the matrix detects invalid classification values.
- `Review`: no hard blocker, but at least one row is `Watch`, `OBSERVATION`, or `OPINION`.
- `Pass`: all rows are valid and no row needs downgrade.

## Current 2026-06-06 Result

Latest generated matrix:

- Status: `Blocked`
- Rows: `763`
- Source layers: `DataTrust=61`, `Reconciliation=21`, `ManualReview=34`, `EntityRegistry=647`
- Evidence classes: `FACT=159`, `OBSERVATION=604`
- Decision grades: `Actionable=77`, `Observe=23`, `Reject=6`, `Watch=657`

Interpretation:

- `Blocked` is expected because upstream Data Trust and Manual Review still contain active fail-closed blockers.
- The matrix does not fix those blockers. It makes them visible, traceable, and available to later report gates.
- Rows marked `Watch` or `OBSERVATION` can support research context only; they cannot be promoted into trading support without stronger evidence.
- AliasMap rows are absent in the current matrix because Alias Map hardening v1 reduced active alias conflicts from `18` to `0`.

## Validation

Recommended validation:

```bash
PYTHONPATH=. python3 -m pytest tests/test_evidence_decision.py -q
PYTHONPATH=. python3 -m pytest tests/test_evidence_decision.py tests/test_entity_registry.py tests/test_manual_review.py tests/test_reconciliation.py tests/test_data_trust.py tests/test_research_bus_bridge.py -q
python3 -m src.cli evidence-decision-audit --date 2026-06-06 --json
```

Use the Codex bundled Python runtime for tests when system Python lacks `pytest`. Use system Python for CLI generation if bundled Python lacks `certifi`.
