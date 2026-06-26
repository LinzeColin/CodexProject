# AGENTS.md

## Project

AI-Research-System is a local personal equity research, portfolio evidence, report generation, and decision-quality control system.

The system is research-only. It must not place real trades, submit broker orders, transfer money, or connect to live execution.

## Run Contract

Each Codex run must have one clear target.

Before editing:

1. Read `HANDOFF.md`.
2. Check current real files and generated artifacts.
3. If `HANDOFF.md` conflicts with current files or user instructions, trust current files and the latest user instruction.
4. Read only the context needed for the current run.

During editing:

- Keep changes scoped to the run target.
- Prefer existing project patterns and CLI entrypoints.
- Use fail-closed behavior for weak, stale, missing, or conflicting evidence.
- Do not refresh OpenD, moomoo, Alipay, policy bridge, PFIOS, or ResearchBus unless the run explicitly targets that refresh.
- Do not silently promote `Watch`, `Observe`, `OBSERVATION`, candidate, cached, or video-derived evidence into actionable conclusions.

At the end of every run, report:

- Changed files.
- Key decisions.
- Validation commands and results.
- Unresolved issues.
- Current overall progress percent.
- Remaining work.
- Estimated remaining time and run count.

## Evidence Rules

All research conclusions and system audit rows must use:

- Evidence classification: `FACT`, `INFERENCE`, `OPINION`, `OBSERVATION`.
- Decision grade: `Actionable`, `Watch`, `Observe`, `Reject`.
- Data trust status where applicable: `RAW_IMPORTED`, `PARSED_CANDIDATE`, `NEEDS_REVIEW`, `USER_CONFIRMED`, `RECONCILED`, `ARCHIVED`, `REJECTED`.

Meaning:

- `Actionable` means usable inside the research evidence chain; it is not trading approval.
- `Reject` or `P0` blocks executable trading support.
- `Watch` and `OBSERVATION` are research context only until stronger evidence exists.

## Required Local Checks

Preferred command entrypoints:

```bash
python3 doctor.py --date 2026-06-06 --json
make doctor DATE=2026-06-06
make test-monitoring
make audit-stack DATE=2026-06-06
make test
```

Known runtime detail:

- System Python usually has `certifi` and `reportlab`, but may not have `pytest`.
- Codex bundled Python usually has `pytest`, but may need the system site-packages path appended for `certifi`.
- Use the exact test wrapper in `Makefile` when system Python lacks `pytest`.

## Output Rules

Formal audit/report outputs should include PDF when practical.

System audit outputs belong under:

```text
data/report_artifacts/system_audit/
```

The public formal report directory is:

```text
~/Downloads/行研报告
```

Do not put sensitive account details, API keys, passwords, or full private records in `HANDOFF.md`, docs, or chat summaries.

## Boundaries

Forbidden unless explicitly requested in a separate scoped run:

- Real trading or broker order submission.
- Payment, transfer, or account mutation.
- Rewriting historical reports to hide missing evidence.
- Deleting weak evidence instead of classifying it.
- Treating generated PDFs as proof unless source logs and gates also pass.
