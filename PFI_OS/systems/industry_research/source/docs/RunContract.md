# AI-Research-System Run Contract

## Purpose

Run Contract defines how each Codex run should change AI-Research-System without losing traceability, expanding scope, or weakening evidence quality.

Every run must be small enough to test and review independently.

## One Run, One Target

Each run must declare one target, for example:

- Data Trust Layer v1
- Reconciliation Layer v1
- Manual Review Queue v1
- Entity Registry / Alias Map v1
- Evidence Decision Matrix v1
- Codex Workflow Layer v1
- Report Layer gate integration v1

Do not mix unrelated system changes in the same run.

## Required Start Sequence

Before edits:

1. Read `HANDOFF.md`.
2. Check current files and generated artifacts.
3. Check whether project-level `AGENTS.md` exists.
4. Read only the files needed for the current target.
5. If current files contradict `HANDOFF.md`, trust current files.

If the referenced upgrade report or taskpack is missing from the project folder, state that explicitly and proceed from current project files plus the active user objective.

## Scope Control

Allowed in a normal run:

- Add or update files directly tied to the declared target.
- Add tests for the changed behavior.
- Generate formal audit artifacts for the target.
- Update README, docs, and HANDOFF when the change affects future runs.

Not allowed unless the run target says so:

- Refresh OpenD, moomoo, policy bridge, PFIOS, ResearchBus, or Alipay data.
- Change report generation semantics.
- Rewrite historical reports.
- Delete weak evidence instead of classifying it.
- Add trading execution or broker connection.

## Evidence Rules

Every conclusion or row that enters the audit chain should use:

- Evidence classification: `FACT`, `INFERENCE`, `OPINION`, `OBSERVATION`.
- Decision grade: `Actionable`, `Watch`, `Observe`, `Reject`.
- Review priority when applicable: `P0`, `P1`, `P2`.

Fail-closed rules:

- `Reject` or `P0` blocks executable trading support.
- `Watch` and `OBSERVATION` remain research context only.
- Candidate, cached, fallback, video-derived, or user-unconfirmed data must not be promoted silently.

## Required End Sequence

At the end of each run:

1. Run relevant tests.
2. Run the target CLI command if one exists.
3. Validate generated JSON/CSV/PDF artifacts when produced.
4. Clean local test caches.
5. Update `HANDOFF.md` only if a durable state changed.
6. Report changed files, key decisions, validation, unresolved issues, progress percent, remaining work, time estimate, and remaining run estimate.

## Recommended Commands

```bash
python3 doctor.py --date 2026-06-06 --json
make doctor DATE=2026-06-06
make test-monitoring
make audit-stack DATE=2026-06-06
make test
make clean-cache
```

## Completion Criteria

A run is complete only when:

- The declared target is implemented.
- Required files exist.
- Tests covering the target pass.
- Generated artifacts are valid when the target creates artifacts.
- Residual risks are explicitly stated.

The whole system upgrade is complete only when all requested subsystem layers have current, verified evidence. Partial layer completion must not be reported as full goal completion.
